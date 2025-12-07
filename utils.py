import requests
import asyncio
import sys
from typing import Optional, Any, Callable
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from prompt import user_goal_prompt

# --------------------------
# FIX: WINDOWS ASYNC ERROR (Resolves BlockingIOError)
# --------------------------
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        pass 
# --------------------------

# Standard configuration
cfg = RunnableConfig(recursion_limit=100)
PIPEDREAM_MCP_URL = "https://remote.mcp.pipedream.net"

def initialize_model(google_api_key: str) -> ChatGoogleGenerativeAI:
    """Initialize the Gemini Model (Fixed to 1.5-flash)"""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=google_api_key
    )

def get_pipedream_access_token(client_id: str, client_secret: str) -> str:
    """Exchanges Client ID/Secret for a Pipedream Access Token"""
    url = "https://api.pipedream.com/v1/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        raise Exception(f"Failed to authenticate with Pipedream: {str(e)}")

async def setup_agent_with_tools(
    google_api_key: str,
    pd_project_id: str,
    pd_client_id: str,
    pd_client_secret: str,
    secondary_tool: str,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Any:
    """Sets up the MCP Client and Agent using dual-channel connection"""
    try:
        if progress_callback:
            progress_callback("Authenticating with Pipedream... 🔐")
            
        access_token = get_pipedream_access_token(pd_client_id, pd_client_secret)
        
        # We use the user ID that has BOTH apps connected
        user_id = "streamlit_user_v2" 
        
        base_headers = {
            "Authorization": f"Bearer {access_token}",
            "x-pd-project-id": pd_project_id,
            "x-pd-environment": "development",
            "x-pd-external-user-id": user_id,
        }

        # --- DUAL-CHANNEL CONFIGURATION (Stable Fix for Simultaneous Tool Access) ---

        # 1. YouTube Config (Using the Data API slug you connected)
        yt_config = {
            "youtube": {
                "url": PIPEDREAM_MCP_URL,
                "transport": "streamable_http",
                "headers": {
                    **base_headers,
                    "x-pd-app-slug": "youtube_data_api" 
                }
            }
        }

        # 2. Secondary Config (Drive)
        app_slug = "google_drive" if secondary_tool == "Drive" else "notion"
        sec_config = {
            "secondary": {
                "url": PIPEDREAM_MCP_URL,
                "transport": "streamable_http",
                "headers": {
                    **base_headers,
                    "x-pd-app-slug": app_slug
                }
            }
        }

        if progress_callback:
            progress_callback("Connecting to YouTube Data API & Drive... 🔌")

        # Create separate clients
        client_yt = MultiServerMCPClient(yt_config)
        client_sec = MultiServerMCPClient(sec_config)

        # Fetch tools separately and combine
        tools_yt = await client_yt.get_tools()
        tools_sec = await client_sec.get_tools()
        
        all_tools = tools_yt + tools_sec
        
        if not all_tools:
             raise ValueError("No tools found. Please check connections.")

        if progress_callback:
            progress_callback(f"Success! Loaded {len(all_tools)} tools. Creating Agent... 🤖")

        mcp_orch_model = initialize_model(google_api_key)
        agent = create_react_agent(mcp_orch_model, all_tools)
        
        return agent

    except Exception as e:
        print(f"Error in setup: {str(e)}")
        raise

def run_agent_sync(
    google_api_key: str,
    pd_project_id: str,
    pd_client_id: str,
    pd_client_secret: str,
    secondary_tool_preference: str,
    user_goal: str = "",
    progress_callback: Optional[Callable[[str], None]] = None
) -> dict:
    async def _run():
        try:
            agent = await setup_agent_with_tools(
                google_api_key, pd_project_id, pd_client_id, pd_client_secret, 
                secondary_tool_preference, progress_callback
            )
            
            full_prompt = (
                f"User Goal: {user_goal}\n"
                f"Preferred Documentation Tool: {secondary_tool_preference}\n"
                f"{user_goal_prompt}"
            )
            
            if progress_callback:
                progress_callback("Generating your learning path...")
            
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=full_prompt)]},
                config=cfg
            )
            return result
        except Exception as e:
            raise e

    # Run in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()