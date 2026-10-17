"""Print the experiment history as a comparison table (latest run per name)."""

import json

from msp_ops_copilot.eval_retrieval import HISTORY


def main() -> None:
    latest = {}
    for line in HISTORY.read_text().splitlines():
        r = json.loads(line)
        latest[(r["experiment"], r["name"])] = r
    print(f"{'experiment':24} {'name':28} {'top1':>7} {'top3':>7} {'sec':>6} {'peakMB':>7} {'apiCalls':>8} {'diskMB':>7}  commit")
    for (exp, name), r in sorted(latest.items()):
        disk = r["model_disk_mb"] if r["model_disk_mb"] is not None else "-"
        print(f"{exp:24} {name:28} {r['top1']:>3}/{r['n']:<3} {r['top3']:>3}/{r['n']:<3} {r['seconds']:>6} {r['peak_rss_mb']:>7} {r['api_calls']:>8} {disk:>7}  {r['git_commit']}")


if __name__ == "__main__":
    main()
