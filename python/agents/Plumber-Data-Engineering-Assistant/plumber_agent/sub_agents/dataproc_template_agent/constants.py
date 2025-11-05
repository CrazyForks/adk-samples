from typing import Literal

DATAPROC_TEMPLATE_GIT_URL = "https://github.com/GoogleCloudPlatform/dataproc-templates"
TEMPLATE_REPO_PATH = (
    "src/agents/plumber/agents/dataproc_template_agent/sources/git/dataproc_template"
)
GIT_PATH = "src/agents/plumber/agents/dataproc_template_agent/sources/git"
MODEL = "gemini-2.5-pro"
TEMP_DIR_PATH = "src/agents/plumber/agents/dataproc_template_agent/temp"
PYTHON_TEMPLATE_START_SCRIPT_BIN_PATH = f"{TEMPLATE_REPO_PATH}/python"
JAVA_TEMPLATE_START_SCRIPT_BIN_PATH = f"{TEMPLATE_REPO_PATH}/java"
LANGUAGE_OPTIONS = Literal["Java", "Python"]
