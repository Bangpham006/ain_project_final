"""Graded AI core for Project 04 (IT Troubleshooting Expert System).

Rule-based forward chaining over the knowledge base loaded by
`rule_loader.py` (symptoms, causes, and `if -> then` rules), conflict
resolution between competing causes, and an explanation facility that
reports which rules fired and why.

Design in one paragraph
-----------------------
Working memory starts as the set of reported symptoms. The engine repeatedly
scans the rule list and fires every not-yet-fired rule whose whole `if` set is
contained in working memory, adding the rule's `then` fact to working memory.
It stops when a full pass fires nothing new (a fixpoint). Every firing is
recorded in a chronological trace; `infer` summarises that trace per cause and
`explain` extracts, per cause, the sub-trace that actually led to it. Nothing
is eliminated: if two rules (or two causes) are supported, both are reported.
Choosing *between* competing causes is a separate, explicit step
(`rank_candidates`, a conflict-resolution strategy) that only orders the
candidates and reports ties instead of breaking them arbitrarily. Because rules
contain only positive conditions the system is *monotonic*: adding a symptom
can add conclusions but never retract one, so contradictory reports are
detected at a meta level (`detect_conflicts`) rather than by the rules.

Do not hand-code the answer for a specific scenario id: the functions below
generalize to any symptom set built from the same `data/` schema.

Forbidden shortcuts (do not paste or adapt any of these into this file
or elsewhere in `starter/`):

- a working general-purpose forward-chaining or rule-engine library
  call standing in for your own inference code;
- a hard-coded lookup table keyed by scenario id that bypasses
  reasoning over `rules.json`;
- calling a hosted LLM to guess the cause instead of reasoning over
  the rule set yourself.

Public API
----------
- `infer(reported_symptoms, rules)`               -> candidate causes + fired rules
- `explain(cause_id, reported_symptoms, rules)`    -> ordered rule ids (an `Explanation`)
- `explain_steps(...)`                             -> same proof, with full step records
- `rank_candidates(results, strategy)`             -> conflict resolution: tiers, best first
- `group_candidates(results)`                      -> competing / independent cause groups
- `detect_conflicts(reported_symptoms, conflicts)` -> incompatible symptom pairs present
- `diagnose(reported_symptoms, rules, conflicts)`  -> one status report for the UI
- `suggest_followups(reported_symptoms, rules, ...)` -> which symptom to ask about next
- `ContradictoryEvidenceError`                     -> typed exception for conflicting input
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

__all__ = [
    "ContradictoryEvidenceError",
    "Explanation",
    "STRATEGIES",
    "DEFAULT_STRATEGY",
    "run_engine",
    "infer",
    "explain",
    "explain_steps",
    "rank_candidates",
    "group_candidates",
    "detect_conflicts",
    "diagnose",
    "suggest_followups",
    "STATUS_ORDER",
]


class ContradictoryEvidenceError(ValueError):
    """The reported symptoms contain mutually incompatible pairs.

    Attributes
    ----------
    conflicts:
        The offending records from the conflict table (`id`, `symptoms`, `reason`).
    rule_ids:
        The proof trace that was computed anyway, so a caller can still show
        what the (monotonic) rules would conclude from the inconsistent input.
    """

    def __init__(self, conflicts: Iterable[dict[str, Any]], rule_ids: Iterable[str] = ()) -> None:
        self.conflicts = list(conflicts)
        self.rule_ids = list(rule_ids)
        pairs = ", ".join(" vs ".join(c["symptoms"]) for c in self.conflicts)
        super().__init__(f"Contradictory symptoms reported: {pairs}")


class Explanation(list):
    """The ordered rule ids proving one cause -- a plain ``list[str]`` (it
    compares equal to one) that also tells the caller whether the cause is
    contested, so ambiguity is visible in the return value and never hidden
    behind an arbitrary pick.

    Attributes
    ----------
    cause_id:     the cause being explained.
    steps:        full trace records of the proof (see `run_engine`).
    rivals:       other candidates competing for the same evidence.
    tied_with:    rivals exactly as well supported under `strategy` (ambiguity).
    outranked_by: rivals better supported under `strategy`.
    strategy:     the conflict-resolution strategy used to compare rivals.
    """

    def __init__(
        self,
        rule_ids: Iterable[str],
        *,
        cause_id: str,
        steps: list[dict[str, Any]],
        rivals: list[str],
        tied_with: list[str],
        outranked_by: list[str],
        strategy: str,
    ) -> None:
        super().__init__(rule_ids)
        self.cause_id = cause_id
        self.steps = steps
        self.rivals = rivals
        self.tied_with = tied_with
        self.outranked_by = outranked_by
        self.strategy = strategy

    @property
    def is_ambiguous(self) -> bool:
        """True when another cause is exactly as well supported as this one."""
        return bool(self.tied_with)


def _as_reported(reported_symptoms: Iterable[str]) -> list[str]:
    """Validate and de-duplicate reported symptoms, keeping first-seen order."""
    if isinstance(reported_symptoms, str):
        raise TypeError("reported_symptoms must be a list of symptom ids, not a single string")
    return list(dict.fromkeys(reported_symptoms))


def run_engine(reported_symptoms: Iterable[str], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run forward chaining to a fixpoint and return the chronological trace.

    Each trace step is ``{"step", "pass", "rule", "matched", "derived"}``:
    the 1-based firing order, the scan pass it fired in, the rule id, the
    premises (`if` list) it matched, and the fact it added to working memory.

    A rule fires at most once (refraction). A rule with an empty `if` list is
    ignored: it would be vacuously true and fire on no evidence at all, which
    contradicts "do not guess a cause from partial information".
    """
    rules = list(rules)  # scanned once per pass: an iterator would be exhausted after the first
    facts = set(_as_reported(reported_symptoms))
    fired: set[int] = set()  # rule *positions*, so duplicate rule ids cannot hide a rule
    trace: list[dict[str, Any]] = []
    pass_no = 0
    progress = True
    while progress:
        progress = False
        pass_no += 1
        for position, rule in enumerate(rules):
            premises = rule["if"]
            if position in fired or not premises:
                continue
            if all(p in facts for p in premises):
                fired.add(position)
                facts.add(rule["then"])
                progress = True
                trace.append(
                    {
                        "step": len(trace) + 1,
                        "pass": pass_no,
                        "rule": rule["id"],
                        "matched": list(premises),
                        "derived": rule["then"],
                    }
                )
    return trace


def _proof(goal: str, trace: list[dict[str, Any]], reported: set[str]) -> list[dict[str, Any]]:
    """Sub-trace needed to derive `goal`: every firing that derived it, plus,
    recursively, every firing that derived a (non-reported) premise of those.
    Returned in firing order, so prerequisites precede their consequences."""
    needed: set[int] = set()
    seen: set[str] = set()
    stack = [goal]
    while stack:
        fact = stack.pop()
        if fact in seen:
            continue
        seen.add(fact)
        for step in trace:
            if step["derived"] == fact:
                needed.add(step["step"])
                stack.extend(p for p in step["matched"] if p not in reported)
    return [step for step in trace if step["step"] in needed]


def infer(reported_symptoms: list[str], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Infer the set of possible causes for `reported_symptoms`.

    Returns one record per candidate cause, ordered by when it was first
    derived::

        {"cause_id": "CAUSE02",
         "fired_rules": ["R005", "R042"],            # every rule that concluded it
         "supporting_symptoms": ["SYM03", "SYM04"],  # reported symptoms the proof rests on
         "specificity": 2}                           # most premises in one of those rules

    No candidate is dropped because another looks stronger (no premature
    elimination), and rules whose conditions are a subset of a more specific
    rule's conditions are all reported. Returns ``[]`` when no rule's `if` set
    is contained in the reported symptoms (including the empty report) --
    the engine never guesses from partial information.
    """
    return _analyse(_as_reported(reported_symptoms), rules)[0]


def _analyse(
    reported: list[str], rules: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """One engine run shared by `infer`, `explain` and `diagnose`:
    the candidate records and, per candidate, its proof steps."""
    reported_set = set(reported)
    trace = run_engine(reported, rules)

    direct: dict[str, list[dict[str, Any]]] = {}
    for step in trace:
        direct.setdefault(step["derived"], []).append(step)

    results, proofs = [], {}
    for cause_id, steps in direct.items():
        proofs[cause_id] = _proof(cause_id, trace, reported_set)
        support = {p for step in proofs[cause_id] for p in step["matched"] if p in reported_set}
        results.append(
            {
                "cause_id": cause_id,
                "fired_rules": [step["rule"] for step in steps],
                "supporting_symptoms": sorted(support),
                # distinct premises: a rule listing a symptom twice is not more specific
                "specificity": max(len(set(step["matched"])) for step in steps),
            }
        )
    return results, proofs


# --------------------------------------------------------------------------- #
# Conflict resolution
# --------------------------------------------------------------------------- #
#: Each strategy maps a candidate record (from `infer`) to a sort key; a larger
#: key is preferred. Strategies only *order* candidates -- none removes one.
#:
#: ``specificity`` (default) -- prefer the cause concluded by the most specific
#:     rule (most premises), then the one covering more reported symptoms.
#:     This is the classical "specificity/complexity" conflict-resolution
#:     strategy of production systems: a rule that matches more evidence
#:     conjunctively is a stronger pattern than a one-symptom shortcut.
#: ``coverage`` -- prefer the cause that accounts for the most reported
#:     symptoms, then specificity (parsimonious covering).
#: ``rule_count`` -- prefer the cause concluded by the most rules. Included as
#:     a contrast for the experiments: it rewards redundant rule authoring,
#:     not stronger evidence.
STRATEGIES: dict[str, Callable[[dict[str, Any]], tuple]] = {
    "specificity": lambda r: (r["specificity"], len(r["supporting_symptoms"])),
    "coverage": lambda r: (len(r["supporting_symptoms"]), r["specificity"]),
    "rule_count": lambda r: (len(r["fired_rules"]),),
}
DEFAULT_STRATEGY = "specificity"


def rank_candidates(results: list[dict[str, Any]], strategy: str = DEFAULT_STRATEGY) -> list[list[str]]:
    """Order candidates best-first into *tiers* of equally supported causes.

    ``[["CAUSE02"], ["CAUSE03"]]`` means CAUSE02 is preferred;
    ``[["CAUSE02", "CAUSE03"]]`` means the strategy cannot separate them (a tie
    is reported, never broken arbitrarily). Within a tier, causes keep their
    first-derived order. Rank one competing group at a time (see
    `group_candidates`): independent faults are not rivals.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy '{strategy}'; choose from {sorted(STRATEGIES)}")
    key = STRATEGIES[strategy]
    tiers: dict[tuple, list[str]] = {}
    for record in results:
        tiers.setdefault(key(record), []).append(record["cause_id"])
    return [tiers[k] for k in sorted(tiers, reverse=True)]


def group_candidates(results: list[dict[str, Any]]) -> list[list[str]]:
    """Partition candidate causes into groups of *competing* causes.

    Two causes compete when the reported symptoms supporting them overlap --
    they are rival explanations of at least one shared observation. Groups
    are the connected components of that relation. A group with more than one
    cause needs conflict resolution; several groups are independent findings
    (a multi-fault incident, e.g. a Wi-Fi fault and a printer fault at once).
    """
    parent = list(range(len(results)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    supports = [set(r["supporting_symptoms"]) for r in results]
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            if supports[i] & supports[j]:
                parent[find(j)] = find(i)

    groups: dict[int, list[str]] = {}
    for i, record in enumerate(results):
        groups.setdefault(find(i), []).append(record["cause_id"])
    return list(groups.values())


def _rivalry(
    cause_id: str, results: list[dict[str, Any]], strategy: str
) -> tuple[list[str], list[str], list[str]]:
    """(rivals, tied_with, outranked_by) of `cause_id` among `results`."""
    group = next((g for g in group_candidates(results) if cause_id in g), [cause_id])
    rivals = [c for c in group if c != cause_id]
    members = [r for r in results if r["cause_id"] in group]
    tiers = rank_candidates(members, strategy)
    own = next(i for i, tier in enumerate(tiers) if cause_id in tier)
    tied = [c for c in tiers[own] if c != cause_id]
    better = [c for tier in tiers[:own] for c in tier]
    return rivals, tied, better


# --------------------------------------------------------------------------- #
# Explanation facility
# --------------------------------------------------------------------------- #
def explain_steps(
    cause_id: str, reported_symptoms: list[str], rules: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Proof of `cause_id` as full step records (see `run_engine`), in firing order.
    Empty when the cause is not derivable from the reported symptoms."""
    reported = _as_reported(reported_symptoms)
    return _proof(cause_id, run_engine(reported, rules), set(reported))


def explain(
    cause_id: str,
    reported_symptoms: list[str],
    rules: list[dict[str, Any]],
    conflicts: list[dict[str, Any]] | None = None,
    strategy: str = DEFAULT_STRATEGY,
) -> Explanation:
    """Explain why `cause_id` was inferred: the ordered rule ids of its proof.

    Prerequisite firings come first (chronological order). Returns an empty
    explanation if `cause_id` cannot be derived from `reported_symptoms`.

    The return value is an `Explanation` -- a ``list[str]`` of rule ids that
    also carries `rivals`, `tied_with` and `outranked_by`, so the caller can
    see when two or more causes are equally supported (``is_ambiguous``)
    instead of trusting a silent pick.

    Contradictions are surfaced as a typed exception: if a `conflicts` table
    is supplied and the reported symptoms contain one of its incompatible
    pairs, `ContradictoryEvidenceError` is raised, carrying the conflicts and
    the proof the rules would still produce (`exc.rule_ids`). Without a
    conflict table no contradiction can be detected: the positive rules have
    no way to say two symptoms are incompatible.
    """
    results, proofs = _analyse(_as_reported(reported_symptoms), rules)
    steps = proofs.get(cause_id, [])
    rule_ids = [step["rule"] for step in steps]
    if conflicts:
        found = detect_conflicts(reported_symptoms, conflicts)
        if found:
            raise ContradictoryEvidenceError(found, rule_ids)

    rivals, tied, better = _rivalry(cause_id, results, strategy) if steps else ([], [], [])
    return Explanation(
        rule_ids,
        cause_id=cause_id,
        steps=steps,
        rivals=rivals,
        tied_with=tied,
        outranked_by=better,
        strategy=strategy,
    )


def detect_conflicts(
    reported_symptoms: list[str], conflicts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return the conflict-table records whose two symptoms are both reported."""
    reported = set(_as_reported(reported_symptoms))
    return [c for c in conflicts if set(c["symptoms"]) <= reported]


# --------------------------------------------------------------------------- #
# One-call diagnosis and follow-up questions
# --------------------------------------------------------------------------- #
#: Statuses from most to least decisive; `suggest_followups` sorts by this.
STATUS_ORDER = ("single_cause", "resolved", "multi_fault", "ambiguous", "insufficient_evidence", "contradictory")


def diagnose(
    reported_symptoms: list[str],
    rules: list[dict[str, Any]],
    conflicts: list[dict[str, Any]] | None = None,
    strategy: str = DEFAULT_STRATEGY,
) -> dict[str, Any]:
    """One-call report for the UI and the experiments.

    ``status`` is the highest-priority condition that applies:

    ``contradictory``         reported symptoms contain an incompatible pair
    ``ambiguous``             in some competing group the best causes tie under `strategy`
    ``multi_fault``           >1 independent groups, each with a unique leader
    ``resolved``              one competing group; `strategy` prefers a unique leader
                              (the others stay listed as alternatives)
    ``single_cause``          exactly one candidate cause
    ``insufficient_evidence`` no rule fired -- nothing is guessed

    The report also carries every candidate (`results`), the competing
    `groups` and their `rankings` (tiers per group, best first), the `leaders`
    (top tier of every group), the tied top tiers (`ambiguous_groups`), the
    `conflicts` found, and a per-cause proof (`traces`: cause id -> ordered
    rule ids).
    """
    results, proofs = _analyse(_as_reported(reported_symptoms), rules)
    groups = group_candidates(results)
    rankings = [rank_candidates([r for r in results if r["cause_id"] in g], strategy) for g in groups]
    ambiguous_groups = [ranking[0] for ranking in rankings if len(ranking[0]) > 1]
    found = detect_conflicts(reported_symptoms, conflicts or [])

    if found:
        status = "contradictory"
    elif ambiguous_groups:
        status = "ambiguous"
    elif len(groups) > 1:
        status = "multi_fault"
    elif len(results) > 1:
        status = "resolved"
    elif len(results) == 1:
        status = "single_cause"
    else:
        status = "insufficient_evidence"

    return {
        "status": status,
        "strategy": strategy,
        "results": results,
        "groups": groups,
        "rankings": rankings,
        "leaders": [cause for ranking in rankings for cause in ranking[0]],
        "ambiguous_groups": ambiguous_groups,
        "conflicts": found,
        "traces": {cause_id: [s["rule"] for s in proof] for cause_id, proof in proofs.items()},
    }


def suggest_followups(
    reported_symptoms: list[str],
    rules: list[dict[str, Any]],
    conflicts: list[dict[str, Any]] | None = None,
    candidates: Iterable[str] | None = None,
    strategy: str = DEFAULT_STRATEGY,
) -> list[dict[str, Any]]:
    """What-if analysis: for each symptom not yet reported, what would the
    diagnosis become if the user confirmed it?

    `candidates` limits the symptoms considered (e.g. one domain's symptoms);
    by default every symptom used in some rule premise is tried. Returns one
    record per *relevant* symptom -- one that would fire at least one new
    rule (asking about anything else cannot change the diagnosis) -- most
    decisive outcome first::

        {"symptom": "SYM05", "status": "resolved", "leaders": ["CAUSE02"],
         "causes": ["CAUSE02", "CAUSE03"], "new_rules": ["R006"]}

    A symptom that would contradict the current report is still listed (with
    status ``contradictory``) but sorted last, so the UI can grey it out.
    """
    reported = _as_reported(reported_symptoms)
    rules = list(rules)  # reused for every what-if run below
    if candidates is None:
        candidates = sorted({p for rule in rules for p in rule["if"]})
    before = {rid for r in infer(reported, rules) for rid in r["fired_rules"]}
    suggestions = []
    for symptom in candidates:
        if symptom in reported:
            continue
        report = diagnose(reported + [symptom], rules, conflicts, strategy)
        fired = [rid for r in report["results"] for rid in r["fired_rules"]]
        if all(rid in before for rid in fired):
            continue
        suggestions.append(
            {
                "symptom": symptom,
                "status": report["status"],
                "leaders": report["leaders"],
                "causes": [r["cause_id"] for r in report["results"]],
                "new_rules": [rid for rid in fired if rid not in before],
            }
        )
    suggestions.sort(key=lambda s: (STATUS_ORDER.index(s["status"]), len(s["causes"]), s["symptom"]))
    return suggestions
