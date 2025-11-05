import os
from typing import Any, Dict, List, Optional

import git
from git import InvalidGitRepositoryError, Repo


def initialize_git_repo(repo_path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(repo_path):
            return {"status": "error", "message": f"Path does not exist: {repo_path}"}
        try:
            existing_repo = Repo(repo_path)
            return {
                "status": "success",
                "message": f"Git repository already exists at {repo_path}",
                "is_existing": True,
                "current_branch": existing_repo.active_branch.name,
            }
        except InvalidGitRepositoryError:
            repo = Repo.init(repo_path)
            return {
                "status": "success",
                "message": f"Git repository initialized at {repo_path}",
                "is_existing": False,
                "current_branch": "main" if repo.heads else "No commits yet",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to initialize Git repository: {str(e)}",
        }


def get_git_status(repo_path: str) -> Dict[str, Any]:
    try:
        repo = Repo(repo_path)
        try:
            has_commits = bool(list(repo.iter_commits(max_count=1)))
        except Exception:
            has_commits = False
        modified_files = [item.a_path for item in repo.index.diff(None)]
        if has_commits:
            try:
                staged_files = [item.a_path for item in repo.index.diff("HEAD")]
                current_branch = repo.active_branch.name
            except Exception:
                staged_files = list(repo.index.entries.keys())
                current_branch = "main"
        else:
            staged_files = list(repo.index.entries.keys())
            try:
                current_branch = repo.active_branch.name
            except Exception:
                try:
                    current_branch = repo.git.branch("--show-current").strip()
                except Exception:
                    current_branch = "main"
        untracked_files = repo.untracked_files
        return {
            "status": "success",
            "current_branch": current_branch,
            "has_commits": has_commits,
            "is_dirty": repo.is_dirty(),
            "modified_files": modified_files,
            "staged_files": staged_files,
            "untracked_files": list(untracked_files),
            "total_changes": len(modified_files)
            + len(staged_files)
            + len(untracked_files),
        }
    except InvalidGitRepositoryError:
        return {"status": "error", "message": f"Not a Git repository: {repo_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get Git status: {str(e)}"}


def add_files_to_git(
    repo_path: str, files: Optional[List[str]] = None, add_all: bool = False
) -> Dict[str, Any]:
    try:
        repo = Repo(repo_path)
        if add_all:
            repo.git.add(A=True)
            added_files = "All modified and untracked files"
        elif files:
            valid_files = []
            for file_path in files:
                full_path = os.path.join(repo_path, file_path)
                if os.path.exists(full_path):
                    valid_files.append(file_path)
                else:
                    return {
                        "status": "error",
                        "message": f"File not found: {file_path}",
                    }
            repo.index.add(valid_files)
            added_files = valid_files
        else:
            return {
                "status": "error",
                "message": "No files specified and add_all is False",
            }
        return {
            "status": "success",
            "message": "Files added to staging area successfully",
            "added_files": added_files,
        }
    except InvalidGitRepositoryError:
        return {"status": "error", "message": f"Not a Git repository: {repo_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to add files: {str(e)}"}


def commit_changes(
    repo_path: str, commit_message: str, author_name: str = "", author_email: str = ""
) -> Dict[str, Any]:
    try:
        repo = Repo(repo_path)
        try:
            has_commits = bool(list(repo.iter_commits(max_count=1)))
        except Exception:
            has_commits = False
        if has_commits:
            if not repo.index.diff("HEAD"):
                return {"status": "error", "message": "No staged changes to commit"}
        else:
            if not repo.index.entries:
                return {"status": "error", "message": "No staged changes to commit"}
        if author_name and author_email:
            author = git.Actor(author_name, author_email)
            commit = repo.index.commit(commit_message, author=author)
        else:
            commit = repo.index.commit(commit_message)
        return {
            "status": "success",
            "message": "Changes committed successfully",
            "commit_hash": commit.hexsha[:8],
            "commit_message": commit_message,
            "files_changed": len(commit.stats.files),
        }
    except InvalidGitRepositoryError:
        return {"status": "error", "message": f"Not a Git repository: {repo_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to commit changes: {str(e)}"}


def list_git_branches(repo_path: str) -> Dict[str, Any]:
    try:
        repo = Repo(repo_path)
        branches = []
        current_branch = None
        for branch in repo.heads:
            branch_info = {
                "name": branch.name,
                "is_current": branch == repo.active_branch,
            }
            if branch_info["is_current"]:
                current_branch = branch.name
            branches.append(branch_info)
        return {
            "status": "success",
            "current_branch": current_branch,
            "branches": branches,
            "total_branches": len(branches),
        }
    except InvalidGitRepositoryError:
        return {"status": "error", "message": f"Not a Git repository: {repo_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list branches: {str(e)}"}


def switch_git_branch(
    repo_path: str, branch_name: str, create_if_not_exists: bool = False
) -> Dict[str, Any]:
    try:
        repo = Repo(repo_path)
        if repo.is_dirty():
            return {
                "status": "error",
                "message": "Cannot switch branches with uncommitted changes. Please commit or stash changes first.",
            }
        try:
            repo.git.checkout(branch_name)
            return {
                "status": "success",
                "message": f"Switched to existing branch '{branch_name}'",
                "current_branch": branch_name,
                "created_new": False,
            }
        except git.exc.GitCommandError:  # type: ignore
            if create_if_not_exists:
                repo.git.checkout("-b", branch_name)
                return {
                    "status": "success",
                    "message": f"Created and switched to new branch '{branch_name}'",
                    "current_branch": branch_name,
                    "created_new": True,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Branch '{branch_name}' does not exist. Set create_if_not_exists=True to create it.",
                }
    except InvalidGitRepositoryError:
        return {"status": "error", "message": f"Not a Git repository: {repo_path}"}  # type: ignore
    except Exception as e:
        return {"status": "error", "message": f"Failed to switch branch: {str(e)}"}
