"""Which questions keep coming up? Suggest changes to the submission template once a pattern repeats.

Counts, per menu, (a) information the ticket form should have collected but did not, and
(b) tickets where nothing specific was missing but the PIC still had to confirm something directly.
A pattern that reaches THRESHOLD occurrences becomes a suggestion for the ops team to review. Nothing changes automatically.
"""

import argparse
import csv
import json
from collections import Counter

from msp_ops_copilot import rag
from msp_ops_copilot.eval_triage import GOLDEN, RUNS

THRESHOLD = 3


def insights(tickets: list[dict], preds: dict[str, dict], threshold: int = THRESHOLD) -> list[str]:
    missing, confirm = Counter(), Counter()
    for t in tickets:
        p = preds[t["id"]]
        where = f"{t['app'] or '-'} / {t['menu'] or '-'}"
        for item in p["missing_info"]:
            missing[(where, item)] += 1
        if not p["missing_info"] and (p["handover"] == "needs_info" or p["resolution_path"] == "ask_user"):
            confirm[where] += 1
    out = [f"{where}: '{item}' was missing in {n} tickets. Make the field required for this menu or add an example next to it." for (where, item), n in missing.most_common() if n >= threshold]
    out += [f"{where}: the PIC had to confirm something directly in {n} tickets. Look at what was asked and add it to the template." for where, n in confirm.most_common() if n >= threshold]
    overall = Counter(item for (_, item) in missing.elements())
    out += [f"All menus: '{item}' was missing in {n} tickets. Check whether the form wording for this field is unclear." for item, n in overall.most_common() if n >= threshold * 2]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="gemini")
    ap.add_argument("--threshold", type=int, default=THRESHOLD)
    args = ap.parse_args()
    runs = [json.loads(f.read_text()) for f in sorted(RUNS.glob("*.json"))]
    runs = [r for r in runs if r["record"]["n"] == 30 and r["record"]["name"].startswith(args.provider)]
    preds = {t["id"]: t["pred"] for t in runs[-1]["tickets"]}
    tickets = list(csv.DictReader(open(GOLDEN, encoding="utf-8-sig")))
    found = insights(tickets, preds, args.threshold)
    print(f"Based on {runs[-1]['record']['name']} over {len(tickets)} tickets (threshold {args.threshold}):")
    print("\n".join(f"- {s}" for s in found) or "- no repeated pattern yet")


if __name__ == "__main__":
    main()
