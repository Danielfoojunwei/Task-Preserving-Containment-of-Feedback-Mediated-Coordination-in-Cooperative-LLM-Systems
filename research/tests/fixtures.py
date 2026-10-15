"""EXPLICIT fixtures for tests; these are not installed Terrarium/Colosseum."""
from dataclasses import dataclass,field
from copy import deepcopy
import json
from tests.vendor.jira_ticket_tools_v011 import JiraTicketTools

@dataclass
class BoardFixture:
    blackboard_id: str="-1"
    participants:list=field(default_factory=list)
    agents:set=field(default_factory=set)
    logs:list=field(default_factory=list)
    template:dict=field(default_factory=dict)
    verify_template:int=0
    suspended:bool=False

class MegaboardFixture:
    def __init__(self):self.blackboards=[]
    def add_blackboard(self,agents,template=None):
        for i,b in enumerate(self.blackboards):
            if b.agents==set(agents):return i
        i=len(self.blackboards);self.blackboards.append(BoardFixture(str(i),list(agents),set(agents),[],template or {}));return i
    def get_agent_blackboards(self,name):
        return [str(i) for i,b in enumerate(self.blackboards) if name in b.agents and not b.suspended]
    def get(self,i,agent,limit=None):
        b=self.blackboards[int(i)]
        if agent not in b.agents:raise ValueError('nonmember')
        return b.logs[-limit:] if limit else b.logs
    def post(self,i,agent,kind,payload=None,phase=None,iteration=None):
        b=self.blackboards[int(i)]
        if b.suspended or agent not in b.agents:raise ValueError('denied')
        b.logs.append({'agent':agent,'kind':kind,'payload':payload or {}});return str(len(b.logs))
    def post_system_message(self,i,kind,payload):
        self.blackboards[i].logs.append({'agent':'SYSTEM','kind':kind,'payload':payload})
    def log_action_to_blackboards(self,agent_name,action,result,phase=None,iteration=None):
        payload={'action_type':action.get('action'),'action_params':action.copy(),
                 'result_status':result.get('status'),'details':result.copy()}
        for i,b in enumerate(self.blackboards):
            if agent_name in b.agents and not b.suspended:self.post(i,agent_name,'action_executed',payload)

class EnvironmentFixture:
    def __init__(self):
        self.tasks={'X':{'priority':'high'},'Y':{'priority':'high'}}
        self.assignment={};self.agent_names=['A','B','C','D']
        self.costs={a:{'X':8.,'Y':9.} for a in self.agent_names}
        self.prompts=None
    def get_agent_names(self):return self.agent_names
    def get_serializable_state(self):return {'tasks':self.tasks,'assignment':self.assignment.copy(),'agent_names':self.agent_names}
    def apply_state_updates(self,s):self.assignment.update(s.get('assignment',{}))
    def _rewards(self,a):
        vals={k:(35-self.costs[k][v] if v not in (None,'skip') else 0.) for k,v in a.items()}
        used=[v for v in a.values() if v not in (None,'skip')]
        penalty=100*(len(used)-len(set(used)))
        return sum(vals.values())-penalty,vals
    def joint_reward(self,a):return self._rewards(a)[0]
    def post_tool_execution_callback(self,updates,response):
        if 'assignment' in updates and 'result' in response:response['result']['joint_reward']=self.joint_reward(self.assignment)
    def get_final_summary(self):return {'assignment':self.assignment.copy(),'joint_reward':self.joint_reward(self.assignment)}

class ProtocolFixture:
    def __init__(self,*,config,megaboard):self.config=config;self.megaboard=megaboard;self.environment=None;self.tool_events=[]
    async def generate_comm_network(self,participants,context,template=None):
        i=self.megaboard.add_blackboard(list(participants),template)
        self.megaboard.post_system_message(i,'context',{'message':context});return i
    async def _prefetch_blackboard_events(self,agent_name,*,phase,iteration):
        return {i:json.dumps(self.megaboard.get(int(i),agent_name,limit=None))
                for i in self.megaboard.get_agent_blackboards(agent_name)}
    async def environment_handle_tool_call(self,tool_name,agent_name,arguments,*,phase=None,iteration=None):
        e=self.environment;r=JiraTicketTools(self.megaboard).handle_tool_call(tool_name,agent_name,arguments,
                           phase=phase,iteration=iteration,env_state=e.get_serializable_state())
        updates=r.get('state_updates') or r.get('result',{}).get('state_updates')
        if updates:e.apply_state_updates(updates);e.post_tool_execution_callback(updates,r)
        self.tool_events.append(deepcopy(r));return r
    async def agent_planning_turn(self,agent,agent_name,agent_context,environment,iteration,planning_round):
        self.environment=environment
        await self._prefetch_blackboard_events(agent_name,phase='planning',iteration=iteration)
        return {'response':'fixture planning','usage':None}
    async def agent_execution_turn(self,agent,agent_name,agent_context,environment,iteration):
        self.environment=environment
        await self._prefetch_blackboard_events(agent_name,phase='execution',iteration=iteration)
        result=await self.environment_handle_tool_call('assign_task',agent_name,{'task_id':agent},phase='execution',iteration=iteration)
        return {'response':result,'usage':None,'tools_executed':1}
