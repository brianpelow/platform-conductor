"""GitHub Discussions poster."""

from __future__ import annotations

import httpx
from conductor.core.config import ConductorConfig


def post_to_discussions(title: str, body: str, config: ConductorConfig) -> bool:
    """Post a weekly summary to GitHub Discussions via GraphQL API."""
    if not config.has_github:
        print(f"[mock] Would post to Discussions: {title}")
        print(body[:200] + "...")
        return True
    try:
        repo_id = _get_repo_id(config)
        category_id = _get_discussion_category(repo_id, config)
        if not repo_id or not category_id:
            print("[discussions] Could not resolve repo or category ID")
            return False

        query = """
        mutation CreateDiscussion($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
          createDiscussion(input: {repositoryId: $repoId, categoryId: $categoryId, title: $title, body: $body}) {
            discussion { url }
          }
        }"""
        with httpx.Client(timeout=30) as client:
            response = client.post(
                "https://api.github.com/graphql",
                headers={
                    "Authorization": f"Bearer {config.github_token}",
                    "Content-Type": "application/json",
                },
                json={"query": query, "variables": {
                    "repoId": repo_id, "categoryId": category_id,
                    "title": title, "body": body,
                }},
            )
            data = response.json()
            url = data.get("data", {}).get("createDiscussion", {}).get("discussion", {}).get("url", "")
            if url:
                print(f"[discussions] Posted: {url}")
                return True
            return False
    except Exception as e:
        print(f"[discussions] Error: {e}")
        return False


def _get_repo_id(config: ConductorConfig) -> str:
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                "https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {config.github_token}"},
                json={"query": f'{{ repository(owner: "{config.org}", name: "platform-conductor") {{ id }} }}'},
            )
            return response.json().get("data", {}).get("repository", {}).get("id", "")
    except Exception:
        return ""


def _get_discussion_category(repo_id: str, config: ConductorConfig) -> str:
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                "https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {config.github_token}"},
                json={"query": f'{{ repository(owner: "{config.org}", name: "platform-conductor") {{ discussionCategories(first: 10) {{ nodes {{ id name }} }} }} }}'},
            )
            categories = response.json().get("data", {}).get("repository", {}).get("discussionCategories", {}).get("nodes", [])
            for cat in categories:
                if "general" in cat.get("name", "").lower() or "announce" in cat.get("name", "").lower():
                    return cat["id"]
            return categories[0]["id"] if categories else ""
    except Exception:
        return ""