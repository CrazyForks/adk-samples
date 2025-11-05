import json
import os
import shutil
import subprocess

import git
import vertexai
from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel

from .constants import (
    DATAPROC_TEMPLATE_GIT_URL,
    GIT_PATH,
    LANGUAGE_OPTIONS,
    TEMP_DIR_PATH,
    TEMPLATE_REPO_PATH,
)
from .prompts import (
    CORRECT_JAVA_TEMPLATE_FILE_INSTRUCTION,
    CORRECT_PYTHON_TEMPLATE_FILE_INSTRUCTION,
    CORRECT_README_FILE_INSTRUCTION,
    SEARCH_DATAPROC_TEMPLATE_INSTRUCTION,
    TRANSFORMATION_CODE_GENERATION_PROMPT,
)

# IMPORTING ENVIRONMENT VARIABLES FROM .env FILE
load_dotenv()

# ENABLING VERTEX AI
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
)


# UTIL FUNCTION TO LIST THE FILES IN THE DIRECTORY BASED ON THE INPUT REGEX
def find_files(dir: str, regex: str) -> list:
    """
    Recursively finds files in a given directory that match a specified regex pattern.

    This function uses the Unix `find` command to search for files with names
    matching the given pattern, excluding those containing "Config" in their name.

    Args:
        dir (str): The directory path in which to search.
        regex (str): The filename pattern to match (e.g., "README.md").

    Returns:
        list: A list of file paths that match the pattern. Returns an empty list if no matches
        are found or if an error occurs during execution.
    """
    try:
        readmd_run_cmd = f'find {dir} -iname "{regex}" -not -iname "*Config*"'

        result = subprocess.run(
            readmd_run_cmd, capture_output=True, shell=True, text=True, check=True
        )
        files = result.stdout.splitlines()

        return files
    except Exception:
        return []


# UTIL FUNCTION TO LIST THE FILES IN THE DIRECTORY BASED ON THE INPUT REGEX
def get_dataproc_template_mapping(
    readme_files_list: list, user_prompt: str, language: LANGUAGE_OPTIONS
) -> str:
    """
    Maps a user's natural language prompt to the most relevant Dataproc template
    by analyzing available README files and template scripts using a generative model.

    This function:
        1. Uses a generative model to select the most appropriate README file based on the prompt.
        2. Finds candidate Python or Java template files in the selected directory.
        3. Uses the model again to identify the best matching template script.
        4. Extracts additional metadata or configuration from the README.
        5. Returns a JSON string containing template details and the selected script path.

    Args:
        readme_files_list (list): A list of file paths to README.md files for all templates.
        user_prompt (str): The user's description of their desired data processing task.
        language (LANGUAGE_OPTIONS): The programming language ("Python" or "Java") to match templates against.

    Returns:
        str: A JSON-formatted string containing:
            - "template_path": The path to the selected template script (.py or .java).
            - Additional metadata extracted from the README file.
            Returns `'{}'` (empty JSON string) if no suitable match is found or on error.

    Exceptions:
        Returns an empty JSON string `'{}'` if any step in the process fails (e.g., model errors, file I/O).
    """
    try:
        model = GenerativeModel("gemini-2.0-flash")

        # FIND THE CORRECT README FILE BASED ON THE USER INPUT
        response = model.generate_content(
            CORRECT_README_FILE_INSTRUCTION.format(
                user_prompt=user_prompt, readme_files_list=readme_files_list
            )
        )
        correct_readme_file = response.text.replace("\n", "")
        readme_path = os.path.dirname(correct_readme_file)

        # IF NO TEMPLATES FOUND FOR A GIVEN SOURCE - RETURN {}
        if correct_readme_file == "not found":
            print("readme file not found")
            return json.dumps({})

        if language == "Python":
            # FETCH ALL THE TEMPLATES FROM THE README PATH
            template_files_list = find_files(dir=readme_path, regex="*_to_*.py")
        elif language == "Java":
            # FETCH ALL THE TEMPLATES FROM THE README PATH
            template_files_list = find_files(dir=readme_path, regex="*To*.java")

        # FIND THE CORRECT TEMPLATE FILE BASED ON THE USER INPUT
        if language.upper() == "JAVA":
            response = model.generate_content(
                CORRECT_JAVA_TEMPLATE_FILE_INSTRUCTION.format(
                    user_prompt=user_prompt, template_files_list=template_files_list
                )
            )
        else:
            response = model.generate_content(
                CORRECT_PYTHON_TEMPLATE_FILE_INSTRUCTION.format(
                    user_prompt=user_prompt, template_files_list=template_files_list
                )
            )
        correct_template = response.text.replace("\n", "")

        # IF NO TEMPLATES FOUND FOR A GIVEN SOURCE TO TARGET - RETURN {}
        if correct_template == "not found":
            print("correct template not found")
            return json.dumps({})

        # READING THE CONTENT OF README FILE
        with open(correct_readme_file, "r") as readme_file:
            readme_content = readme_file.read()

        # FETCHING THE CORRECT DATAPROC TEMPLATE FROM THE README FILE
        instruction = SEARCH_DATAPROC_TEMPLATE_INSTRUCTION.format(
            user_prompt=user_prompt, readme_content=readme_content
        )
        response = model.generate_content(instruction)

        # CLEANING THE API RESPONSE
        response = response.text.replace("```json", "").replace("```", "")
        response = eval(response)
        response["template_path"] = correct_template

        return json.dumps(response)

    except Exception:
        return json.dumps({})


# UTILITY FUNCTION TO CLONE DATAPROC TEMPLATE GIT REPO
def get_dataproc_template_repo() -> dict:
    """
    Clones or updates the local copy of the Dataproc templates GitHub repository.

    This function checks whether the `dataproc_template` repository already exists locally.
    - If it does, it performs a `git pull` to update it with the latest changes from the `main` branch.
    - If it does not, it clones the repository from the configured remote Git URL.

    Returns:
        dict: A dictionary containing:
            - "status" (str): A message indicating whether the repo was updated or cloned, or an error occurred.
            - "repo_path" (str): The local path to the cloned/updated repository (only on success).

    Exceptions:
        Catches all exceptions and returns an error message in the "status" field.
    """
    try:
        # IF THE TEMPLATE ALREADY EXISTS, JUST PULL THE LATEST CHANGES TO REPO
        if os.path.exists(f"./{GIT_PATH}/dataproc_template"):
            repo = git.Repo(f"./{GIT_PATH}/dataproc_template")
            origin = repo.remotes.origin
            origin.pull("main")
            return {
                "status": "success - repo already exists, updated with latest changes",
                "repo_path": f"./{GIT_PATH}/dataproc_template",
            }
        # CLONE THE DATAPROC TEMPLATE REPO
        else:
            repo = git.Repo.clone_from(
                DATAPROC_TEMPLATE_GIT_URL,
                to_path=f"./{GIT_PATH}/dataproc_template",
                branch="main",
            )
            return {
                "status": "success - repo created",
                "repo_path": f"./{GIT_PATH}/dataproc_template",
            }
    except Exception as err:
        return {"status": f"error - {str(err)}"}


# UTILITY FUNCTION TO VALIDATE THE USER INPUT PARAMS FOR A GIVEN TEMPLATE
def validate_input_params(template_params: dict, input_params: dict) -> dict:
    """
    Validates user-provided input parameters against a template's required and optional parameters.

    This function checks:
        1. If all required parameters are present in the input.
        2. If no extra/unknown parameters are provided.

    Args:
        template_params (dict): A dictionary with two keys:
            - "required" (list): List of required parameter names.
            - "optional" (list): List of optional parameter names.
        input_params (dict): Dictionary of parameters provided by the user.

    Returns:
        dict: A dictionary containing:
            - "validation_result" (str): Either "success" or "failed".
            - "comment" (str): Descriptive message about the validation outcome.

    Exceptions:
        Returns a failure response with an error message if an exception is raised during validation.
    """
    try:
        required_template_params = template_params.get("required", [])
        optional_template_params = template_params.get("optional", [])

        all_params = required_template_params + optional_template_params
        input_params_name = input_params.keys()

        # CHECK FOR ANY INVALID PARAMETER
        invalid_input_params = list(set(input_params_name) - set(all_params))

        if invalid_input_params:
            return {"validation_result": "failed", "comment": "Invalid param passed"}

        # CHECK WHETHER ALL REQUIRED PARAMS ARE PASSED OR NOT
        all_required_params = set(required_template_params).issubset(
            set(input_params_name)
        )

        if not all_required_params:
            return {"validation_result": "failed", "comment": "Missing required params"}

        return {"validation_result": "success", "comment": "Validation Passed"}
    except Exception as err:
        return {
            "validation_result": "failed",
            "comment": f"Error while running validation - {str(err)}",
        }


# UTILITY FUNCTION TO REPLICATE THE DATAPROC TEMPLATE DIRECTORY TO THE TEMP DIRECTORY WITH THE UPDATED TEMPLATE CODE
def update_dataproc_template(
    run_id: str, template_file_name: str, template_dir: str, transformation_sql: str
) -> str:
    """
    Creates a temporary, modified copy of a Dataproc template with transformation logic embedded.

    This function:
        - Clones the existing template repository into a temporary directory specific to the current run.
        - Reads the original template script.
        - Uses a generative model to inject transformation SQL logic into the template.
        - Writes the updated script into the temp directory, preserving the directory structure.

    Args:
        run_id (str): A unique identifier for this job run (used to isolate temp directories).
        template_file_name (str): The name of the original Dataproc template script (e.g., `gcs_to_bq.py`).
        template_dir (str): The directory containing the original template script.
        transformation_sql (str): The SQL transformation logic to embed into the template.

    Returns:
        str: Path to the root of the temporary Dataproc template repository that includes the modified template.
    """
    template_path = (
        f"{template_dir}/{template_file_name}"  # PATH OF THE TEMPLATE TO BE RUN
    )

    temp_template_repo_path = f"./{TEMP_DIR_PATH}/{run_id}/dataproc_template"  # PATH OF THE TEMP FOLDER FOR THE GIVEN JOB RUN WITH TRANSFORMATION
    temp_template_path = template_path.replace(
        f"./{TEMPLATE_REPO_PATH}", temp_template_repo_path
    )  # PATH OF THE TEMPLATE TO BE RUN IN THE TEMP FOLDER

    # COPY THE ORIGINAL TEMPLATE TO THE TEMP FOLDER
    shutil.copytree(
        f"./{TEMPLATE_REPO_PATH}", temp_template_repo_path, dirs_exist_ok=True
    )

    # READ THE ORIGINAL TEMPLATE
    with open(template_path, "r") as f:
        original_template_code = f.read()

    prompt = TRANSFORMATION_CODE_GENERATION_PROMPT.format(
        original_template_code=original_template_code,
        transformation_sql=transformation_sql,
    )

    model = GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    new_template_code = response.text

    new_template_code = (
        new_template_code.strip()
        .replace("```python", "")
        .replace("```java", "")
        .replace("```", "")
        .strip()
    )  # CODE WITH THE ADDED LOGIC FOR TRANSFORMATION

    # WRITING THE UPDATED TEMPLATE CODE TO THE TEMP DIRECTORY
    with open(temp_template_path, "w") as f:
        f.write(new_template_code)

    return temp_template_repo_path
