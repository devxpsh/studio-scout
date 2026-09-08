from __future__ import annotations

import os
from pathlib import Path

import vertexai
from vertexai import agent_engines
from vertexai.agent_engines import AdkApp

from app.agent import root_agent


REPO_ROOT = Path(__file__).resolve().parent


def main() -> None:
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    staging_bucket = os.environ["GOOGLE_CLOUD_STAGING_BUCKET"]

    vertexai.init(project=project, location=location, staging_bucket=staging_bucket)
    remote_agent = agent_engines.create(
        agent_engine=AdkApp(agent=root_agent),
        requirements=str(REPO_ROOT / "requirements.txt"),
        extra_packages=[str(REPO_ROOT / "app")],
        display_name="studio-scout",
        description="Screenplay location scouting agent",
        env_vars={
            "GOOGLE_CLOUD_PROJECT": project,
            "GOOGLE_CLOUD_LOCATION": location,
            "GOOGLE_GENAI_USE_VERTEXAI": "True",
            "PARALLEL_API_KEY": os.environ["PARALLEL_API_KEY"],
        },
    )
    print(remote_agent.api_resource.name)


if __name__ == "__main__":
    main()
