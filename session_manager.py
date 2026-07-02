import streamlit as st
import streamlit.components.v1 as components

def inject_session_persistence_engine():
    """
    Synchronizes Streamlit's in-memory session state with the browser's 
    persistent localStorage API to protect sessions against accidental refreshes.
    """
    # 1. READ PIPELINE: Check if browser data needs to be recovered
    if st.session_state.get("authenticated_user") is None:
        try:
            q_params = dict(st.query_params)
        except Exception:
            q_params = {}

        # Capture the cryptographic recovery hook from the URL
        if "rec_u" in q_params:
            recovered_user = str(q_params["rec_u"]).strip()
            if recovered_user and recovered_user != "None" and recovered_user != "null":
                st.session_state.authenticated_user = recovered_user
                st.session_state.is_admin = str(q_params.get("rec_a", "false")).lower() == "true"
                st.session_state.current_view = "dashboard"
                st.query_params.clear()
                st.rerun()
        else:
            # Inject background JavaScript to extract tokens from localStorage
            components.html(
                """
                <script>
                    const u = localStorage.getItem("isc2_cc_session_user");
                    const a = localStorage.getItem("isc2_cc_session_admin");
                    if (u && u.trim() !== "" && u !== "null") {
                        const url = new URL(window.parent.location.href);
                        url.searchParams.set("rec_u", u);
                        url.searchParams.set("rec_a", a || "false");
                        window.parent.location.href = url.toString();
                    }
                </script>
                """,
                height=0
            )

    # 2. WRITE PIPELINE: Keep browser storage updated when state changes
    if st.session_state.get("authenticated_user") is not None:
        user = st.session_state.authenticated_user
        admin_flag = str(st.session_state.get("is_admin", False)).lower()
        
        components.html(
            f"""
            <script>
                if (localStorage.getItem("isc2_cc_session_user") !== "{user}") {{
                    localStorage.setItem("isc2_cc_session_user", "{user}");
                    localStorage.setItem("isc2_cc_session_admin", "{admin_flag}");
                }}
            </script>
            """,
            height=0
        )

def execute_secure_logout():
    """
    Clears all in-memory properties and purges browser memory storage blocks.
    """
    st.session_state.authenticated_user = None
    st.session_state.is_admin = False
    st.session_state.current_exam = None
    st.session_state.session_active = False
    st.session_state.selected_mode = None
    st.session_state.current_view = "landing"
    
    components.html(
        """
        <script>
            localStorage.removeItem("isc2_cc_session_user");
            localStorage.removeItem("isc2_cc_session_admin");
            window.parent.location.search = ""; 
        </script>
        """,
        height=0
    )
    st.rerun()