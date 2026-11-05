"""Loader for the team-authored symptom conflict table (`data/conflicts.json`).

`rule_loader.py` is the instructor-provided infrastructure and rejects unknown
keys, so the extra knowledge we add (pairs of symptoms that cannot both be
true of the same device at the same time) lives in its own file with its own
loader. The table is *meta-level* knowledge: the rules in `rules.json` are
purely positive conjunctions and cannot express "these two symptoms are
incompatible" on their own.
"""

from __future__ import annotations

import json
from pathlib import Path


class ConflictSchemaError(ValueError):
    """Raised when `conflicts.json` does not match the documented schema."""


CONFLICT_KEYS = {"id", "symptoms", "reason"}


def load_conflicts(path: str | Path, symptom_ids: set[str]) -> list[dict]:
    """Load and validate `conflicts.json`. Each record is a pair of symptom ids."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ConflictSchemaError(f"{path}: not valid JSON ({exc})") from exc
    if not isinstance(data, dict) or "conflicts" not in data:
        raise ConflictSchemaError(f"{path}: top-level object must contain a 'conflicts' key")

    seen_ids: set[str] = set()
    for i, record in enumerate(data["conflicts"]):
        where = f"{path}#conflicts[{i}]"
        if not isinstance(record, dict) or set(record) != CONFLICT_KEYS:
            raise ConflictSchemaError(f"{where}: keys must be exactly {sorted(CONFLICT_KEYS)}")
        if record["id"] in seen_ids:
            raise ConflictSchemaError(f"{where}: duplicate conflict id '{record['id']}'")
        seen_ids.add(record["id"])
        pair = record["symptoms"]
        if not isinstance(pair, list) or len(pair) != 2 or pair[0] == pair[1]:
            raise ConflictSchemaError(f"{where}: 'symptoms' must list two distinct symptom ids")
        for sym in pair:
            if sym not in symptom_ids:
                raise ConflictSchemaError(f"{where}: unknown symptom id '{sym}'")
        if not str(record["reason"]).strip():
            raise ConflictSchemaError(f"{where}: 'reason' must not be empty")
    return data["conflicts"]
