# main.py
import os
import requests
import google.auth
import google.auth.transport.requests
from google.auth import impersonated_credentials
from google.adk.agents import Agent

# ==============================================================================
# --- CONFIGURATION: UPDATE THESE VALUES FOR YOUR ENVIRONMENT ---
# ==============================================================================

# The full, official URL of your private Cloud Run service.
# Find this on the Cloud Run service details page.
PRIVATE_CLOUD_RUN_URL = "https://your-private-agent-....run.app"

# The dedicated service account that this agent will impersonate to make its call.
# This service account needs the 'Cloud Run Invoker' role on the service above.
TARGET_SERVICE_ACCOUNT = "your-caller-sa@your-gcp-project.iam.gserviceaccount.com"

# ==============================================================================
# --- AGENT LOGIC ---
# ==============================================================================

def get_a_better_joke(original_joke: str) -> str:
    """
    Securely generates an ID token by impersonating a service account and uses it
    to make an authenticated call directly to a private Cloud Run service.
    """
    try:
        # 1. Get the credentials of the environment this agent is running in.
        #    This requires the 'roles/browser' permission for the runtime SA.
        source_credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

        # 2. Create the base impersonated credential object. This requires the
        #    'Service Account Token Creator' IAM permission.
        target_creds_base = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=TARGET_SERVICE_ACCOUNT,
            delegates=[],
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            lifetime=300
        )

        # 3. Wrap the base credential to create a specific ID Token credential.
        #    CRITICAL: For direct Cloud Run IAM, the audience MUST be the URL of the service.
        id_token_creds = impersonated_credentials.IDTokenCredentials(
            target_credentials=target_creds_base,
            target_audience=PRIVATE_CLOUD_RUN_URL, # Use the Cloud Run URL as the audience
            include_email=True
        )

        # 4. Use the final credential object to fetch the actual ID token.
        request = google.auth.transport.requests.Request()
        id_token_creds.refresh(request)
        token = id_token_creds.token
        
        # 5. Prepare the headers for the authenticated call.
        auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # 6. Make the secure, authenticated call directly to the Cloud Run URL.
        response = requests.post(
            f"{PRIVATE_CLOUD_RUN_URL}/ask",
            json={"original_joke": original_joke},
            headers=auth_headers,
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("answer", "The professional comedian was speechless.")

    except Exception as e:
        # If any part of the process fails, return the error for debugging.
        return f"An unexpected error occurred while calling the professional comedian: {e}"

# This is the agent that will be deployed by Agent Engine.
root_agent = Agent(
    name="IAMClassicJokeAgent",
    model="gemini-2.0-flash",
    instruction=(
        "You are the Classic Joke Agent. First, tell a simple, classic joke. "
        "Then, use the 'get_a_better_joke' tool to get a funnier one from a professional comedian. "
        "If the tool returns an error, apologize and say the professional comedian is busy."
    ),
    tools=[get_a_better_joke],
)