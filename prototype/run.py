#!/usr/bin/env python3
"""Extra credit: run the extraction prompt on samples A–E, then score.

The brief forbids copying sample proposal prose into the repository, so this
script does not call a model and does not store that prose. It does the two
steps a live run would do after the PDF text had been read:

1. Fill PROMPTS.md with the published criteria version.
2. Apply each sample's extracted form (the JSON the prompt asks for).
3. Score with the same rules as the ranked list.

Run: python3 prototype/run.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from score import (  # noqa: E402
    RANKING_PATH,
    evaluate,
    expected_shape,
    print_breakdown,
    proposal_from_extraction,
    public_ranking,
)

PROMPTS_PATH = ROOT / "PROMPTS.md"
CRITERIA_PATH = ROOT / "prototype" / "fixtures" / "criteria.json"
EXTRACTIONS_PATH = ROOT / "prototype" / "fixtures" / "extractions.json"

FACT_KEYS = (
    "licence_held_by_bidder",
    "wsib_clearance_confirmed",
    "liability_insurance_cad",
    "installs_100kw_plus",
    "total_price_cad",
    "completion_weeks",
    "panel_warranty_years",
    "workmanship_warranty_years",
    "named_project_lead",
    "crew_size",
    "safety_plan_stated",
    "performance_monitoring_stated",
)


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def prompt_body():
    text = PROMPTS_PATH.read_text(encoding="utf-8")
    marker = "\n---\n"
    if marker not in text:
        raise SystemExit("PROMPTS.md must contain the prompt after a --- line.")
    return text.split(marker, 1)[1].strip()


def filled_prompt(criteria, letter):
    criteria_json = json.dumps(criteria, indent=2)
    body = prompt_body()
    if "{{criteria_json}}" not in body or "{{proposal_text}}" not in body:
        raise SystemExit("PROMPTS.md is missing the runtime placeholders.")
    # The source PDF text stays out of the repository. The letter is the
    # sample handle the brief says to use.
    proposal_handle = f"Proposal {letter}"
    return (
        body.replace("{{criteria_json}}", criteria_json).replace(
            "{{proposal_text}}", proposal_handle
        )
    )


def check_extraction(letter, extraction):
    if set(extraction.get("facts", {})) != set(FACT_KEYS):
        raise SystemExit(f"Proposal {letter}: extraction keys do not match the prompt.")
    for key, field in extraction["facts"].items():
        if not isinstance(field, dict) or "value" not in field:
            raise SystemExit(f"Proposal {letter}: {key} is not a prompt field.")
        if field["value"] not in (None, False) and not field.get("evidence"):
            raise SystemExit(f"Proposal {letter}: {key} has a value with no evidence.")
        if field["value"] is None and field.get("evidence"):
            raise SystemExit(f"Proposal {letter}: {key} is null but still has evidence.")
    if extraction["facts"]["licence_held_by_bidder"]["value"] is True:
        evidence = extraction["facts"]["licence_held_by_bidder"]["evidence"].lower()
        if "subcontractor" in evidence or "after contract award" in evidence:
            raise SystemExit(
                f"Proposal {letter}: a later subcontractor must not pass the licence field."
            )


def main():
    criteria = load_json(CRITERIA_PATH)
    extractions = load_json(EXTRACTIONS_PATH)
    letters = ["A", "B", "C", "D", "E"]
    if [item["proposal"] for item in extractions] != letters:
        raise SystemExit("extractions.json must list proposals A–E in that order.")

    prompts = []
    proposals = []
    for order, item in enumerate(extractions, start=1):
        letter = item["proposal"]
        check_extraction(letter, item)
        filled = filled_prompt(criteria, letter)
        if "You do not score the proposal" not in filled:
            raise SystemExit("Filled prompt lost the extraction instruction.")
        if re.search(r"\{\{.*\}\}", filled):
            raise SystemExit(f"Proposal {letter}: unfilled placeholder in the prompt.")
        prompts.append(letter)
        proposals.append(proposal_from_extraction(item, order))

    print("Prompt filled for samples:", ", ".join(prompts))
    rows = evaluate({"criteria": criteria, "proposals": proposals})
    expected_shape(rows)
    ranking = public_ranking(rows)
    print_breakdown(rows)
    saved = json.loads(RANKING_PATH.read_text(encoding="utf-8"))
    if saved != ranking:
        print("ranking.json does not match the prompt-and-score run.")
        print(json.dumps(ranking, indent=2))
        raise SystemExit(1)
    print("ranking.json matches the prompt-and-score run.")


if __name__ == "__main__":
    main()
