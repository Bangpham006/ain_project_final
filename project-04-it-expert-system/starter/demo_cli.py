"""Terminal demo of the Project 04 expert system (for the midterm live demo).

    python starter/demo_cli.py SYM03 SYM04             # diagnose any symptom set
    python starter/demo_cli.py --scenario SC04         # load a fixture (an id prefix is enough)
    python starter/demo_cli.py --scenario SC06 --ask   # consultation: the engine asks follow-up questions
    python starter/demo_cli.py SYM03 SYM04 --strategy rule_count
    python starter/demo_cli.py --list                  # symptom catalogue by domain

All reasoning comes from `student_core`; this file only formats results and
asks the questions `suggest_followups` proposes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import conflicts as conflicts_mod
import rule_loader
import student_core as core

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ASK_WHEN = {"ambiguous", "insufficient_evidence"}  # statuses where another question can help

STATUS_TEXT = {
    "single_cause": "SINGLE CAUSE",
    "resolved": "RESOLVED (rivals exist, one is preferred)",
    "ambiguous": "AMBIGUOUS (rivals are equally supported)",
    "multi_fault": "MULTI-FAULT (independent problems)",
    "contradictory": "CONTRADICTORY REPORT",
    "insufficient_evidence": "INSUFFICIENT EVIDENCE (no rule fires; nothing is guessed)",
}


def load_kb():
    kb = rule_loader.load_all(DATA_DIR)
    conflicts = conflicts_mod.load_conflicts(DATA_DIR / "conflicts.json", {s["id"] for s in kb["symptoms"]})
    return kb, conflicts


def show(report: dict, symptoms: list[str], kb: dict) -> None:
    sym = {s["id"]: s for s in kb["symptoms"]}
    causes = {c["id"]: c for c in kb["causes"]}
    rules = {r["id"]: r for r in kb["rules"]}

    print("\nReported symptoms:")
    for s in symptoms:
        print(f"  {s}  {sym[s]['description']}")
    if not symptoms:
        print("  (none)")
    print(f"\n=> {STATUS_TEXT[report['status']]}   [conflict resolution: {report['strategy']}]")

    for c in report["conflicts"]:
        print(f"   ! {c['id']}: {' vs '.join(c['symptoms'])} -- {c['reason']}")
    for ranking in report["rankings"]:
        if sum(len(tier) for tier in ranking) > 1:
            print("   ranking: " + "  >  ".join(" = ".join(tier) for tier in ranking))

    for record in report["results"]:
        cause_id = record["cause_id"]
        marker = "*" if cause_id in report["leaders"] else " "
        print(f"\n {marker} {cause_id}  {causes[cause_id]['description']}")
        print(f"     support {record['supporting_symptoms']}, specificity {record['specificity']}")
        for rule_id in report["traces"][cause_id]:
            rule = rules[rule_id]
            comment = f"   ({rule['comment']})" if rule.get("comment") else ""
            print(f"     {rule_id}: {' ∧ '.join(rule['if'])} → {rule['then']}{comment}")

    if report["leaders"]:
        print("\nRecommended action:")
        for cause_id in report["leaders"]:
            print(f"  {cause_id}: {causes[cause_id].get('recommended_action', '-')}")


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip().lower()
    except EOFError:
        return "q"


def consult(symptoms: list[str], kb: dict, conflicts: list[dict], strategy: str, interactive: bool) -> None:
    sym = {s["id"]: s for s in kb["symptoms"]}
    denied: set[str] = set()
    while True:
        report = core.diagnose(symptoms, kb["rules"], conflicts, strategy)
        show(report, symptoms, kb)
        if not interactive or report["status"] not in ASK_WHEN:
            return

        domains = sorted({sym[s]["domain"] for s in symptoms})
        if not domains:
            all_domains = sorted({s["domain"] for s in kb["symptoms"]})
            print("\nWhich service is the problem about?")
            for i, d in enumerate(all_domains, 1):
                print(f"  {i}. {d}")
            choice = ask("Number (q to quit): ")
            if not choice.isdigit() or not 1 <= int(choice) <= len(all_domains):
                return
            domains = [all_domains[int(choice) - 1]]

        pool = [s for s in sym if sym[s]["domain"] in domains and s not in denied]
        options = [
            f for f in core.suggest_followups(symptoms, kb["rules"], conflicts, pool, strategy)
            if f["status"] != "contradictory"
        ]
        if not options:
            print("\nNo further question in this domain can change the diagnosis.")
            return
        question = options[0]
        answer = ask(f"\n? Do you also observe {question['symptom']}: "
                     f"{sym[question['symptom']]['description']}  [y/n/q] ")
        if answer.startswith("y"):
            symptoms = symptoms + [question["symptom"]]
        elif answer.startswith("n"):
            denied.add(question["symptom"])
        else:
            return


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to cp1252
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="IT helpdesk expert system -- terminal demo")
    parser.add_argument("symptoms", nargs="*", help="symptom ids, e.g. SYM03 SYM04")
    parser.add_argument("--scenario", help="load a fixture from scenarios.json (id or unique prefix)")
    parser.add_argument("--ask", action="store_true", help="ask follow-up questions while ambiguous or empty")
    parser.add_argument("--strategy", default=core.DEFAULT_STRATEGY, choices=sorted(core.STRATEGIES))
    parser.add_argument("--list", action="store_true", help="print the symptom catalogue and exit")
    args = parser.parse_args(argv)

    kb, conflicts = load_kb()
    known = {s["id"] for s in kb["symptoms"]}

    if args.list:
        for domain in sorted({s["domain"] for s in kb["symptoms"]}):
            print(f"\n[{domain}]")
            for s in kb["symptoms"]:
                if s["domain"] == domain:
                    print(f"  {s['id']}  {s['description']}")
        return 0

    symptoms = [s.upper() for s in args.symptoms]
    if args.scenario:
        matches = [sc for sc in kb["scenarios"] if sc["id"].upper().startswith(args.scenario.upper())]
        if len(matches) != 1:
            parser.error(f"--scenario {args.scenario!r} matches {len(matches)} fixtures")
        print(f"Scenario {matches[0]['id']}: {matches[0].get('description', '')}")
        symptoms = list(matches[0]["presented_symptoms"]) + symptoms

    unknown = [s for s in symptoms if s not in known]
    if unknown:
        print(f"Ignoring unknown symptom id(s): {', '.join(unknown)}  (see --list)")
    symptoms = list(dict.fromkeys(s for s in symptoms if s in known))

    consult(symptoms, kb, conflicts, args.strategy, args.ask)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
