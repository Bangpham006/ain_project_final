# Knowledge-base and kit issues found while building Project 04

Hand-written log for the team, the instructor, and the report's "Limitations" section.
Each item gives the evidence and what we did about it. Nothing in `data/` provided by the kit
has been edited; our only data addition is `data/conflicts.json`.

## 1. Printer causes CAUSE13 / CAUSE14 look swapped in `causes.json` — ask the instructor

`causes.json` says CAUSE13 = *driver missing or mismatched* and CAUSE14 = *toner empty or paper-jam sensor*.
Every other source in the kit says the opposite:

| source | text | implies |
|---|---|---|
| `R036` SYM22 → CAUSE14 | "Printer offline can also be driver mismatch" | CAUSE14 = driver |
| `R037` SYM23 ∧ SYM26 → CAUSE14 | "driver issue on student laptop" | CAUSE14 = driver |
| `R041` SYM26 → CAUSE14 | "Prints from staff PC but not student laptop — driver mismatch" | CAUSE14 = driver |
| `R038` SYM24 → CAUSE13 | "Blank pages — out of toner" | CAUSE13 = toner |
| `R039` SYM25 → CAUSE13 | "Faded/streaky output — low toner" | CAUSE13 = toner |
| `R040` SYM27 → CAUSE13 | "Paper-jam sensor stuck even after clearing" | CAUSE13 = jam |
| `SC02` expected_behavior | "CAUSE13 (toner empty or hardware fault) and CAUSE14 (driver mismatch)" | both |

Impact: inference is unaffected (it only uses ids), but the **remediation shown to the user is wrong** for
printer diagnoses, e.g. blank pages (SYM24 → R038 → CAUSE13) would advise "install the correct driver".
Action: confirm with the instructor before the final product; until then the UI should show the cause id
and rule trace next to the advice.

## 2. Fixture `class` labels that disagree with the rule base

Measured by `experiments/ablation.py` (E0) and pinned by `test_scenario_labels_vs_rule_base`:

| fixture | label | what the rules produce |
|---|---|---|
| SC02_single_cause_printer_offline | single_cause | 2 candidates (CAUSE13, CAUSE14); its own `expected_behavior` calls it ambiguous. Specificity prefers CAUSE13 (status `resolved`). |
| SC05_ambiguous_account_locked | ambiguous | 1 candidate (CAUSE11 via R027, R028, R029). |
| SC13_wifi_laptop_only | ambiguous | 1 candidate (CAUSE02 via R006). |

The causes named in every fixture's `expected_behavior` text do match the engine on 15/15 fixtures; only the
labels disagree. Some texts name fewer rules than fire (SC01 omits R002; SC04 omits R042, R008, R043; SC05
omits R029) — the extra rules are subsumed one-symptom rules with the same conclusion.

## 3. "Remove R007" in the README is an *interpretation* question, not a bug

Removing R007 alone does **not** remove CAUSE03 from the candidates of SC04 (R008 and R043 still fire), and the
brief forbids premature elimination. It **does** turn SC04 into a single preferred cause once conflict resolution
by specificity is applied (R007 was CAUSE03's only two-premise rule). The report should state both views
(ablation E1, rows M0/M1).

## 4. A shipped rule fires only on contradictory input

`R048` requires SYM22 ∧ SYM23 ∧ SYM26; SYM22/SYM26 is the pair SC07 calls contradictory. Consequently the
question SC02 asks ("which additional symptom would disambiguate CAUSE13/CAUSE14?") can only be answered in
CAUSE14's favour by reporting that same contradictory pair (ablation E9).

## 5. Semantically weak rules (knowledge-quality observations)

- `R046` SYM13 (keyboard/mouse unresponsive) → CAUSE08 (LAN cable / NIC failed) and `R021` SYM13 ∧ SYM16
  (colour lines on screen) → CAUSE08: a peripheral or display fault is concluded to be a network fault.
- There is no cause for peripheral or display faults at all, so SYM13/SYM16 can only be explained by
  CAUSE07/CAUSE08.
- SYM11 (deadline display mismatch) is a premise for three unrelated causes (R014 → CAUSE05, R016 → CAUSE06,
  R045 → CAUSE04), which links otherwise independent LMS faults into one competing group.

## 6. Why `conflicts.json` covers the printer only

Applying SC07's "same device, same moment" principle to other domains would contradict shipped rules:
`R009` requires SYM02 (laptop cannot see the network) ∧ SYM04 (connects in the corridor) and `R018` requires
SYM12 (GRUB error, OS never loads) ∧ SYM14 (no network icon / no IP). The rule base therefore treats such
time- or location-dependent combinations as valid evidence, and so do we.

## 7. Kit / environment issues

- `requirements.txt` pins `numpy==1.26.4` but not `pyarrow`; a fresh install pulls a pyarrow that needs
  NumPy ≥ 2 and Streamlit crashes on `st.write(list_of_dicts)` / dataframes. Fixed by pinning `pyarrow==17.0.0`.
- The instructor's `test_student_core_is_not_implemented` asserts the stubs still raise
  `NotImplementedError`, so it necessarily fails once the core exists. Replaced by an entry-point check.
- The root README lists `.streamlit/config.toml`, but the root `.gitignore` excludes `.streamlit/`, so the
  shared theme is not in the repository (cosmetic only).
- The root `.gitignore` also excludes `docs/`: do **not** keep `presentation.pdf` / `report.pdf` there or
  they will never be committed.
