from google.adk.agents import Agent 
from google.adk.runners import Runner
from google.genai import types
from google.adk.memory import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
import uuid
import asyncio
from dotenv import load_dotenv 
from .prompt import prompt
 
USER_ID="sherlockED"
load_dotenv()
        
questions_generator_agent = Agent(
    name="questions_generator_agent",
    description="Agent that generates new perseus format questions",
    model="gemini-2.0-flash",
    instruction=prompt,
    output_key="question_json"
)

runner = Runner(
    app_name="QuestionsGenerator",
    agent=questions_generator_agent,
    session_service=InMemorySessionService(),
    artifact_service=InMemoryArtifactService(),
    memory_service=InMemoryMemoryService()
)

session_service = runner.session_service

async def create_session():
    session = await session_service.create_session(
        app_name="QuestionsGenerator",
        user_id=USER_ID
    )
    return session.id

SESSION_ID = asyncio.run(create_session())


async def execute(data: str) -> str:
    msg = f"Generate new question from: {data}"
    async for ev in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=msg)]
        )
    ):
        if ev.is_final_response() and ev.content and ev.content.parts:
            return ev.content.parts[0].text