"""IT Troubleshooting Expert System — Enterprise Diagnostic Dashboard.

Refactored with Modern Tech / Elevated 3D UI:
- Multi-layer elevation, subtle border highlights, clean typography.
- Zero generic emojis; professional badges, pills, and SVG-styled indicators.
- 100% preservation of forward-chaining deduction and domain KB.
"""

from __future__ import annotations

from pathlib import Path
import streamlit as st

import conflicts as conflicts_mod
import rule_loader
import student_core

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

st.set_page_config(
    page_title="FIT HANU — IT Expert System Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom 3D Elevated CSS
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* Modern Header Banner */
.portal-header {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
}

.portal-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #F8FAFC;
    letter-spacing: -0.02em;
    margin: 0;
}

.portal-subtitle {
    font-size: 0.9rem;
    color: #94A3B8;
    margin-top: 6px;
    letter-spacing: 0.01em;
}

/* Breadcrumb Bar */
.breadcrumb-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 14px;
    font-size: 0.78rem;
    color: #64748B;
    font-family: 'JetBrains Mono', monospace;
}

.breadcrumb-tag {
    background: rgba(148, 163, 184, 0.1);
    color: #CBD5E1;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}

/* Domain Badges / Pills */
.domain-badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

.badge-wifi { background: rgba(59, 130, 246, 0.12); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.3); }
.badge-lms { background: rgba(168, 85, 247, 0.12); color: #C084FC; border: 1px solid rgba(168, 85, 247, 0.3); }
.badge-lab { background: rgba(20, 184, 166, 0.12); color: #2DD4BF; border: 1px solid rgba(20, 184, 166, 0.3); }
.badge-account { background: rgba(245, 158, 11, 0.12); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-printer { background: rgba(236, 72, 153, 0.12); color: #F472B6; border: 1px solid rgba(236, 72, 153, 0.3); }

/* Hero Action Button */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 10px !important;
    padding: 12px 28px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35), 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 22px rgba(37, 99, 235, 0.45) !important;
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
}

div.stButton > button[kind="primary"]:active {
    transform: translateY(1px) !important;
}

/* Secondary Button (Reset) */
div.stButton > button[kind="secondary"] {
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background: rgba(30, 41, 59, 0.6) !important;
    color: #94A3B8 !important;
    transition: all 0.15s ease !important;
}
div.stButton > button[kind="secondary"]:hover {
    background: rgba(51, 65, 85, 0.8) !important;
    color: #F8FAFC !important;
    transform: translateY(-1px) !important;
}

/* Status Hero Banners with 3D Elevation */
.status-hero {
    border-radius: 14px;
    padding: 20px 24px;
    margin: 20px 0 24px 0;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2);
    position: relative;
    overflow: hidden;
}

.status-single-cause {
    background: linear-gradient(135deg, rgba(5, 150, 105, 0.18) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid #059669;
}
.status-resolved {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.18) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid #2563EB;
}
.status-ambiguous {
    background: linear-gradient(135deg, rgba(217, 119, 6, 0.18) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid #D97706;
}
.status-contradictory {
    background: linear-gradient(135deg, rgba(220, 38, 38, 0.18) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid #DC2626;
}
.status-multi-fault {
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.18) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid #7C3AED;
}
.status-insufficient {
    background: linear-gradient(135deg, rgba(71, 85, 105, 0.22) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid #475569;
}

.status-title {
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    margin-bottom: 6px;
}
.status-single-cause .status-title { color: #34D399; }
.status-resolved .status-title { color: #60A5FA; }
.status-ambiguous .status-title { color: #FBBF24; }
.status-contradictory .status-title { color: #F87171; }
.status-multi-fault .status-title { color: #C084FC; }
.status-insufficient .status-title { color: #94A3B8; }

.status-desc {
    font-size: 0.88rem;
    color: #CBD5E1;
    line-height: 1.5;
}

/* Remediation Plan Box */
.remediation-card {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.04) 100%);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 12px 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.remediation-header {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #34D399;
    margin-bottom: 8px;
}

.remediation-body {
    font-size: 0.92rem;
    font-weight: 500;
    color: #F1F5F9;
    line-height: 1.5;
}

/* Pipeline Step for Proof Trace */
.pipeline-step {
    background: #1E293B;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-left: 3px solid #3B82F6;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.rule-id {
    color: #38BDF8;
    font-weight: 600;
    margin-right: 8px;
}
.rule-logic {
    color: #E2E8F0;
}
.rule-comment {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #94A3B8;
    margin-top: 4px;
}

/* Conflict Alert Box */
.conflict-card {
    background: rgba(220, 38, 38, 0.08);
    border: 1px solid rgba(220, 38, 38, 0.35);
    border-radius: 12px;
    padding: 14px 18px;
    margin: 12px 0;
}
.conflict-id {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    color: #F87171;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #0F172A;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-box {
    background: #1E293B;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

DOMAIN_CONFIG = {
    "hanu_wifi": {"label": "Campus Wi-Fi", "badge_class": "badge-wifi"},
    "fit_lms": {"label": "FIT LMS", "badge_class": "badge-lms"},
    "lab_computers": {"label": "Lab Computers", "badge_class": "badge-lab"},
    "hanu_account": {"label": "Student Accounts", "badge_class": "badge-account"},
    "fit_printer": {"label": "Network Printer", "badge_class": "badge-printer"},
}

STATUS_DATA = {
    "single_cause": {
        "title": "SINGLE CAUSE DETERMINED",
        "css_class": "status-single-cause",
        "desc": "Reported symptoms form a deterministic closed trail leading exclusively to one verified failure cause.",
    },
    "resolved": {
        "title": "COMPETING HYPOTHESES RESOLVED",
        "css_class": "status-resolved",
        "desc": "Multiple causes triggered, but structural specificity arbitration prioritised the most precise hypothesis.",
    },
    "ambiguous": {
        "title": "AMBIGUOUS MULTI-CAUSE INCIDENT",
        "css_class": "status-ambiguous",
        "desc": "Competing hypotheses exhibit identical specificity and support counts. Discriminative follow-up is required.",
    },
    "multi_fault": {
        "title": "MULTI-FAULT CONCURRENT INCIDENT",
        "css_class": "status-multi-fault",
        "desc": "Independent failure causes identified across disjoint observation clusters. Each requires dedicated remediation.",
    },
    "contradictory": {
        "title": "CONTRADICTORY EVIDENCE DETECTED",
        "css_class": "status-contradictory",
        "desc": "Input symptoms include mutually incompatible device states governed by domain constraint rules.",
    },
    "insufficient_evidence": {
        "title": "INSUFFICIENT SYMPTOM EVIDENCE",
        "css_class": "status-insufficient",
        "desc": "Current observations satisfy no rule preconditions. Non-monotonic speculation is strictly suppressed.",
    },
}

@st.cache_data
def load_kb():
    kb_data = rule_loader.load_all(DATA_DIR)
    sym_ids = {s["id"] for s in kb_data["symptoms"]}
    confs = conflicts_mod.load_conflicts(DATA_DIR / "conflicts.json", sym_ids)
    return kb_data, confs

try:
    kb, conflicts_list = load_kb()
except Exception as exc:
    st.error(f"Failed to load knowledge base: {exc}")
    st.stop()

symptoms = kb["symptoms"]
sym_dict = {s["id"]: s for s in symptoms}
causes_dict = {c["id"]: c for c in kb["causes"]}
rules_dict = {r["id"]: r for r in kb["rules"]}
domains = sorted({s["domain"] for s in symptoms})

# Top Enterprise Banner
st.markdown(
    """
    <div class="portal-header">
        <h1 class="portal-title">IT Troubleshooting Expert System</h1>
        <div class="portal-subtitle">Deductive Forward-Chaining Inference Engine • FIT HANU Helpdesk Architecture</div>
        <div class="breadcrumb-bar">
            <span class="breadcrumb-tag">ENGINE: RULE-BASED FIXPOINT</span>
            <span>/</span>
            <span class="breadcrumb-tag">SPECIFICATION: v2.0-STABLE</span>
            <span>/</span>
            <span class="breadcrumb-tag">ARBITRATION: MULTI-STRATEGY</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar Controls
with st.sidebar:
    st.markdown("### Diagnostic Fixture")
    scenario_options = ["Custom Selection"] + [s["id"] for s in kb["scenarios"]]
    scenario_choice = st.selectbox("Load Test Scenario Fixture:", scenario_options, label_visibility="collapsed")
    
    preselected: list[str] = []
    if scenario_choice != "Custom Selection":
        sc = next(s for s in kb["scenarios"] if s["id"] == scenario_choice)
        preselected = sc["presented_symptoms"]
        st.markdown(
            f"""
            <div class="sidebar-box">
                <div style="font-size:0.75rem; font-weight:700; color:#38BDF8; letter-spacing:0.05em; text-transform:uppercase;">CLASS: {sc['class']}</div>
                <div style="font-size:0.85rem; color:#CBD5E1; margin-top:6px; line-height:1.4;">{sc['description']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Arbitration Strategy")
    strategy = st.selectbox(
        "Conflict Resolution Rule:",
        options=["specificity", "rule_count", "coverage"],
        index=0,
        help="Specificity: Prioritises rules matching the largest premise set conjunctively.",
    )

# Sync Scenario Selection into Checkboxes State
if "last_scenario" not in st.session_state or st.session_state["last_scenario"] != scenario_choice:
    st.session_state["last_scenario"] = scenario_choice
    for s in symptoms:
        st.session_state[f"chk_{s['id']}"] = (s["id"] in preselected)

# Main Symptom Checklist Area
st.markdown("### Symptom Checklist")
st.markdown(
    "<span style='color:#94A3B8; font-size:0.88rem;'>Report observed technical anomalies across service domains:</span>",
    unsafe_allow_html=True,
)

col_act1, col_act2 = st.columns([1, 4])
with col_act1:
    if st.button("Reset Selection", type="secondary"):
        for s in symptoms:
            st.session_state[f"chk_{s['id']}"] = False
        st.session_state["last_scenario"] = "Custom Selection"
        st.rerun()

# 5 Domain Tabs (Clean Segmented Style)
tabs = st.tabs([DOMAIN_CONFIG.get(d, {}).get("label", d) for d in domains])
for idx, d in enumerate(domains):
    with tabs[idx]:
        dom_syms = [s for s in symptoms if s["domain"] == d]
        b_class = DOMAIN_CONFIG.get(d, {}).get("badge_class", "badge-wifi")
        for s in dom_syms:
            sid = s["id"]
            if f"chk_{sid}" not in st.session_state:
                st.session_state[f"chk_{sid}"] = (sid in preselected)
            st.checkbox(
                f"{sid} — {s['description']}",
                key=f"chk_{sid}",
            )

# Read active symptoms
selected_list = sorted([s["id"] for s in symptoms if st.session_state.get(f"chk_{s['id']}", False)])

st.markdown("---")
st.markdown(f"#### Active Observations ({len(selected_list)})")
if selected_list:
    chips_html = "".join(
        [
            f"<div style='display:inline-block; background:#1E293B; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:6px 12px; margin:4px 6px 4px 0;'><span class='domain-badge {DOMAIN_CONFIG.get(sym_dict[sid]['domain'], {}).get('badge_class', 'badge-wifi')}'>{sid}</span> <span style='font-size:0.84rem; color:#E2E8F0; margin-left:6px;'>{sym_dict[sid]['description']}</span></div>"
            for sid in selected_list
        ]
    )
    st.markdown(f"<div>{chips_html}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div style='color:#64748B; font-size:0.85rem; font-style:italic;'>No symptoms currently engaged. Select indicators above or load a fixture from the sidebar.</div>", unsafe_allow_html=True)

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
btn_diagnose = st.button("Run Diagnostic Analysis", type="primary")

# ==============================================================================
# REASONING & DIAGNOSIS SECTION
# ==============================================================================
st.markdown("---")
st.markdown("### Inference & Diagnosis Assessment")

if not selected_list:
    st.markdown(
        """
        <div class="status-hero status-insufficient">
            <div class="status-title">AWAITING OBSERVATION INPUT</div>
            <div class="status-desc">The inference engine operates on positive preconditions. Please check observed symptoms or select a fixture to proceed.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # Run core diagnosis
    report = student_core.diagnose(selected_list, kb["rules"], conflicts_list, strategy=strategy)
    status = report["status"]
    s_meta = STATUS_DATA.get(status, STATUS_DATA["insufficient_evidence"])
    
    # 1. Status Hero Banner
    st.markdown(
        f"""
        <div class="status-hero {s_meta['css_class']}">
            <div class="status-title">{s_meta['title']}</div>
            <div class="status-desc">{s_meta['desc']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Contradiction Notification
    if report["conflicts"]:
        st.markdown("#### Logical Inconsistency Audit")
        for c in report["conflicts"]:
            s0 = c['symptoms'][0]
            s1 = c['symptoms'][1]
            s0_desc = sym_dict.get(s0, {}).get("description", "")
            s1_desc = sym_dict.get(s1, {}).get("description", "")
            c_html = (
                f"<div class='conflict-card' style='padding:12px 16px; margin-bottom:10px;'>"
                f"<div style='display:flex; align-items:center; gap:8px; margin-bottom:4px;'>"
                f"<span class='conflict-id' style='font-weight:700;'>{c['id']}:</span> "
                f"<span style='font-weight:700; color:#F87171;'>{s0} ⟷ {s1}</span>"
                f"</div>"
                f"<div style='font-size:0.83rem; color:#CBD5E1; margin:4px 0; line-height:1.4;'>"
                f"• <span style='color:#FCA5A5; font-family:JetBrains Mono; font-weight:600;'>{s0}</span>: {s0_desc}<br>"
                f"• <span style='color:#FCA5A5; font-family:JetBrains Mono; font-weight:600;'>{s1}</span>: {s1_desc}"
                f"</div>"
                f"<div style='font-size:0.83rem; color:#FDE047; margin-top:6px; background:rgba(220,38,38,0.15); padding:6px 10px; border-radius:6px; border:1px solid rgba(220,38,38,0.25);'>"
                f"<strong>Lý do mâu thuẫn:</strong> {c['reason']}"
                f"</div>"
                f"</div>"
            )
            st.markdown(c_html, unsafe_allow_html=True)

    # 3. Candidate Causes Details
    if report["results"]:
        st.markdown("#### Diagnosed Root Causes")
        
        for res in report["results"]:
            cid = res["cause_id"]
            is_leader = cid in report["leaders"]
            cause_data = causes_dict.get(cid, {})
            dom_key = cause_data.get("domain", "")
            badge_cls = DOMAIN_CONFIG.get(dom_key, {}).get("badge_class", "badge-wifi")
            dom_lbl = DOMAIN_CONFIG.get(dom_key, {}).get("label", dom_key)
            
            p_badge = " [PRIMARY CAUSE]" if is_leader else " [PLAUSIBLE ALTERNATIVE]"
            exp_title = f"{cid} • {cause_data.get('description', '')}{p_badge}"
            
            with st.expander(exp_title, expanded=is_leader):
                c_left, c_right = st.columns([1, 1])
                
                with c_left:
                    st.markdown("<div style='font-size:0.8rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;'>Deductive Metrics</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <div style="background:#0F172A; border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:12px; margin-bottom:12px;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                                <span style="color:#94A3B8; font-size:0.82rem;">Domain:</span>
                                <span class="domain-badge {badge_cls}">{dom_lbl}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                                <span style="color:#94A3B8; font-size:0.82rem;">Structural Specificity:</span>
                                <span style="font-weight:700; color:#38BDF8; font-family:'JetBrains Mono'; font-size:0.85rem;">{res['specificity']}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between;">
                                <span style="color:#94A3B8; font-size:0.82rem;">Fired Rule Count:</span>
                                <span style="font-weight:700; color:#38BDF8; font-family:'JetBrains Mono'; font-size:0.85rem;">{len(res['fired_rules'])}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    
                    st.markdown("<div style='font-size:0.8rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px;'>Supporting Premise Symptoms</div>", unsafe_allow_html=True)
                    for sid in res["supporting_symptoms"]:
                        st.markdown(f"<div style='font-size:0.84rem; color:#CBD5E1; padding:3px 0;'>• <span style='font-family:JetBrains Mono; color:#38BDF8; font-weight:600;'>{sid}</span>: {sym_dict[sid]['description']}</div>", unsafe_allow_html=True)
                
                with c_right:
                    remediation = cause_data.get("recommended_action", "No remediation specified.")
                    st.markdown(
                        f"""
                        <div class="remediation-card">
                            <div class="remediation-header">Recommended ITIL Remediation Protocol</div>
                            <div class="remediation-body">{remediation}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Proof trace
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:0.82rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;'>Formal Rule Execution Pipeline</div>", unsafe_allow_html=True)
                traces = report["traces"].get(cid, [])
                if traces:
                    for rid in traces:
                        rule = rules_dict[rid]
                        then_id = rule["then"]
                        then_desc = causes_dict.get(then_id, {}).get("description", then_id)
                        premise_str = " ∧ ".join(rule["if"])
                        comment_html = f"<div class='rule-comment'>// {rule['comment']}</div>" if rule.get("comment") else ""
                        
                        sym_notes = "".join([
                            f"<div style='margin-bottom:2px;'>• <span style='color:#38BDF8; font-family:JetBrains Mono; font-weight:600;'>{sid}</span>: <span style='color:#CBD5E1;'>{sym_dict.get(sid, {}).get('description', '')}</span></div>"
                            for sid in rule["if"]
                        ])
                        cause_note = f"<div style='margin-top:4px;'>➔ <span style='color:#34D399; font-family:JetBrains Mono; font-weight:600;'>{then_id}</span>: <span style='color:#A7F3D0;'>{then_desc}</span></div>"
                        notes_html = f"<div style='margin-top:8px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.06); font-family:Inter,sans-serif; font-size:0.82rem; line-height:1.4;'>{sym_notes}{cause_note}</div>"
                        
                        step_html = (
                            f"<div class='pipeline-step'>"
                            f"<div><span class='rule-id'>{rid}:</span> <span class='rule-logic'>{premise_str} ➔ {then_id}</span></div>"
                            f"{comment_html}"
                            f"{notes_html}"
                            f"</div>"
                        )
                        st.markdown(step_html, unsafe_allow_html=True)

    # 4. Dynamic Follow-up Questioning
    if status in {"ambiguous", "insufficient_evidence"}:
        st.markdown("---")
        st.markdown("#### Dynamic Hypothesis Discriminator")
        st.markdown("<span style='font-size:0.86rem; color:#94A3B8;'>The inference engine suggests validating the following observations to resolve hypothesis ambiguity:</span>", unsafe_allow_html=True)
        
        followups = student_core.suggest_followups(selected_list, kb["rules"], conflicts_list)
        if followups:
            for idx, f in enumerate(followups[:3], 1):
                f_sym = sym_dict.get(f["symptom"], {})
                b_cls = DOMAIN_CONFIG.get(f_sym.get("domain", ""), {}).get("badge_class", "badge-wifi")
                
                col_q, col_act = st.columns([4, 1])
                with col_q:
                    st.markdown(
                        f"""
                        <div style="background:#1E293B; border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:12px 16px; margin-bottom:8px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span class="domain-badge {b_cls}">{f['symptom']}</span>
                                <span style="font-weight:600; color:#F1F5F9; font-size:0.88rem;">{f_sym.get('description', '')}</span>
                            </div>
                            <div style="font-size:0.78rem; color:#64748B; margin-top:4px; font-family:'JetBrains Mono';">Expected transition: {f['status']} ➔ Leading: {', '.join(f['leaders'])}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col_act:
                    if st.button(f"Confirm {f['symptom']}", key=f"btn_add_{f['symptom']}", type="secondary"):
                        st.session_state[f"chk_{f['symptom']}"] = True
                        st.rerun()
