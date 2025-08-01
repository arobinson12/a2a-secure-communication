# agent.py
import os
import requests
import google.auth
import google.auth.transport.requests
from google.auth import impersonated_credentials
from google.adk.agents import Agent

# ==============================================================================
# --- CONFIGURATION: UPDATE THESE VALUES FOR YOUR ENVIRONMENT ---
# ==============================================================================

# The full public DNS name of your IAP-protected External HTTPS Load Balancer.
LOAD_BALANCER_URL = "https://your-load-balancer-dns.your-domain.com"

# The dedicated service account that this agent will impersonate to make its call.
TARGET_SERVICE_ACCOUNT = "your-caller-sa@your-gcp-project.iam.gserviceaccount.com"

# The OAuth 2.0 Client ID for the IAP instance protecting your load balancer.
IAP_CLIENT_ID = "YOUR_IAP_OAUTH_CLIENT_ID.apps.googleusercontent.com"

# ==============================================================================
# --- AGENT LOGIC ---
# ==============================================================================

def get_a_better_joke(original_joke: str) -> str:
    """
    Performs a step-by-step trace of the IAP impersonation and HTTPS call,
    returning a formatted markdown log of its success or failure at each stage.
    """
    debug_log = ["### IAP Authentication Debug Log\n"]

    try:
        # STEP A: Get the credentials of the agent's own runtime environment.
        source_credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        debug_log.append("✅ **Step A: Get Source Credentials** - PASSED. Found the agent's own identity.")

        # STEP B: Prepare to impersonate the target service account.
        target_creds_base = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=TARGET_SERVICE_ACCOUNT,
            delegates=[],
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            lifetime=300
        )
        debug_log.append(f"✅ **Step B: Create Impersonated Credentials** - PASSED. Prepared to act as `{TARGET_SERVICE_ACCOUNT}`.")

        # STEP C: Configure the request for an IAP-compatible ID Token.
        id_token_creds = impersonated_credentials.IDTokenCredentials(
            target_credentials=target_creds_base,
            target_audience=IAP_CLIENT_ID,
            include_email=True
        )
        debug_log.append("✅ **Step C: Prepare ID Token** - PASSED. Configured request for the correct IAP audience.")
        
        # STEP D: Perform the impersonation and fetch the secure ID token.
        request = google.auth.transport.requests.Request()
        id_token_creds.refresh(request)
        token = id_token_creds.token
        debug_log.append("✅ **Step D: Fetch ID Token** - PASSED. Successfully impersonated and received a secure token from Google.")
        
        # STEP E: Prepare the authorization headers for the final call.
        auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        debug_log.append("✅ **Step E: Prepare Headers** - PASSED. Attached the secure token to the request.")

        # STEP F: Make the secure HTTPS request to the load balancer.
        response = requests.post(
            f"{LOAD_BALANCER_URL}/ask",
            json={"original_joke": original_joke},
            headers=auth_headers,
            timeout=60
        )
        response.raise_for_status()
        debug_log.append(f"✅ **Step F: Make HTTPS Request** - PASSED. Successfully connected to the Load Balancer.")

        # FINAL STEP: Parse the response from the comedian agent.
        joke = response.json().get("answer", "No answer field in response.")
        debug_log.append("\n---\n**SUCCESS! The full flow worked.**")
        debug_log.append(f"\n**The Professional Comedian's Joke:** {joke}")

    except Exception as e:
        # If any step fails, append a formatted error block to the log.
        debug_log.append(f"\n---\n❌ **A FAILURE OCCURRED.**")
        debug_log.append(f"\n**The full error is:**\n```\n{e}\n```")

    # Return the entire log as a single, formatted markdown string.
    return "\n".join(debug_log)


# This is the agent that will be deployed by Agent Engine.
root_agent = Agent(
    name="IAPClassicJokeAgentDebugger",
    model="gemini-2.0-flash",
    instruction=(
        "You are a debug assistant. A user will ask for a joke. You must first tell the user this joke: 'Why don't scientists trust atoms? Because they make up everything!' "
        "Then, you MUST immediately call the 'get_a_better_joke' tool. "
        "The tool will return an important, multi-line debug log formatted in markdown. "
        "Your final response to the user MUST be ONLY the full, exact, unmodified debug log from the tool and nothing else."
    ),
    tools=[get_a_better_joke],
)