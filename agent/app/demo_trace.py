from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
from google.genai import types
from google.adk.runners import InMemoryRunner
from app.agent import root_agent


async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="studio_scout_app")

    session = await runner.session_service.create_session(
        app_name="studio_scout_app",
        user_id="test_user",
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text="find filming locations in hyderabad")],
    )

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=message,
    ):
        calls = event.get_function_calls()
        responses = event.get_function_responses()

        if calls:
            for call in calls:
                print("=" * 60)
                print("TOOL CALL — Gemini invoked a tool at runtime")
                print("=" * 60)
                print(f"  tool name : {call.name}")
                print(f"  args      : {call.args}")
                print()

        if responses:
            for resp in responses:
                print("=" * 60)
                print("TOOL RESPONSE — actual data returned to Gemini")
                print("=" * 60)
                print(f"  tool name : {resp.name}")
                print(f"  response  :")
                print(json.dumps(resp.response, indent=2, default=str)[:2000])
                print()

        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print("=" * 60)
                    print("FINAL SYNTHESIZED ANSWER")
                    print("=" * 60)
                    print(part.text)


if __name__ == "__main__":
    asyncio.run(main())