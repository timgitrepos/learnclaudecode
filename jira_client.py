"""
Jira Data Center on-premise client.
Set JIRA_URL and JIRA_PAT as environment variables before use.
"""

import os
from jira import JIRA


def get_client() -> JIRA:
    url = os.environ["JIRA_URL"]   # e.g. https://jira.yourcompany.com
    token = os.environ["JIRA_PAT"] # Personal Access Token
    return JIRA(server=url, token_auth=token)


# --- Issues ---

def search_issues(jql: str, max_results: int = 50) -> list:
    client = get_client()
    return client.search_issues(jql, maxResults=max_results)


def get_issue(issue_key: str):
    return get_client().issue(issue_key)


def create_issue(project_key: str, summary: str, description: str = "", issue_type: str = "Task"):
    client = get_client()
    return client.create_issue(fields={
        "project": {"key": project_key},
        "summary": summary,
        "description": description,
        "issuetype": {"name": issue_type},
    })


def update_issue(issue_key: str, fields: dict):
    issue = get_client().issue(issue_key)
    issue.update(fields=fields)


# --- Projects & metadata ---

def list_projects() -> list:
    return get_client().projects()


def get_issue_types() -> list:
    return get_client().issue_types()


# --- Comments & attachments ---

def add_comment(issue_key: str, body: str):
    return get_client().add_comment(issue_key, body)


def get_comments(issue_key: str) -> list:
    return get_client().comments(issue_key)


def add_attachment(issue_key: str, file_path: str):
    client = get_client()
    with open(file_path, "rb") as f:
        return client.add_attachment(issue=issue_key, attachment=f)


# --- Transitions ---

def get_transitions(issue_key: str) -> list:
    return get_client().transitions(issue_key)


def transition_issue(issue_key: str, transition_name: str):
    client = get_client()
    transitions = client.transitions(issue_key)
    for t in transitions:
        if t["name"].lower() == transition_name.lower():
            client.transition_issue(issue_key, t["id"])
            return
    raise ValueError(f"Transition '{transition_name}' not found. Available: {[t['name'] for t in transitions]}")


if __name__ == "__main__":
    # Quick connection test
    client = get_client()
    me = client.myself()
    print(f"Connected as: {me['displayName']} ({me['emailAddress']})")
    print(f"Jira version: {client.server_info()['version']}")
