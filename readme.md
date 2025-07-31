Secure A2A Communication Patterns: Agent Engine to Cloud Run
============================================================

This repository provides a complete, deployable project to demonstrate two distinct, secure patterns for agent-to-agent (A2A) communication between an agent hosted on **Agent Engine** and a private backend agent on **Cloud Run**.

The goal is to test and evaluate two production-grade authentication methods:

1.  **Direct IAM:** The frontend agent calls a private Cloud Run service directly, authenticating using a standard IAM-validated ID token.
    
2.  **IAP-Protected Load Balancer:** The frontend agent calls a private Cloud Run service via an External HTTPS Load Balancer, which is protected by Identity-Aware Proxy (IAP).
    

Project Structure
-----------------

This repository is organized into the three main components of the architecture:

Generated code

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   .  ├── agent_engine_agents  │   ├── iam_classic_joke_agent  # Frontend agent for direct IAM authentication  │   │   ├── agent.py  │   │   └── pyproject.toml  │   └── iap_classic_joke_agent  # Frontend agent for IAP authentication  │       ├── agent.py  │       └── pyproject.toml  ├── cloud_run_agent             # Backend agent that runs on Cloud Run  │   ├── Dockerfile  │   ├── main.py  │   └── requirements.txt  └── readme.md   `

Use code [with caution](https://support.google.com/legal/answer/13505487).

Prerequisites
-------------

Before you begin, ensure you have the following:

1.  **Google Cloud Project:** A GCP project with billing enabled.
    
2.  **gcloud CLI:** The Google Cloud CLI installed and authenticated.
    
3.  **ADK CLI:** The Agent Development Kit CLI installed (pip install "google-cloud-aiplatform\[adk,agent\_engines\]").
    
4.  **Permissions:** You need permissions to create Service Accounts, set IAM policies, and deploy to Cloud Run and Agent Engine (e.g., Owner or Editor role).
    
5.  **Agent Registration Tool:** Clone the Agent Registration Tool from https://github.com/VeerMuchandi/agent\_registration\_tool to a convenient location.
    
6.  **Staging Bucket:** A Cloud Storage bucket for Agent Engine deployments (e.g., gs://my-agent-staging-bucket).
    

Deployment Steps
----------------

The deployment must be done in a specific order: the backend service must exist before the frontend agent that calls it can be deployed.

### Part 1: Deploy the Backend (Professional Comedian Agent)

This agent is a private Cloud Run service that uses the Google Search tool.

#### 1.1: Prepare Google Search Credentials

1.  **Create a Programmable Search Engine:**
    
    *   Go to the Programmable Search Engine control panel.
        
    *   Create a new search engine configured to **Search the entire web**.
        
    *   Copy the **Search engine ID**.
        
2.  **Enable the Custom Search API & Get an API Key:**
    
    *   In the GCP Console, **Enable** the **Custom Search API**.
        
    *   Go to the **Credentials** page and create a new **API key**.
        
    *   Copy the **API key**.
        

#### 1.2: Create a Dedicated Service Account

Create a service account that this Cloud Run service will run as.

Generated sh

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   gcloud iam service-accounts create comedian-agent-sa \    --display-name="Professional Comedian Agent SA" \    --project=""   `

Use code [with caution](https://support.google.com/legal/answer/13505487).Sh

#### 1.3: Deploy to Cloud Run

Navigate to the cloud\_run\_agent directory and deploy it as a **private service**. Replace the <...> placeholders with your own values.

Generated sh

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # Navigate to the correct directory  cd cloud_run_agent  # Deploy the service  gcloud run deploy professional-comedian-agent \      --source . \      --platform managed \      --region us-central1 \      --project "" \      --no-allow-unauthenticated \      --service-account "comedian-agent-sa@.iam.gserviceaccount.com" \      --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_API_KEY=,SEARCH_ENGINE_ID="   `

Use code [with caution](https://support.google.com/legal/answer/13505487).Sh

After deployment, copy the service's **URL**. You will need it for the frontend agent.

### Part 2: Set Up IAM for Secure Communication

This step configures the permissions that allow the frontend agent to securely call the backend.

#### 2.1: Create a Service Account for the Frontend Agent

This is the identity that the Classic Joke Agent will _impersonate_.

Generated sh

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   gcloud iam service-accounts create classic-joke-caller-sa \    --display-name="Classic Joke Caller SA" \    --project=""   `

Use code [with caution](https://support.google.com/legal/answer/13505487).Sh

#### 2.2: Grant IAM Permissions

1.  Generated shgcloud iam service-accounts add-iam-policy-binding \\ classic-joke-caller-sa@.iam.gserviceaccount.com \\ --member="serviceAccount:service-@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \\ --role="roles/iam.serviceAccountTokenCreator" \\ --project=""Use code [with caution](https://support.google.com/legal/answer/13505487).Sh
    
    *   Agent Engine runs as a special Google-managed service account. We need to grant it permission to create tokens for our classic-joke-caller-sa.
        
    *   Replace  with your actual project number (e.g., 123456789).
        
2.  Generated shgcloud run services add-iam-policy-binding professional-comedian-agent \\ --region=us-central1 \\ --project="" \\ --member="serviceAccount:classic-joke-caller-sa@.iam.gserviceaccount.com" \\ --role="roles/run.invoker"Use code [with caution](https://support.google.com/legal/answer/13505487).Sh
    
    *   Give our classic-joke-caller-sa permission to call the professional-comedian-agent.
        
3.  Generated shgcloud projects add-iam-policy-binding \\ --member="serviceAccount:service-@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \\ --role="roles/browser"Use code [with caution](https://support.google.com/legal/answer/13505487).Sh
    
    *   The google-auth library needs to know which project it's in. Grant the Agent Engine's service account read-only access to the project.
        

### Part 3: Deploy the Frontend (Classic Joke Agent)

You can now deploy one of the two frontend agents to test the different communication patterns.

#### Testing Scenario 1: Direct IAM Authentication

1.  Generated shcd agent\_engine\_agents/iam\_classic\_joke\_agentUse code [with caution](https://support.google.com/legal/answer/13505487).Sh
    
2.  **Configure:** Open the agent.py file and update the PRIVATE\_CLOUD\_RUN\_URL and TARGET\_SERVICE\_ACCOUNT variables with your specific values.
    
3.  Generated shadk deploy agent\_engine \\ --project="" \\ --region="us-central1" \\ --staging\_bucket="gs://" \\ --display\_name="classic-joke-agent-iam" \\ .Use code [with caution](https://support.google.com/legal/answer/13505487).Sh
    

#### Testing Scenario 2: IAP Authentication

This requires additional setup of an External HTTPS Load Balancer. See the official documentation for details.

1.  Generated shcd agent\_engine\_agents/iap\_classic\_joke\_agentUse code [with caution](https://support.google.com/legal/answer/13505487).Sh
    
2.  **Configure:** Open the agent.py file and update the LOAD\_BALANCER\_URL, TARGET\_SERVICE\_ACCOUNT, and IAP\_CLIENT\_ID variables.
    
3.  Generated shadk deploy agent\_engine \\ --project="" \\ --region="us-central1" \\ --staging\_bucket="gs://" \\ --display\_name="classic-joke-agent-iap" \\ .Use code [with caution](https://support.google.com/legal/answer/13505487).Sh
    

### Part 4: Register the Agent in AgentSpace

After the adk deploy command completes, it will output a **Reasoning Engine ID**. You need this to register your agent so it can be used in the AgentSpace UI.

1.  **Navigate** to the agent\_registration\_tool directory you cloned in the prerequisites.
    
2.  Generated shpython as\_registry\_client.py register\_agent \\ --project\_id \\ --app\_id \\ --adk\_deployment\_id Use code [with caution](https://support.google.com/legal/answer/13505487).Sh
    
    *   Find your **AgentSpace App ID** in the GCP Console under **Vertex AI -> Agent Builders -> Apps**. It will look like agentspace-123....
        
    *   Replace the placeholders below with your values.
        

You can now go to AgentSpace, find your newly registered agent, and chat with it to test the full, secure, end-to-end communication flow.
