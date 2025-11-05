# # Import root_agents from each subagent
from .sub_agents.dataflow_agent.agent import root_agent as dataflow_agent
from .sub_agents.dataproc_agent.agent import root_agent as dataproc_agent
from .sub_agents.dataproc_template_agent.agent import root_agent as dataproc_template_agent
from .sub_agents.dbt_agent.agent import root_agent as dbt_agent
from .sub_agents.github_agent.agent import root_agent as github_agent
from .sub_agents.monitoring_agent.agent import root_agent as monitoring_agent

from google.adk.agents import Agent
from .prompts import AGENT_INSTRUCTIONS
from .constants import MODEL

root_agent = Agent(
    name="core",
    model=MODEL,
    description=(
        "A master orchestrator that intelligently routes user requests to specialized sub-agents. "
        "It delegates tasks across key domains: data processing (Dataflow, Dataproc clusters & templates), "
        "data transformation (dbt), code & file management (GitHub, GCS), and cloud observability (Monitoring logs & metrics)."
  
    ),
    instruction=(
        AGENT_INSTRUCTIONS 
    ),

    sub_agents=[
        dataflow_agent,
        dataproc_agent,
        dataproc_template_agent,
        dbt_agent,
        github_agent,
        monitoring_agent
    ]
)

