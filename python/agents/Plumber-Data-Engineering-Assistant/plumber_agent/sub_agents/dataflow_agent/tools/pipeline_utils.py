import asyncio
import json
import os
import re
import subprocess
import sys
import uuid
from typing import Dict

from google.cloud import storage


def _sanitize_job_name(name: str) -> str:
    """
    Sanitizes a string to conform to Google Cloud Dataflow job name requirements.

    Rules applied:
    - Converts the input string to lowercase.
    - Replaces any character not in [a-z0-9-] with a hyphen.
    - Collapses multiple consecutive hyphens into a single hyphen.
    - Strips leading and trailing hyphens.
    - If the resulting name is empty, generates a default name with a random UUID suffix.
    - Ensures the name starts with an alphabetic character by prefixing 'job-' if needed.
    - Ensures the name ends with an alphanumeric character by removing trailing non-alphanumeric characters.
    - Truncates the name to a maximum length of 63 characters.

    Args:
        name (str): The original job name string.

    Returns:
        str: A sanitized string valid for use as a Dataflow job name.
    """
    sanitized = name.lower()
    sanitized = re.sub(r"[^a-z0-9-]", "-", sanitized)
    sanitized = re.sub(r"-+", "-", sanitized)
    sanitized = sanitized.strip("-")
    if not sanitized:
        return f"job-{uuid.uuid4().hex[:8]}"
    if not sanitized[0].isalpha():
        sanitized = "job-" + sanitized
    if not sanitized[-1].isalnum():
        sanitized = sanitized[:-1]
    return sanitized[:63]


async def create_pipeline_from_scratch(
    project_id: str,
    region: str,
    gcs_bucket_path: str,
    job_name: str,
    pipeline_code: str,
    pipeline_args: Dict[str, str],
    pipeline_type: str,
) -> str:
    """
    Generates and executes a Python Apache Beam pipeline on Google Cloud Dataflow.

    Args:
        project_id (str): Google Cloud project ID where the Dataflow job will run.
        region (str): Region where the Dataflow job will be executed.
        gcs_bucket_path (str): Google Cloud Storage path for staging pipeline artifacts.
        job_name (str): Desired name for the Dataflow job.
        pipeline_code (str): The source code of the Beam pipeline to run.
        pipeline_args (Dict[str, str]): Key-value pairs of pipeline arguments.
        pipeline_type (str): Type of the pipeline, either 'batch' or 'streaming'.

    Returns:
        str: JSON-formatted string with the status and any relevant messages or errors.
    """
    if pipeline_type not in ["batch", "streaming"]:
        return json.dumps(
            {
                "status": "error",
                "error_message": "Invalid pipeline type. Please choose 'batch' or 'streaming'.",
            }
        )

    if pipeline_type == "streaming":
        pipeline_args["streaming"] = "true"

    return await generate_and_run_beam_pipeline(
        project_id,
        region,
        gcs_bucket_path,
        job_name,
        pipeline_code,
        pipeline_args,
        pipeline_type,
    )


async def generate_and_run_beam_pipeline(
    project_id: str,
    region: str,
    gcs_bucket_path: str,
    job_name: str,
    pipeline_code: str,
    pipeline_args: Dict[str, str],
    pipeline_type: str,
) -> str:
    """
    Generates, executes, and archives a Python Apache Beam pipeline on Google Cloud Dataflow.

    This function writes the given pipeline code to a temporary file, runs it asynchronously
    as a subprocess with the provided parameters, captures the output, extracts the Dataflow job ID,
    and uploads the pipeline code to a specified GCS bucket for archival.

    Args:
        project_id (str): Google Cloud project ID where the job will run.
        region (str): Region for the Dataflow job.
        gcs_bucket_path (str): Google Cloud Storage path (must start with "gs://") for staging and archival.
        job_name (str): Desired job name for the Dataflow pipeline (will be sanitized).
        pipeline_code (str): Python source code of the Beam pipeline.
        pipeline_args (Dict[str, str]): Dictionary of pipeline parameters to pass at runtime.
        pipeline_type (str): Pipeline type, either "batch" or "streaming". Streaming pipelines
            will run indefinitely until manually stopped.

    Returns:
        str: A JSON-formatted string containing:
            - status: "success", "success_with_warning", or "error"
            - report: A human-readable summary of the job launch and archival process.
            - job_id: The Dataflow job ID if successfully parsed.
            - gcs_script_path: The GCS path where the pipeline code was archived (if successful).
            - error_message: Present if an error occurred.

    Raises:
        No exceptions are raised; errors are captured and returned as JSON error responses.
    """
    if not all([project_id, region, gcs_bucket_path]):
        return json.dumps(
            {
                "status": "error",
                "error_message": "project_id, region, and gcs_bucket_path are required.",
            }
        )

    if not gcs_bucket_path.startswith("gs://"):
        return json.dumps(
            {
                "status": "error",
                "error_message": "gcs_bucket_path must start with 'gs://'.",
            }
        )

    base_path = os.path.join("plumber", "agent", "agents", "dataflow_agent")
    os.makedirs(base_path, exist_ok=True)
    temp_filename = os.path.join(base_path, f"temp_pipeline_{uuid.uuid4()}.py")
    sanitized_job_name = _sanitize_job_name(job_name)

    full_args = {
        "runner": "DataflowRunner",
        "project": project_id,
        "region": region,
        "job_name": sanitized_job_name,
        "temp_location": os.path.join(gcs_bucket_path, "temp"),
        "staging_location": os.path.join(gcs_bucket_path, "staging"),
        "labels": json.dumps({"source": "plumber"}),
        **pipeline_args,
    }

    try:
        with open(temp_filename, "w") as f:
            f.write(pipeline_code)

        command = [sys.executable, temp_filename]
        for key, value in full_args.items():
            command.append(f"--{key}")
            command.append(str(value))

        output = ""
        job_id_match = None

        if pipeline_type == "streaming":
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            if process.stdout is not None:
                async for line_bytes in process.stdout:
                    line = line_bytes.decode("utf-8", errors="ignore")
                    output += line
                    print(line, end="")
                    match = re.search(
                        r"(\d{4}-\d{2}-\d{2}_\d{2}_\d{2}_\d{2}-\d+)", line
                    )
                    if match:
                        job_id_match = match
                        print(
                            f"\n--- INFO: Found Dataflow Job ID: {job_id_match.group(1)}. Terminating script watcher. ---"
                        )
                        break

            if process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    print(
                        "--- WARNING: Subprocess did not terminate gracefully, killing it. ---"
                    )
                    process.kill()
                except ProcessLookupError:
                    pass  # Process already terminated

            if not job_id_match:
                stdout, stderr = await process.communicate()
                output += stdout.decode("utf-8", errors="ignore")
                if stderr:
                    output += stderr.decode("utf-8", errors="ignore")
                raise subprocess.CalledProcessError(
                    process.returncode or 1, command, output=output
                )
        else:  # Batch
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            output = stdout.decode("utf-8", errors="ignore") + stderr.decode(
                "utf-8", errors="ignore"
            )
            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode or 1, command, output=output
                )
            job_id_match = re.search(
                r"(?P<id>\d{4}-\d{2}-\d{2}_\d{2}_\d{2}_\d{2}-\d+)", output
            )

        if not job_id_match:
            return json.dumps(
                {
                    "status": "error",
                    "error_message": f"Job launched, but could not find Job ID in output. Full output:\n{output}",
                }
            )

        # Reporting and GCS Archival
        job_details = {"name": sanitized_job_name}
        id_match = re.search(r"id: '([^']*)'", output)
        client_request_id_match = re.search(r"clientRequestId: '([^']*)'", output)
        create_time_match = re.search(r"createTime: '([^']*)'", output)

        job_id = job_id_match.group(1) if job_id_match else "unknown"
        job_details["id"] = job_id
        if id_match:
            if client_request_id_match:
                job_details["clientRequestId"] = client_request_id_match.group(1)
            if create_time_match:
                job_details["createTime"] = create_time_match.group(1)

        gcs_path, gcs_error = None, None
        try:
            storage_client = storage.Client(project=project_id)
            bucket_name, *path_parts = gcs_bucket_path.replace("gs://", "").split("/")
            base_prefix = "/".join(filter(None, path_parts))
            script_filename = f"{sanitized_job_name}-{uuid.uuid4().hex[:8]}.py"
            gcs_path_str = os.path.join(
                base_prefix, "generated_pipelines", script_filename
            )

            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(gcs_path_str)
            blob.upload_from_string(pipeline_code, content_type="text/x-python")
            gcs_path = f"gs://{bucket_name}/{gcs_path_str}"
        except Exception as e:
            gcs_error = e

        report_lines = [f"Successfully launched Dataflow job '{sanitized_job_name}'."]
        report_lines.append("Job Details:")
        for key, value in sorted(job_details.items()):
            report_lines.append(f"  {key}: {value}")

        status = "success"
        if gcs_path:
            report_lines.append(f"\nThe pipeline script was saved to {gcs_path}")
        if gcs_error:
            status = "success_with_warning"
            report_lines.append(
                f"\nWARNING: Failed to save the script to GCS. Error: {gcs_error}"
            )

        final_report = {
            "status": status,
            "report": "\n".join(report_lines),
            "job_id": job_id,
            "gcs_script_path": gcs_path,
        }
        print(json.dumps(final_report, indent=2))
        return json.dumps(final_report)

    except subprocess.CalledProcessError as e:
        return json.dumps(
            {
                "status": "error",
                "error_message": f"Failed to execute pipeline script.\n--- ERROR ---\n{e.output}",
            }
        )
    except Exception as e:
        return json.dumps(
            {"status": "error", "error_message": f"Unexpected error: {str(e)}"}
        )
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
