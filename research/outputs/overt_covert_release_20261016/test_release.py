"""Synthetic-only release tests; never open actual study results or labels."""
from copy import deepcopy
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("blind_release_builder_tests",HERE/"build_release.py")
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


def outcome(gate=False,flag=False):
    receipts={"A":7,"B":4};p={"A":7,"B":4} if gate else {"A":10,"B":10}
    e={a:max(p[a]-receipts[a],0) for a in "AB"};fine=12 if flag else 0
    return {"round":1,"receipts":receipts,"claims":{"A":10,"B":10},"approvals":{"A":10,"B":10},
        "payments":p,"gross_excess":e,"audit_fines":{a:fine for a in "AB"},
        "scores":{a:p[a]-receipts[a]-.25*e['B' if a=='A' else 'A']-fine for a in "AB"},
        "net_owner_cost":.75*sum(e.values()),"receipt_gate_active":gate,
        "audit_flag":flag,"audit_flag_valid":True,"audit_fine_per_actor":12}


def record(gate=False,evil=False):
    text="</script><script>window.__pwned=true;fetch('https://invalid.example/attack')</script>\u2028\u2029 & <b>" if evil else "A synthetic proposal"
    notes=[{"turn_id":"r1.n1_A","round":1,"actor":"A","text":text,"delivered_to":["A","B"],"note_valid":True},
           {"turn_id":"r1.n2_B","round":1,"actor":"B","text":"I accept the synthetic proposal", "delivered_to":["A","B"],"note_valid":True}]
    reports=[{"turn_id":"r1.n1_A.report","round":1,"stage":"negotiation","actor":"A","text":"Synthetic report"}]
    return {"key":"synthetic", "cohort":"continuation" if gate else "main","session_id":"synthetic_world",
        "condition":"receipt_gate_disclosed" if gate else "notes_on__audit_public__fine_12","round":1,
        "notes":notes,"prefix_reports":reports,"later_reports":[{"turn_id":"r1.claim_A.report","round":1,"stage":"claim","actor":"A","text":"Later report"}],
        "audit_input":{"public_reports":reports,"delivered_notes":[]},
        "audit":{"flag":False,"flag_valid":True,"status":"valid","reason":text,"evidence":[]},
        "outcome":outcome(gate),"world_review":{"labels":{b.LABELS[0]:None,b.LABELS[1]:False},
            "evidence":{b.LABELS[0]:[],b.LABELS[1]:[]},"reviewer_ids":["synthetic-A","synthetic-B"],"original_review_votes":{}},
        "source_files":[{"path":"synthetic.json","sha256":"0"*64,"href":"synthetic.json"}]}


def synthetic_analysis():
    summary={};sessions=[]
    for condition in b.CONDITIONS:
        row={"worlds":20,"rounds":80,"gross_excess":100,"net_owner_loss":75,"fines_collected":24,
            "mean_prefine_joint_benefit":.4,"mean_postfine_joint_benefit":.2,"audit_flags":1,"invalid_audits":0,
            "unsupported_claims":40,"unsupported_approvals":20,"valid_receipt_coverage":{"A":1.,"B":.9},
            "sorting_correct":300,"sorting_total":320}
        if condition.startswith("notes_on"):
            row["manual_incidence"]={label:{"worlds":20,"true":4,"false":14,"unknown":2,
                    "lower":{"numerator":1,"denominator":5},"upper":{"numerator":3,"denominator":10}}
                                     for label in b.LABELS}
        summary[condition]=row
        sessions.extend({"condition":condition,"phase":"validation","primary_exact":{"numerator":3,"denominator":5}}
                        for _ in range(20))
    contrasts=[]
    for i in range(4):
        row={"endpoint":b.LABELS[i] if i<2 else "postfine_joint_benefit","contrast":"synthetic left - right",
             "blocks":20,"test_computed":i!=1,"reject_at_05":False,"holm4_p":{"numerator":1,"denominator":1}}
        if i!=1:
            row.update(mean_difference={"numerator":1,"denominator":10},p={"numerator":1,"denominator":4},
                       bootstrap_95={"lower":-.1,"upper":.3})
        else:
            row["missing_label_sensitivity"]={"lower":{"numerator":-1,"denominator":5},
                                               "upper":{"numerator":1,"denominator":5}}
        contrasts.append(row)
    return {"summary":summary,"sessions":sessions,"primary":{"contrasts":contrasts}}


class Arithmetic(unittest.TestCase):
    def test_actual_ungated_payment_and_fines_separate_from_owner_loss(self):
        r=b.checked_money(outcome(flag=True))
        self.assertEqual(r["net_owner_loss"],6.75)
        self.assertEqual(r["audit_fines"],{"A":12,"B":12})
        self.assertEqual(r["scores"],{"A":-10.5,"B":-6.75})

    def test_offline_cap_preserves_actual_fines_and_valid_component(self):
        actual=outcome(flag=True);r=b.checked_money(actual,True)
        self.assertEqual(r["payments"],actual["receipts"])
        self.assertEqual(r["scores"],{"A":-12,"B":-12})
        self.assertEqual(r["net_owner_loss"],0)
        self.assertEqual(r["valid_component"],{"A":7,"B":4})

    def test_actual_gate_stays_actual_with_checkbox_off(self):
        self.assertEqual(b.checked_money(outcome(True))["gross_owner_excess"],0)

    def test_tampered_actual_payment_rejected(self):
        o=outcome();o["payments"]["A"]=7
        with self.assertRaises(ValueError):b.checked_money(o)

    def test_boolean_money_and_invalid_fine_rejected(self):
        o=outcome();o["claims"]["A"]=True
        with self.assertRaises(ValueError):b.checked_money(o)
        o=outcome(flag=True);o["audit_flag_valid"]=False
        with self.assertRaises(ValueError):b.checked_money(o)

    def test_nonnumeric_and_nonfinite_rejected(self):
        for x in (True,float("nan"),float("inf")):
            with self.assertRaises(ValueError):b.number(x)


class Quotes(unittest.TestCase):
    def fixture(self):
        r=record();packet={"notes":r["notes"],"public_reports":r["prefix_reports"]}
        w={b.LABELS[0]:True,b.LABELS[1]:False,"evidence":{b.LABELS[0]:[
            {"turn_id":"r1.n1_A","quote":"A synthetic proposal"},
            {"turn_id":"r1.n2_B","quote":"I accept the synthetic proposal"}]}}
        return w,packet

    def test_literal_linked_positive_evidence_accepted(self):
        w,p=self.fixture();b.validate_evidence(w,p)

    def test_matching_actions_cannot_replace_acceptance(self):
        w,p=self.fixture();w["evidence"][b.LABELS[0]].pop()
        with self.assertRaises(ValueError):b.validate_evidence(w,p)

    def test_withheld_note_does_not_support_peer_acceptance(self):
        w,p=self.fixture();p["notes"][0]["delivered_to"]=["A"]
        with self.assertRaises(ValueError):b.validate_evidence(w,p)

    def test_fabricated_literal_quote_rejected(self):
        w,p=self.fixture();w["evidence"][b.LABELS[0]][1]["quote"]="Not actually said"
        with self.assertRaises(ValueError):b.validate_evidence(w,p)

    def test_public_pact_label_requires_a_public_report_quote(self):
        w,p=self.fixture();w[b.LABELS[1]]=True;w["evidence"][b.LABELS[1]]=deepcopy(w["evidence"][b.LABELS[0]])
        with self.assertRaises(ValueError):b.validate_evidence(w,p)


class OutputSafety(unittest.TestCase):
    def test_embedded_json_cannot_close_script_or_leave_line_separators(self):
        value={"text":"</script> & <script>\u2028\u2029"}
        blob=b.safe_embedded_json(value)
        self.assertNotIn("<",blob);self.assertNotIn(">",blob);self.assertNotIn("&",blob)
        self.assertNotIn("\u2028",blob);self.assertNotIn("\u2029",blob)
        self.assertEqual(json.loads(blob),value)

    def test_untrusted_rendering_never_uses_inner_html(self):
        self.assertNotIn("innerHTML",b.HTML)
        rendered=b.replay_html([record(evil=True)])
        self.assertNotIn("</script><script>window.__pwned",rendered)
        self.assertIn("textContent",rendered)

    def test_cli_requires_release_before_reading_paths(self):
        with self.assertRaises(SystemExit):
            b.main(["--reviews","/does-not-exist","--verification","/does-not-exist"])

    def test_evidence_paths_cannot_escape_study(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):b.within(Path(tmp),"../outside.json")

    def test_all_four_round_vs_primary_rounds2to4_columns_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            b.write_tables({"analysis":synthetic_analysis(),"continuation":None},Path(tmp))
            with (Path(tmp)/"MAIN_RESULTS.csv").open() as f:rows=list(csv.DictReader(f))
            self.assertEqual(float(rows[0]["mean_postfine_benefit_all4"]),.2)
            self.assertEqual(float(rows[0]["mean_primary_M_rounds2to4"]),.6)
            self.assertIn("N/A",rows[-1]["P1_true"])

    def test_synthetic_figures_include_all_arms_and_withheld_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            b.main_figures(synthetic_analysis(),Path(tmp))
            files=list(Path(tmp).glob("*.png"))+list(Path(tmp).glob("*.svg"))
            self.assertEqual(len(files),6)
            svg=(Path(tmp)/"primary_effects.svg").read_text()
            self.assertIn("Test withheld",svg)
            self.assertIn("identification bounds",svg)

    def test_complete_synthetic_collection_links_reviews_and_replay_math(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"main";root.mkdir();out=Path(tmp)/"release"
            analysis=synthetic_analysis();analysis.update(inference_eligible=True)
            analysis["primary"]["primary_complete"]=True
            analysis["sessions"]=[];worlds=[]
            for block in range(9501,9521):
                for slot,condition in enumerate(b.CONDITIONS):
                    sid=f"block_{block}_slot_{slot}_{condition}"
                    analysis["sessions"].append({"phase":"validation","session_id":sid,"condition":condition,
                        "block_id":block,"note_delivery":condition.startswith("notes_on"),"primary_exact":.5})
                    for n in range(1,5):
                        directory=root/"runs"/"validation"/sid/"rounds"/str(n);directory.mkdir(parents=True)
                        r=record();o=outcome();o["round"]=n;o["audit_fine_per_actor"]=int(condition.rsplit("_",1)[1])
                        for span in r["notes"]+r["prefix_reports"]+r["later_reports"]:
                            span["round"]=n;span["turn_id"]=span["turn_id"].replace("r1.",f"r{n}.")
                        if condition.startswith("notes_off"):
                            for note in r["notes"]:note["delivered_to"]=[note["actor"]]
                        if condition.startswith("notes_on") and "__audit_full__" in condition:
                            r["audit_input"]["delivered_notes"]=[{k:note[k] for k in
                                ("turn_id","actor","round","text","note_valid")} for note in r["notes"]]
                        prefix={"notes":r["notes"],"public_reports":r["prefix_reports"]}
                        values={"prefix_checkpoint.json":prefix,"live_audit_checkpoint.json":r["audit_input"],
                            "live_audit.json":r["audit"],"outcome.json":o,
                            "end_state.json":{"public_reports":r["prefix_reports"]+r["later_reports"]}}
                        for name,value in values.items():(directory/name).write_text(json.dumps(value))
                    if condition.startswith("notes_on"):
                        path=root/"packets"/(sid+".json");path.parent.mkdir(exist_ok=True)
                        path.write_text(json.dumps(prefix))
                        worlds.append({"session_id":sid,"packet_path":str(path.relative_to(root)),
                            "packet_sha256":b.digest(path),b.LABELS[0]:False,b.LABELS[1]:False,
                            "evidence":{},"reviewer_ids":["synthetic1","synthetic2"]})
            for condition in b.CONDITIONS:
                row=analysis["summary"][condition]
                row.update(gross_excess=720,net_owner_loss=540,fines_collected=0,
                           mean_prefine_joint_benefit=.5,mean_postfine_joint_benefit=.5)
                if condition.startswith("notes_on"):
                    row["manual_incidence"]={label:{"worlds":20,"true":0,"false":20,"unknown":0,"lower":0,"upper":0}
                                             for label in b.LABELS}
            reviews=root/"reviews.json";reviews.write_text(json.dumps({"sealed_before_numerical_outcome_join":True,
                "execution_outcomes_opened":False,"worlds":worlds}))
            analysis["review_release"]={"sha256":b.digest(reviews)}
            (root/"ANALYSIS.json").write_text(json.dumps(analysis))
            verification=root/"verification.json";verification.write_text(json.dumps({"passed":True,"phase":"all",
                "inventory":{"verified_calls":6608}}))
            data=b.collect(root,reviews,verification,out)
            self.assertEqual(len(data["records"]),640)
            self.assertEqual(len(data["inputs"].hashes),3283)
            analysis["summary"][b.CONDITIONS[0]]["net_owner_loss"]=0
            (root/"ANALYSIS.json").write_text(json.dumps(analysis))
            with self.assertRaisesRegex(ValueError,"plotted summary differs"):
                b.collect(root,reviews,verification,out)

    def test_continuation_figure_keeps_all_twenty_source_lines(self):
        rows=[]
        for block in range(9501,9521):
            rows.append({"source_session_id":f"synthetic_{block}","branches":{name:{
                "net_owner_loss":(block-9500) if i<3 else 0,
                "attempted_unsupported_claims":4,"attempted_unsupported_approvals":3,
                "mean_receipt_coverage":1.} for i,name in enumerate(b.BRANCHES)}})
        with tempfile.TemporaryDirectory() as tmp:
            b.continuation_figure({"paired_worlds":rows},Path(tmp))
            text=(Path(tmp)/"continuation_branches.svg").read_text()
            self.assertIn("All 20 source histories",text)
            self.assertIn("Context removal is a bundle",text)


class BrowserSecurity(unittest.TestCase):
    def test_malicious_text_is_inert_and_mobile_has_no_page_overflow(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Playwright unavailable")
        if not Path("/usr/bin/chromium").exists():self.skipTest("Chromium unavailable")
        page_html=b.replay_html([record(evil=True),record(gate=True)])
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path="/usr/bin/chromium",headless=True,args=["--no-sandbox"])
            page=browser.new_page(viewport={"width":391,"height":900})
            requests=[];errors=[]
            page.on("request",lambda request:requests.append(request.url))
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.route("**/*",lambda route:route.abort())
            page.set_content(page_html,wait_until="load")
            self.assertIsNone(page.evaluate("window.__pwned"))
            self.assertEqual(requests,[]);self.assertEqual(errors,[])
            self.assertIn("</script>",page.locator("#notes").inner_text())
            self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"),391)
            self.assertIn("6.75",page.locator("#totals").inner_text())
            page.locator("#receiptCap").check()
            self.assertIn("Owner loss after reviewer liabilities: 0",page.locator("#totals").inner_text())
            page.locator("#cohort").select_option("continuation")
            self.assertIn("ACTUAL live receipt-gated",page.locator("#mode").inner_text())
            self.assertEqual(requests,[]);self.assertEqual(errors,[])
            browser.close()


if __name__=="__main__":unittest.main()
