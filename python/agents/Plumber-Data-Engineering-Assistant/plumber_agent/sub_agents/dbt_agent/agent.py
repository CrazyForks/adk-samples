import warnings

from google.adk.agents import Agent

# UTILITY IMPORTS
from .constants import MODEL
from .prompts import AGENT_INSTRUCTIONS
from .tools.dbt_model_sql_generator import (
    generate_dbt_model_sql,
)

# TOOL IMPORTS
from .tools.dbt_project_deployment import deploy_dbt_project
from .tools.dbt_project_runner import run_dbt_project

warnings.filterwarnings("ignore")

root_agent = Agent(
    name="dbt_agent",
    model=MODEL,
    description=(
        "Agent to convert source to target mapping image/csv file to corresponding dbt sql model"
    ),
    instruction=(AGENT_INSTRUCTIONS),
    tools=[generate_dbt_model_sql, deploy_dbt_project, run_dbt_project],
)
