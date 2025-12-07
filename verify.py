import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
import requests

# --- ENTER YOUR CREDENTIALS ---
PD_PROJECT_ID = "proj_yes3xDb"  # I got this from your logs
PD_CLIENT_ID = "oezVr0kTCPNnXO0ukkMHoFk7FFUq6T4s_0UgEwuJ2hA"      # <--- PASTE YOUR CLIENT ID
PD_CLIENT_SECRET = "bPG2awe1LHgzX6WROEkm4wluvR-4NGCdamKMHFEVAWo"  # <--- PASTE YOUR CLIENT SECRET
# ------------------------------

async def check_real_user():
    print(f"1. Authenticating for Project: {PD_PROJECT_ID}...")
    
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
        print(f"❌ Auth Failed: {e}")
        return

    print(f"\n2. Checking tools for user: 'streamlit_user_1'...")
    
    # Check YouTube specifically
    config = {
        "youtube": {
            "url": "https://remote.mcp.pipedream.net",
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {token}",
                "x-pd-project-id": PD_PROJECT_ID,
                "x-pd-environment": "development",
                "x-pd-external-user-id": "streamlit_user_1", # <--- THE REAL USER
                "x-pd-app-slug": "youtube"
            }
        }
    }

    try:
        client = MultiServerMCPClient(config)
        tools = await client.get_tools()
        
        if len(tools) > 0:
            print(f"\n✅ SUCCESS! Found {len(tools)} YouTube tools!")
            print("Your main app will work now.")
        else:
            print("\n❌ STILL 0 TOOLS. This is unexpected given the screenshot.")
            print("Try clicking the '...' menu on the user row in Pipedream and hit 'Reconnect' or 'Delete' and try again.")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_real_user())