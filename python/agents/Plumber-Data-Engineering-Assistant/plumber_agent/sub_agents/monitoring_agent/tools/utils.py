import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from google.cloud import logging_v2, monitoring_v3
from google.protobuf import duration_pb2, timestamp_pb2

from ..prompt import (
    LATEST_ERROR_PROMT,
    LATEST_LOGS_PROMT,
    SEVERITIES_LIST,
    TIME_RANGE_LOGS_PROMT,
)

logger = logging.getLogger("plumber-agent")


def get_cpu_utilization(project_id: str) -> dict:
    """
    Connects to Google Cloud Monitoring and retrieves CPU utilization
    for all VM instances in the specified project over the last 5 minutes.

    This function queries Google Cloud Monitoring to obtain CPU utilization metrics
    for all virtual machine (VM) instances within the configured Google Cloud project.
    It fetches data for the last 5 minutes, aggregates it by instance ID and zone,
    and calculates the mean CPU utilization for each instance over 1-minute intervals.

    Args:
        project_id (str, required): The Google Cloud project ID. from which logs are to be fetched.

    Returns:
        dict: A dictionary containing the status of the operation and a report of
            CPU utilization data or an error message if the operation fails.
            The dictionary will have the following keys:
            - "status" (str): "success" if the data was fetched, or "error" on failure.
            - "report" (str): A detailed string containing the CPU utilization
                data for each instance (Instance ID, Zone, Timestamp, and Value)
                or a message indicating no data was found.
            - "message" (str, optional): Only present if "status" is "error",
                providing details about the specific error encountered.

    Note: [IMPORTANT]
        - Call only when user ask's about CPU utilization
    """
    project_path = f"projects/{project_id}"

    util_client = monitoring_v3.MetricServiceClient()
    # Define the time range for the query
    now = time.time()

    end_timestamp = timestamp_pb2.Timestamp()
    end_timestamp.seconds = int(now)
    end_timestamp.nanos = int((now - int(now)) * 10**9)

    start_timestamp = timestamp_pb2.Timestamp()
    start_timestamp.seconds = int(now) - 300  # 5 minutes ago (300 seconds)
    start_timestamp.nanos = int((now - int(now)) * 10**9)

    interval = monitoring_v3.TimeInterval(
        end_time=end_timestamp, start_time=start_timestamp
    )

    # Define the metric filter
    metric_filter = 'metric.type = "compute.googleapis.com/instance/cpu/utilization"'

    # Define the aggregation parameters
    aggregation = monitoring_v3.Aggregation()

    # And then assign it to the aggregation object.
    aggregation.alignment_period = duration_pb2.Duration(seconds=60)

    aggregation.per_series_aligner = monitoring_v3.Aggregation.Aligner.ALIGN_MEAN
    aggregation.cross_series_reducer = monitoring_v3.Aggregation.Reducer.REDUCE_MEAN
    aggregation.group_by_fields.append("resource.label.instance_id")
    aggregation.group_by_fields.append("resource.label.zone")

    try:
        response = util_client.list_time_series(
            request={
                "name": project_path,
                "filter": metric_filter,
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                "aggregation": aggregation,
            }
        )

        found_data = False
        cpu_data_report = []
        for series in response.time_series:
            found_data = True
            resource_labels = series.resource.labels

            instance_id = resource_labels.get("instance_id", "N/A")
            zone = resource_labels.get("zone", "N/A")

            series_info = f"  Instance ID: {instance_id}, Zone: {zone}"
            cpu_data_report.append(series_info)

            for point in series.points:
                value = point.value.double_value
                timestamp = point.interval.end_time
                cpu_data_report.append(
                    f"    Timestamp: {timestamp}, Value: {value:.2f}%"
                )

        if not found_data:
            print(
                "No CPU utilization data found for the specified project and time range."
            )
            return {
                "status": "success",
                "report": "No CPU utilization data found for the specified project and time range.",
            }
        else:
            print("Successfully fetched CPU utilization data.")
            return {
                "status": "success",
                "report": "CPU Utilization Data:\n" + "\n".join(cpu_data_report),
            }

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        print(f"An error occurred: {e}")
        return {"status": "error", "message": f"Failed to get CPU utilization: {e}"}


def get_latest_error(project_id: str) -> dict:
    f""" {LATEST_ERROR_PROMT} """

    try:
        client = logging_v2.Client(project=project_id)
        project_path = f"projects/{project_id}"
        latest_errors_iterator = client.list_entries(
            resource_names=[project_path],
            order_by="timestamp desc",
            page_size=1,
            filter_=f'severity = ERROR AND timestamp >= "{(datetime.now() - timedelta(days=90)).isoformat()}Z"',
        )

        latest_error_entry = next(latest_errors_iterator)
        print("Error - ", latest_error_entry)
        return {
            "status": "success",
            "report": f"Latest Error Log: {str(latest_error_entry)}",
        }

    except StopIteration:
        print("No ERROR log entries found.")
        return {"status": "success", "report": "No ERROR log entries found."}
    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {str(e)}")
        return {"status": "error", "message": f"Failed to get latest error: {e}"}


def get_latest_resource_based_logs(
    project_id: str, severity: str = "", resource: str = "", _limit: int = 10
) -> dict:
    """
    Fetches log entries from Google Cloud Logging filtered by severity and resource type.

    This function retrieves the most recent log entries from Google Cloud Logging,
    allowing filters based on the log's severity level and the type of Google Cloud
    resource that generated the log. It is useful for quickly pinpointing logs
    of interest for specific services or error levels.

    Args:
        project_id (str, required): The Google Cloud project ID from which logs are to be fetched.
        severity (str, optional): Filters logs by their severity level (e.g., "ERROR", "WARNING", "INFO", "DEBUG").
                                This string should directly correspond to a valid Google Cloud Logging severity.
                                If an invalid or empty string is provided, the filter defaults to `severity != ""`,
                                which effectively includes all severity levels. The supported severities are:
                                - 'severity = INFO'
                                - 'severity = DEFAULT'
                                - 'severity = WARNING'
                                - 'severity = NOTICE'
                                - 'severity = DEBUG'
                                - 'severity = ERROR'
                                - Defaults to '' (fetches all logs).
        resource (str, required): Filters logs by the resource type (e.g., "cloud_run_revision",
                                "cloud_dataproc_cluster", "gce_instance"). This string should directly correspond
                                to a valid Google Cloud resource type. The supported resource types include:
                                - 'resource.type=cloud_dataproc_cluster'
                                - 'resource.type=dataflow_step'
                                - 'resource.type=gce_instance'
                                - 'resource.type=audited_resource'
                                - 'resource.type=project'
                                - 'resource.type=gce_firewall_rule'
                                - 'resource.type=gce_instance_group_manager'
                                - 'resource.type=gce_instance_template'
                                - 'resource.type=gce_instance_group'
                                - 'resource.type=gcs_bucket'
                                - 'resource.type=api'
                                - 'resource.type=pubsub_topic'
                                - 'resource.type=datapipelines.googleapis.com/Pipeline'
                                - 'resource.type=gce_subnetwork'
                                - 'resource.type=networking.googleapis.com/Location'
                                - 'resource.type=client_auth_config_brand'
                                - 'resource.type=service_account'
                                Defaults to an empty string.
        _limit (int, optional): The maximum number of log entries to retrieve. The function
                                will fetch up to this many entries, ordered by timestamp in descending order
                                (most recent first). Defaults to 10.

    Returns:
        dict: A dictionary containing the status of the operation and the retrieved logs.
            The dictionary will have the following structure:
            - "status" (str): "success" if logs were fetched successfully, or "error"
            if an error occurred during the API call.
            - "report" (str): A human-readable message. If successful, it includes
            a summary and a list of the fetched log entries. If no logs are found
            matching the criteria, it indicates that.
            - "message" (str, optional): Only present if "status" is "error", providing
            details about the specific error.

    Note: [IMPORTANT]
        - make sure you have required fields before calling this tool.

    """
    client = logging_v2.Client(project=project_id)
    project_path = f"projects/{project_id}"
    call_args = {
        "resource_names": [project_path],
        "order_by": "timestamp desc",
        "page_size": 5,
        "max_results": _limit,
        "filter_": f'timestamp >= "{(datetime.now() - timedelta(days=90)).isoformat()}Z"',
    }

    full_filter = f"{resource}"

    for severity_exist in SEVERITIES_LIST:
        if severity is not None and severity.upper().find(severity_exist) != -1:
            full_filter += f" AND {severity}"
            break

    call_args["filter_"] = full_filter

    collected_logs = []

    try:
        iterator = client.list_entries(**call_args)

        log_count = 0
        for entry in iterator:
            log_count += 1
            print(f"Entry - {log_count} \n", entry)
            collected_logs.append(f"Entry {log_count}: {str(entry)}")
            if log_count >= 10:
                break

        if log_count == 0:
            print("No log entries found matching the criteria.")
            return {
                "status": "success",
                "report": "No log entries found matching the criteria.",
            }
        else:
            print(f"\nSuccessfully fetched {log_count} log entries.")
            return {
                "status": "success",
                "report": "Fetched recent log entries:\n" + "\n".join(collected_logs),
            }

    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to get latest resource based 10 logs: {e}",
        }


def get_latest_10_logs(project_id: str, severity: str = "") -> dict:
    f""" {LATEST_LOGS_PROMT} """

    collected_logs = []
    client = logging_v2.Client(project=project_id)
    project_path = f"projects/{project_id}"

    call_args = {
        "resource_names": [project_path],
        "order_by": "timestamp desc",
        "page_size": 10,
        "filter_": None,
    }

    for severity_exist in SEVERITIES_LIST:
        if severity is not None and severity.upper().find(severity_exist) != -1:
            call_args["filter_"] = severity
            break

    if call_args["filter_"] is not None:
        call_args["filter_"] += (
            f' AND timestamp >= "{(datetime.now() - timedelta(days=90)).isoformat()}Z"'
        )
    else:
        call_args["filter_"] = (
            f'timestamp >= "{(datetime.now() - timedelta(days=90)).isoformat()}Z"'
        )

    print("filter", call_args["filter_"])

    try:
        iterator = client.list_entries(**call_args)

        log_count = 0
        for entry in iterator:
            log_count += 1
            print(f"Entry - {log_count} \n", entry)
            collected_logs.append(f"Entry {log_count}: {str(entry)}")
            if log_count >= 10:
                break

        if log_count == 0:
            print("No log entries found matching the criteria.")
            return {
                "status": "success",
                "report": "No log entries found matching the criteria.",
            }
        else:
            print(f"\nSuccessfully fetched {log_count} log entries.")
            return {
                "status": "success",
                "report": "Fetched recent log entries:\n" + "\n".join(collected_logs),
            }

    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {str(e)}")
        return {"status": "error", "message": f"Failed to get latest 10 logs: {e}"}


def get_logs(
    project_id: str,
    severity: str = "",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    _limit: int = 10,
) -> dict:
    f""" {TIME_RANGE_LOGS_PROMT} """
    client = logging_v2.Client(project=project_id)
    project_path = f"projects/{project_id}"

    call_args = {
        "resource_names": [project_path],
        "order_by": "timestamp desc",
        "page_size": 5,
        "max_results": _limit,
    }

    full_filter_str = ""

    for severity_exist in SEVERITIES_LIST:
        if severity is not None and severity.upper().find(severity_exist) != -1:
            full_filter_str = f"{severity} AND "
            break

    # Initialize default time range if not provided
    if end_time is None:
        end_time = datetime.now()
    if start_time is None:
        start_time = end_time - timedelta(days=90)

    start_time_str = start_time.isoformat()
    end_time_str = end_time.isoformat()

    if start_time:
        full_filter_str += f'timestamp>="{start_time_str}"'

    if end_time:
        if full_filter_str:
            full_filter_str += f' AND timestamp<="{end_time_str}"'
        else:
            full_filter_str += f'timestamp<="{end_time_str}"'

    call_args["filter_"] = full_filter_str

    print("-" * 30)

    collected_logs = []

    try:
        iterator = client.list_entries(**call_args)

        log_count = 0
        for entry in iterator:
            log_count += 1
            print(f"Entry - {log_count} \n", entry)
            collected_logs.append(f"Entry {log_count}: {str(entry)}")

        if log_count == 0:
            print("No log entries found matching the criteria.")
            return {
                "status": "success",
                "report": "No log entries found matching the criteria.",
            }
        else:
            print(f"\nSuccessfully fetched {log_count} log entries.")
            return {
                "status": "success",
                "report": "Fetched filtered log entries:\n" + "\n".join(collected_logs),
            }

    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {str(e)}")
        return {"status": "error", "message": f"Failed to fetch GCP logs: {e}"}
