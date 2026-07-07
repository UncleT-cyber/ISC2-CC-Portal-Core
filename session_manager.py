import streamlit as st

def inject_session_persistence_engine():
    """
    Synchronizes Streamlit's session state directly with official URL query parameters.
    Bypasses iframe sandbox constraints to seamlessly persist sessions on browser refresh.
    """
    # 1. READ PIPELINE: If memory is wiped on refresh, look at the URL query parameters
    if st.session_state.get("authenticated_user") is None:
        # Check if the session keys exist in the URL
        if "user" in st.query_params:
            st.session_state.authenticated_user = st.query_params["user"]
            st.session_state.is_admin = st.query_params.get("admin", "false").lower() == "true"
            st.session_state.current_view = "dashboard"
            st.rerun()

    # 2. WRITE PIPELINE: Keep the URL synchronized whenever the user is logged in
    else:
        user = st.session_state.authenticated_user
        admin_flag = str(st.session_state.get("is_admin", False)).lower()
        
        # Safely inject state into URL parameters if they aren't already matching
        if st.query_params.get("user") != user:
            st.query_params["user"] = user
            st.query_params["admin"] = admin_flag


def execute_secure_logout():
    """
    Completely purges state variables and strips query string targets cleanly.
    """
    st.session_state.authenticated_user = None
    st.session_state.is_admin = False
    st.session_state.current_exam = None
    st.session_state.session_active = False
    st.session_state.selected_mode = None
    st.session_state.current_view = "landing"
    
    # Clear the URL parameters entirely on logout
    st.query_params.clear()
    st.rerun()