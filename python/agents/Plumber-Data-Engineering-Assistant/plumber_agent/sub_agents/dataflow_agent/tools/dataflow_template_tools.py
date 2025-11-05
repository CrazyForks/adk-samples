import json
import os
import re  # Import the regular expression module
import subprocess

import git
import vertexai
from vertexai.generative_models import GenerativeModel

# Import everything from your other files
from ..constants import (
    DATAFLOW_TEMPLATE_GIT_URL,
    GIT_PATH,
    MODEL,
    TEMPLATE_MAPPING_PATH,
)
from ..prompts import (
    CORRECT_JAVA_FILE_INSTRUCTION,
    SEARCH_DATAFLOW_TEMPLATE_INSTRUCTION,
)
from ..utils import find_all_java_files_in_dir


def get_dataflow_template_repo() -> dict:
    """
    Clones or updates the local DataflowTemplates git repository.

    If the repository already exists locally, pulls the latest changes from the 'main' branch.
    Otherwise, clones the repository from the remote URL.

    Returns:
        dict: A dictionary with:
            - 'status': "success" or "error - <error message>"
            - 'repo_path': The local path to the repository on success.
    """
    try:
        repo_path = f"./{GIT_PATH}/DataflowTemplates"
        if os.path.exists(repo_path):
            repo = git.Repo(repo_path)
            repo.remotes.origin.pull("main")
            return {"status": "success", "repo_path": repo_path}
        else:
            git.Repo.clone_from(
                DATAFLOW_TEMPLATE_GIT_URL, to_path=repo_path, branch="main"
            )
            return {"status": "success", "repo_path": repo_path}
    except Exception as err:
        return {"status": f"error - {str(err)}"}


# UTILITY FUNCTION TO VALIDATE THE USER INPUT PARAMS FOR A GIVEN TEMPLATE
def validate_input_params(template_definition: dict, user_inputs: dict) -> dict:
    """
    Validates user input parameters against a template definition.

    Args:
        template_definition (dict): Dictionary containing 'required' and 'optional' parameter lists.
        user_inputs (dict): Dictionary of user-provided parameters to validate.

    Returns:
        dict: Validation result with keys:
            - "validation_result": "success" or "failed"
            - "comment": Explanation of validation outcome, including any missing or invalid params.

    The function checks that:
    - No invalid parameters are present in user_inputs (i.e., parameters not defined in template_definition).
    - All required parameters defined in the template are present in user_inputs.
    """
    try:
        # Use .get() with an empty list as a default to prevent KeyErrors
        required_params = template_definition.get("required", [])
        optional_params = template_definition.get("optional", [])

        all_defined_params = required_params + optional_params
        user_param_keys = user_inputs.keys()

        # CHECK FOR INVALID PARAMETERS (parameters the user gave that don't exist in the template)
        invalid_params = list(set(user_param_keys) - set(all_defined_params))
        if invalid_params:
            return {
                "validation_result": "failed",
                "comment": f"Invalid param(s) passed: {invalid_params}. Valid params are: {all_defined_params}",
            }

        # CHECK IF ALL REQUIRED PARAMS ARE PRESENT in the user's input
        missing_required = list(set(required_params) - set(user_param_keys))
        if missing_required:
            return {
                "validation_result": "failed",
                "comment": f"Missing required param(s): {missing_required}",
            }

        return {"validation_result": "success", "comment": "Validation Passed"}
    except Exception as err:
        return {
            "validation_result": "failed",
            "comment": f"An unexpected error occurred during validation - {str(err)}",
        }


# This function remains correct. It uses your hardcoded JSON.
def get_dataflow_template(user_prompt: str):
    """
    Retrieves a Dataflow template based on a user prompt by querying a generative model.

    The function:
    - Ensures the Dataflow template repository is cloned or updated locally.
    - Initializes the Vertex AI environment.
    - Loads the template mapping JSON.
    - Generates an instruction for the generative model using the user prompt and template mappings.
    - Uses the model to generate a response containing the matching Dataflow template.

    Args:
        user_prompt (str): A natural language description or request for a Dataflow template.

    Returns:
        str: The generated Dataflow template as text, or a JSON string with an error message if an exception occurs.
    """
    try:
        get_dataflow_template_repo()
        vertexai.init(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )
        model = GenerativeModel(MODEL)
        with open(f"./{TEMPLATE_MAPPING_PATH}", "r") as json_file:
            template_mapping_dict = json.load(json_file)
        instruction = SEARCH_DATAFLOW_TEMPLATE_INSTRUCTION.format(
            task=user_prompt, template_mapping_json=json.dumps(template_mapping_dict)
        )
        response = model.generate_content(instruction)
        return response.text
    except Exception as err:
        return json.dumps({"error": f"An unexpected error occurred: {str(err)}"})


def customize_and_build_template(
    gcp_project: str,
    bucket_name: str,
    template_name: str,
    template_path: str,
    sttm_gcs_path: str,
) -> dict:
    """
    Finds, modifies, builds, and stages a custom Dataflow template.

    This function performs the following steps:
    1. Ensures the Dataflow template repository is cloned and accessible.
    2. Searches for Java source files in the specified directory and uses an LLM to select the correct main template file.
    3. Initializes the Vertex AI environment and calls the model to identify the correct Java file.
    4. Constructs and executes a Maven build command with parameters for GCP project, bucket, and template.
    5. Parses the Maven output to extract the staged template GCS path.
    6. Returns the status and details about the staged template.

    Args:
        gcp_project (str): Google Cloud project ID where the Dataflow job will be deployed.
        bucket_name (str): GCS bucket name used for staging the template.
        template_name (str): The name of the Dataflow template to build.
        template_path (str): Relative path within the cloned repository where the template source code resides.
        sttm_gcs_path (str): (Unused in this function, possibly for future use or extension.)

    Returns:
        dict: A dictionary with keys:
            - "status": "success" or "failed"
            - "comment": Description of the outcome or error
            - "staged_template_gcs_path" (on success): The GCS path where the template is staged
            - "stdout" (on failure): The Maven command output if build fails or output can't be parsed
    """
    try:
        # Step 1: Ensure the source code is cloned and available.
        repo_status = get_dataflow_template_repo()
        if "error" in repo_status["status"]:
            return {
                "status": "failed",
                "comment": f"Could not access template repo: {repo_status['status']}",
            }

        repo_root_path = repo_status["repo_path"]
        search_directory = os.path.join(repo_root_path, template_path)

        # Step 2: Use the "Python Finds, LLM Chooses" pattern to locate the source file.
        all_java_files = find_all_java_files_in_dir(search_directory)
        if not all_java_files:
            return {
                "status": "failed",
                "comment": f"No .java source files found in directory: {search_directory}",
            }

        vertexai.init(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )
        model = GenerativeModel(MODEL)
        prompt = CORRECT_JAVA_FILE_INSTRUCTION.format(
            template_name=template_name, java_files_list="\n".join(all_java_files)
        )
        response = model.generate_content(prompt)
        main_java_file_path = response.text.strip()
        print(f"Found template file: {main_java_file_path}")

        if main_java_file_path == "not_found" or not os.path.exists(
            main_java_file_path
        ):
            return {
                "status": "failed",
                "comment": f"LLM could not identify the correct source file for {template_name}.",
            }

        template_module_path = os.path.join(repo_root_path, template_path)

        default_labels = "plumber"
        mvn_cmd = f"""
        mvn clean package -PtemplatesStage -DskipTests \\
            -DprojectId="{gcp_project}" \\
            -DbucketName="{bucket_name}" \\
            -DstagePrefix="templates" \\
            -DtemplateName="{template_name}" \\
            -Dlabels={default_labels} \\
            -f "{template_module_path}"
        """
        print(f"Executing build command...\n{mvn_cmd}")
        # Step 5: Run the build command, capturing all output.
        cmd_run_status = subprocess.run(
            mvn_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
            shell=True,
        )

        # Step 6: Parse the output to get the GCS path using a robust regex search.
        staged_path = ""
        combined_output = cmd_run_status.stdout
        patterns = [
            r"Flex Template was staged!\s+(gs://[^\s]+)",
            r"Template staged successfully\. It is available at\s+(gs://[^\s]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, combined_output)
            if match:
                staged_path = match.group(1)
                break

        if not staged_path:
            return {
                "status": "failed",
                "comment": "Build succeeded, but could not find the staged template GCS path in the build output.",
                "stdout": combined_output,
            }

        # Step 7: Return the successful result.
        print(f"Successfully found staged template path: {staged_path}")
        return {
            "status": "success",
            "comment": f"Template '{template_name}' was built and staged.",
            "staged_template_gcs_path": staged_path,
        }

    except subprocess.CalledProcessError as cmd_err:
        return {
            "status": "failed",
            "comment": "The maven build command failed.",
            "stdout": cmd_err.stdout,
            "stderr": "",
        }
    except Exception as err:
        return {
            "status": "failed",
            "comment": f"An unexpected error occurred: {str(err)}",
        }


def submit_dataflow_template(
    job_name: str,
    input_params: str,
    template_params: str,
    gcp_project: str,
    region: str,
    gcs_staging_location: str,
    custom_gcs_path: str = "",
) -> dict:
    """
    Submits a Dataflow job using a given template, optionally bypassing parameter validation for custom templates.

    This function performs the following steps:
    1. Parses input parameters and template definition from JSON strings.
    2. Handles cases where the template definition may be wrapped in a list.
    3. Determines the GCS path of the Dataflow template, either custom or from the template definition.
    4. Validates user input parameters against the template definition parameters unless a custom template path is provided.
    5. Constructs the parameter string required by the gcloud CLI, using a custom delimiter.
    6. Decides whether to use a flex-template or classic template gcloud command based on the template type or path.
    7. Executes the gcloud command to submit the Dataflow job.
    8. Returns the result status and command output or error details.

    Args:
        job_name (str): Name to assign to the Dataflow job.
        input_params (str): JSON string containing user input parameters for the job.
        template_params (str): JSON string containing the Dataflow template definition.
        gcp_project (str): Google Cloud project ID.
        region (str): Google Cloud region where the job will run.
        gcs_staging_location (str): GCS path used for staging Dataflow job artifacts.
        custom_gcs_path (str, optional): Optional custom GCS path for the Dataflow template. If provided, parameter validation is skipped.

    Returns:
        dict: A dictionary with keys:
            - "status": "success" or "failed"
            - "comment": Explanation of success or failure
            - "stdout": Standard output from the gcloud command on success
    """

    try:
        user_input_dict = json.loads(input_params)
        template_definition_dict = json.loads(template_params)

        # Handle cases where the template definition might be wrapped in a list.
        if isinstance(template_definition_dict, list):
            if len(template_definition_dict) > 0:
                template_definition_dict = template_definition_dict[0]
            else:
                # If the list is empty, we cannot proceed.
                return {
                    "status": "failed",
                    "comment": "Job could not be submitted because the template definition was an empty list.",
                }

        if not isinstance(template_definition_dict, dict):
            return {
                "status": "failed",
                "comment": "Job could not be submitted because the processed template definition is not a valid dictionary (JSON object).",
            }

        template_gcs_path = (
            custom_gcs_path
            if custom_gcs_path
            else template_definition_dict.get("template_gcs_path")
        )

        if not template_gcs_path:
            return {
                "status": "failed",
                "comment": 'Job could not be submitted because the "template_gcs_path" key was not found.',
            }

        # If a custom GCS path is NOT provided, validate parameters against the definition.
        if not custom_gcs_path and isinstance(template_definition_dict, dict):
            params_to_validate = template_definition_dict.get("params", {})
            if not params_to_validate:
                return {
                    "status": "failed",
                    "comment": 'Job could not be submitted because the template definition is missing the "params" key.',
                }

            param_validation_result = validate_input_params(
                template_definition=params_to_validate,
                user_inputs=user_input_dict,
            )
            if param_validation_result["validation_result"] != "success":
                return {
                    "status": "failed",
                    "comment": f"Job could not be submitted due to a parameter validation error: {param_validation_result.get('comment', 'Unknown reason')}",
                }

        delemeter = "~"

        parameters_str = f"{delemeter}".join(
            [f"{key}={value}" for key, value in user_input_dict.items()]
        )
        parameters_str = f"^{delemeter}^{parameters_str}"
        print(f"Final parameters string for gcloud command: {parameters_str}")

        is_flex = (
            "/flex/" in template_gcs_path
            or template_definition_dict.get("type") == "FLEX"
        )
        default_labels = "source=plumber"

        if is_flex:
            run_cmd = f'gcloud dataflow flex-template run {job_name} --project={gcp_project} --region={region} --template-file-gcs-location={template_gcs_path} --parameters "{parameters_str}" --additional-user-labels={default_labels}'
        else:
            run_cmd = f'gcloud dataflow jobs run {job_name} --project={gcp_project} --region={region} --gcs-location={template_gcs_path} --parameters "{parameters_str}" --staging-location={gcs_staging_location} --additional-user-labels={default_labels}'

        print("Executing command:\n", run_cmd)
        cmd_run_status = subprocess.run(
            run_cmd, capture_output=True, text=True, check=True, shell=True
        )
        return {
            "status": "success",
            "stdout": cmd_run_status.stdout,
            "comment": "Job Submitted Successfully",
        }
    except Exception as err:
        return {
            "status": "failed",
            "comment": f"An unexpected error occurred: {str(err)}",
        }
