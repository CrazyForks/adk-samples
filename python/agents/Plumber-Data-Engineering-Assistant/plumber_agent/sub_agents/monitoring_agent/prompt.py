SEVERITIES = """
                    - 'severity = INFO'
                    - 'severity = DEFAULT'
                    - 'severity = WARNING'
                    - 'severity = NOTICE'
                    - 'severity = DEBUG'
                    - 'severity = ERROR'
                    - Defaults to '' (fetches all logs).
                """

SEVERITIES_LIST = ["INFO", "DEFAULT", "WARNING", "DEBUG", "ERROR", "NOTICE"]

SEVERITY_PROMT = f"""

                Filters logs by their severity level (e.g., "ERROR", "WARNING", "INFO", "DEBUG").
                This string should directly correspond to a valid Google Cloud Logging severity.
                If an invalid or empty string is provided, the filter defaults to `severity != ""`,
                which effectively includes all severity levels. The supported severities are
                expected to be defined in a global or accessible variable named `{SEVERITIES}`.

                """


RESOURCE_TYPES = """
                    - 'resource.type=cloud_dataproc_cluster',
                    - 'resource.type=dataflow_step',
                    - 'resource.type=gce_instance',
                    - 'resource.type=audited_resource',
                    - 'resource.type=project',
                    - 'resource.type=gce_firewall_rule',
                    - 'resource.type=gce_instance_group_manager',
                    - 'resource.type=gce_instance_template',
                    - 'resource.type=gce_instance_group',
                    - 'resource.type=gcs_bucket',
                    - 'resource.type=api',
                    - 'resource.type=pubsub_topic',
                    - 'resource.type=datapipelines.googleapis.com/Pipeline',
                    - 'resource.type=gce_subnetwork',
                    - 'resource.type=networking.googleapis.com/Location',
                    - 'resource.type=client_auth_config_brand',
                    - 'resource.type=service_account'

                """

DATAPROC_LOGS_WITH_CLUSTERS_NAME_PROMT = """

                *** Fetches Google Cloud Logging log entries specifically for Dataproc clusters. ***

                This function retrieves log entries from Google Cloud Logging for a specified
                Dataproc cluster with it's name, with an option to limit the number of results.
                It is designed to provide an overview of recent cluster activities and potential issues.

                Args:
                    project_id (str, required): The Google Cloud project ID. from which logs are to be fetched.
                    dataproc_cluster_name (str, required): The name of the Dataproc cluster
                        to filter logs for. If not provided don't call this tool.
                    _limit (int, optional): The maximum number of log entries to retrieve.
                        The function will fetch up to this many entries, Defaults to 10.

                Returns:
                    dict: A dictionary containing the status of the operation and the retrieved logs.
                        The dictionary will have the following structure:
                            - "status" (str): "success" if logs were fetched successfully, or "error"
                                if an error occurred.
                            - "report" (str): A human-readable message detailing the outcome.
                                If successful, it includes a summary and a list of the fetched log entries.
                                If no logs are found, it indicates that.
                            - "message" (str, optional): Only present if "status" is "error", providing
                                details about the error that occurred.

                Note: [IMPORTANT]
                    - Call this tool only when user want's logs of a cluster with the name

                """


DATAPROC_LOGS_WITH_CLUSTERS_ID_PROMT = """

                Fetches Google Cloud Logging log entries for a specific Dataproc cluster using its UUID or ID.

                This function retrieves log entries from Google Cloud Logging that are associated
                with a particular Dataproc cluster, identified by its unique ID (UUID). It allows
                for limiting the number of log entries returned, ordered by the most recent first.

                Args:
                    project_id (str, required): The Google Cloud project ID. from which logs are to be fetched.
                    cluster_id (str, required): The **UUID** of the Dataproc cluster to filter logs for.
                        This uniquely identifies a Dataproc cluster across its lifecycle. If not
                        provided don't call this tool.
                        - format of UUID : 0278aa3c-085a-4ccc-b79d-78b82fbb2ba3
                    _limit (int, optional): The maximum number of log entries to fetch. The function
                        will retrieve up to this many entries, Defaults to 10.

                Returns:
                    dict: A dictionary containing the status of the operation and the retrieved logs.
                        The dictionary will have the following keys:
                        - "status" (str): "success" if the logs were fetched successfully, or "error"
                        if an issue occurred.
                        - "report" (str): A descriptive message about the outcome. If successful,
                        it includes a summary and a list of the fetched log entries. If no
                        matching logs are found, it indicates that.
                        - "message" (str, optional): Present only if "status" is "error", providing
                        details about the specific error.

                Note: [IMPORTANT]
                        - Call this tool only when user want's logs of a cluster with it's UUID or ID

                """

DATAPROC_LOGS_WITH_JOB_ID_PROMT = """

                Fetches log entries for a specific Dataproc job using its ID from Google Cloud Logging.

                This function retrieves log entries from Google Cloud Logging that are associated
                with a particular Google Cloud Dataproc job, identified by its unique `job_id`.
                It aims to provide insights into the job's execution, status, and any potential issues.
                By default, it fetches up to 10 of the most recent log entries.

                Args:
                    project_id (str, required): The Google Cloud project ID. from which logs are to be fetched.
                    job_id (str, required): The unique identifier of the Dataproc job for which logs are to be fetched.
                        This argument is required to filter the logs specifically for a given job.
                    _limit (int, optional): The maximum number of log entries to fetch. The function
                        will retrieve up to this many entries, Defaults to 10.

                Returns:
                    dict: A dictionary containing the status of the operation and the retrieved logs.
                        The dictionary will have the following structure:
                        - "status" (str): "success" if logs were fetched successfully, or "error"
                        if an error occurred.
                        - "report" (str): A human-readable message detailing the outcome.
                        If successful, it includes a summary and a list of the fetched log entries.
                        If no logs are found for the given job ID, it indicates that.
                        - "message" (str, optional): Only present if "status" is "error", providing
                        details about the error that occurred.

                Note: [IMPORTANT]
                    - Don't call this tool till u have job_id
                        - example job_id : pyspark_job-xvqzft55adfra, dd9121f1-7925-4f18-b49a-0edc5d9b004f

                """

CPU_UTILIZATION_PROMT = """

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

DATAFLOW_LOGS_WITH_JOB_ID_PROMT = """

                Fetches log entries for a specific Dataflow job using its ID from Google Cloud Logging.

                This function retrieves log entries from Google Cloud Logging that are associated
                with a particular Google Cloud Dataflow job, identified by its unique `job_id`.
                It aims to provide insights into the job's execution, status, and any potential issues.
                By default, it fetches up to 10 of the most recent log entries.

                Args:
                    project_id (str, required): The Google Cloud project ID. from which logs are to be fetched.
                    job_id (str, required): The unique identifier of the Dataflow job for which logs are to be fetched.
                        This argument is required to filter the logs specifically for a given job.
                    _limit (int, optional): The maximum number of log entries to fetch. The function
                        will retrieve up to this many entries, Defaults to 10.

                Returns:
                    dict: A dictionary containing the status of the operation and the retrieved logs.
                        The dictionary will have the following structure:
                        - "status" (str): "success" if logs were fetched successfully, or "error"
                        if an error occurred.
                        - "report" (str): A human-readable message detailing the outcome.
                        If successful, it includes a summary and a list of the fetched log entries.
                        If no logs are found for the given job ID, it indicates that.
                        - "message" (str, optional): Only present if "status" is "error", providing
                        details about the error that occurred.

                Note: [IMPORTANT]
                    - Don't call this tool till u have job_id
                        - example job_id : 2025-07-11_02_51_43-12657112666808971216

                """

LATEST_ERROR_PROMT = """

                Fetches the most recent error log entry from Google Cloud Logging for the specified project.

                This function queries Google Cloud Logging to retrieve the single most recent
                log entry that has a severity level of 'ERROR'. It provides a quick way to
                identify and review the latest error reported across all resources in the
                configured Google Cloud project.

                Args:
                    project_id (str, required): The Google Cloud project ID. from which logs are to be fetched.

                Returns:
                    dict: A dictionary containing the status of the operation and the retrieved
                        error log. The dictionary will have the following structure:
                        - "status" (str): "success" if an error log was found or if no errors
                            were found, or "error" if an API call issue occurred.
                        - "report" (str): A human-readable message. If successful, it includes
                            the latest error log entry as a string. If no error logs are found,
                            it indicates that.
                        - "message" (str, optional): Only present if "status" is "error",
                            providing details about the specific error encountered during the API call.

                Note: [IMPORTANT]
                    - Call this tool when user specifically ask's only for one | single | latest without any resource specific logs

                """

LATEST_RESOURCE_BASED_LOGS_PROMT = f"""

                Fetches log entries from Google Cloud Logging filtered by severity and resource type.

                This function retrieves the most recent log entries from Google Cloud Logging,
                allowing filters based on the log's severity level and the type of Google Cloud
                resource that generated the log. It is useful for quickly pinpointing logs
                of interest for specific services or error levels.

                Args:
                    project_id (str, required): The Google Cloud project ID. from which logs are to be fetched.
                    severity (str, optional): {SEVERITY_PROMT}
                    resource (str, required): Filters logs by the resource type (e.g., "cloud_run_revision",
                        "cloud_dataproc_cluster", "gce_instance"). This string should directly correspond
                        to a valid Google Cloud resource type. The supported resource types are
                        expected to be defined in a global or accessible variable named `{RESOURCE_TYPES}`.
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

                Note: [IMPORTANT]
                    - make sure you have required fields before calling this tool.

                """

LATEST_LOGS_PROMT = f"""

                Fetches the 10 most recent log entries from Google Cloud Logging for the specified project.

                This function retrieves the most recent log entries from Google Cloud Logging
                for the configured project. It allows for an optional filter based on the
                log's severity level. By default, it fetches up to 10 logs.

                Args:
                    project_id (str, required): The Google Cloud project ID. from which logs are to be fetched.
                    severity (str, optional): {SEVERITY_PROMT}

                Returns:
                    dict: A dictionary containing the status of the operation and the retrieved logs.
                        The dictionary will have the following structure:
                        - "status" (str): "success" if logs were fetched successfully, or "error"
                        if an error occurred during the API call.
                        - "report" (str): A human-readable message. If successful, it includes
                        a summary and a list of the fetched log entries. If no logs are found
                        matching the criteria, it indicates that.
                        - "message" (str, optional): Only present if "status" is "error", providing
                        details about the specific error encountered.

                Note: [IMPORTANT]
                    - Invoke only when user is requesting about latest logs, without any resource specifict information is provided.

                """

TIME_RANGE_LOGS_PROMT = f"""

                Fetches log entries from Google Cloud Logging for a given project, with flexible filtering.

                This function retrieves log entries from Google Cloud Logging for the configured project,
                allowing filtering by severity level and a specific time range. It's a general-purpose
                log fetching utility that can be tailored to various logging needs.

                Args:
                    project_id (str, required): The Google Cloud project ID. from which logs are to be fetched.
                    severity (str, optional): {SEVERITY_PROMT}
                    start_time (str, required): The beginning of the time range for logs.
                        Expected in a format parseable by `datetime.datetime.fromisoformat()`, e.g.,
                        "YYYY-MM-DDTHH:MM:SSZ". If an empty string or `None`, no start time
                        constraint is applied. Defaults to an empty string.
                    end_time (str, required): The end of the time range for logs.
                        Expected in a format parseable by `datetime.datetime.fromisoformat()`, e.g.,
                        "YYYY-MM-DDTHH:MM:SSZ". If an empty string or `None`, defaults to the current time.
                        Defaults to an empty string.
                    _limit (int, optional): The maximum number of log entries to return.
                        The function will fetch up to this many entries, ordered by timestamp
                        in descending order (most recent first). Defaults to 10.

                Returns:
                    dict: A dictionary containing the status of the operation and the retrieved logs.
                        The dictionary will have the following structure:
                        - "status" (str): "success" if logs were fetched successfully, or "error"
                        if an error occurred during the API call.
                        - "report" (str): A human-readable message. If successful, it includes
                        a summary and a list of the fetched log entries. If no logs are found
                        matching the criteria, it indicates that.
                        - "message" (str, optional): Only present if "status" is "error", providing
                        details about the specific error encountered.

                Note: [IMPORTANT]
                    - Invoke this tool when user is provided with required information
                    - if start_time and end_time is not in expected format try to convert to "YYYY-MM-DDTHH:MM:SSZ" format.

                """

AGENT_DESCRIPTION = """
        "This agent monitors Google Cloud Platform (GCP) resources. It can fetch CPU utilization "
        "metrics for VM instances and retrieve various types of log entries from Cloud Logging. "
        "This includes recent logs, the latest error log, resource-specific logs (e.g., Dataproc, Dataflow jobs), "
        "and logs filtered by severity or time range. It can also return HTML content."
"""

AGENT_INSTRUCTIONS = f"""
        You are an intelligent Google Cloud monitoring and logging assistant. Your core task is to help users "
        "query GCP metrics and logs efficiently. Follow these guidelines to determine which tool to use "
        "and how to interact with the user:\n"
        "### Tool Usage Directives:\n"
        "* **For CPU utilization queries:** Use the `get_cpu_utilization` tool."
        "* **For latest resource based queries:** Use the `get_latest_resource_based_logs` tool."
                f" - If user provided any of this values => {RESOURCE_TYPES}"
        "* **For the most recent | latest log entries:** Use the `get_latest_10_logs` tool."
                f" - If user provided any of this values => {SEVERITIES}"
        "* **For the single latest error log entry:** Use the `get_latest_error` tool."
                " - when user asks for error not errors"
        "* **For cluster name queries:** Use the `get_dataproc_cluster_logs_with_name` tool."
                " - if user not provided cluster name asking for dataproc logs route request to `get_latest_resource_based_logs`"
        "* **For dataproc job id queries:** Use the `get_dataproc_job_logs_with_id` tool."
                f" - If user is provided this type of values ex: 'pyspark_job-xvqzft55adfra, dd9121f1-7925-4f18-b49a-0edc5d9b004f'"
        "* **For dataflow job id queries:** Use the `get_dataflow_job_logs_with_id` tool."
                f" - If user is provided this type of values ex: '2025-07-09_12_35_31-8291205053243125328'"
        "Before calling any tool ask for the required arguments if not provided already "

        "### Interaction Protocol:\n"
        "- **Check for matching tool first found any call it. else ask for minimal required information.**"
        "- **Before calling any tool**, always check if all **required arguments** are explicitly provided by the user. "
        "If a required argument is missing, **ask the user clearly and concisely for that specific piece of information** (e.g., 'Please provide the Dataflow job ID.'). Do not proceed with the tool call until all required arguments are met.\n"
        "- **Display results**: Present tool outputs in an easy-to-read format. Prefer **bullet points** or **key-value pairs** for structured data. If no data is found, clearly state that.\n"
        "- **Error Handling**: If a tool reports an error, convey the error message to the user along with any provided troubleshooting steps.\n"
        "- **Time Formatting**: When asking for `start_time` or `end_time`, specify the expected ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ'). If the user provides a different format, politely ask them to rephrase it or attempt a conversion if feasible and unambiguous.\n"
        "- **Clarity**: Maintain clear, straightforward language throughout the conversation."""
