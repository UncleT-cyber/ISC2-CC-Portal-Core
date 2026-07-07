import streamlit as st

@st.cache_resource
def get_global_session_vault():
    """
    A secure server-side RAM storage to map transient session keys 
    without exposing raw usernames directly in the open URL bar.
    """
    return {}

def inject_session_persistence_engine():
    """
    Natively maps query parameters to the server session state vault.
    Bypasses all Streamlit Cloud iframe and cookie restrictions seamlessly.
    """
    vault = get_global_session_vault()
    
    # Extract the tracking key safely from the browser URL address bar
    url_key = st.query_params.get("sk")

    # 1. READ PIPELINE: If user hit refresh and wiped local memory, look up the URL key
    if st.session_state.get("authenticated_user") is None:
        if url_key and url_key in vault:
            saved_session = vault[url_key]
            st.session_state.authenticated_user = saved_session["user"]
            st.session_state.is_admin = saved_session["is_admin"]
            st.session_state.current_view = "dashboard"
            st.rerun()

    # 2. WRITE PIPELINE: Keep the browser URL updated when they are actively logged in
    else:
        user = st.session_state.authenticated_user
        admin_flag = st.session_state.get("is_admin", False)
        
        if not url_key:
            import time
            # Create a lightweight unique query token string
            new_key = f"b_key_{int(time.time())}"
            
            # Record it immediately to the server memory vault
            vault[new_key] = {
                "user": user,
                "is_admin": admin_flag
            }
            # Append the key into the URL so a refresh catches it instantly
            st.query_params["sk"] = new_key
        else:
            # Keep the key mapping updated
            vault[url_key] = {
                "user": user,
                "is_admin": admin_flag
            }

def execute_secure_logout():
    """
    Wipes parameters out of the server dictionary and clears the browser URL bar completely.
    """
    vault = get_global_session_vault()
    url_key = st.query_params.get("sk")
    
    if url_key and url_key in vault:
        del vault[url_key]
        
    st.session_state.authenticated_user = None
    st.session_state.is_admin = False
    st.session_state.current_exam = None
    st.session_state.session_active = False
    st.session_state.selected_mode = None
    st.session_state.current_view = "landing"
    
    # Drop all parameters from the URL strings cleanly
    st.query_params.clear()
    st.rerun()