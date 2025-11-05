# dataflow_template_agent/utils.py

import os
import subprocess

import vertexai
from google.cloud import storage
from vertexai.generative_models import GenerativeModel

from .constants import MODEL
from .prompts import CORRECT_JAVA_FILE_INSTRUCTION, STTM_PARSING_INSTRUCTIONS_BEAM


def find_all_java_files_in_dir(directory: str) -> list:
    """
    Recursively finds all Java source files (.java) within the given directory.

    This function uses the Unix `find` command to perform the search and returns
    a list of file paths. It is designed to be the "Python Finds" part of a pattern
    where Python identifies candidate files before further processing.

    Args:
        directory (str): The path to the directory where the search should be performed.

    Returns:
        list: A list of strings representing the full paths to all found .java files.
              Returns an empty list if the directory does not exist or an error occurs.

    """
    if not os.path.isdir(directory):
        print(f"Error: Search directory does not exist: {directory}")
        return []
    try:
        # Use find to recursively get all .java files in the specified directory
        find_cmd = f'find "{directory}" -name "*.java"'
        result = subprocess.run(
            find_cmd, capture_output=True, shell=True, text=True, check=True
        )
        # Return a clean list of file paths
        return result.stdout.strip().splitlines()
    except Exception as e:
        print(f"Error finding Java files in {directory}: {e}")
        return []


def find_template_source_file_with_llm(
    repo_root_path: str, template_name: str, template_path_in_repo: str
) -> str:
    """
    Locates the main Java source file for a Dataflow template by combining local file search with LLM-based selection.

    This function performs the following steps:
    1. Searches the specified directory within the local repository to find all Java source files.
    2. If only one Java file is found, returns it immediately.
    3. If multiple Java files are found, uses a Large Language Model (LLM) to select the most appropriate file based on the template name and file list.
    4. Verifies the existence of the file chosen by the LLM before returning.

    Args:
        repo_root_path (str): The root directory of the cloned Dataflow templates repository.
        template_name (str): The name of the Dataflow template whose source file is to be identified.
        template_path_in_repo (str): The relative path within the repo where the template's source files are located.

    Returns:
        str: The full path to the identified main Java source file.
             Returns an empty string if no suitable file is found or an error occurs.

    Raises:
        None explicitly; all exceptions are caught internally and logged.

    """
    try:
        # 1. Define the specific subdirectory for the template we want to customize.
        search_directory = os.path.join(repo_root_path, template_path_in_repo)

        # 2. Python does the searching. It gets a list of all possible candidate files.
        all_java_files = find_all_java_files_in_dir(search_directory)

        if not all_java_files:
            return ""

        # Optimization: If there's only one Java file, it must be the correct one.
        if len(all_java_files) == 1:
            return all_java_files[0]

        # 3. The LLM does the choosing from the real list provided by Python.
        vertexai.init(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )
        model = GenerativeModel(MODEL)
        prompt = CORRECT_JAVA_FILE_INSTRUCTION.format(
            template_name=template_name, java_files_list="\n".join(all_java_files)
        )

        response = model.generate_content(prompt)
        correct_file_path = response.text.strip()

        # Final check to ensure the LLM's choice is valid and exists.
        if correct_file_path == "not_found" or not os.path.exists(correct_file_path):
            return ""

        return correct_file_path

    except Exception as e:
        print(
            f"An unexpected error occurred while finding source file for {template_name}: {e}"
        )
        return ""


def generate_beam_sql_query_from_sttm(gcs_path: str) -> str:
    """
    Generates a Beam SQL query from a CSV file stored in Google Cloud Storage using a generative model.

    This function downloads a CSV file from the provided GCS path, initializes a generative AI model,
    and uses it to parse the CSV content into a Beam SQL query based on predefined instructions.

    Args:
        gcs_path (str): The Google Cloud Storage URI (starting with "gs://") pointing to the CSV file.

    Returns:
        str: The generated Beam SQL query as a string. Returns an empty string if an error occurs.

    Raises:
        FileNotFoundError: If the CSV file does not exist at the specified GCS path.
        Exception: Captures any other exceptions during download or query generation, logging the error and returning an empty string.
    """
    try:
        storage_client = storage.Client()
        bucket_name, blob_name = gcs_path.replace("gs://", "").split("/", 1)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            raise FileNotFoundError(f"Object not found at GCS path: {gcs_path}")

        file_content = blob.download_as_text()

        vertexai.init(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )
        model = GenerativeModel(MODEL)
        response = model.generate_content(
            [STTM_PARSING_INSTRUCTIONS_BEAM, file_content]
        )

        output_sql = response.text.replace("```sql", "").replace("```", "").strip()
        return output_sql

    except Exception as e:
        print(f"An error occurred while generating the Beam SQL query: {e}")
        return ""
