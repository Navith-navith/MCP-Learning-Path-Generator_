import streamlit as st
from utils import run_agent_sync
import json
import re

st.set_page_config(page_title="MCP POC", page_icon="🤖", layout="wide")

st.title("Model Context Protocol(MCP) - Learning Path Generator")

# Initialize session state
if 'current_step' not in st.session_state:
    st.session_state.current_step = ""
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'last_section' not in st.session_state:
    st.session_state.last_section = ""
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False

# Sidebar for API and Configuration
st.sidebar.header("Configuration")
google_api_key = st.sidebar.text_input("Google AI Studio API Key", type="password")

st.sidebar.divider()
st.sidebar.subheader("Pipedream Configuration")
st.sidebar.info("Use 'Client Credentials' from Pipedream Org Settings.")

pd_project_id = st.sidebar.text_input("Project ID", placeholder="proj_xxxxxx",value ="proj_yes3xDb")
pd_client_id = st.sidebar.text_input("Client ID", type="password", value ="oezVr0kTCPNnXO0ukkMHoFk7FFUq6T4s_0UgEwuJ2hA")
pd_client_secret = st.sidebar.text_input("Client Secret", type="password", value ="bPG2awe1LHgzX6WROEkm4wluvR-4NGCdamKMHFEVAWo")

st.sidebar.divider()
secondary_tool = st.sidebar.radio("Select Documentation Tool:", ["Drive", "Notion"])

st.header("Enter Your Goal")
user_goal = st.text_input("Enter your learning goal:",
                        help="e.g., 'I want to learn python basics in 3 days'")

# Progress UI
progress_container = st.container()
progress_bar = st.empty()

def update_progress(message: str):
    st.session_state.current_step = message
    if st.session_state.progress < 0.9:
        st.session_state.progress += 0.05
    progress_bar.progress(st.session_state.progress)
    
    with progress_container:
        st.info(f"⚙️ {message}")

# Generate Learning Path button
if st.button("Generate Learning Path", type="primary", disabled=st.session_state.is_generating):
    if not (google_api_key and pd_project_id and pd_client_id and pd_client_secret and user_goal):
        st.error("❌ Please fill in ALL fields in the sidebar and enter a goal.")
    else:
        try:
            st.session_state.is_generating = True
            st.session_state.progress = 0.1
            
            # --- AGENT RUN ---
            result = run_agent_sync(
                google_api_key=google_api_key,
                pd_project_id=pd_project_id,
                pd_client_id=pd_client_id,
                pd_client_secret=pd_client_secret,
                secondary_tool_preference=secondary_tool,
                user_goal=user_goal,
                progress_callback=update_progress
            )
            
            # --- DISPLAY LOGIC ---
            st.session_state.progress = 1.0
            progress_bar.progress(1.0)
            with progress_container:
                st.success("✅ Process Complete!")

            st.divider()
            st.header("Your Learning Path")
            
            drive_link = None
            final_ai_text = ""

            if result and "messages" in result:
                for msg in result["messages"]:
                    
                    # 1. Handle Tool Outputs (Search for the Drive Link)
                    if msg.type == "tool":
                        
                        # --- ROBUST LINK EXTRACTION ---
                        # Universal Regex to find a file ID from any Google Docs/Drive URL
                        match = re.search(r'([a-zA-Z0-9_-]{20,})', str(msg.content))
                        if match and ("docs.google.com" in str(msg.content) or "drive.google.com" in str(msg.content)):
                            doc_id = match.group(0)
                            drive_link = f"https://docs.google.com/document/d/{doc_id}/edit?usp=sharing"
                        # -----------------------------
                        
                        # Show all tool outputs in an expander for debugging
                        with st.expander(f"🛠️ Tool Output: {msg.name}", expanded=False):
                            st.code(msg.content)

                    # 2. Handle AI Responses (Capture the final text)
                    elif msg.type == "ai":
                        content = msg.content
                        
                        # Robustly extract text
                        if isinstance(content, list):
                            text = "".join([block.get('text', '') if isinstance(block, dict) else str(block) for block in content])
                        else:
                            text = str(content)
                        
                        final_ai_text = text # Always save the last AI message

            # --- FINAL STEP: Display the Processed Text with the Injected Link ---
            if final_ai_text:
                # Inject the found link into the final text
                if drive_link and "[Drive Link]" in final_ai_text:
                    # Inject the actual link and make it clickable
                    processed_text = final_ai_text.replace("[Drive Link]", f"🔗 [Open Document Here]({drive_link})")
                else:
                    processed_text = final_ai_text
                    
                st.markdown(processed_text)
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
        finally:
            st.session_state.is_generating = False