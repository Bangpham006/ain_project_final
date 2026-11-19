"""IT Troubleshooting Expert System — Interactive Diagnostic Application.

Final Milestone product built on top of the validated forward-chaining AI core
(`student_core.py`) and meta-level conflict checker (`conflicts.py`):
- 100% offline execution (no external fonts, CDNs, or hosted APIs).
- Unified Enterprise Light-Slate UI engineered for projector & desktop clarity.
- Interactive symptom selection organised across the 5 campus IT domains.
- Top-positioned Dynamic Follow-Up Questioning (`suggest_followups`) with
  callback-safe Yes/No consultation memory and per-symptom Undo (`Restore SYMxx ×`).
- Live visual reasoning graph (layered SVG + Graphviz DOT specification).
- Explicit multi-fault cluster decomposition (`group_candidates`) and
  interactive rule-ablation sandbox (`R001`-`R048`).
"""

from __future__ import annotations

import html
import sys
from pathlib import Path
from typing import Any

import streamlit as st

STARTER_DIR = Path(__file__).resolve().parent
if str(STARTER_DIR) not in sys.path:
    sys.path.insert(0, str(STARTER_DIR))

import conflicts as conflicts_mod  # noqa: E402
import reasoning_graph  # noqa: E402
import rule_loader  # noqa: E402
import student_core  # noqa: E402

DATA_DIR = STARTER_DIR.parent / "data"

DOMAIN_ORDER = [
    "hanu_wifi",
    "fit_lms",
    "lab_computers",
    "hanu_account",
    "fit_printer",
]

DOMAIN_CONFIG: dict[str, dict[str, str]] = {
    "hanu_wifi": {"label": "Campus Wi-Fi", "badge_class": "badge-wifi"},
    "fit_lms": {"label": "FIT LMS", "badge_class": "badge-lms"},
    "lab_computers": {"label": "Lab Computers", "badge_class": "badge-lab"},
    "hanu_account": {"label": "Student Accounts", "badge_class": "badge-account"},
    "fit_printer": {"label": "Network Printer", "badge_class": "badge-printer"},
}

STRESS_PRESETS: dict[str, dict[str, Any]] = {
    "STRESS_MF01_wifi_and_lms": {
        "id": "STRESS_MF01_wifi_and_lms",
        "class": "multi_fault",
        "domain": "hanu_wifi",
        "presented_symptoms": ["SYM01", "SYM06", "SYM07"],
        "description": "Concurrent two-domain incident: HANU_Student captive portal redirect loop plus missing AIN301 course on FIT LMS.",
        "reasoning_probe": "Verify that the engine partitions the candidates into two disjoint fault clusters without conflating them.",
    },
    "STRESS_MF02_triple_campus_incident": {
        "id": "STRESS_MF02_triple_campus_incident",
        "class": "multi_fault",
        "domain": "lab_computers",
        "presented_symptoms": ["SYM03", "SYM04", "SYM05", "SYM12", "SYM18"],
        "description": "Complex three-domain incident: Wi-Fi drop resolved by laptop-only clue (CAUSE02 > CAUSE03), Lab GRUB boot failure (CAUSE07), and unlicensed M365 (CAUSE12).",
        "reasoning_probe": "Confirm independent arbitration inside Cluster 1 (CAUSE02 > CAUSE03) alongside single-cause Clusters 2 and 3.",
    },
}

STATUS_DATA: dict[str, dict[str, str]] = {
    "single_cause": {
        "title": "SINGLE CAUSE DETERMINED",
        "css_class": "status-single-cause",
        "desc": "Reported observations form a deterministic deductive chain leading to one supported root cause.",
    },
    "resolved": {
        "title": "COMPETING HYPOTHESES RESOLVED",
        "css_class": "status-resolved",
        "desc": "Multiple competing causes fired on shared symptoms; conflict resolution ranked a unique primary cause while retaining alternatives.",
    },
    "ambiguous": {
        "title": "AMBIGUOUS MULTI-CAUSE INCIDENT",
        "css_class": "status-ambiguous",
        "desc": "Competing hypotheses tie under the active arbitration strategy. Answer the dynamic follow-up questions immediately below to disambiguate.",
    },
    "multi_fault": {
        "title": "MULTI-FAULT CONCURRENT INCIDENT",
        "css_class": "status-multi-fault",
        "desc": "Multiple independent root causes detected across disjoint symptom clusters. Each fault cluster requires its own remediation action.",
    },
    "contradictory": {
        "title": "CONTRADICTORY EVIDENCE DETECTED",
        "css_class": "status-contradictory",
        "desc": "Reported symptoms violate physical/logical integrity constraints (conflicts.json). Monotonic conclusions are shown below with conflict audit flags.",
    },
    "insufficient_evidence": {
        "title": "INSUFFICIENT SYMPTOM EVIDENCE",
        "css_class": "status-insufficient",
        "desc": "Current observations satisfy zero rule preconditions. Premature guessing is suppressed; answer the guided follow-up questions immediately below.",
    },
}

PRINTER_KB_AUDIT_NOTE = (
    "KB Audit Note (data_issues.md #1): In the provided dataset, causes.json assigns "
    "CAUSE13 to OS printer driver mismatch and CAUSE14 to empty toner / jam sensor, "
    "whereas rules.json comments (R036-R041) and SC02 text invert those two labels. "
    "Because deductive inference operates strictly on symbolic IDs, operators should "
    "verify both the fired rule comment and the physical queue/toner state in P.210."
)

CUSTOM_CSS = """
<style>
html, body, [class*="css"] {
    font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif;
}

/* Primary Buttons: Royal Blue instead of Streamlit Coral Red */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid #1E40AF !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.24) !important;
    transition: all 0.15s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1D4ED8 0%, #1E3A8A 100%) !important;
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.34) !important;
}

/* Secondary Buttons: Crisp Slate Outline */
div.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
div.stButton > button[kind="secondary"]:hover {
    background: #F1F5F9 !important;
    border-color: #94A3B8 !important;
    color: #0F172A !important;
}

/* Header Banner */
.portal-header {
    background: linear-gradient(135deg, #EFF6FF 0%, #F8FAFC 100%);
    border: 1px solid #BFDBFE;
    border-left: 5px solid #2563EB;
    border-radius: 12px;
    padding: 18px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.portal-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.02em;
    margin: 0;
}

.portal-subtitle {
    font-size: 0.88rem;
    color: #475569;
    margin-top: 4px;
}

.breadcrumb-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
    font-size: 0.75rem;
    color: #64748B;
    font-family: Consolas, "Cascadia Mono", monospace;
}

.breadcrumb-tag {
    background: #FFFFFF;
    color: #1E3A8A;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid #BFDBFE;
    font-weight: 600;
}

/* Domain Badges */
.domain-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 9px;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: Consolas, "Cascadia Mono", monospace;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

.badge-wifi { background: #DBEAFE; color: #1D4ED8; border: 1px solid #93C5FD; }
.badge-lms { background: #F3E8FF; color: #7E22CE; border: 1px solid #D8B4FE; }
.badge-lab { background: #CCFBF1; color: #0F766E; border: 1px solid #5EEAD4; }
.badge-account { background: #FEF3C7; color: #B45309; border: 1px solid #FCD34D; }
.badge-printer { background: #FCE7F3; color: #BE185D; border: 1px solid #F9A8D4; }

/* Unified Light-Slate Status Hero Cards */
.status-hero {
    border-radius: 12px;
    padding: 16px 20px;
    margin: 10px 0 14px 0;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}

.status-single-cause { background: #ECFDF5; border: 1.5px solid #10B981; border-left: 6px solid #059669; }
.status-resolved { background: #EFF6FF; border: 1.5px solid #60A5FA; border-left: 6px solid #2563EB; }
.status-ambiguous { background: #FFFBEB; border: 1.5px solid #FBBF24; border-left: 6px solid #D97706; }
.status-contradictory { background: #FEF2F2; border: 1.5px solid #F87171; border-left: 6px solid #DC2626; }
.status-multi-fault { background: #F5F3FF; border: 1.5px solid #A78BFA; border-left: 6px solid #7C3AED; }
.status-insufficient { background: #F8FAFC; border: 1.5px solid #CBD5E1; border-left: 6px solid #64748B; }

.status-title { font-size: 1.08rem; font-weight: 700; margin-bottom: 4px; }
.status-single-cause .status-title { color: #065F46; }
.status-resolved .status-title { color: #1E40AF; }
.status-ambiguous .status-title { color: #92400E; }
.status-contradictory .status-title { color: #991B1B; }
.status-multi-fault .status-title { color: #5B21B6; }
.status-insufficient .status-title { color: #334155; }

.status-desc { font-size: 0.88rem; color: #1E293B; line-height: 1.48; }

/* Follow-up Triage Card */
.followup-panel {
    background: #F8FAFC;
    border: 1.5px solid #93C5FD;
    border-radius: 12px;
    padding: 14px 18px 6px 18px;
    margin: 8px 0 16px 0;
}

.followup-card {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #2563EB;
    border-radius: 9px;
    padding: 10px 14px;
    margin-bottom: 8px;
}

/* Remediation & Audit Cards */
.remediation-card {
    background: #ECFDF5;
    border: 1.5px solid #34D399;
    border-left: 5px solid #059669;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 6px 0;
}

.remediation-header {
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #065F46;
    margin-bottom: 5px;
}

.remediation-body { font-size: 0.9rem; color: #0F172A; font-weight: 500; line-height: 1.48; }

.audit-card {
    background: #FFFBEB;
    border: 1px solid #F59E0B;
    border-left: 4px solid #D97706;
    border-radius: 9px;
    padding: 10px 14px;
    margin-top: 8px;
    font-size: 0.81rem;
    color: #78350F;
    line-height: 1.45;
}

/* Proof Trace Steps */
.pipeline-step {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #2563EB;
    border-radius: 8px;
    padding: 9px 13px;
    margin-bottom: 7px;
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 0.84rem;
}

.rule-id { color: #1D4ED8; font-weight: 700; margin-right: 8px; }
.rule-logic { color: #0F172A; font-weight: 600; }
.rule-comment {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 0.79rem;
    color: #475569;
    margin-top: 3px;
}

.conflict-card {
    background: #FEF2F2;
    border: 1.5px solid #FCA5A5;
    border-left: 5px solid #DC2626;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
}

.cluster-card {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #6366F1;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
}

.sidebar-box {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #2563EB;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 12px;
}
</style>
"""


@st.cache_data
def load_kb() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    kb_data = rule_loader.load_all(DATA_DIR)
    sym_ids = {s["id"] for s in kb_data["symptoms"]}
    confs = conflicts_mod.load_conflicts(DATA_DIR / "conflicts.json", sym_ids)
    return kb_data, confs


def compute_followup_partitions(
    selected_symptoms: list[str],
    active_rules: list[dict[str, Any]],
    conflicts_list: list[dict[str, Any]],
    all_symptoms: list[dict[str, Any]],
    *,
    domain_filter: str = "ALL",
    denied_symptoms: set[str] | None = None,
    strategy: str = student_core.DEFAULT_STRATEGY,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split candidate follow-up questions into (valid_questions, contradictory_questions)."""
    denied = denied_symptoms or set()
    if domain_filter == "ALL":
        pool = [s["id"] for s in all_symptoms if s["id"] not in denied]
    else:
        pool = [
            s["id"]
            for s in all_symptoms
            if s["domain"] == domain_filter and s["id"] not in denied
        ]
    raw = student_core.suggest_followups(
        selected_symptoms,
        active_rules,
        conflicts_list,
        candidates=pool,
        strategy=strategy,
    )
    valid = [item for item in raw if item["status"] != "contradictory"]
    contradictory = [item for item in raw if item["status"] == "contradictory"]
    return valid, contradictory


def main() -> None:
    st.set_page_config(
        page_title="FIT HANU — IT Expert System",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    try:
        kb, conflicts_list = load_kb()
    except Exception as exc:
        st.error(f"Failed to load knowledge base: {exc}")
        st.stop()

    symptoms = kb["symptoms"]
    sym_dict = {s["id"]: s for s in symptoms}
    causes_dict = {c["id"]: c for c in kb["causes"]}
    all_rules = kb["rules"]
    domains = [d for d in DOMAIN_ORDER if any(s["domain"] == d for s in symptoms)]

    scenarios_by_id: dict[str, dict[str, Any]] = {s["id"]: s for s in kb["scenarios"]}
    scenarios_by_id.update(STRESS_PRESETS)

    if "denied_symptoms" not in st.session_state:
        st.session_state["denied_symptoms"] = set()

    def _reset_all_callback() -> None:
        for s in symptoms:
            st.session_state[f"chk_{s['id']}"] = False
        st.session_state["denied_symptoms"] = set()
        st.session_state["scenario_select"] = "Custom Selection"
        st.session_state["last_scenario"] = "Custom Selection"

    def _clear_denied_callback() -> None:
        st.session_state["denied_symptoms"] = set()

    def _restore_single_denied_callback(sym_id: str) -> None:
        updated = set(st.session_state.get("denied_symptoms", set()))
        updated.discard(sym_id)
        st.session_state["denied_symptoms"] = updated

    def _confirm_symptom_callback(sym_id: str) -> None:
        st.session_state[f"chk_{sym_id}"] = True

    def _deny_symptom_callback(sym_id: str) -> None:
        updated = set(st.session_state.get("denied_symptoms", set()))
        updated.add(sym_id)
        st.session_state["denied_symptoms"] = updated

    # Sidebar Controls
    with st.sidebar:
        st.markdown("### Diagnostic Scenario Fixture")
        scenario_options = ["Custom Selection"] + list(scenarios_by_id.keys())
        scenario_choice = st.selectbox(
            "Load Benchmark or Stress Fixture:",
            scenario_options,
            key="scenario_select",
        )

        active_fixture = scenarios_by_id.get(scenario_choice)
        preselected: list[str] = active_fixture["presented_symptoms"] if active_fixture else []

        if active_fixture:
            probe_html = ""
            if active_fixture.get("reasoning_probe"):
                probe_html = (
                    f"<div style='font-size:0.78rem; color:#475569; margin-top:8px; "
                    f"border-top:1px solid #E2E8F0; padding-top:6px;'>"
                    f"<b>Oral-Defence Probe:</b> {html.escape(active_fixture['reasoning_probe'])}</div>"
                )
            st.markdown(
                f"""
                <div class="sidebar-box">
                    <div style="font-size:0.74rem; font-weight:700; color:#1D4ED8; text-transform:uppercase;">
                        CLASS: {html.escape(active_fixture['class'])} • {html.escape(active_fixture['domain'])}
                    </div>
                    <div style="font-size:0.84rem; color:#1E293B; margin-top:5px; line-height:1.42;">
                        {html.escape(active_fixture['description'])}
                    </div>
                    {probe_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### Conflict Resolution Strategy")
        strategy = st.selectbox(
            "Arbitration Rule:",
            options=["specificity", "coverage", "rule_count"],
            index=0,
            help=(
                "specificity: prefer causes proven by rules with more premises, then broader symptom support. "
                "coverage: prefer broader symptom support first. "
                "rule_count: prefer causes concluded by more rules."
            ),
        )

        st.markdown("---")
        st.markdown("### Rule Ablation Sandbox")
        disabled_rule_ids = st.multiselect(
            "Temporarily disable rules (e.g. R007 for SC04):",
            options=[r["id"] for r in all_rules],
            default=[],
            help="Reproduces Midterm Experiment E1 interactively: disable R007 on SC04 to observe ambiguous -> resolved.",
        )

    # Synchronise fixture changes into checkbox state & default follow-up domain
    if st.session_state.get("last_scenario") != scenario_choice:
        st.session_state["last_scenario"] = scenario_choice
        st.session_state["denied_symptoms"] = set()
        for s in symptoms:
            st.session_state[f"chk_{s['id']}"] = s["id"] in preselected
        if active_fixture and not preselected:
            st.session_state["followup_domain"] = active_fixture["domain"]
        else:
            st.session_state["followup_domain"] = "AUTO"

    active_rules = [r for r in all_rules if r["id"] not in set(disabled_rule_ids)]
    rules_dict = {r["id"]: r for r in all_rules}

    # Header Banner
    ablation_tag = (
        f"ABLATION: -{len(disabled_rule_ids)} RULES ({', '.join(disabled_rule_ids)})"
        if disabled_rule_ids
        else f"ACTIVE KB: {len(active_rules)} RULES / 5 CONFLICTS"
    )
    st.markdown(
        f"""
        <div class="portal-header">
            <h1 class="portal-title">IT Troubleshooting Expert System</h1>
            <div class="portal-subtitle">
                Deductive Forward-Chaining Inference, Visual Proof Graph &amp; Dynamic Disambiguation • FIT HANU Helpdesk
            </div>
            <div class="breadcrumb-bar">
                <span class="breadcrumb-tag">ENGINE: MONOTONIC HORN FIXPOINT</span>
                <span>/</span>
                <span class="breadcrumb-tag">STRATEGY: {html.escape(strategy.upper())}</span>
                <span>/</span>
                <span class="breadcrumb-tag">{html.escape(ablation_tag)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Symptom Checklist Controls
    st.markdown("### 1. Observed Symptom Selection")
    ctrl_col1, ctrl_col2 = st.columns([3.5, 1.2])
    with ctrl_col1:
        search_query = st.text_input(
            "Filter symptoms by keyword or ID:",
            value="",
            placeholder="Search symptoms by keyword or ID (e.g. Wi-Fi, portal, LMS, GRUB, printer, SYM03)...",
            label_visibility="collapsed",
        ).strip().lower()
    with ctrl_col2:
        st.button(
            "Reset All Observations",
            on_click=_reset_all_callback,
            use_container_width=True,
        )

    tab_labels = []
    for d in domains:
        dom_syms = [s for s in symptoms if s["domain"] == d]
        active_cnt = sum(1 for s in dom_syms if st.session_state.get(f"chk_{s['id']}", False))
        lbl = DOMAIN_CONFIG.get(d, {}).get("label", d)
        tab_labels.append(f"{lbl} ({active_cnt}/{len(dom_syms)})")

    tabs = st.tabs(tab_labels)
    for idx, d in enumerate(domains):
        with tabs[idx]:
            dom_syms = [s for s in symptoms if s["domain"] == d]
            visible_syms = [
                s
                for s in dom_syms
                if not search_query
                or search_query in s["id"].lower()
                or search_query in s["description"].lower()
            ]
            if not visible_syms:
                st.caption("No symptoms in this domain match the active search filter.")
            for s in visible_syms:
                sid = s["id"]
                if f"chk_{sid}" not in st.session_state:
                    st.session_state[f"chk_{sid}"] = sid in preselected
                st.checkbox(
                    f"{sid} — {s['description']}",
                    key=f"chk_{sid}",
                )

    selected_list = sorted(
        s["id"] for s in symptoms if st.session_state.get(f"chk_{s['id']}", False)
    )

    # Active Symptom Summary Bar
    st.markdown(f"#### Active Working Memory ({len(selected_list)} reported)")
    if selected_list:
        chips_html = "".join(
            f"<div style='display:inline-block; background:#FFFFFF; border:1px solid #CBD5E1; "
            f"border-radius:8px; padding:4px 10px; margin:3px 6px 3px 0;'>"
            f"<span class='domain-badge {DOMAIN_CONFIG.get(sym_dict[sid]['domain'], {}).get('badge_class', 'badge-wifi')}'>"
            f"{html.escape(sid)}</span> "
            f"<span style='font-size:0.83rem; color:#0F172A; margin-left:6px;'>"
            f"{html.escape(sym_dict[sid]['description'])}</span></div>"
            for sid in selected_list
        )
        st.markdown(f"<div>{chips_html}</div>", unsafe_allow_html=True)
    else:
        st.caption(
            "Working memory is currently empty (0 symptoms). Select symptoms above, load a scenario from the sidebar, "
            "or answer the guided triage questions below."
        )

    # Execute Core Diagnosis (always runs, including empty input SC06)
    report = student_core.diagnose(
        selected_list,
        active_rules,
        conflicts_list,
        strategy=strategy,
    )
    status = report["status"]
    s_meta = STATUS_DATA.get(status, STATUS_DATA["insufficient_evidence"])

    st.markdown("---")
    st.markdown("### 2. Deductive Assessment & Interactive Triage")

    # Summary Metrics Strip
    m1, m2, m3, m4 = st.columns([1.55, 0.85, 0.85, 1.15])
    fired_total = sum(len(r["fired_rules"]) for r in report["results"])
    m1.metric("Diagnostic Status", status.replace("_", " ").title())
    m2.metric("Candidate Causes", len(report["results"]))
    m3.metric("Fault Clusters", len(report["groups"]))
    m4.metric("Fired Rules / Conflicts", f"{fired_total} / {len(report['conflicts'])}")

    # Status Hero Banner
    st.markdown(
        f"""
        <div class="status-hero {s_meta['css_class']}">
            <div class="status-title">{html.escape(s_meta['title'])}</div>
            <div class="status-desc">{html.escape(s_meta['desc'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Per-Symptom Ruled-Out ("No") Undo Bar — always visible whenever consultation history exists
    denied_set: set[str] = set(st.session_state.get("denied_symptoms", set()))
    if denied_set:
        st.markdown("**Ruled-Out Follow-Up Answers (`No`) — Click to Undo Individually:**")
        sorted_denied = sorted(denied_set)
        undo_cols = st.columns(min(len(sorted_denied) + 1, 6))
        for u_i, d_sid in enumerate(sorted_denied[:5]):
            with undo_cols[u_i]:
                st.button(
                    f"Undo No: {d_sid} ×",
                    key=f"undo_{d_sid}",
                    on_click=_restore_single_denied_callback,
                    args=(d_sid,),
                    use_container_width=True,
                )
        with undo_cols[min(len(sorted_denied), 5)]:
            st.button(
                "Clear All Ruled-Out",
                key="clear_all_denied_inline",
                on_click=_clear_denied_callback,
                use_container_width=True,
            )

    # Contradiction Notification
    if report["conflicts"]:
        st.markdown("#### Integrity Constraint Violations (`conflicts.json`)")
        for c in report["conflicts"]:
            s_left, s_right = c["symptoms"][0], c["symptoms"][1]
            st.markdown(
                f"""
                <div class="conflict-card">
                    <span style="font-family:Consolas,monospace; font-weight:700; color:#991B1B;">
                        CONFLICT [{html.escape(c['id'])}]:
                    </span>
                    <span style="font-weight:700; color:#0F172A; margin-left:6px;">
                        {html.escape(s_left)} ⟷ {html.escape(s_right)}
                    </span>
                    <div style="font-size:0.85rem; color:#334155; margin-top:4px;">
                        {html.escape(c['reason'])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Dynamic Follow-Up Questioning — Positioned IMMEDIATELY below Status Banner!
    show_followups = status in {"ambiguous", "insufficient_evidence"}
    if not show_followups and status == "resolved":
        show_followups = st.checkbox(
            "Show optional follow-up questions to further confirm or challenge the resolved cause",
            value=False,
        )

    if show_followups:
        st.markdown("#### Dynamic Follow-Up Questioning (`suggest_followups`)")

        inferred_domains = sorted({sym_dict[s]["domain"] for s in selected_list})
        if len(inferred_domains) == 1:
            auto_domain = inferred_domains[0]
        elif active_fixture and not selected_list:
            auto_domain = active_fixture["domain"]
        else:
            auto_domain = "ALL"

        domain_choices = ["AUTO"] + domains + ["ALL"]
        domain_labels = {
            "AUTO": (
                f"Auto Scope ({DOMAIN_CONFIG[auto_domain]['label']})"
                if auto_domain != "ALL"
                else "Auto Scope (All 5 Domains)"
            ),
            "ALL": "All 5 Support Domains",
            **{d: DOMAIN_CONFIG[d]["label"] for d in domains},
        }

        fcol1, fcol2 = st.columns([2.1, 2.9])
        with fcol1:
            chosen_scope = st.selectbox(
                "Questioning Domain Scope:",
                options=domain_choices,
                format_func=lambda k: domain_labels.get(k, k),
                key="followup_domain",
            )
        with fcol2:
            st.caption(
                "Questions are ranked most-decisive-first via one-step forward-chaining simulation. "
                "Confirm ('Yes') to add evidence or rule out ('No') to advance to the next hypothesis."
            )
        effective_domain = auto_domain if chosen_scope == "AUTO" else chosen_scope

        valid_qs, contra_qs = compute_followup_partitions(
            selected_list,
            active_rules,
            conflicts_list,
            symptoms,
            domain_filter=effective_domain,
            denied_symptoms=denied_set,
            strategy=strategy,
        )

        if valid_qs:
            for q in valid_qs[:4]:
                q_sid = q["symptom"]
                q_sym = sym_dict[q_sid]
                b_cls = DOMAIN_CONFIG.get(q_sym["domain"], {}).get(
                    "badge_class", "badge-wifi"
                )
                leaders_txt = ", ".join(q["leaders"]) if q["leaders"] else "none"
                rules_txt = ", ".join(q["new_rules"])

                q_col, yes_col, no_col = st.columns([4.2, 1.0, 1.0])
                with q_col:
                    st.markdown(
                        f"""
                        <div class="followup-card">
                            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                                <span class="domain-badge {b_cls}">{html.escape(q_sid)}</span>
                                <span style="font-weight:600; color:#0F172A; font-size:0.89rem;">
                                    Do you observe: {html.escape(q_sym['description'])}?
                                </span>
                            </div>
                            <div style="font-size:0.78rem; color:#475569; margin-top:4px; font-family:Consolas,monospace;">
                                If YES ➔ status: <b>{html.escape(q['status'])}</b> • leader(s): <b>{html.escape(leaders_txt)}</b> • fires: {html.escape(rules_txt)}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with yes_col:
                    st.button(
                        f"Yes ({q_sid})",
                        key=f"yes_{q_sid}",
                        type="primary",
                        on_click=_confirm_symptom_callback,
                        args=(q_sid,),
                        use_container_width=True,
                    )
                with no_col:
                    st.button(
                        f"No ({q_sid})",
                        key=f"no_{q_sid}",
                        on_click=_deny_symptom_callback,
                        args=(q_sid,),
                        use_container_width=True,
                    )
        else:
            st.info(
                "No remaining non-contradictory single symptom in this domain scope can fire a new rule. "
                "Switch Questioning Domain Scope to 'All 5 Support Domains' or undo ruled-out answers above."
            )

        if contra_qs:
            with st.expander(
                f"Suppressed Contradictory Follow-Ups ({len(contra_qs)} incompatible with current evidence)"
            ):
                for cq in contra_qs:
                    cq_sid = cq["symptom"]
                    violated = student_core.detect_conflicts(
                        selected_list + [cq_sid], conflicts_list
                    )
                    v_ids = ", ".join(c["id"] for c in violated)
                    st.markdown(
                        f"- <span style='color:#475569;'><code>{html.escape(cq_sid)}</code> — "
                        f"{html.escape(sym_dict[cq_sid]['description'])} "
                        f"<i>(suppressed: would trigger conflict {html.escape(v_ids)})</i></span>",
                        unsafe_allow_html=True,
                    )

    # 3. Visual Reasoning Graph
    st.markdown("### 3. Visual Reasoning Graph")
    svg_xml = reasoning_graph.build_reasoning_svg(
        selected_list,
        report,
        kb,
        active_rules=active_rules,
    )
    svg_uri = reasoning_graph.svg_to_data_uri(svg_xml)
    st.markdown(
        f'<img src="{svg_uri}" alt="Visual Reasoning Graph" '
        f'style="width:100%; height:auto; border-radius:12px; display:block; margin-bottom:8px;"/>',
        unsafe_allow_html=True,
    )
    with st.expander("Inspect Formal Graphviz DOT Representation"):
        st.code(
            reasoning_graph.build_reasoning_dot(
                selected_list, report, kb, active_rules=active_rules
            ),
            language="dot",
        )

    # 4. Fault Cluster Decomposition
    if report["groups"]:
        st.markdown("### 4. Fault Cluster & Conflict-Resolution Breakdown")
        res_by_id = {r["cause_id"]: r for r in report["results"]}
        for g_idx, (grp, ranking) in enumerate(zip(report["groups"], report["rankings"]), 1):
            shared_syms = sorted(
                {s for cid in grp for s in res_by_id[cid]["supporting_symptoms"]}
            )
            order_expr = "  >  ".join(" = ".join(tier) for tier in ranking)
            cluster_kind = (
                "Competing Hypothesis Cluster (Tie)"
                if len(ranking[0]) > 1
                else (
                    "Competing Hypothesis Cluster (Resolved)"
                    if len(grp) > 1
                    else "Independent Single-Cause Cluster"
                )
            )
            st.markdown(
                f"""
                <div class="cluster-card">
                    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                        <span style="font-weight:700; color:#1D4ED8; font-family:Consolas,monospace;">
                            CLUSTER #{g_idx} • {html.escape(cluster_kind)}
                        </span>
                        <span style="font-family:Consolas,monospace; font-size:0.85rem; color:#0F172A;">
                            Ranking ({html.escape(strategy)}): <b>{html.escape(order_expr)}</b>
                        </span>
                    </div>
                    <div style="font-size:0.83rem; color:#475569; margin-top:5px;">
                        Supporting Evidence Cluster: <code>{html.escape(', '.join(shared_syms))}</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 5. Candidate Causes & Actionable Remediation Recommendations
    if report["results"]:
        st.markdown("### 5. Diagnosed Root Causes & Actionable Remediations")
        tied_causes = {cid for grp in report["ambiguous_groups"] for cid in grp}

        for res in report["results"]:
            cid = res["cause_id"]
            is_leader = cid in report["leaders"]
            cause_data = causes_dict.get(cid, {})
            dom_key = cause_data.get("domain", "")
            badge_cls = DOMAIN_CONFIG.get(dom_key, {}).get("badge_class", "badge-wifi")
            dom_lbl = DOMAIN_CONFIG.get(dom_key, {}).get("label", dom_key)

            if status == "contradictory":
                role_tag = " [CONFLICTED CANDIDATE]"
            elif cid in tied_causes:
                role_tag = " [TIED CO-LEADER]"
            elif is_leader:
                role_tag = " [PRIMARY CAUSE]"
            else:
                role_tag = " [ALTERNATIVE HYPOTHESIS]"

            exp_title = f"{cid} • {cause_data.get('description', '')}{role_tag}"
            with st.expander(exp_title, expanded=is_leader):
                c_left, c_right = st.columns([1.05, 1.0])
                with c_left:
                    st.markdown(
                        f"""
                        <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:8px; padding:12px; margin-bottom:10px;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                                <span style="color:#475569; font-size:0.82rem;">Support Domain:</span>
                                <span class="domain-badge {badge_cls}">{html.escape(dom_lbl)}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                                <span style="color:#475569; font-size:0.82rem;">Max Rule Specificity:</span>
                                <span style="font-weight:700; color:#1D4ED8; font-family:Consolas,monospace;">{res['specificity']}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between;">
                                <span style="color:#475569; font-size:0.82rem;">Fired Rules Supporting Cause:</span>
                                <span style="font-weight:700; color:#1D4ED8; font-family:Consolas,monospace;">{len(res['fired_rules'])} ({html.escape(', '.join(res['fired_rules']))})</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("**Supporting Reported Symptoms:**")
                    for sid in res["supporting_symptoms"]:
                        st.markdown(
                            f"- `{sid}`: {sym_dict[sid]['description']}"
                        )

                with c_right:
                    remediation = cause_data.get(
                        "recommended_action", "No remediation specified."
                    )
                    st.markdown(
                        f"""
                        <div class="remediation-card">
                            <div class="remediation-header">Actionable Remediation Recommendation</div>
                            <div class="remediation-body">{html.escape(remediation)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if cid in {"CAUSE13", "CAUSE14"}:
                        st.markdown(
                            f'<div class="audit-card">{html.escape(PRINTER_KB_AUDIT_NOTE)}</div>',
                            unsafe_allow_html=True,
                        )

                st.markdown("**Chronological Proof Trace (`explain`):**")
                traces = report["traces"].get(cid, [])
                for rid in traces:
                    rule = rules_dict[rid]
                    premise_str = " ∧ ".join(rule["if"])
                    comment_html = (
                        f"<div class='rule-comment'>// {html.escape(rule['comment'])}</div>"
                        if rule.get("comment")
                        else ""
                    )
                    st.markdown(
                        f"""
                        <div class="pipeline-step">
                            <span class="rule-id">{html.escape(rid)}:</span>
                            <span class="rule-logic">{html.escape(premise_str)} ➔ {html.escape(rule['then'])}</span>
                            {comment_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


if __name__ == "__main__":
    main()
