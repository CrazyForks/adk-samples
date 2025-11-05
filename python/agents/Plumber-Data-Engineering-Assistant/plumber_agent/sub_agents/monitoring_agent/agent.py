from google.adk.agents import Agent

from .constants import MODEL
from .prompt import AGENT_DESCRIPTION, AGENT_INSTRUCTIONS
from .tools.dataflow import get_dataflow_job_logs_with_id
from .tools.dataproc import (
    get_dataproc_cluster_logs_with_name,
    get_dataproc_job_logs_with_id,
)
from .tools.utils import (
    get_cpu_utilization,
    get_latest_10_logs,
    get_latest_error,
    get_latest_resource_based_logs,
)

root_agent = Agent(
    name="monitoring_agent",
    model=MODEL,
    description=(f"{AGENT_DESCRIPTION}"),
    instruction=(f"{AGENT_INSTRUCTIONS}"),
    tools=[
        get_cpu_utilization,
        get_latest_10_logs,
        get_latest_error,
        get_latest_resource_based_logs,
        get_dataflow_job_logs_with_id,
        get_dataproc_job_logs_with_id,
        get_dataproc_cluster_logs_with_name,
    ],
)
