"""Product & UI tests for Project 04 Final Milestone (`app.py` & `reasoning_graph.py`)."""

from __future__ import annotations

import importlib.util
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STARTER_DIR = PROJECT_ROOT / "starter"


def _load_starter():
    if str(STARTER_DIR) not in sys.path:
        sys.path.insert(0, str(STARTER_DIR))
    import conflicts as conflicts_mod
    import reasoning_graph
    import rule_loader
    import student_core

    return rule_loader, conflicts_mod, student_core, reasoning_graph


def test_reasoning_svg_is_valid_xml_across_all_archetypes():
    rule_loader, conflicts_mod, core, rg = _load_starter()
    kb = rule_loader.load_all(DATA_DIR)
    confs = conflicts_mod.load_conflicts(
        DATA_DIR / "conflicts.json", {s["id"] for s in kb["symptoms"]}
    )

    test_inputs = [
        [],  # SC06 empty working memory
        ["SYM02"],  # Unmatched partial premise
        ["SYM01", "SYM06"],  # SC01 single cause
        ["SYM03", "SYM04"],  # SC04 ambiguous tie
        ["SYM22", "SYM25", "SYM26"],  # SC07 contradictory (X01, X02)
        ["SYM01", "SYM06", "SYM07", "SYM12"],  # Multi-fault
    ]
    for syms in test_inputs:
        rep = core.diagnose(syms, kb["rules"], confs)
        svg = rg.build_reasoning_svg(syms, rep, kb)
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")
        dot = rg.build_reasoning_dot(syms, rep, kb)
        assert "digraph ReasoningGraph" in dot


def test_reasoning_svg_surfaces_conflict_badges_and_unmatched_symptoms():
    rule_loader, conflicts_mod, core, rg = _load_starter()
    kb = rule_loader.load_all(DATA_DIR)
    confs = conflicts_mod.load_conflicts(
        DATA_DIR / "conflicts.json", {s["id"] for s in kb["symptoms"]}
    )

    rep_conf = core.diagnose(["SYM22", "SYM25", "SYM26"], kb["rules"], confs)
    svg_conf = rg.build_reasoning_svg(["SYM22", "SYM25", "SYM26"], rep_conf, kb)
    assert "X01" in svg_conf and "X02" in svg_conf

    rep_unmatched = core.diagnose(["SYM02"], kb["rules"], confs)
    svg_unmatched = rg.build_reasoning_svg(["SYM02"], rep_unmatched, kb)
    assert "[UNMATCHED]" in svg_unmatched


def test_streamlit_app_sc06_empty_shows_lms_followups():
    at = AppTest.from_file(str(STARTER_DIR / "app.py"), default_timeout=20)
    at.run()
    assert not at.exception

    # Select SC06_missing_info_no_symptoms in sidebar
    at.sidebar.selectbox[0].select("SC06_missing_info_no_symptoms").run()
    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Diagnostic Status"] == "Insufficient Evidence"
    assert metrics["Candidate Causes"] == "0"

    # Follow-up buttons for FIT LMS should be rendered (SYM07, SYM08, SYM09, SYM10)
    btn_labels = [b.label for b in at.button]
    assert "Yes (SYM07)" in btn_labels

    # Confirming SYM07 transitions SC06 directly to Single Cause (CAUSE04)
    next(b for b in at.button if b.label == "Yes (SYM07)").click().run()
    assert not at.exception
    metrics_after = {m.label: m.value for m in at.metric}
    assert metrics_after["Diagnostic Status"] == "Single Cause"
    assert metrics_after["Candidate Causes"] == "1"


def test_streamlit_app_sc04_followup_yes_no_and_ablation():
    at = AppTest.from_file(str(STARTER_DIR / "app.py"), default_timeout=20)
    at.run()
    at.sidebar.selectbox[0].select("SC04_ambiguous_wifi_drop").run()
    assert not at.exception
    assert {m.label: m.value for m in at.metric}["Diagnostic Status"] == "Ambiguous"

    # Rule out SYM02 via "No (SYM02)" -> SYM05 remains available & individual Undo chip appears
    no_sym02 = next(b for b in at.button if b.label == "No (SYM02)")
    no_sym02.click().run()
    assert not at.exception
    btn_labels = [b.label for b in at.button]
    assert "Yes (SYM02)" not in btn_labels
    assert "Yes (SYM05)" in btn_labels
    assert "Undo No: SYM02 ×" in btn_labels

    # Undo SYM02 individually -> SYM02 is restored to follow-up options
    undo_sym02 = next(b for b in at.button if b.label == "Undo No: SYM02 ×")
    undo_sym02.click().run()
    assert not at.exception
    assert "Yes (SYM02)" in [b.label for b in at.button]

    # Disable R007 in the sidebar Rule Ablation Sandbox -> Ambiguous flips to Resolved
    at.sidebar.multiselect[0].select("R007").run()
    assert not at.exception
    assert {m.label: m.value for m in at.metric}["Diagnostic Status"] == "Resolved"


def test_streamlit_app_sc07_contradiction_and_multi_fault_preset():
    at = AppTest.from_file(str(STARTER_DIR / "app.py"), default_timeout=20)
    at.run()
    at.sidebar.selectbox[0].select("SC07_contradictory_printer").run()
    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Diagnostic Status"] == "Contradictory"
    assert metrics["Fired Rules / Conflicts"].endswith("/ 2")

    # Switch to triple-domain multi-fault stress preset
    at.sidebar.selectbox[0].select("STRESS_MF02_triple_campus_incident").run()
    assert not at.exception
    mf_metrics = {m.label: m.value for m in at.metric}
    assert mf_metrics["Diagnostic Status"] == "Multi Fault"
    assert mf_metrics["Fault Clusters"] == "3"


def test_ui_files_make_zero_external_network_requests():
    for fname in ("app.py", "reasoning_graph.py"):
        src = (STARTER_DIR / fname).read_text(encoding="utf-8")
        # Allow standard W3C SVG XML namespace only; forbid external HTTP(S) URLs
        cleaned = src.replace("http://www.w3.org/2000/svg", "")
        assert not re.search(r"https?://", cleaned), f"{fname} contains an external URL"
