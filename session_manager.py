import streamlit as st
import streamlit.components.v1 as components

@st.cache_resource
def get_global_session_vault():
    """
    A persistent dictionary in server RAM to map a cookie UUID to user records.
    """
    return {}

def inject_session_persistence_engine():
    """
    Leverages a native browser cookie wrapper to fetch or assign session tokens, 
    matching them seamlessly with the server vault across hard page reloads.
    """
    vault = get_global_session_vault()

    # Read the cookie value out of the official st.context.cookies dictionary
    # It will look like a unique 13-digit string if set previously
    session_token = st.context.cookies.get("isc2_cc_session_token")

    # 1. READ PIPELINE: If memory was wiped but a valid tracking cookie exists
    if st.session_state.get("authenticated_user") is None:
        if session_token and session_token in vault:
            saved_data = vault[session_token]
            st.session_state.authenticated_user = saved_data["user"]
            st.session_state.is_admin = saved_data["is_admin"]
            st.session_state.current_view = "dashboard"
            st.rerun()

    # 2. WRITE PIPELINE: If user just authenticated, write the cookie tracking token
    else:
        # If no cookie exists yet, we generate one and tell the browser to save it
        if not session_token:
            import time
            new_token = f"tok_{int(time.time() * 1000)}"
            
            # Map the new token to our user data on the server side
            vault[new_token] = {
                "user": st.session_state.authenticated_user,
                "is_admin": st.session_state.get("is_admin", False)
            }
            
            # Inject background JavaScript to set a clean browser-level cookie
            # Max-Age=86400 keeps it alive for 24 hours
            components.html(
                f"""
                <script>
                    document.cookie = "isc2_cc_session_token={new_token}; path=/; max-age=86400; SameSite=Lax";
                    window.parent.location.reload();
                </script>
                """,
                height=0
            )
        else:
            # Keep the token record actively synced up in the server vault
            vault[session_token] = {
                "user": st.session_state.authenticated_user,
                "is_admin": st.session_state.get("is_admin", False)
            }

def execute_secure_logout():
    """
    Wipes the session values out of server vault and clears out the browser cookie.
    """
    vault = get_global_session_vault()
    session_token = st.context.cookies.get("isc2_cc_session_token")
    
    if session_token and session_token in vault:
        del vault[session_token]
        
    st.session_state.authenticated_user = None
    st.session_state.is_admin = False
    st.session_state.current_exam = None
    st.session_state.session_active = False
    st.session_state.selected_mode = None
    st.session_state.current_view = "landing"
    
    # Overwrite cookie with an immediate expiration date to delete it instantly
    components.html(
        """
        <script>
            document.cookie = "isc2_cc_session_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT;";
            window.parent.location.reload();
        </script>
        """,
        height=0
    )