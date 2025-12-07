import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
import requests

# --- ENTER YOUR CREDENTIALS HERE FOR TESTING ---
PD_PROJECT_ID = "proj_yes3xDb"  # Replace with your Project ID
PD_CLIENT_ID = "oezVr0kTCPNnXO0ukkMHoFk7FFUq6T4s_0UgEwuJ2hA"        # Replace with your Client ID
PD_CLIENT_SECRET = "bPG2awe1LHgzX6WROEkm4wluvR-4NGCdamKMHFEVAWo"    # Replace with your Client Secret
# -----------------------------------------------

async def test_youtube_connection():
    print(f"1. Getting Access Token for Project: {PD_PROJECT_ID}...")
    
    # Get Token
    try:
        url = "https://api.pipedream.com/v1/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": PD_CLIENT_ID,
            "client_secret": PD_CLIENT_SECRET
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        token = response.json()["access_token"]
        print("✅ Access Token acquired.")
    except Exception as e:
        print(f"❌ Failed to get token: {e}")
        return

    print("\n2. Connecting to Pipedream MCP (YouTube Only)...")
    
    config = {
        "youtube": {
            "url": "https://remote.mcp.pipedream.net",
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {token}",
                "x-pd-project-id": PD_PROJECT_ID,
                "x-pd-environment": "development",
                "x-pd-external-user-id": "debug_user_01",
                "x-pd-app-slug": "youtube"
            }
        }
    }

    try:
        client = MultiServerMCPClient(config)
        tools = await client.get_tools()
        
        print(f"\n3. Result: Found {len(tools)} tools.")
        
        if len(tools) > 0:
            print("✅ SUCCESS! YouTube is connected.")
            print("Tools found:")
            for t in tools:
                print(f" - {t.name}")
        else:
            print("❌ FAILURE: Connected to Pipedream, but 0 tools were returned.")
            print("   Likely Cause: The YouTube App is not added to THIS specific Project ID.")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_youtube_connection())