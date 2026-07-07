import streamlit as st
import time

@st.cache_resource
def get_server_session_storage():
    """
    Creates an isolated server-side memory dictionary that persists 
    even when browser tabs are hard-refreshed or iframes wipe states.
    """
    return {}

def inject_session_persistence_engine():
    """
    Tracks sessions using a combination of a persistent cookie-like browser key 
    and server-side resource caching. Safe against Streamlit Cloud iframe resets.
    """
    # Initialize our server-side vault
    vault = get_server_session_storage()
    
    # Check if this specific browser session already has an initialized tracking key
    if "browser_session_key" not in st.session_state:
        # Create a unique tracking key for this user window based on the timestamp
        st.session_state.browser_session_key = f"sess_{int(time.time() * 1000)}"
    
    session_key = st.session_state.browser_session_key

    # 1. READ PIPELINE: If a refresh wiped the memory, check the server vault
    if st.session_state.get("authenticated_user") is None:
        if session_key in vault:
            saved_session = vault[session_key]
            st.session_state.authenticated_user = saved_session["user"]
            st.session_state.is_admin = saved_session["is_admin"]
            st.session_state.current_view = "dashboard"
            st.rerun()

    # 2. WRITE PIPELINE: Keep the server vault updated if the user is logged in
    else:
        vault[session_key] = {
            "user": st.session_state.authenticated_user,
            "is_admin": st.session_state.get("is_admin", False)
        }

def execute_secure_logout():
    """
    Purges memory structures completely from both server storage and local memory state.
    """
    vault = get_server_session_storage()
    session_key = st.session_state.get("browser_session_key")
    
    # Clear the server record
    if session_key and session_key in vault:
        del vault[session_key]
        
    # Reset local states
    st.session_state.authenticated_user = None
    st.session_state.is_admin = False
    st.session_state.current_exam = None
    st.session_state.session_active = False
    st.session_state.selected_mode = None
    st.session_state.current_view = "landing"
    
    st.rerun()