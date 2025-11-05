##  Google Cloud Log and Monitoring Retrieval Tools

This section details the available utility functions for retrieving logs and monitoring data across various Google Cloud services within the project.

---

### **1. Data Processing Service Log Retrieval**

These tools are specialized for fetching logs from specific data processing services like Dataflow and Dataproc.

**get_dataflow_job_logs_with_id**
    * **Purpose**: Retrieves log entries for a **specific Dataflow job** using its **ID**. Useful for debugging and monitoring job execution.
    * **Details**: Fetches logs from the last **90 days** and returns up to a specified limit.

**get_dataproc_cluster_logs_with_name**
    * **Purpose**: Fetches log entries for a **Dataproc cluster** based on its **name**. Ideal for monitoring cluster health and activity when the name is known.
    * **Details**: Retrieves logs from the last **90 days**, ordered by timestamp in **descending order**.

**get_dataproc_job_logs_with_id**
    * **Purpose**: Retrieves log entries for a **specific Dataproc job** using its **unique job ID**. Essential for detailed job-level logging.
    * **Details**: Fetches logs from the last **90 days**, ordered by timestamp in **descending order**.

---

### **2. General Log and Monitoring Functions**

These tools provide general-purpose insights into system health and recent activities.

**get_cpu_utilization**
    * **Purpose**: Gathers **CPU utilization data** for instances within the project. Quickly assesses current CPU performance.
    * **Details**: Queries for data from the last **5 minutes** and groups it by **instance ID** and **zone**.

**get_latest_error**
    * **Purpose**: Finds and returns the **most recent log entry** with a severity of **ERROR**. Used for quickly identifying and addressing the most recent critical issues.
    * **Details**: Scans all project logs.

**get_latest_resource_based_logs**
    * **Purpose**: Fetches the **latest log entries** filtered by a specified **resource** and **optional severity**. Enables targeted log analysis.
    * **Details**: Returns up to **10 log entries**, ordered by timestamp in **descending order**.

**get_latest_10_logs**
    * **Purpose**: Retrieves the **10 most recent log entries** across the project. Provides a quick overview of recent system activities.
    * **Details**: Optionally, can filter these logs by a specified **severity level**.
