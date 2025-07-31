# main.py
import os
import uuid
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================

# You can change the model name to any compatible model available in Vertex AI.
# The necessary API keys for the google_search tool will be provided via
# environment variables during deployment.
MODEL_NAME = "gemini-2.0-flash"


# ==============================================================================
# --- AGENT LOGIC ---
# ==============================================================================

# Define the agent that will be served.
root_agent = Agent(
    name="ProfessionalComedianAgent",
    model=MODEL_NAME,
    description="An agent that creates topical jokes using Google Search.",
    instruction=(
        "You are a sharp and witty professional comedian. You will be given a cheesy joke. "
        "Your task is to FIRST use the google_search tool to find a very recent pop culture event, news story, or popular meme. "
        "Then, create a new, much funnier joke that references both the topic of the original joke AND the pop culture item you found. "
        "You MUST use the search tool to get up-to-the-minute information."
    ),
    tools=[google_search],
)

# Initialize the ADK Runner to execute the agent.
runner = Runner(
    agent=root_agent,
    app_name=root_agent.name,
    session_service=InMemorySessionService()
)

# Create the FastAPI web application.
app = FastAPI()

# Define the data model for incoming requests.
class JokeRequest(BaseModel):
    original_joke: str

# Define the API endpoint that will process requests.
@app.post("/ask")
async def ask(request: JokeRequest):
    """
    Receives a joke, uses the agent to process it with a tool,
    and returns a new, better joke.
    """
    try:
        prompt = f"Here's a joke to roast: '{request.original_joke}'"
        content = types.Content(role='user', parts=[types.Part.from_text(text=prompt)])
        response_text = ""
        user_id = "a2a-user"
        session_id = str(uuid.uuid4())

        # Create a session for the agent to use.
        await runner.session_service.create_session(
            app_name=root_agent.name,
            user_id=user_id,
            session_id=session_id,
            state={}
        )

        # Execute the agent's logic.
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text

        if not response_text:
             raise Exception("Agent did not produce a final text response.")

        return {"answer": response_text.strip()}

    except Exception as e:
        # Log the error and return a standard 500 response.
        logging.error(f"Agent execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Agent Error: {str(e)}")

# Define a root endpoint for simple health checks.
@app.get("/")
def root():
    return {"message": "Professional Comedian Agent is running."}