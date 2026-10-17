"""Print the experiment history as comparison tables (latest run per experiment and name)."""

import json

from msp_ops_copilot.eval_retrieval import HISTORY


def main() -> None:
    latest = {}
    for line in HISTORY.read_text().splitlines():
        r = json.loads(line)
        latest[(r["experiment"], r["name"])] = r

    print("RETRIEVAL (right menu section ranked first)")
    print(f"{'name':28} {'top1':>7} {'top3':>7} {'sec':>6} {'peakMB':>7} {'apiCalls':>8} {'diskMB':>7}")
    for (exp, name), r in sorted(latest.items()):
        if exp.startswith("retrieval"):
            disk = r["model_disk_mb"] if r["model_disk_mb"] is not None else "-"
            print(f"{name:28} {r['top1']:>3}/{r['n']:<3} {r['top3']:>3}/{r['n']:<3} {r['seconds']:>6} {r['peak_rss_mb']:>7} {r['api_calls']:>8} {disk:>7}")

    print("\nTRIAGE V2 (share of tickets matching the labelled set; only full 30-ticket runs)")
    print(f"{'name':40} {'type':>5} {'prio':>5} {'hand':>5} {'path':>5} {'tokIn':>7} {'tokOut':>7} {'s/call':>6} {'429':>4} {'cost$':>7}")
    for (exp, name), r in sorted(latest.items()):
        if exp == "triage-v2" and r["n"] == 30:
            a = r["accuracy"]
            cost = r["est_cost_usd"] if r["est_cost_usd"] is not None else "-"
            print(f"{name:40} {a['type']:>5.0%} {a['priority']:>5.0%} {a['handover']:>5.0%} {a['resolution_path']:>5.0%} {r['prompt_tokens']:>7} {r['completion_tokens']:>7} {r['avg_latency_s']:>6} {r['retries_429']:>4} {cost:>7}")


if __name__ == "__main__":
    main()
