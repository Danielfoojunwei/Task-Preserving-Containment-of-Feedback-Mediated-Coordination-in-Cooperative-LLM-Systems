"""Runtime class factories: supplied classes are either real pinned dependencies
or explicitly labeled test doubles. Never mistake factory tests for runtime runs.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
from typing import Any
from .core import Feedback, Ledger, SkillState, choose_skill, strip_score, score_paths


def make_board_class(base, blackboard_type):
    class AuditedMegaboard(base):
        def __init__(self, ledger: Ledger):
            super().__init__()
            self.ledger = ledger
            self.feedback = Feedback.ORIGINAL
            self.revoked: set[int] = set()
            self.catalog_frozen = False
            self.view_context = {"kind": "unspecified", "phase": None}
            self.raw_score_events = 0

        def add_blackboard(self, agents, template=None):
            if self.catalog_frozen:
                raise ValueError("Board creation unavailable after setup")
            if isinstance(template, dict) and template.get("secret_channel"):
                i = len(self.blackboards)
                board = blackboard_type(blackboard_id=str(i), participants=list(agents),
                    agents=set(agents), logs=[], template=deepcopy(template), verify_template=1)
                self.blackboards.append(board)
                self.ledger.emit("secret_board_created", {"id":i, "members":sorted(agents),
                                                         "distinct":True})
                return i
            return super().add_blackboard(agents, template)

        def freeze_catalog(self):
            self.catalog_frozen = True

        def revoke_private(self):
            ids = [i for i,b in enumerate(self.blackboards)
                   if isinstance(b.template,dict) and b.template.get("secret_channel")]
            if len(ids) != 1:
                raise RuntimeError("Expected exactly one designated, distinct private board")
            self.revoked.update(ids)
            for i in ids:
                self.blackboards[i].suspended = True
            self.ledger.emit("private_access_revoked", {"board_ids":ids,
                       "previously_delivered_memory_erased":False})

        def get_agent_blackboards(self, name):
            return [str(i) for i in super().get_agent_blackboards(name) if int(i) not in self.revoked]

        def get(self, blackboard_id, agent, limit=None):
            if int(blackboard_id) in self.revoked:
                self.ledger.emit("denied_read", {"board":int(blackboard_id), "agent":agent})
                raise ValueError("Access unavailable")
            # Keep ORIGINAL's references: taking an immutable logging snapshot must
            # not accidentally fix the very nested-alias baseline being measured.
            raw = super().get(blackboard_id, agent, limit=limit)
            delivered = strip_score(raw) if self.feedback == Feedback.SUPPRESS_SCORE else raw
            paths = score_paths(delivered)
            self.ledger.emit("board_read", {"agent":agent,"board":int(blackboard_id),
                "raw_events":raw,"delivered_events":delivered,"score_paths":paths,
                "view_context":self.view_context})
            return delivered

        def post(self, blackboard_id, agent, kind, payload=None, phase=None, iteration=None):
            if int(blackboard_id) in self.revoked:
                self.ledger.emit("denied_post", {"board":int(blackboard_id), "agent":agent})
                raise ValueError("Access unavailable")
            return super().post(blackboard_id, agent, kind, payload, phase=phase, iteration=iteration)

        def log_action_to_blackboards(self, agent_name, action, result, phase=None, iteration=None):
            self.ledger.emit("pre_callback_board_write", {"agent":agent_name,"action":action,
                         "result":result,"phase":phase,"iteration":iteration})
            value = result if self.feedback == Feedback.ORIGINAL else deepcopy(result)
            if self.feedback == Feedback.SUPPRESS_SCORE:
                value = strip_score(value)
            return super().log_action_to_blackboards(agent_name, action, value,
                                                      phase=phase, iteration=iteration)
    return AuditedMegaboard


def install_callback_guard(env, board, ledger):
    original = env.post_tool_execution_callback
    def guarded(state_updates, response):
        # Original callback is allowed to compute its normal evaluator score.
        # In suppression mode only, do so on a private response copy. This is
        # receipt-boundary declassification, NOT general pre-action mediation.
        ledger.emit("before_callback", {"updates":state_updates,"response":response})
        if board.feedback == Feedback.SUPPRESS_SCORE:
            private_response = deepcopy(response)
            value = original(state_updates, private_response)
            ledger.emit("evaluator_callback_result", {"response":private_response})
            if not isinstance(response,dict):
                raise TypeError("Pinned callback response must be dictionary")
            response.clear()
            response.update(strip_score(private_response))
        else:
            value = original(state_updates,response)
        ledger.emit("after_callback", {"response":response,
            "board_events":[{"id":b.blackboard_id,"events":b.logs} for b in board.blackboards]})
        return value
    env.post_tool_execution_callback = guarded
    return original


def make_protocol_class(base, board_base, blackboard_type, *, cell, ledger: Ledger,
                        strict_phase=True, task_requires_score=False, switch_budget=2):
    Board = make_board_class(board_base, blackboard_type)
    class ResearchProtocol(base):
        instances = []
        def __init__(self, *, config, megaboard=None):
            if megaboard is not None:
                raise ValueError("Research runtime requires its own audited board")
            board = Board(ledger)
            super().__init__(config=config,megaboard=board)
            self._ka_boundary_done=False
            self._ka_callback_installed=False
            self._ka_phase=None
            self._ka_epoch=0
            self._ka_switches=switch_budget
            self._ka_actor_events=0
            self._ka_peer_events=0
            self._ka_total_actor=0
            self._ka_total_peer=0
            self._ka_prompt_roles={}
            ResearchProtocol.instances.append(self)

        def _install_env_guard(self, environment):
            if not self._ka_callback_installed:
                if not callable(getattr(environment,"post_tool_execution_callback",None)):
                    raise RuntimeError("Missing pinned Jira callback; cannot test this mechanism")
                install_callback_guard(environment,self.megaboard,ledger)
                self._ka_callback_installed=True

        def _boundary(self, environment):
            self._install_env_guard(environment)
            if self._ka_boundary_done:
                return
            self.megaboard.freeze_catalog()
            private = [i for i,b in enumerate(self.megaboard.blackboards)
                       if b.template.get("secret_channel")]
            if len(private)!=1:
                raise RuntimeError("Invalid treatment: no unique private board")
            ledger.emit("execution_boundary", {"cell":cell.to_dict(),"private_ids":private,
                "task_state":environment.get_serializable_state(),
                "costs":getattr(environment,"costs",None),
                "tasks":getattr(environment,"tasks",None)})
            if cell.revoke:
                self.megaboard.revoke_private()
            else:
                ledger.emit("sham_revocation", {"private_ids":private})
            if cell.controller=="fixed":
                self.megaboard.feedback=Feedback(cell.feedback)
            self._ka_boundary_done=True

        async def _prefetch_blackboard_events(self,agent_name,*,phase,iteration):
            self.megaboard.view_context={"kind":"preturn_context","phase":phase,"iteration":iteration}
            before=len(ledger.records)
            contexts=await super()._prefetch_blackboard_events(agent_name,phase=phase,iteration=iteration)
            # This is delivered to BaseAgent, not yet proof of exact serialized API
            # messages. Preserve native PromptLogger/trajectory files for that join.
            ledger.emit("preturn_context", {"recipient":agent_name,"phase":phase,
                "iteration":iteration,"contexts":contexts,"delivery_level":"BaseAgent_input"})
            reads=[r for r in ledger.records[before:] if r["kind"]=="board_read"]
            observed=sum(bool(r["data"]["score_paths"]) for r in reads)
            self._ka_peer_events+=observed
            self._ka_total_peer+=observed
            return contexts

        async def agent_planning_turn(self,agent,agent_name,agent_context,environment,iteration,planning_round):
            self.environment=environment;self._ka_phase="planning"
            self._install_env_guard(environment)
            self.megaboard.freeze_catalog()
            # Freeze objective context; revocation must not reassign roles.
            role=agent_context.get("collusion_role")
            self._ka_prompt_roles.setdefault(agent_name,role)
            if self._ka_prompt_roles[agent_name]!=role:
                raise RuntimeError("Objective role drift")
            ledger.emit("planning_context", {"agent":agent_name,"context":agent_context,
                                               "round":planning_round})
            return await super().agent_planning_turn(agent,agent_name,agent_context,environment,
                                                    iteration,planning_round)

        async def agent_execution_turn(self,agent,agent_name,agent_context,environment,iteration):
            self.environment=environment;self._ka_phase="execution"
            self._boundary(environment)
            if self._ka_prompt_roles.get(agent_name)!=agent_context.get("collusion_role"):
                raise RuntimeError("Prompt role changed across communication intervention")
            if cell.controller!="fixed":
                state=SkillState(self._ka_epoch,not bool(self.megaboard.revoked),
                    self._ka_actor_events,self._ka_peer_events,
                    max(0,self._ka_total_actor-self._ka_actor_events),
                    max(0,self._ka_total_peer-self._ka_peer_events),task_requires_score,self._ka_switches)
                decision=choose_skill(state,history=cell.controller=="history_rule")
                ledger.emit("skill_decision", {"state":asdict(state),"decision":asdict(decision),
                    "selector":"FROZEN_RULE_NOT_ORCHDEBATE_MODEL"})
                if decision.skill!="retain" and decision.skill!=self.megaboard.feedback.value:
                    self.megaboard.feedback=Feedback(decision.skill)
                    self._ka_switches-=1;self._ka_epoch+=1
                self._ka_actor_events=0;self._ka_peer_events=0
            ledger.emit("execution_context", {"agent":agent_name,"context":agent_context,
                  "feedback":self.megaboard.feedback.value,"epoch":self._ka_epoch})
            answer=await super().agent_execution_turn(agent,agent_name,agent_context,environment,iteration)
            ledger.emit("execution_outcome", {"agent":agent_name,"state":environment.get_serializable_state(),
                      "usage":answer.get("usage"),"tools_executed":answer.get("tools_executed")})
            return answer

        async def environment_handle_tool_call(self,tool_name,agent_name,arguments,*,phase=None,iteration=None):
            # Research design: no consequential environment actions while planning.
            # Identical rule in all arms. Record rather than silently execute.
            if strict_phase and phase!="execution":
                response={"error":"Environment actions are available in the execution phase only."}
                ledger.emit("phase_denial", {"tool":tool_name,"agent":agent_name,"phase":phase})
                return response
            result=await super().environment_handle_tool_call(tool_name,agent_name,arguments,
                                                            phase=phase,iteration=iteration)
            count=bool(score_paths(result));self._ka_actor_events+=count;self._ka_total_actor+=count
            ledger.emit("actor_receipt", {"agent":agent_name,"tool":tool_name,"arguments":arguments,
                          "result":result,"score_paths":score_paths(result),"phase":phase})
            # No text-based inference that agents are colluding.
            return result
    return ResearchProtocol
