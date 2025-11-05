import getpass
import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

USER_AGENT = "GitHub-Downloader-ADK/2.0"


def _create_github_headers(token: str) -> Dict[str, str]:
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get_auth_token(token: str) -> str:
    token = token or os.getenv("GITHUB_TOKEN") or ""
    if not token or not token.strip():
        token = getpass.getpass("Enter your GitHub Personal Access Token: ")
    return token.strip()


def _parse_repo_path(repository: str) -> tuple[str | None, str | None]:
    if repository.startswith(("http://", "https://")):
        repo_path = repository.split("github.com/")[-1].rstrip(".git")
    else:
        repo_path = repository
    if "/" not in repo_path:
        return None, None
    owner, repo = repo_path.split("/", 1)
    return owner, repo
