from google.adk.agents import Agent

from .constants import MODEL
from .tools.cloud_storage import (
    create_gcs_bucket,
    delete_from_gcs,
    delete_gcs_bucket,
    download_from_gcs,
    list_gcs_buckets,
    list_gcs_objects,
    upload_directory_to_gcs,
    upload_repository_to_gcs,
)
from .tools.git_ops import (
    add_files_to_git,
    commit_changes,
    get_git_status,
    initialize_git_repo,
    list_git_branches,
    switch_git_branch,
)
from .tools.github_api import (
    authenticate_github,
    download_repository,
    download_repository_to_gcs,
    list_branches,
    search_repositories,
)
from .tools.github_prompts import AGENT_INSTRUCTIONS

root_agent = Agent(
    name="github_agent",
    model=MODEL,
    description="Advanced GitHub, Git, and Google Cloud Storage repository management agent with full version control and cloud storage capabilities.",
    instruction=AGENT_INSTRUCTIONS,
    tools=[
        # GitHub API Tools
        authenticate_github,
        search_repositories,
        list_branches,
        download_repository,
        download_repository_to_gcs,
        # Git Operations Tools
        initialize_git_repo,
        get_git_status,
        add_files_to_git,
        commit_changes,
        list_git_branches,
        switch_git_branch,
        # Google Cloud Storage Tools
        create_gcs_bucket,
        list_gcs_buckets,
        delete_gcs_bucket,
        upload_repository_to_gcs,
        upload_directory_to_gcs,
        download_from_gcs,
        list_gcs_objects,
        delete_from_gcs,
    ],
)
