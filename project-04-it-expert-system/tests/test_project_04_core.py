"""Behaviour tests for the Project 04 AI core (`starter/student_core.py`).

Expected values below were derived from `data/rules.json` by hand-tracing the
rules, not copied from `expected_behavior` in `scenarios.json`: that free-text
field disagrees with the rule base for a few fixtures (see
`test_scenario_labels_vs_rule_base`), so the rule base is the source of truth.
"""

from __future__ import annotations

import copy
import importlib.util
import itertools
import random
import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STARTER_DIR = PROJECT_ROOT / "starter"


def _load_module(module_name: str, file_path: Path):
    # Same by-path loading as the sanity tests: `student_core.py` is a filename
    # shared by every project in the kit, so a plain import would collide.
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


rule_loader = _load_module("project04core_rule_loader", STARTER_DIR / "rule_loader.py")
conflicts_mod = _load_module("project04core_conflicts", STARTER_DIR / "conflicts.py")
core = _load_module("project04core_student_core", STARTER_DIR / "student_core.py")

KB = rule_loader.load_all(DATA_DIR)
RULES = KB["rules"]
SYMPTOMS = KB["symptoms"]
SYMPTOM_IDS = {s["id"] for s in SYMPTOMS}
CONFLICTS = conflicts_mod.load_conflicts(DATA_DIR / "conflicts.json", SYMPTOM_IDS)
SCENARIOS = {s["id"]: s for s in KB["scenarios"]}
SC04 = SCENARIOS["SC04_ambiguous_wifi_drop"]["presented_symptoms"]


def causes_of(symptoms, rules=RULES):
    return {r["cause_id"] for r in core.infer(symptoms, rules)}


def fired_by_cause(symptoms, rules=RULES):
    return {r["cause_id"]: r["fired_rules"] for r in core.infer(symptoms, rules)}


def without(*rule_ids):
    return [r for r in RULES if r["id"] not in rule_ids]


# --------------------------------------------------------------------------- #
# infer: the four mandatory archetypes
# --------------------------------------------------------------------------- #
def test_single_cause_portal_loop():
    s = SCENARIOS["SC01_single_cause_portal_loop"]["presented_symptoms"]
    # R002 (SYM01 alone) fires too -- the fixture text only names R001/R003.
    assert fired_by_cause(s) == {"CAUSE01": ["R001", "R002", "R003"]}


def test_ambiguous_wifi_drop_returns_both_rivals_with_all_their_rules():
    assert fired_by_cause(SC04) == {
        "CAUSE02": ["R005", "R042"],
        "CAUSE03": ["R007", "R008", "R043"],
    }


def test_missing_info_returns_empty_not_a_guess():
    assert core.infer([], RULES) == []
    assert core.infer(SCENARIOS["SC06_missing_info_no_symptoms"]["presented_symptoms"], RULES) == []


def test_symptom_that_is_only_ever_a_partial_premise_gives_empty():
    # SYM02 appears in R004 (needs SYM05) and R009 (needs SYM04) only.
    assert core.infer(["SYM02"], RULES) == []


def test_contradictory_printer_still_lists_candidates():
    s = SCENARIOS["SC07_contradictory_printer"]["presented_symptoms"]
    assert fired_by_cause(s) == {
        "CAUSE13": ["R034", "R039"],
        "CAUSE14": ["R036", "R041"],
    }


def test_records_carry_support_and_specificity():
    by_cause = {r["cause_id"]: r for r in core.infer(SC04, RULES)}
    assert by_cause["CAUSE02"]["supporting_symptoms"] == ["SYM03", "SYM04"]
    assert by_cause["CAUSE02"]["specificity"] == 2  # R005 has two premises
    assert by_cause["CAUSE03"]["specificity"] == 2  # R007 has two premises


# --------------------------------------------------------------------------- #
# infer: generalisation beyond the fixtures
# --------------------------------------------------------------------------- #
def _oracle(symptom_set):
    # Textbook definition for a one-level KB: a cause is a candidate iff some
    # rule's premises are all reported.
    return {r["then"] for r in RULES if r["if"] and set(r["if"]) <= set(symptom_set)}


def _by_domain():
    groups: dict[str, list[str]] = {}
    for s in SYMPTOMS:
        groups.setdefault(s["domain"], []).append(s["id"])
    return groups


def _within_domain_sets():
    for domain_ids in _by_domain().values():
        for k in range(len(domain_ids) + 1):
            yield from itertools.combinations(domain_ids, k)


def test_unseen_cross_domain_symptom_set():
    # Not in scenarios.json: an LMS fault and a lab fault at the same time.
    assert causes_of(["SYM07", "SYM12"]) == {"CAUSE04", "CAUSE07"}


def test_matches_oracle_on_every_within_domain_symptom_set():
    for combo in _within_domain_sets():
        assert causes_of(list(combo)) == _oracle(combo)


def test_matches_oracle_on_random_cross_domain_symptom_sets():
    rng = random.Random(42)
    ids = [s["id"] for s in SYMPTOMS]
    for _ in range(500):
        combo = rng.sample(ids, rng.randint(0, 8))
        assert causes_of(combo) == _oracle(combo)


def test_monotonic_adding_a_symptom_never_retracts_a_cause():
    ids = [s["id"] for s in SYMPTOMS]
    for combo in _within_domain_sets():
        before = causes_of(list(combo))
        for extra in ids:
            assert before <= causes_of(list(combo) + [extra])


def test_monotonic_removing_a_rule_never_adds_a_cause():
    for rule in RULES:
        reduced = without(rule["id"])
        for scenario in SCENARIOS.values():
            s = scenario["presented_symptoms"]
            assert causes_of(s, reduced) <= causes_of(s)


def test_candidate_set_does_not_depend_on_rule_order():
    # The fixpoint is unique, so shuffling the rules may reorder the trace
    # but can never change which causes are concluded.
    rng = random.Random(42)
    for _ in range(50):
        shuffled = RULES[:]
        rng.shuffle(shuffled)
        for combo in [SC04, ["SYM22", "SYM23", "SYM26"], ["SYM07", "SYM12", "SYM17"]]:
            assert causes_of(combo, shuffled) == causes_of(combo)


def test_order_and_duplicates_of_input_do_not_change_candidates():
    assert fired_by_cause(["SYM03", "SYM04"]) == fired_by_cause(["SYM04", "SYM03", "SYM03"])


def test_unknown_symptom_id_is_ignored_not_fatal():
    assert core.infer(["SYM999"], RULES) == []


def test_string_instead_of_list_is_rejected():
    with pytest.raises(TypeError):
        core.infer("SYM01", RULES)


def test_inputs_are_not_mutated():
    symptoms, rules = ["SYM03", "SYM04"], copy.deepcopy(RULES)
    snapshot = copy.deepcopy(rules)
    core.infer(symptoms, rules)
    core.explain("CAUSE02", symptoms, rules)
    core.diagnose(symptoms, rules, CONFLICTS)
    core.suggest_followups(symptoms, rules, CONFLICTS)
    assert symptoms == ["SYM03", "SYM04"] and rules == snapshot


def test_supporting_symptoms_are_reported_symptoms_only():
    record = next(r for r in core.infer(["SYM03", "SYM04", "SYM01"], RULES) if r["cause_id"] == "CAUSE03")
    assert record["supporting_symptoms"] == ["SYM03", "SYM04"]


# --------------------------------------------------------------------------- #
# Forward chaining proper (the shipped KB is one level deep; engine is not)
# --------------------------------------------------------------------------- #
CHAIN = [
    # Deliberately listed consumer-first: a single scan would miss it.
    {"id": "RB", "if": ["CAUSE01", "SYM02"], "then": "CAUSE02"},
    {"id": "RA", "if": ["SYM01"], "then": "CAUSE01"},
    {"id": "RC", "if": ["CAUSE02"], "then": "CAUSE03"},
]


def test_chained_rules_reach_a_fixpoint():
    assert causes_of(["SYM01", "SYM02"], CHAIN) == {"CAUSE01", "CAUSE02", "CAUSE03"}
    assert causes_of(["SYM01"], CHAIN) == {"CAUSE01"}


def test_chained_proof_lists_prerequisites_first():
    assert core.explain("CAUSE03", ["SYM01", "SYM02"], CHAIN) == ["RA", "RB", "RC"]


def test_empty_premise_rule_never_fires():
    assert core.infer([], [{"id": "RX", "if": [], "then": "CAUSE01"}]) == []


def test_rules_may_be_any_iterable():
    # An iterator would be exhausted after the first scan and silently break chaining.
    assert causes_of(["SYM01", "SYM02"], iter(CHAIN)) == {"CAUSE01", "CAUSE02", "CAUSE03"}
    assert core.diagnose(SC04, iter(RULES), CONFLICTS)["status"] == "ambiguous"
    assert core.suggest_followups(SC04, iter(RULES), CONFLICTS)


def test_repeated_premise_does_not_inflate_specificity():
    rules = [{"id": "R1", "if": ["SYM01", "SYM01"], "then": "CAUSE01"}]
    assert core.infer(["SYM01"], rules)[0]["specificity"] == 1


def test_duplicate_rule_ids_do_not_hide_a_rule():
    rules = [
        {"id": "R1", "if": ["SYM01"], "then": "CAUSE01"},
        {"id": "R1", "if": ["SYM02"], "then": "CAUSE02"},
    ]
    assert causes_of(["SYM01", "SYM02"], rules) == {"CAUSE01", "CAUSE02"}


# --------------------------------------------------------------------------- #
# Conflict resolution
# --------------------------------------------------------------------------- #
def test_ambiguous_wifi_drop_is_a_genuine_tie_under_specificity():
    assert core.rank_candidates(core.infer(SC04, RULES)) == [["CAUSE02", "CAUSE03"]]


def test_removing_r007_turns_the_tie_into_a_single_preferred_cause():
    # The README's ablation: CAUSE03 stays a candidate (R008, R043 still fire)
    # but loses its only two-premise rule, so specificity now prefers CAUSE02.
    reduced = without("R007")
    assert causes_of(SC04, reduced) == {"CAUSE02", "CAUSE03"}
    report = core.diagnose(SC04, reduced, CONFLICTS)
    assert report["status"] == "resolved"
    assert report["leaders"] == ["CAUSE02"]
    assert report["rankings"] == [[["CAUSE02"], ["CAUSE03"]]]


def test_eliminating_the_rival_needs_all_of_its_fired_rules_removed():
    assert causes_of(SC04, without("R007", "R008", "R043")) == {"CAUSE02"}
    assert causes_of(SC04, without("R005", "R042")) == {"CAUSE03"}


def test_strategies_disagree_so_the_choice_must_be_explicit():
    results = core.infer(SC04, RULES)
    assert core.rank_candidates(results, "specificity") == [["CAUSE02", "CAUSE03"]]
    assert core.rank_candidates(results, "coverage") == [["CAUSE02", "CAUSE03"]]
    # rule_count prefers CAUSE03 only because it has more (redundant) rules.
    assert core.rank_candidates(results, "rule_count") == [["CAUSE03"], ["CAUSE02"]]


def test_specificity_and_coverage_order_their_keys_differently():
    results = [
        {"cause_id": "A", "fired_rules": ["r1", "r2", "r3"], "supporting_symptoms": ["s1", "s2", "s3"], "specificity": 1},
        {"cause_id": "B", "fired_rules": ["r4"], "supporting_symptoms": ["s1", "s2"], "specificity": 2},
    ]
    assert core.rank_candidates(results, "specificity") == [["B"], ["A"]]
    assert core.rank_candidates(results, "coverage") == [["A"], ["B"]]


def test_unknown_strategy_is_rejected():
    with pytest.raises(ValueError):
        core.rank_candidates([], "salience")


def test_ranking_never_drops_a_candidate():
    for combo in _within_domain_sets():
        results = core.infer(list(combo), RULES)
        for strategy in core.STRATEGIES:
            ranked = [c for tier in core.rank_candidates(results, strategy) for c in tier]
            assert sorted(ranked) == sorted(r["cause_id"] for r in results)


# --------------------------------------------------------------------------- #
# explain
# --------------------------------------------------------------------------- #
def test_explain_lists_fired_rules_in_firing_order():
    assert core.explain("CAUSE01", ["SYM01", "SYM06"], RULES) == ["R001", "R002", "R003"]


def test_explain_cause_not_supported_returns_empty():
    assert core.explain("CAUSE03", ["SYM01", "SYM06"], RULES) == []
    assert core.explain("CAUSE01", [], RULES) == []


def test_explain_steps_carry_matched_premises():
    steps = core.explain_steps("CAUSE02", SC04, RULES)
    assert [s["rule"] for s in steps] == ["R005", "R042"]
    assert steps[0]["matched"] == ["SYM03", "SYM04"] and steps[0]["derived"] == "CAUSE02"
    assert [s["step"] for s in steps] == sorted(s["step"] for s in steps)


def test_explain_return_value_exposes_a_tie():
    explanation = core.explain("CAUSE02", SC04, RULES)
    assert explanation == ["R005", "R042"]  # still a plain list of rule ids
    assert explanation.is_ambiguous
    assert explanation.tied_with == ["CAUSE03"] and explanation.rivals == ["CAUSE03"]


def test_explain_return_value_exposes_a_better_rival():
    s = SCENARIOS["SC02_single_cause_printer_offline"]["presented_symptoms"]
    explanation = core.explain("CAUSE14", s, RULES)
    assert explanation == ["R036"]
    assert explanation.outranked_by == ["CAUSE13"] and not explanation.is_ambiguous


def test_explain_uncontested_cause_has_no_rivals():
    explanation = core.explain("CAUSE04", ["SYM07", "SYM12"], RULES)  # independent faults
    assert explanation.rivals == [] and not explanation.is_ambiguous


def test_explain_without_conflict_table_never_raises():
    assert core.explain("CAUSE13", ["SYM22", "SYM25", "SYM26"], RULES) == ["R034", "R039"]


def test_explain_raises_typed_error_on_contradiction_and_keeps_the_trace():
    s = SCENARIOS["SC07_contradictory_printer"]["presented_symptoms"]
    with pytest.raises(core.ContradictoryEvidenceError) as info:
        core.explain("CAUSE13", s, RULES, conflicts=CONFLICTS)
    pairs = {tuple(sorted(c["symptoms"])) for c in info.value.conflicts}
    assert pairs == {("SYM22", "SYM26"), ("SYM22", "SYM25")}
    assert info.value.rule_ids == ["R034", "R039"]


def test_explain_with_conflict_table_is_silent_on_consistent_input():
    assert core.explain("CAUSE02", SC04, RULES, conflicts=CONFLICTS) == ["R005", "R042"]


# --------------------------------------------------------------------------- #
# diagnose: status for every fixture, multi-fault vs ambiguity
# --------------------------------------------------------------------------- #
EXPECTED_STATUS = {
    "SC01_single_cause_portal_loop": "single_cause",
    "SC02_single_cause_printer_offline": "resolved",  # 2 candidates; specificity prefers CAUSE13
    "SC03_single_cause_lms_not_enrolled": "single_cause",
    "SC04_ambiguous_wifi_drop": "ambiguous",
    "SC05_ambiguous_account_locked": "single_cause",  # labelled ambiguous in the fixture
    "SC06_missing_info_no_symptoms": "insufficient_evidence",
    "SC07_contradictory_printer": "contradictory",
    "SC08_lab_grub_error": "single_cause",
    "SC09_lab_no_network": "single_cause",
    "SC10_projector_hdmi": "single_cause",
    "SC11_password_expired": "single_cause",
    "SC12_submission_size_exceeded": "single_cause",
    "SC13_wifi_laptop_only": "single_cause",  # labelled ambiguous in the fixture
    "SC14_office365_unlicensed": "single_cause",
    "SC15_lms_session_timeout": "single_cause",
}


@pytest.mark.parametrize("scenario_id", sorted(EXPECTED_STATUS))
def test_diagnose_status_for_every_fixture(scenario_id):
    report = core.diagnose(SCENARIOS[scenario_id]["presented_symptoms"], RULES, CONFLICTS)
    assert report["status"] == EXPECTED_STATUS[scenario_id]


def test_scenario_labels_vs_rule_base():
    """Documents (and pins) where the fixture `class` label and the number of
    candidates the rules actually produce disagree."""
    assert set(EXPECTED_STATUS) == set(SCENARIOS)
    expected_count = {"single_cause": "one", "ambiguous": "several", "missing_info": "none"}
    mismatched = set()
    for sid, scenario in SCENARIOS.items():
        n = len(core.infer(scenario["presented_symptoms"], RULES))
        actual = "none" if n == 0 else "one" if n == 1 else "several"
        if scenario["class"] in expected_count and expected_count[scenario["class"]] != actual:
            mismatched.add(sid)
    assert mismatched == {
        "SC02_single_cause_printer_offline",
        "SC05_ambiguous_account_locked",
        "SC13_wifi_laptop_only",
    }


def test_only_the_contradictory_fixture_trips_the_conflict_table():
    flagged = {
        sid
        for sid, s in SCENARIOS.items()
        if core.detect_conflicts(s["presented_symptoms"], CONFLICTS)
    }
    assert flagged == {"SC07_contradictory_printer"}


def test_multi_fault_is_distinguished_from_ambiguity():
    report = core.diagnose(["SYM07", "SYM12"], RULES, CONFLICTS)
    assert report["status"] == "multi_fault"
    assert sorted(map(sorted, report["groups"])) == [["CAUSE04"], ["CAUSE07"]]
    assert report["ambiguous_groups"] == []


def test_ambiguity_inside_a_multi_fault_incident_is_still_ambiguous():
    report = core.diagnose(["SYM03", "SYM04", "SYM07"], RULES, CONFLICTS)
    assert report["status"] == "ambiguous"
    assert report["ambiguous_groups"] == [["CAUSE02", "CAUSE03"]]
    assert ["CAUSE04"] in report["groups"]


def test_diagnose_report_has_a_proof_for_every_candidate():
    report = core.diagnose(SC04, RULES, CONFLICTS)
    assert set(report["traces"]) == {r["cause_id"] for r in report["results"]}
    assert report["traces"]["CAUSE03"] == ["R007", "R008", "R043"]


# --------------------------------------------------------------------------- #
# Follow-up questions (what-if one more symptom)
# --------------------------------------------------------------------------- #
def test_followups_find_the_two_discriminating_questions_for_the_wifi_tie():
    wifi = [s["id"] for s in SYMPTOMS if s["domain"] == "hanu_wifi"]
    suggestions = core.suggest_followups(SC04, RULES, CONFLICTS, candidates=wifi)
    decisive = {s["symptom"]: s["leaders"] for s in suggestions if s["status"] == "resolved"}
    assert decisive == {"SYM02": ["CAUSE03"], "SYM05": ["CAUSE02"]}


def test_followups_on_empty_report_start_with_single_cause_answers():
    lms = [s["id"] for s in SYMPTOMS if s["domain"] == "fit_lms"]
    suggestions = core.suggest_followups([], RULES, CONFLICTS, candidates=lms)
    assert suggestions and all(s["status"] == "single_cause" for s in suggestions)
    # SYM11 alone fires nothing, so asking about it first cannot help.
    assert "SYM11" not in {s["symptom"] for s in suggestions}


def test_followups_put_contradicting_answers_last():
    s = SCENARIOS["SC02_single_cause_printer_offline"]["presented_symptoms"]
    printer = [x["id"] for x in SYMPTOMS if x["domain"] == "fit_printer"]
    suggestions = core.suggest_followups(s, RULES, CONFLICTS, candidates=printer)
    statuses = [x["status"] for x in suggestions]
    assert statuses == sorted(statuses, key=core.STATUS_ORDER.index)
    assert {x["symptom"] for x in suggestions if x["status"] == "contradictory"} == {"SYM24", "SYM25", "SYM26"}


# --------------------------------------------------------------------------- #
# conflict table integrity
# --------------------------------------------------------------------------- #
def test_conflict_table_loads_and_is_well_formed():
    assert len(CONFLICTS) >= 1
    assert all(len(set(c["symptoms"])) == 2 for c in CONFLICTS)


def test_conflict_loader_rejects_unknown_symptom(tmp_path):
    bad = tmp_path / "conflicts.json"
    bad.write_text('{"conflicts": [{"id": "X", "symptoms": ["SYM01", "NOPE"], "reason": "r"}]}', encoding="utf-8")
    with pytest.raises(conflicts_mod.ConflictSchemaError):
        conflicts_mod.load_conflicts(bad, SYMPTOM_IDS)


def test_conflict_loader_rejects_unknown_key(tmp_path):
    bad = tmp_path / "conflicts.json"
    bad.write_text(
        '{"conflicts": [{"id": "X", "symptoms": ["SYM01", "SYM02"], "reason": "r", "extra": 1}]}',
        encoding="utf-8",
    )
    with pytest.raises(conflicts_mod.ConflictSchemaError):
        conflicts_mod.load_conflicts(bad, SYMPTOM_IDS)


def test_rules_that_premise_a_conflicting_pair_are_exactly_the_known_one():
    # R048 requires SYM22 and SYM26 together, i.e. the shipped rule base itself
    # fires on a pair our conflict table calls incompatible. Pin it so any new
    # rule/conflict that creates another such overlap is noticed and discussed.
    overlapping = {
        r["id"]
        for r in RULES
        for c in CONFLICTS
        if set(c["symptoms"]) <= set(r["if"])
    }
    assert overlapping == {"R048"}


# --------------------------------------------------------------------------- #
# scripts run on a non-UTF-8 Windows console (cp1252 is the default for pipes)
# --------------------------------------------------------------------------- #
def _run_script(args, stdin="", timeout=120):
    import os
    import subprocess

    env = dict(os.environ, PYTHONIOENCODING="cp1252")
    return subprocess.run(
        [sys.executable, *args], cwd=PROJECT_ROOT, input=stdin, capture_output=True,
        text=True, encoding="utf-8", errors="replace", env=env, timeout=timeout,
    )


def test_demo_cli_one_shot_and_unknown_ids():
    run = _run_script(["starter/demo_cli.py", "--scenario", "SC07", "SYM99"])
    assert run.returncode == 0, run.stderr
    assert "CONTRADICTORY REPORT" in run.stdout and "Ignoring unknown symptom id(s): SYM99" in run.stdout


def test_demo_cli_consultation_asks_the_discriminating_question():
    run = _run_script(["starter/demo_cli.py", "--scenario", "SC04", "--ask"], stdin="y\n")
    assert run.returncode == 0, run.stderr
    assert "Do you also observe SYM02" in run.stdout
    assert run.stdout.rstrip().endswith("try connecting from a different location or access point.")


def test_reasoning_probes_script(tmp_path):
    out = tmp_path / "Kì 1 Năm 4"  # the script prints this path; 'ă' is not in cp1252
    run = _run_script(["experiments/reasoning_probes.py", str(out)])
    assert run.returncode == 0, run.stderr
    assert "## SC04_ambiguous_wifi_drop" in (out / "reasoning_probes.md").read_text(encoding="utf-8")


def test_ablation_script(tmp_path):
    # ~8 s: regenerates every table into a temp dir, never over the committed results.
    run = _run_script(["experiments/ablation.py", str(tmp_path)], timeout=300)
    assert run.returncode == 0, run.stderr
    report = (tmp_path / "ablation_report.md").read_text(encoding="utf-8")
    assert "## E9." in report and "**0** violations" in report


# --------------------------------------------------------------------------- #
# course rules: no shortcuts
# --------------------------------------------------------------------------- #
def test_core_has_no_scenario_lookup_or_forbidden_dependencies():
    source = (STARTER_DIR / "student_core.py").read_text(encoding="utf-8")
    assert not re.search(r"\bSC\d{2}\b", source), "scenario ids must not appear in the core"
    code_lines = [ln for ln in source.splitlines() if ln.lstrip().startswith(("import ", "from "))]
    banned = ("clips", "pyke", "experta", "durable", "openai", "anthropic", "requests", "httpx")
    assert not [ln for ln in code_lines if any(b in ln.lower() for b in banned)]
