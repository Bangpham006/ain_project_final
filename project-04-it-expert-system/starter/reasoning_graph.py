"""Pure-Python offline visual reasoning graph generator for Project 04.

Builds a crisp Enterprise Light-Slate layered directed acyclic graph
(Symptoms -> Fired Rules -> Candidate Causes) plus meta-level conflict arcs
(`conflicts.json`) as both standalone responsive SVG and Graphviz DOT source,
with zero external binary or network dependencies.
"""

from __future__ import annotations

import base64
import html
import textwrap
from typing import Any

import student_core

DOMAIN_SHORT = {
    "hanu_wifi": ("WIFI", "#1D4ED8", "#DBEAFE"),
    "fit_lms": ("LMS", "#7E22CE", "#F3E8FF"),
    "lab_computers": ("LAB", "#0F766E", "#CCFBF1"),
    "hanu_account": ("ACCT", "#B45309", "#FEF3C7"),
    "fit_printer": ("PRNT", "#BE185D", "#FCE7F3"),
}


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _wrap(text: str, width: int, max_lines: int = 2) -> list[str]:
    lines = textwrap.wrap(str(text), width=width)
    if not lines:
        return [""]
    if len(lines) > max_lines:
        kept = lines[:max_lines]
        kept[-1] = kept[-1][: max(1, width - 3)].rstrip() + "..."
        return kept
    return lines


def build_reasoning_svg(
    reported_symptoms: list[str],
    report: dict[str, Any],
    kb: dict[str, Any],
    *,
    active_rules: list[dict[str, Any]] | None = None,
) -> str:
    """Return a self-contained UTF-8 `<svg>` visualising the deduction and conflicts."""
    rules_used = active_rules if active_rules is not None else kb["rules"]
    sym_by_id = {s["id"]: s for s in kb["symptoms"]}
    cause_by_id = {c["id"]: c for c in kb["causes"]}

    trace = student_core.run_engine(reported_symptoms, rules_used)
    results = report["results"]
    status = report["status"]
    leaders = set(report["leaders"])
    tied_causes = {cid for grp in report["ambiguous_groups"] for cid in grp}
    conflicts = report["conflicts"]

    cause_group: dict[str, int] = {}
    for g_idx, grp in enumerate(report["groups"], 1):
        for cid in grp:
            cause_group[cid] = g_idx

    reported_unique = list(dict.fromkeys(reported_symptoms))
    matched_syms = {p for step in trace for p in step["matched"] if p in sym_by_id}

    def _sym_sort_key(sid: str) -> tuple[int, str]:
        for g_idx, grp in enumerate(report["groups"], 1):
            for res in results:
                if res["cause_id"] in grp and sid in res["supporting_symptoms"]:
                    return (g_idx, sid)
        return (99, sid)

    ordered_syms = sorted(reported_unique, key=_sym_sort_key)

    result_by_cid = {r["cause_id"]: r for r in results}
    ordered_causes: list[str] = []
    for ranking in report["rankings"]:
        for tier in ranking:
            for cid in tier:
                if cid not in ordered_causes:
                    ordered_causes.append(cid)

    width = 1120
    header_h = 56
    footer_h = 44

    sym_box_h = 66
    sym_gap = 16
    rule_box_h = 54
    rule_gap = 13
    cause_box_h = 86
    cause_gap = 18

    n_syms = max(1, len(ordered_syms))
    n_rules = max(1, len(trace))
    n_causes = max(1, len(ordered_causes))

    col1_h = n_syms * sym_box_h + (n_syms - 1) * sym_gap
    col2_h = n_rules * rule_box_h + (n_rules - 1) * rule_gap
    col3_h = n_causes * cause_box_h + (n_causes - 1) * cause_gap

    body_h = max(col1_h, col2_h, col3_h, 175) + 36
    height = header_h + body_h + footer_h

    # Column x-coordinates (extra left gutter when conflict arcs are drawn)
    col1_x, col1_w = (102 if conflicts else 36), 268
    col2_x, col2_w = 436, 240
    col3_x, col3_w = 780, 304

    def _col_start_y(content_h: int) -> float:
        return header_h + 18 + max(0.0, (body_h - 36 - content_h) / 2.0)

    sym_y0 = _col_start_y(col1_h)
    rule_y0 = _col_start_y(col2_h)
    cause_y0 = _col_start_y(col3_h)

    sym_pos: dict[str, tuple[float, float]] = {
        sid: (col1_x, sym_y0 + idx * (sym_box_h + sym_gap))
        for idx, sid in enumerate(ordered_syms)
    }
    rule_pos: dict[str, tuple[float, float]] = {
        step["rule"]: (col2_x, rule_y0 + idx * (rule_box_h + rule_gap))
        for idx, step in enumerate(trace)
    }
    cause_pos: dict[str, tuple[float, float]] = {
        cid: (col3_x, cause_y0 + idx * (cause_box_h + cause_gap))
        for idx, cid in enumerate(ordered_causes)
    }

    def _cause_theme(cid: str) -> tuple[str, str, str, str]:
        """(stroke_hex, fill_hex, badge_bg_hex, role_label)"""
        if status == "contradictory":
            role = "CONFLICTED LEADER" if cid in leaders else "CONFLICTED ALT"
            return ("#DC2626", "#FEF2F2", "#FEE2E2", role)
        if cid in tied_causes:
            return ("#D97706", "#FFFBEB", "#FEF3C7", "TIED RIVAL")
        if cid in leaders:
            if len(report["groups"]) > 1:
                return ("#7C3AED", "#F5F3FF", "#EDE9FE", f"FAULT #{cause_group[cid]} LEADER")
            return ("#059669", "#ECFDF5", "#D1FAE5", "PRIMARY CAUSE")
        return ("#64748B", "#F8FAFC", "#E2E8F0", "ALTERNATIVE")

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="auto">',
        "<defs>",
        '  <linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">',
        '    <stop offset="0%" stop-color="#F8FAFC"/>',
        '    <stop offset="100%" stop-color="#F1F5F9"/>',
        "  </linearGradient>",
    ]
    for m_id, m_col in [
        ("arrPrimary", "#059669"),
        ("arrTied", "#D97706"),
        ("arrMulti", "#7C3AED"),
        ("arrConflict", "#DC2626"),
        ("arrAlt", "#64748B"),
    ]:
        parts.append(
            f'  <marker id="{m_id}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
            f'<path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="{m_col}"/></marker>'
        )
    parts.append("</defs>")

    # Light-Slate Canvas Panel
    parts.append(
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" '
        f'fill="url(#bgGrad)" stroke="#CBD5E1" stroke-width="1.5"/>'
    )
    parts.append(
        f'<rect x="1" y="1" width="{width - 2}" height="{header_h - 8}" rx="12" '
        f'fill="#EFF6FF" opacity="0.65"/>'
    )

    # Column Headers
    col_headers = [
        (col1_x + col1_w / 2, f"1. WORKING MEMORY ({len(ordered_syms)} SYMPTOMS)"),
        (col2_x + col2_w / 2, f"2. FIRED RULES ({len(trace)} / {len(rules_used)})"),
        (col3_x + col3_w / 2, f"3. CANDIDATE CAUSES ({len(ordered_causes)})"),
    ]
    for cx, title in col_headers:
        parts.append(
            f'<text x="{cx:.1f}" y="33" text-anchor="middle" fill="#1E293B" '
            f'font-family="Segoe UI, Arial, sans-serif" font-size="11.5" font-weight="700" letter-spacing="0.6">'
            f"{_esc(title)}</text>"
        )
    parts.append(
        f'<line x1="24" y1="{header_h - 8}" x2="{width - 24}" y2="{header_h - 8}" '
        f'stroke="#CBD5E1" stroke-width="1.2"/>'
    )

    # Edges: Symptoms -> Fired Rules -> Candidate Causes
    for step in trace:
        rid = step["rule"]
        cid = step["derived"]
        rx, ry = rule_pos[rid]
        rule_in_x, rule_in_y = rx, ry + rule_box_h / 2
        rule_out_x, rule_out_y = rx + col2_w, ry + rule_box_h / 2

        stroke_col, _, _, _ = _cause_theme(cid)
        is_alt = cid not in leaders and cid not in tied_causes and status != "contradictory"
        dash = ' stroke-dasharray="5,4"' if is_alt else ""
        if status == "contradictory":
            marker = "arrConflict"
        elif cid in tied_causes:
            marker = "arrTied"
        elif cid in leaders and len(report["groups"]) > 1:
            marker = "arrMulti"
        elif cid in leaders:
            marker = "arrPrimary"
        else:
            marker = "arrAlt"
        opacity = "0.55" if is_alt else "0.92"

        for prem in step["matched"]:
            if prem in sym_pos:
                sx, sy = sym_pos[prem]
                s_out_x, s_out_y = sx + col1_w, sy + sym_box_h / 2
                c1x = s_out_x + (rule_in_x - s_out_x) * 0.48
                c2x = s_out_x + (rule_in_x - s_out_x) * 0.52
                parts.append(
                    f'<path d="M {s_out_x:.1f} {s_out_y:.1f} C {c1x:.1f} {s_out_y:.1f}, '
                    f'{c2x:.1f} {rule_in_y:.1f}, {rule_in_x - 2:.1f} {rule_in_y:.1f}" '
                    f'fill="none" stroke="{stroke_col}" stroke-width="2.0" stroke-opacity="{opacity}"{dash} '
                    f'marker-end="url(#{marker})"/>'
                )

        if cid in cause_pos:
            cx, cy = cause_pos[cid]
            c_in_x, c_in_y = cx, cy + cause_box_h / 2
            c1x = rule_out_x + (c_in_x - rule_out_x) * 0.45
            c2x = rule_out_x + (c_in_x - rule_out_x) * 0.55
            parts.append(
                f'<path d="M {rule_out_x:.1f} {rule_out_y:.1f} C {c1x:.1f} {rule_out_y:.1f}, '
                f'{c2x:.1f} {c_in_y:.1f}, {c_in_x - 2:.1f} {c_in_y:.1f}" '
                f'fill="none" stroke="{stroke_col}" stroke-width="2.3" stroke-opacity="{opacity}"{dash} '
                f'marker-end="url(#{marker})"/>'
            )

    # Conflict arcs on the left of Column 1
    for c_idx, conf in enumerate(conflicts):
        s_a, s_b = conf["symptoms"][0], conf["symptoms"][1]
        if s_a in sym_pos and s_b in sym_pos:
            _, ya = sym_pos[s_a]
            _, yb = sym_pos[s_b]
            y1 = min(ya, yb) + sym_box_h / 2
            y2 = max(ya, yb) + sym_box_h / 2
            arc_x = max(28, col1_x - 36 - c_idx * 26)
            mid_y = (y1 + y2) / 2
            parts.append(
                f'<path d="M {col1_x - 2:.1f} {y1:.1f} C {arc_x:.1f} {y1:.1f}, '
                f'{arc_x:.1f} {y2:.1f}, {col1_x - 2:.1f} {y2:.1f}" '
                f'fill="none" stroke="#DC2626" stroke-width="2.1" stroke-dasharray="4,3" '
                f'marker-start="url(#arrConflict)" marker-end="url(#arrConflict)"/>'
            )
            parts.append(
                f'<rect x="{arc_x - 12:.1f}" y="{mid_y - 10:.1f}" width="36" height="20" rx="5" '
                f'fill="#FEE2E2" stroke="#DC2626" stroke-width="1.2"/>'
            )
            parts.append(
                f'<text x="{arc_x + 6:.1f}" y="{mid_y + 4:.1f}" text-anchor="middle" fill="#991B1B" '
                f'font-family="Consolas, monospace" font-size="10" font-weight="700">{_esc(conf["id"])}</text>'
            )

    # Column 1 Nodes: Symptoms
    if not ordered_syms:
        sy = _col_start_y(sym_box_h)
        parts.append(
            f'<rect x="{col1_x}" y="{sy:.1f}" width="{col1_w}" height="{sym_box_h}" rx="10" '
            f'fill="#FFFFFF" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="5,4"/>'
        )
        parts.append(
            f'<text x="{col1_x + col1_w / 2:.1f}" y="{sy + 28:.1f}" text-anchor="middle" fill="#334155" '
            f'font-family="Consolas, monospace" font-size="12" font-weight="700">WORKING MEMORY = EMPTY</text>'
        )
        parts.append(
            f'<text x="{col1_x + col1_w / 2:.1f}" y="{sy + 47:.1f}" text-anchor="middle" fill="#64748B" '
            f'font-family="Segoe UI, Arial, sans-serif" font-size="11">No observations reported yet</text>'
        )
    else:
        conf_syms = {s for c in conflicts for s in c["symptoms"]}
        for sid in ordered_syms:
            sx, sy = sym_pos[sid]
            s_obj = sym_by_id.get(sid, {"domain": "", "description": sid})
            dom_tag, dom_fg, dom_bg = DOMAIN_SHORT.get(s_obj["domain"], ("IT", "#1D4ED8", "#DBEAFE"))
            used = sid in matched_syms
            in_conf = sid in conf_syms
            border = "#DC2626" if in_conf else ("#2563EB" if used else "#94A3B8")
            fill = "#FEF2F2" if in_conf else "#FFFFFF"
            dash = "" if used or in_conf else ' stroke-dasharray="5,4"'
            parts.append(
                f'<rect x="{sx}" y="{sy:.1f}" width="{col1_w}" height="{sym_box_h}" rx="10" '
                f'fill="{fill}" stroke="{border}" stroke-width="1.6"{dash}/>'
            )
            parts.append(
                f'<rect x="{sx + 10}" y="{sy + 9:.1f}" width="44" height="17" rx="4" '
                f'fill="{dom_bg}" stroke="{dom_fg}" stroke-width="0.9"/>'
            )
            parts.append(
                f'<text x="{sx + 32}" y="{sy + 21:.1f}" text-anchor="middle" fill="{dom_fg}" '
                f'font-family="Consolas, monospace" font-size="9.5" font-weight="700">{_esc(dom_tag)}</text>'
            )
            tag_extra = " [UNMATCHED]" if not used else ""
            parts.append(
                f'<text x="{sx + 62}" y="{sy + 21:.1f}" fill="#0F172A" '
                f'font-family="Consolas, monospace" font-size="12" font-weight="700">{_esc(sid + tag_extra)}</text>'
            )
            desc_lines = _wrap(s_obj["description"], width=37, max_lines=2)
            for l_i, line in enumerate(desc_lines):
                parts.append(
                    f'<text x="{sx + 12}" y="{sy + 39 + l_i * 14:.1f}" fill="#334155" '
                    f'font-family="Segoe UI, Arial, sans-serif" font-size="10.8">{_esc(line)}</text>'
                )

    # Column 2 Nodes: Fired Rules
    if not trace:
        ry = _col_start_y(rule_box_h)
        parts.append(
            f'<rect x="{col2_x}" y="{ry:.1f}" width="{col2_w}" height="{rule_box_h + 10}" rx="10" '
            f'fill="#FFFFFF" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="5,4"/>'
        )
        parts.append(
            f'<text x="{col2_x + col2_w / 2:.1f}" y="{ry + 27:.1f}" text-anchor="middle" fill="#334155" '
            f'font-family="Consolas, monospace" font-size="11.5" font-weight="700">0 RULES SATISFIED</text>'
        )
        parts.append(
            f'<text x="{col2_x + col2_w / 2:.1f}" y="{ry + 45:.1f}" text-anchor="middle" fill="#64748B" '
            f'font-family="Segoe UI, Arial, sans-serif" font-size="10.8">Fixpoint reached on Pass #1</text>'
        )
    else:
        for step in trace:
            rid = step["rule"]
            cid = step["derived"]
            rx, ry = rule_pos[rid]
            stroke_col, _, badge_bg, _ = _cause_theme(cid)
            arity = len(set(step["matched"]))
            prem_expr = " ^ ".join(step["matched"])
            parts.append(
                f'<rect x="{rx}" y="{ry:.1f}" width="{col2_w}" height="{rule_box_h}" rx="9" '
                f'fill="#FFFFFF" stroke="{stroke_col}" stroke-width="1.6"/>'
            )
            parts.append(
                f'<text x="{rx + 12}" y="{ry + 20:.1f}" fill="#1D4ED8" '
                f'font-family="Consolas, monospace" font-size="11.8" font-weight="700">'
                f'#{step["step"]} {_esc(rid)}</text>'
            )
            parts.append(
                f'<rect x="{rx + col2_w - 64}" y="{ry + 7:.1f}" width="52" height="17" rx="4" '
                f'fill="{badge_bg}" stroke="{stroke_col}" stroke-width="0.9"/>'
            )
            parts.append(
                f'<text x="{rx + col2_w - 38}" y="{ry + 19:.1f}" text-anchor="middle" fill="#0F172A" '
                f'font-family="Consolas, monospace" font-size="9.5" font-weight="700">spec={arity}</text>'
            )
            formula = _wrap(f"{prem_expr} -> {cid}", width=30, max_lines=1)[0]
            parts.append(
                f'<text x="{rx + 12}" y="{ry + 40:.1f}" fill="#334155" '
                f'font-family="Consolas, monospace" font-size="10.5">{_esc(formula)}</text>'
            )

    # Column 3 Nodes: Candidate Causes
    if not ordered_causes:
        cy = _col_start_y(cause_box_h)
        parts.append(
            f'<rect x="{col3_x}" y="{cy:.1f}" width="{col3_w}" height="{cause_box_h}" rx="11" '
            f'fill="#FFFFFF" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="5,4"/>'
        )
        parts.append(
            f'<text x="{col3_x + col3_w / 2:.1f}" y="{cy + 36:.1f}" text-anchor="middle" fill="#334155" '
            f'font-family="Consolas, monospace" font-size="12" font-weight="700">NO CANDIDATE DERIVED</text>'
        )
        parts.append(
            f'<text x="{col3_x + col3_w / 2:.1f}" y="{cy + 56:.1f}" text-anchor="middle" fill="#64748B" '
            f'font-family="Segoe UI, Arial, sans-serif" font-size="11">Abstention enforced (no unsupported guess)</text>'
        )
    else:
        for cid in ordered_causes:
            cx, cy = cause_pos[cid]
            res = result_by_cid[cid]
            c_obj = cause_by_id.get(cid, {"description": cid, "domain": ""})
            stroke_col, fill_col, badge_bg, role_lbl = _cause_theme(cid)
            parts.append(
                f'<rect x="{cx}" y="{cy:.1f}" width="{col3_w}" height="{cause_box_h}" rx="11" '
                f'fill="{fill_col}" stroke="{stroke_col}" stroke-width="2.0"/>'
            )
            parts.append(
                f'<text x="{cx + 12}" y="{cy + 22:.1f}" fill="#0F172A" '
                f'font-family="Consolas, monospace" font-size="12.5" font-weight="700">{_esc(cid)}</text>'
            )
            badge_w = max(90, len(role_lbl) * 6.5 + 14)
            parts.append(
                f'<rect x="{cx + col3_w - badge_w - 10:.1f}" y="{cy + 7:.1f}" width="{badge_w:.1f}" height="18" rx="5" '
                f'fill="{badge_bg}" stroke="{stroke_col}" stroke-width="1.0"/>'
            )
            parts.append(
                f'<text x="{cx + col3_w - badge_w / 2 - 10:.1f}" y="{cy + 19.5:.1f}" text-anchor="middle" '
                f'fill="{stroke_col}" font-family="Consolas, monospace" font-size="9.5" font-weight="700">'
                f"{_esc(role_lbl)}</text>"
            )
            desc_lines = _wrap(c_obj.get("description", ""), width=41, max_lines=2)
            for l_i, line in enumerate(desc_lines):
                parts.append(
                    f'<text x="{cx + 12}" y="{cy + 40 + l_i * 14:.1f}" fill="#1E293B" '
                    f'font-family="Segoe UI, Arial, sans-serif" font-size="10.8">{_esc(line)}</text>'
                )
            metrics_str = (
                f"Specificity: {res['specificity']}  |  "
                f"Support: {len(res['supporting_symptoms'])} syms  |  "
                f"Rules: {len(res['fired_rules'])}"
            )
            parts.append(
                f'<text x="{cx + 12}" y="{cy + 75:.1f}" fill="#475569" '
                f'font-family="Consolas, monospace" font-size="10" font-weight="600">{_esc(metrics_str)}</text>'
            )

    # Legend Footer
    ly = height - 16
    parts.append(
        f'<line x1="24" y1="{height - footer_h + 4}" x2="{width - 24}" y2="{height - footer_h + 4}" '
        f'stroke="#CBD5E1" stroke-width="1.2"/>'
    )
    legend_items = [
        ("#059669", "Primary / Resolved Leader"),
        ("#D97706", "Tied Ambiguous Rivals"),
        ("#7C3AED", "Independent Multi-Fault Leaders"),
        ("#64748B", "Outranked Alternative (Retained)"),
        ("#DC2626", "Meta-Constraint Conflict (X01-X05)"),
    ]
    lx = 36.0
    for col, label in legend_items:
        parts.append(f'<circle cx="{lx}" cy="{ly - 4}" r="4.8" fill="{col}"/>')
        parts.append(
            f'<text x="{lx + 10}" y="{ly}" fill="#334155" '
            f'font-family="Segoe UI, Arial, sans-serif" font-size="10.5" font-weight="600">{_esc(label)}</text>'
        )
        lx += len(label) * 6.2 + 34

    parts.append("</svg>")
    return "\n".join(parts)


def svg_to_data_uri(svg_xml: str) -> str:
    """Encode an SVG XML string as a `data:image/svg+xml;base64,...` URI."""
    encoded = base64.b64encode(svg_xml.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_reasoning_dot(
    reported_symptoms: list[str],
    report: dict[str, Any],
    kb: dict[str, Any],
    *,
    active_rules: list[dict[str, Any]] | None = None,
) -> str:
    """Return a Graphviz DOT string representing the exact proof and conflict graph."""
    rules_used = active_rules if active_rules is not None else kb["rules"]
    trace = student_core.run_engine(reported_symptoms, rules_used)
    leaders = set(report["leaders"])

    lines = [
        "digraph ReasoningGraph {",
        "  rankdir=LR;",
        '  node [fontname="Consolas", fontsize=10, shape=box, style="rounded,filled"];',
    ]
    for sid in dict.fromkeys(reported_symptoms):
        lines.append(f'  "{sid}" [fillcolor="#FFFFFF", fontcolor="#0F172A", color="#2563EB"];')
    for step in trace:
        rid = step["rule"]
        arity = len(set(step["matched"]))
        lines.append(
            f'  "{rid}" [label="{rid} (spec={arity})", fillcolor="#F8FAFC", fontcolor="#1D4ED8", color="#64748B"];'
        )
        for prem in step["matched"]:
            lines.append(f'  "{prem}" -> "{rid}";')
        lines.append(f'  "{rid}" -> "{step["derived"]}";')
    for res in report["results"]:
        cid = res["cause_id"]
        col = "#059669" if cid in leaders else "#64748B"
        lines.append(
            f'  "{cid}" [label="{cid} (spec={res["specificity"]})", fillcolor="#ECFDF5", fontcolor="#0F172A", color="{col}"];'
        )
    for conf in report["conflicts"]:
        a, b = conf["symptoms"]
        lines.append(
            f'  "{a}" -> "{b}" [dir=both, style=dashed, color="#DC2626", label="{conf["id"]}", constraint=false];'
        )
    lines.append("}")
    return "\n".join(lines)
