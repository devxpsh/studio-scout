from dotenv import load_dotenv
load_dotenv()

import asyncio
from google.genai import types
from google.adk.runners import InMemoryRunner
from app.agent import root_agent

async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="studio_scout_app")

    session = await runner.session_service.create_session(
        app_name="studio_scout_app",
        user_id="test_user",
    )

    message = types.Content(role="user", parts=[types.Part(text="find three filming locations in hyderabad suitable for a police-station scene. provide the source for each.")])

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)

if __name__ == "__main__":
    asyncio.run(main())