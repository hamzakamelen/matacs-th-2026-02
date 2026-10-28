#!/usr/bin/env python3
"""Score proposals from structured facts and a criteria version.

The model is not involved. Facts are booleans and numbers already taken
from a proposal. This is the same arithmetic the ranked list would use.
"""

import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRITERIA_PATH = ROOT / "prototype" / "fixtures" / "criteria.json"
EXTRACTIONS_PATH = ROOT / "prototype" / "fixtures" / "extractions.json"
RANKING_PATH = ROOT / "ranking.json"

REASONS = {
    "A": (
        "Passed both mandatory checks and scored highest, led by experience "
        "and a complete team, safety, and monitoring package."
    ),
    "B": (
        "Fails the licence rule: the bidder does not state its own Ontario "
        "electrical contractor licence."
    ),
    "C": (
        "Held for a person to review because the file tries to tell the tool "
        "what rank and marks to give."
    ),
    "D": (
        "Held because no completion time is stated, so timeline cannot be "
        "scored without inventing one."
    ),
    "E": (
        "Passed both mandatory checks. Strong warranty and team, with less "
        "experience and a higher price than the proposal ranked first."
    ),
}


def D(value):
    return Decimal(str(value))


def round1(value):
    quantized = D(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return json.loads(format(quantized, "f"))


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def proposal_from_extraction(item, order):
    facts = item["facts"]
    instructions = item.get("instructions_to_the_tool") or []
    planted = any(
        entry.get("evidence") for entry in instructions if isinstance(entry, dict)
    )
    return {
        "proposal": item["proposal"],
        "upload_order": order,
        "licence_held_by_bidder": facts["licence_held_by_bidder"]["value"],
        "wsib_clearance_confirmed": facts["wsib_clearance_confirmed"]["value"],
        "liability_insurance_cad": facts["liability_insurance_cad"]["value"],
        "installs_100kw_plus": facts["installs_100kw_plus"]["value"],
        "total_price_cad": facts["total_price_cad"]["value"],
        "completion_weeks": facts["completion_weeks"]["value"],
        "panel_warranty_years": facts["panel_warranty_years"]["value"],
        "workmanship_warranty_years": facts["workmanship_warranty_years"]["value"],
        "named_project_lead": facts["named_project_lead"]["value"],
        "crew_size": facts["crew_size"]["value"],
        "safety_plan": bool(facts["safety_plan_stated"]["value"]),
        "monitoring_plan": bool(facts["performance_monitoring_stated"]["value"]),
        "instructions_found": planted,
    }


def load_facts():
    criteria = load_json(CRITERIA_PATH)
    extractions = load_json(EXTRACTIONS_PATH)
    proposals = [
        proposal_from_extraction(item, order)
        for order, item in enumerate(extractions, start=1)
    ]
    return {"criteria": criteria, "proposals": proposals}


def experience_score(count, full_marks):
    if count >= full_marks:
        return D(100)
    return D(count) / D(full_marks) * D(100)


def price_score(price, ceiling, full_ratio):
    full_at = D(ceiling) * D(full_ratio)
    price = D(price)
    ceiling = D(ceiling)
    if price <= full_at:
        return D(100)
    if price >= ceiling:
        return D(0)
    return (ceiling - price) / (ceiling - full_at) * D(100)


def timeline_score(weeks, cap, full_at, score_at_cap):
    weeks = D(weeks)
    cap = D(cap)
    full_at = D(full_at)
    score_at_cap = D(score_at_cap)
    if weeks <= full_at:
        return D(100)
    if weeks > cap:
        return D(0)
    if weeks == cap:
        return score_at_cap
    span = cap - full_at
    drop = D(100) - score_at_cap
    return D(100) - ((weeks - full_at) / span) * drop


def capped_percent(value, full_marks):
    return min(D(100), D(value) / D(full_marks) * D(100))


def warranty_score(panel_years, work_years, panel_full, work_full):
    panel = capped_percent(panel_years, panel_full)
    work = capped_percent(work_years, work_full)
    return (panel + work) / D(2)


def team_score(proposal, points):
    total = D(0)
    if proposal["named_project_lead"]:
        total += D(points["named_project_lead"])
    crew = proposal["crew_size"]
    if crew is not None and crew > 0:
        total += D(points["crew_size_stated"])
    if proposal["safety_plan"]:
        total += D(points["safety_plan"])
    if proposal["monitoring_plan"]:
        total += D(points["monitoring_plan"])
    return total


def mandatory_failure(proposal, criteria):
    if not proposal["licence_held_by_bidder"]:
        return "licence"
    if not proposal["wsib_clearance_confirmed"]:
        return "wsib"
    insurance = proposal["liability_insurance_cad"]
    if insurance is None or D(insurance) < D(criteria["insurance_minimum_cad"]):
        return "insurance"
    return None


def hold_reason(proposal, criteria):
    if proposal["instructions_found"]:
        return "instructions"
    if proposal["completion_weeks"] is None:
        return "timeline_missing"
    if proposal["total_price_cad"] is None:
        return "price_missing"
    if proposal["installs_100kw_plus"] is None:
        return "experience_missing"
    if (
        proposal["panel_warranty_years"] is None
        or proposal["workmanship_warranty_years"] is None
    ):
        return "warranty_missing"
    if D(proposal["total_price_cad"]) > D(criteria["budget_ceiling_cad"]):
        return "over_budget"
    if D(proposal["completion_weeks"]) > D(criteria["timeline_cap_weeks"]):
        return "over_time"
    return None


def component_scores(proposal, criteria):
    scores = {
        "experience": experience_score(
            proposal["installs_100kw_plus"],
            criteria["experience_full_marks_count"],
        ),
        "price": price_score(
            proposal["total_price_cad"],
            criteria["budget_ceiling_cad"],
            criteria["price_full_marks_ratio"],
        ),
        "warranty": warranty_score(
            proposal["panel_warranty_years"],
            proposal["workmanship_warranty_years"],
            criteria["panel_full_marks_years"],
            criteria["workmanship_full_marks_years"],
        ),
        "team": team_score(proposal, criteria["team_points"]),
    }
    if proposal["completion_weeks"] is None:
        scores["timeline"] = None
    else:
        scores["timeline"] = timeline_score(
            proposal["completion_weeks"],
            criteria["timeline_cap_weeks"],
            criteria["timeline_full_marks_weeks"],
            criteria["timeline_score_at_cap"],
        )
    return scores


def weighted_total(scores, weights):
    if scores["timeline"] is None:
        return None
    total = D(0)
    for name, weight in weights.items():
        total += scores[name] * D(weight) / D(100)
    return total


def evaluate(bundle):
    criteria = bundle["criteria"]
    weights = criteria["weights"]
    if sum(weights.values()) != 100:
        raise SystemExit("Criteria weights must add up to 100.")
    if sum(criteria["team_points"].values()) != 100:
        raise SystemExit("Team checklist points must add up to 100.")

    rows = []
    for proposal in bundle["proposals"]:
        parts = component_scores(proposal, criteria)
        total = weighted_total(parts, weights)
        failure = mandatory_failure(proposal, criteria)
        hold = None if failure else hold_reason(proposal, criteria)
        if failure:
            status = "ineligible"
        elif hold:
            status = "flagged"
        else:
            status = "ranked"
        rows.append(
            {
                "proposal": proposal["proposal"],
                "upload_order": proposal["upload_order"],
                "status": status,
                "failure": failure,
                "hold": hold,
                "parts": parts,
                "total": total,
                "price": proposal["total_price_cad"],
                "workmanship": proposal["workmanship_warranty_years"],
            }
        )

    ranked = [row for row in rows if row["status"] == "ranked"]
    ranked.sort(
        key=lambda row: (
            -row["total"],
            -row["parts"]["experience"],
            D(row["price"]),
            -(D(row["workmanship"]) if row["workmanship"] is not None else D(0)),
            row["upload_order"],
        )
    )
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    for row in rows:
        row.setdefault("rank", None)
    return rows


def public_ranking(rows):
    by_letter = []
    for row in sorted(rows, key=lambda item: item["proposal"]):
        published_score = (
            round1(row["total"]) if row["status"] == "ranked" else None
        )
        by_letter.append(
            {
                "proposal": row["proposal"],
                "rank": row["rank"],
                "status": row["status"],
                "score": published_score,
                "reason": REASONS[row["proposal"]],
            }
        )
    return by_letter


def expected_shape(rows):
    found = {row["proposal"]: (row["status"], row["rank"]) for row in rows}
    expected = {
        "A": ("ranked", 1),
        "B": ("ineligible", None),
        "C": ("flagged", None),
        "D": ("flagged", None),
        "E": ("ranked", 2),
    }
    if found != expected:
        raise SystemExit(f"Ranking shape changed: {found}")


def print_breakdown(rows):
    for row in sorted(rows, key=lambda item: item["proposal"]):
        parts = row["parts"]
        printable = {
            name: (None if value is None else str(round1(value)))
            for name, value in parts.items()
        }
        total = None if row["total"] is None else str(round1(row["total"]))
        print(
            f"{row['proposal']}  {row['status']:11}  "
            f"rank={row['rank']}  total={total}  parts={printable}"
        )


def main():
    rows = evaluate(load_facts())
    expected_shape(rows)
    ranking = public_ranking(rows)
    print_breakdown(rows)
    payload = json.dumps(ranking, indent=2) + "\n"
    if "--write" in sys.argv:
        RANKING_PATH.write_text(payload, encoding="utf-8")
        print(f"Wrote {RANKING_PATH}")
        return
    if not RANKING_PATH.exists():
        print(payload)
        raise SystemExit("ranking.json is missing. Re-run with --write.")
    saved = json.loads(RANKING_PATH.read_text(encoding="utf-8"))
    if saved != ranking:
        print("ranking.json does not match the scorer.")
        print(payload)
        raise SystemExit(1)
    print("ranking.json matches the scorer.")


if __name__ == "__main__":
    main()
