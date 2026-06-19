"""
Rapportage voor Jira-projecten DWP, HLPD en ATL.

Gebruik:
    python jira_report.py                  # volledig rapport alle projecten
    python jira_report.py --project DWP    # enkel project DWP
    python jira_report.py --export         # exporteer naar CSV
"""

import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime, timezone

from jira_client import get_client

TRACKED_PROJECTS = ["DWP", "HLPD", "ATL"]


def _issues_for_project(client, project: str) -> list:
    return client.search_issues(
        f"project = {project} ORDER BY updated DESC",
        maxResults=500,
        fields="summary,status,priority,assignee,created,updated,issuetype,resolutiondate",
    )


def _build_project_stats(issues: list) -> dict:
    stats = {
        "total": len(issues),
        "by_status": defaultdict(int),
        "by_priority": defaultdict(int),
        "by_type": defaultdict(int),
        "unassigned": 0,
        "overdue": 0,
    }
    now = datetime.now(timezone.utc)

    for issue in issues:
        f = issue.fields
        stats["by_status"][f.status.name] += 1
        stats["by_priority"][getattr(f.priority, "name", "None")] += 1
        stats["by_type"][f.issuetype.name] += 1
        if not f.assignee:
            stats["unassigned"] += 1

    return stats


def _print_project_report(project: str, issues: list, stats: dict):
    width = 60
    print("=" * width)
    print(f"  PROJECT: {project}  ({stats['total']} issues)")
    print("=" * width)

    print("\nStatus verdeling:")
    for status, count in sorted(stats["by_status"].items()):
        bar = "█" * count
        print(f"  {status:<25} {count:>4}  {bar}")

    print("\nPrioriteit:")
    for prio, count in sorted(stats["by_priority"].items()):
        print(f"  {prio:<25} {count:>4}")

    print("\nIssue types:")
    for itype, count in sorted(stats["by_type"].items()):
        print(f"  {itype:<25} {count:>4}")

    print(f"\nNiet toegewezen:  {stats['unassigned']}")
    print()


def _print_summary(all_stats: dict):
    print("=" * 60)
    print("  SAMENVATTING ALLE PROJECTEN")
    print("=" * 60)
    totals = defaultdict(int)
    for project, stats in all_stats.items():
        totals["total"] += stats["total"]
        totals["unassigned"] += stats["unassigned"]
        for s, c in stats["by_status"].items():
            totals[f"status:{s}"] += c

    print(f"\n{'Project':<10} {'Totaal':>8} {'Niet toegew.':>14}")
    print("-" * 35)
    for project, stats in all_stats.items():
        print(f"{project:<10} {stats['total']:>8} {stats['unassigned']:>14}")
    print("-" * 35)
    print(f"{'TOTAAL':<10} {totals['total']:>8} {totals['unassigned']:>14}")
    print()


def _export_csv(all_issues: dict, filename: str):
    rows = []
    for project, issues in all_issues.items():
        for issue in issues:
            f = issue.fields
            rows.append({
                "project": project,
                "key": issue.key,
                "summary": f.summary,
                "type": f.issuetype.name,
                "status": f.status.name,
                "priority": getattr(f.priority, "name", ""),
                "assignee": getattr(f.assignee, "displayName", "") if f.assignee else "",
                "created": f.created[:10] if f.created else "",
                "updated": f.updated[:10] if f.updated else "",
            })

    with open(filename, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Geëxporteerd naar: {filename}")


def run_report(projects: list = None, export: bool = False):
    projects = projects or TRACKED_PROJECTS
    client = get_client()

    all_issues = {}
    all_stats = {}

    for project in projects:
        print(f"Ophalen issues voor {project}...")
        issues = _issues_for_project(client, project)
        stats = _build_project_stats(issues)
        all_issues[project] = issues
        all_stats[project] = stats

    print()
    for project in projects:
        _print_project_report(project, all_issues[project], all_stats[project])

    if len(projects) > 1:
        _print_summary(all_stats)

    if export:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jira_rapport_{ts}.csv"
        _export_csv(all_issues, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jira rapportage voor DWP, HLPD en ATL")
    parser.add_argument("--project", choices=TRACKED_PROJECTS, help="Enkel dit project rapporteren")
    parser.add_argument("--export", action="store_true", help="Exporteer resultaten naar CSV")
    args = parser.parse_args()

    projects = [args.project] if args.project else TRACKED_PROJECTS
    run_report(projects=projects, export=args.export)
