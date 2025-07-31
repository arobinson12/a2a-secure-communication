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

# The full public URL of your IAP-protected External HTTPS Load Balancer.
# This should point to the DNS name you have configured.
LOAD_BALANCER_URL = "https://comedian.your-domain.com"

# The dedicated service account that this agent will impersonate to make its call.
# This service account needs the 'IAP-secured Web App User' and 'Cloud Run Invoker' roles.
TARGET_SERVICE_ACCOUNT = "your-caller-sa@your-gcp-project.iam.gserviceaccount.com"

# The OAuth 2.0 Client ID for the IAP instance protecting your load balancer.
# Find this in the GCP Console under Security > Identity-Aware Proxy.
IAP_CLIENT_ID = "YOUR_IAP_OAUTH_CLIENT_ID.apps.googleusercontent.com"

# ==============================================================================
# --- AGENT LOGIC ---
# ==============================================================================

def get_a_better_joke(original_joke: str) -> str:
    """
    Securely generates an IAP-compatible ID token by impersonating a service account
    and uses it to call the professional comedian agent via an HTTPS Load Balancer.
    """
    try:
        # 1. Get the credentials of the environment this agent is running in.
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

        # 3. Wrap the base credential to create a specific ID Token credential,
        #    using the IAP Client ID as the intended audience.
        id_token_creds = impersonated_credentials.IDTokenCredentials(
            target_credentials=target_creds_base,
            target_audience=IAP_CLIENT_ID,
            include_email=True
        )

        # 4. Use the final credential object to fetch the actual ID token.
        request = google.auth.transport.requests.Request()
        id_token_creds.refresh(request)
        token = id_token_creds.token
        
        # 5. Prepare the headers for the authenticated call.
        auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # 6. Make the secure, authenticated call to the load balancer.
        response = requests.post(
            f"{LOAD_BALANCER_URL}/ask",
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
    name="IAPClassicJokeAgent",
    model="gemini-2.0-flash",
    instruction=(
        "You are the Classic Joke Agent. First, tell a simple, classic joke. "
        "Then, use the 'get_a_better_joke' tool to get a funnier one from a professional comedian. "
        "If the tool returns an error, apologize and say the professional comedian is busy."
    ),
    tools=[get_a_better_joke],
)