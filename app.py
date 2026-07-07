import streamlit as st
import sqlite3
import random
import time
import hashlib
import smtplib
import json
import streamlit.components.v1 as components
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3  
from session_manager import inject_session_persistence_engine, execute_secure_logout

# =====================================================================
# 1. CRYPTOGRAPHIC SECURITY & CONFIGURATION MATRIX
# =====================================================================
DEFAULT_FALLBACK_HASH = "64b7bd3b82736b009e992764f1e967a57fa85bd486a4387d85ef66bb8b6639c4"

def get_admin_hash_target():
    return st.secrets.get("ADMIN_HASH_TARGET", DEFAULT_FALLBACK_HASH)

def verify_is_admin(input_username):
    hashed_input = hashlib.sha256(input_username.strip().encode()).hexdigest()
    return hashed_input == get_admin_hash_target()

def hash_password(plain_text_pass):
    return hashlib.sha256(plain_text_pass.strip().encode()).hexdigest()

def play_audio_feedback(is_success=True):
    frequency = 587.33 if is_success else 220.0  
    duration = 0.15 if is_success else 0.4
    components.html(f"""
        <script>
        var context = new (window.AudioContext || window.webkitAudioContext)();
        var osc = context.createOscillator();
        var gain = context.createGain();
        osc.type = '{'sine' if is_success else 'sawtooth'}';
        osc.frequency.setValueAtTime({frequency}, context.currentTime);
        gain.gain.setValueAtTime(0.1, context.currentTime);
        osc.connect(gain);
        gain.connect(context.destination);
        osc.start();
        setTimeout(function() {{ osc.stop(); }}, {duration * 1000});
        </script>
    """, height=0)

def send_smtp_email(recipient_email, subject, html_content):
    smtp_config = st.secrets.get("smtp", {})
    if not smtp_config:
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_config["SENDER_EMAIL"]
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        server = smtplib.SMTP(smtp_config["SERVER"], int(smtp_config["PORT"]))
        server.starttls() 
        server.login(smtp_config["USERNAME"], smtp_config["PASSWORD"])
        server.sendmail(smtp_config["SENDER_EMAIL"], recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False

# =====================================================================
# 2. DATABASE REPOSITORY SETUP
# =====================================================================
DB_FILE = "isc2_simulator.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_registry (
            username TEXT PRIMARY KEY,
            candidate_email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            recovery_question TEXT NOT NULL,
            recovery_answer_hash TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            official_rationale TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM question_pool")
    if cursor.fetchone()[0] == 0:
        default_qs = [
            ("GLOBAL_ADMIN", "Domain 1: Security Principles", "Which leg of the CIA Triad is directly violated when an unauthorized modification occurs?", "Confidentiality", "Integrity", "Availability", "Non-repudiation", "B", "Integrity deals explicitly with preventing unauthorized modifications to data."),
            ("GLOBAL_ADMIN", "Domain 5: Security Operations", "How long does it take to crack a non-complex 10-number numeric password using standard software?", "Five seconds", "Thirty-five days", "Twelve months", "152,000 years", "A", "A completely numeric, non-complex 10-character password can be broken in seconds by automated tools."),
            ("GLOBAL_ADMIN", "Domain 3: Access Control Concepts", "Which identification principle maps back directly to maintaining distinct tracking verification histories across users?", "Authentication", "Accountability", "Authorization", "Anonymization", "B", "Accountability maps individual identities back to their distinctive historical event logs.")
        ]
        cursor.executemany("""
            INSERT INTO question_pool (user_id, domain, question_text, option_a, option_b, option_c, option_d, correct_option, official_rationale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, default_qs)
    conn.commit()
    conn.close()

init_db()

# =====================================================================
# 3. STREAMLIT CONFIGURATION & CRASH-SAFE SESSION STATE SYNC
# =====================================================================
st.set_page_config(page_title="(ISC)² CC Simulator Engine", page_icon="🛡️", layout="wide")

if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "current_view" not in st.session_state:
    st.session_state.current_view = "landing"
if "current_exam" not in st.session_state:
    st.session_state.current_exam = None
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "user_confidence" not in st.session_state:
    st.session_state.user_confidence = {}
if "ai_response_cache" not in st.session_state:
    st.session_state.ai_response_cache = {}
if "exam_end_timestamp" not in st.session_state:
    st.session_state.exam_end_timestamp = None
if "session_active" not in st.session_state:
    st.session_state.session_active = False
if "selected_count" not in st.session_state:
    st.session_state.selected_count = 20
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = None

inject_session_persistence_engine()

try:
    q_params = dict(st.query_params)
except Exception:
    q_params = {}

if st.session_state.authenticated_user is not None or "rec_u" in q_params:
    st.session_state.current_view = "dashboard"

# High-Contrast Cross-Theme Stylesheet (Patched Contrast Leaks)
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    .hero-container {
        text-align: center;
        padding: 5rem 2rem 4rem 2rem;
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        border-radius: 16px;
        margin-bottom: 2.5rem;
        border: 1px solid #1e293b;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .hero-title { font-size: 3.6rem; font-weight: 800; color: #ffffff !important; margin-bottom: 1rem; letter-spacing: -1px; }
    .hero-subtitle { font-size: 1.35rem; color: #e2e8f0 !important; max-width: 800px; margin: 0 auto 1.5rem auto; line-height: 1.6; }
    
    .feature-card {
        background-color: #1e293b; padding: 2rem; border-radius: 12px; border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); transition: transform 0.2s ease, border-color 0.2s ease;
        height: 280px; margin-bottom: 1rem;
    }
    .feature-card:hover { transform: translateY(-5px); border-color: #2563eb; }
    .feature-icon { font-size: 2.3rem; margin-bottom: 1rem; }
    .feature-title { font-size: 1.25rem; font-weight: 700; color: #ffffff !important; margin-bottom: 0.5rem; }
    .feature-text { font-size: 0.95rem; color: #cbd5e1 !important; line-height: 1.5; }
    
    .isc2-header { color: #22c55e !important; font-weight: 800; font-size: 2.6rem; text-align: center; margin-bottom: 0.2rem; }
    .isc2-subheader { color: #cbd5e1 !important; font-size: 1rem; text-align: center; font-weight: 600; margin-bottom: 2rem; letter-spacing: 1px; }
    .card { background-color: #1e293b; padding: 1.8rem; border-radius: 8px; border-left: 5px solid #22c55e; box-shadow: 0 4px 10px rgba(0,0,0,0.2); color: #f8fafc !important; margin-bottom: 1rem; }
    
    .ai-box { background-color: #1e293b; padding: 1.5rem; border-radius: 8px; border-left: 5px solid #0284c7; color: #f8fafc !important; border: 1px solid #334155; }
    .ai-box-offline { background-color: #2d1a1a; padding: 1.5rem; border-radius: 8px; border-left: 5px solid #ef4444; color: #fca5a5 !important; border: 1px solid #451a1a; }
    
    .login-box { background: #1e293b; padding: 2.5rem; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); border-top: 6px solid #22c55e; max-width: 650px; margin: 3rem auto; color: #f8fafc !important; }
    .dashboard-box { background: #1e293b; padding: 2.5rem; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.3); border-top: 6px solid #22c55e; max-width: 800px; margin: 2rem auto; color: #f8fafc !important; }
    .timer-sidebar { background-color: #7f1d1d; border: 1px solid #f87171; color: #fca5a5 !important; padding: 0.8rem; border-radius: 8px; font-weight: 800; text-align: center; font-size: 1.1rem; margin: 1rem 0; }
    
    /* CRITICAL CONTRAST FIXES: Force visibility across ALL standard button profiles */
    div.stButton > button {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 2px solid #cbd5e1 !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }
    div.stButton > button p {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    div.stButton > button:hover {
        color: #2563eb !important;
        border-color: #2563eb !important;
        background-color: #f8fafc !important;
    }
    div.stButton > button:hover p {
        color: #2563eb !important;
    }
    
    /* Primary Action Buttons (Override) */
    div.stButton > button[kind="primary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"] p {
        color: #ffffff !important;
    }

    /* Core typography isolation inside app views */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p:not(button p), .stApp label, .stApp span:not([data-baseweb="tab"]) {
        color: #f8fafc !important;
    }
    
    /* Tab Control text visibility safety rules */
    div[data-baseweb="tab-list"] button p {
        color: #cbd5e1 !important;
    }
    div[data-baseweb="tab-list"] button[aria-selected="true"] p {
        color: #3b82f6 !important;
        font-weight: bold !important;
    }
    
    div[data-baseweb="input"] input, div[data-baseweb="select"] div {
        color: #f8fafc !important;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 4. VIEW ROUTER DISPATCHER
# =====================================================================
if st.session_state.authenticated_user is not None and st.session_state.current_view != "dashboard":
    st.session_state.current_view = "dashboard"

if st.session_state.current_view == "landing":
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">🛡️ ISC² CC Training Core</div>
            <div class="hero-subtitle">
                Learn cybersecurity the smart way — practice questions, mock exams, and cloud-native AI mentoring engineered into one ecosystem.
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_btn1, col_btn2, _ = st.columns([2, 2, 4])
    with col_btn1:
        if st.button("🟢 Get Started / Register", use_container_width=True, type="primary", key="landing_reg_btn"):
            st.session_state.current_view = "auth"
            st.rerun()
    with col_btn2:
        if st.button("🔵 Log In To Dashboard", use_container_width=True, key="landing_login_btn"):
            st.session_state.current_view = "auth"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## ✨ Engineered Platform Capabilities")
    
    feat_col1, feat_col2, feat_col3, feat_col4 = st.columns(4)
    with feat_col1:
        st.markdown('<div class="feature-card"><div class="feature-icon">🧠</div><div class="feature-title">AWS Bedrock Tutoring</div><div class="feature-text">Powered securely by AWS cloud intelligence infrastructure. Get contextual option teardowns and domain syllabus rationales inside the sandbox.</div></div>', unsafe_allow_html=True)
    with feat_col2:
        st.markdown('<div class="feature-card"><div class="feature-icon">📝</div><div class="feature-title">Custom Question Pools</div><div class="feature-text">Build your own security database schema. Add customized domain vectors that integrate directly with your study runs.</div></div>', unsafe_allow_html=True)
    with feat_col3:
        st.markdown('<div class="feature-card"><div class="feature-icon">⏱️</div><div class="feature-title">High-Fidelity Mocks</div><div class="feature-text">Simulate strict exam environments. Randomized question delivery vectors, disabled AI coaches, and standalone countdown state synchronization.</div></div>', unsafe_allow_html=True)
    with feat_col4:
        st.markdown('<div class="feature-card"><div class="feature-icon">📊</div><div class="feature-title">Confidence Metrics</div><div class="feature-text">Track knowledge accuracy alongside user-reported certainty percentages (0-100%) to flag structural bias and systematic gaps before testing.</div></div>', unsafe_allow_html=True)

elif st.session_state.current_view == "auth":
    if st.button("⬅️ Back to Landing Page", key="back_to_landing"):
        st.session_state.current_view = "landing"
        st.rerun()
        
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Sign In", "📝 Create Account", "🔄 Reset Password"])
    
    with auth_tab1:
        st.markdown("### Profile Authentication Entry")
        login_user = st.text_input("Username Identifier:", key="login_u_box").strip().upper()
        login_pass = st.text_input("Access Password:", type="password", key="login_p_box")
        
        if st.button("🔑 Access System Dashboard", use_container_width=True, key="btn_signin"):
            if not login_user or not login_pass:
                st.error("Please enter both parameters to authenticate access nodes.")
            else:
                is_admin_flag = verify_is_admin(login_user)
                if is_admin_flag:
                    resolved_user = "PLATFORM_ADMIN"
                    st.session_state.is_admin = True
                    st.session_state.authenticated_user = resolved_user
                    st.session_state.current_view = "dashboard"
                    components.html(f"<script>localStorage.setItem('isc2_cc_session_user', '{resolved_user}'); localStorage.setItem('isc2_cc_session_admin', 'true');</script>", height=0)
                    time.sleep(0.1)
                    st.rerun()
                else:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("SELECT password_hash FROM user_registry WHERE username = ?", (login_user,))
                    row = cursor.fetchone()
                    conn.close()
                    
                    if row and row[0] == hash_password(login_pass):
                        st.session_state.is_admin = False
                        st.session_state.authenticated_user = login_user
                        st.session_state.current_view = "dashboard"
                        components.html(f"<script>localStorage.setItem('isc2_cc_session_user', '{login_user}'); localStorage.setItem('isc2_cc_session_admin', 'false');</script>", height=0)
                        time.sleep(0.1)
                        st.rerun()
                    else:
                        st.error("Access verification handshake dropped: Invalid Credentials.")

    with auth_tab2:
        st.markdown("### Account Registration Onboarding")
        reg_user = st.text_input("Select Unique Username Key:", key="reg_u").strip().upper()
        reg_email = st.text_input("Candidate Notification Email Address Contact:", key="reg_e").strip()
        reg_pass = st.text_input("Formulate Account Safe Password:", type="password", key="reg_p")
        
        st.markdown("🔧 **Self-Service Password Recovery Setup**")
        recovery_q = st.selectbox("Choose a Challenge Verification Question:", [
            "What was the name of your first primary computer system vendor?",
            "What city did you acquire your first technical training cert inside?",
            "What is the brand name of your favorite networking router firmware?"
        ], key="reg_rq")
        recovery_a = st.text_input("Verification Answer (Case-Insensitive):", key="reg_ra").strip().upper()
        
        if st.button("🚀 Finalize & Register Profile Node", use_container_width=True):
            current_target_hash = get_admin_hash_target()
            input_user_hash = hashlib.sha256(reg_user.encode()).hexdigest()
            
            if not reg_user or not reg_email or not reg_pass or not recovery_a:
                st.error("All configuration fields must be fully populated.")
            elif input_user_hash == current_target_hash or reg_user == "SUPER_SECRET_ADMIN_PORTAL":
                st.error("Operation Denied: This administrative identity namespace is reserved.")
            elif "@" not in reg_email or "." not in reg_email:
                st.error("Please provide a syntactically valid email address structure.")
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM user_registry WHERE username = ?", (reg_user,))
                if cursor.fetchone():
                    st.error("Identity conflict detected. This username has already been issued.")
                    conn.close()
                else:
                    cursor.execute("""
                        INSERT INTO user_registry (username, candidate_email, password_hash, recovery_question, recovery_answer_hash)
                        VALUES (?, ?, ?, ?, ?)
                    """, (reg_user, reg_email, hash_password(reg_pass), recovery_q, hash_password(recovery_a)))
                    conn.commit()
                    conn.close()
                    
                    welcome_html = f"<h2>🛡️ Account Activated</h2><p>Hello {reg_user}, profile node initialized successfully.</p>"
                    send_smtp_email(reg_email, "Account Activated - (ISC)2 Engine Sandbox", welcome_html)
                    st.success(f"✨ Registration Completed! Toggle back to 'Sign In' to access your dashboard.")

    with auth_tab3:
        st.markdown("### Self-Service Password Recovery Gateway")
        reset_user = st.text_input("Enter Locked Username Identification String:", key="rst_u").strip().upper()
        
        if reset_user:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT recovery_question, candidate_email FROM user_registry WHERE username = ?", (reset_user,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                stored_question, registered_email = row[0], row[1]
                st.warning(f"**Security Challenge Question:** {stored_question}")
                answer_attempt = st.text_input("Your Secret Challenge Verification Answer:", key="rst_a").strip().upper()
                new_pass_entry = st.text_input("Define New Core Access Password String:", type="password", key="new_p")
                
                if st.button("💾 Verify Security Answers & Save Password", use_container_width=True):
                    if not answer_attempt or not new_pass_entry:
                        st.error("Both parameters must be filled out.")
                    else:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("SELECT recovery_answer_hash FROM user_registry WHERE username = ?", (reset_user,))
                        true_answer_hash = cursor.fetchone()[0]
                        
                        if true_answer_hash == hash_password(answer_attempt):
                            cursor.execute("UPDATE user_registry SET password_hash = ? WHERE username = ?", (hash_password(new_pass_entry), reset_user))
                            conn.commit()
                            conn.close()
                            alert_html = f"<h3>⚠️ Security Notice</h3><p>Your access keys were updated via challenge confirmation.</p>"
                            send_smtp_email(registered_email, "Security Alert: Passcode Modified", alert_html)
                            st.success("🔒 Access details updated successfully! Head back to 'Sign In'.")
                        else:
                            st.error("Verification failure. Security challenge response mismatch.")
                            conn.close()
            else:
                st.error("The specified profile string target does not exist.")
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.current_view == "dashboard":
    current_user = st.session_state.authenticated_user
    is_admin_session = st.session_state.is_admin
    
    st.sidebar.title(f"👤 Node: {current_user}")
    if st.session_state.session_active:
        st.sidebar.markdown(f"Environment: **{st.session_state.selected_mode}**")
        st.sidebar.markdown(f"Allocation Target: **{st.session_state.selected_count} Items**")
        
        if st.session_state.selected_mode == "Exam Mode" and st.session_state.get("exam_end_timestamp"):
            time_left = int(st.session_state.exam_end_timestamp - time.time())
            if time_left <= 0:
                st.sidebar.markdown("<div class='timer-sidebar'>🚨 TIME EXPIRED!</div>", unsafe_allow_html=True)
                if st.session_state.current_exam and st.session_state.current_index < len(st.session_state.current_exam):
                    st.session_state.current_index = len(st.session_state.current_exam)
                    st.rerun()
            else:
                m, s = divmod(time_left, 60)
                st.sidebar.markdown(f"<div class='timer-sidebar'>⏳ TIME LEFT: {m:02d}:{s:02d}</div>", unsafe_allow_html=True)

        # CRITICAL RECOVERY FEATURE: The Escape Hatch Button
        st.sidebar.markdown("---")
        if st.sidebar.button("⚠️ Quit & Abandon Exam", use_container_width=True, type="primary"):
            st.session_state.current_exam = None
            st.session_state.current_index = 0
            st.session_state.user_answers = {}
            st.session_state.user_confidence = {}
            st.session_state.ai_response_cache = {}
            st.session_state.session_active = False
            st.session_state.selected_mode = None
            st.rerun()
    
    app_mode = st.sidebar.radio("Console Navigation Matrix", ["Run Practice Exam", "Admin Content Manager"])
    
    if st.sidebar.button("Log Out / Exit Portal Context", use_container_width=True):
        execute_secure_logout()

    if app_mode == "Admin Content Manager":
        st.subheader("📝 Live Training Portal Questionnaire Sync")
        if is_admin_session or verify_is_admin(current_user):
            st.success("👑 MASTER ADMINISTRATIVE PRIVILEGES GRANTED: Entries apply globally.")
        else:
            st.info("👤 Private Sandbox Mode: Added items will save to your profile folder exclusively.")
        
        with st.form("add_question_form"):
            domain = st.selectbox("Blueprint Target Domain Cluster", [
                "Domain 1: Security Principles", "Domain 2: Incident Response, BCP & DRP",
                "Domain 3: Access Control Concepts", "Domain 4: Network Security", "Domain 5: Security Operations"
            ])
            q_text = st.text_area("Question Stem Text Formulation:")
            a = st.text_input("Option Structure Alpha (A):")
            b = st.text_input("Option Structure Bravo (B):")
            c = st.text_input("Option Structure Charlie (C):")
            d = st.text_input("Option Structure Delta (D):")
            correct = st.selectbox("Correct Target Key Value Verification", ["A", "B", "C", "D"])
            rationale = st.text_area("Official Training Syllabus Rationale Context:")
            
            if st.form_submit_button("Commit Node Entry to Database Core"):
                if q_text and a and b and c and d:
                    resolved_storage_id = "GLOBAL_ADMIN" if (is_admin_session or verify_is_admin(current_user)) else current_user
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO question_pool (user_id, domain, question_text, option_a, option_b, option_c, option_d, correct_option, official_rationale)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (resolved_storage_id, domain, q_text, a, b, c, d, correct, rationale))
                    conn.commit()
                    conn.close()
                    st.success("Database entry created successfully!")
                else:
                    st.error("All configuration targets must be populated.")

    elif app_mode == "Run Practice Exam":
        if not st.session_state.session_active:
            st.markdown(f"<div class='isc2-header'>🛡️ Welcome, Candidate {current_user}</div>", unsafe_allow_html=True)
            st.markdown("<div class='isc2-subheader'>Configure your active testing framework options below.</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='dashboard-box'>", unsafe_allow_html=True)
            st.markdown("### ⚙️ Session Parameters Configuration")
            chosen_q_count = st.selectbox("Exam Evaluation Pool Item Target Count Length:", [20, 40, 60, 80, 100], index=0)
            
            st.write("---")
            st.markdown("#### Select Active Environment Simulation Profile Mode:")
            
            col_dash_p, col_dash_e = st.columns(2)
            with col_dash_p:
                if st.button("📖 Launch Practice Session Lounge", use_container_width=True):
                    st.session_state.selected_count = chosen_q_count
                    st.session_state.selected_mode = "Practice Mode"
                    st.session_state.session_active = True
                    st.rerun()
            with col_dash_e:
                if st.button("⚡ Launch High-Fidelity Examination Sandbox", use_container_width=True):
                    st.session_state.selected_count = chosen_q_count
                    st.session_state.selected_mode = "Exam Mode"
                    st.session_state.session_active = True
                    st.session_state.exam_end_timestamp = time.time() + (chosen_q_count * 60)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Interactive Consultation Box (Ask Nexus)
            st.markdown("<div class='dashboard-box'>", unsafe_allow_html=True)
            st.markdown("### 💬 Direct Consultation Portal")
            st.info("Have a specific structural question about an ISC² security domain? Query Nexus directly below.")
            nexus_query = st.text_input("Type your message or ask Nexus...", key="global_nexus_chat_input")
            
            if st.button("✨ Transmit Query Payload", use_container_width=True):
                if not nexus_query:
                    st.warning("Please enter a question payload before transmitting.")
                elif "aws" not in st.secrets:
                    st.error("Engine Cluster Offline: 'aws' credentials section is missing from your Streamlit Secrets control panel.")
                else:
                    with st.spinner("Core Nexus AWS Engine is parsing context..."):
                        try:
                            bedrock = boto3.client(
                                service_name="bedrock-runtime",
                                aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
                                aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"],
                                region_name=st.secrets["aws"]["AWS_DEFAULT_REGION"]
                            )
                            llama_prompt = f"You are an elite (ISC)2 Certified in Cybersecurity (CC) professor. Provide a complete, comprehensive, and crisp tutorial answering this student question: {nexus_query}"
                            body_payload = json.dumps({
                                "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{llama_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                                "max_gen_len": 512,
                                "temperature": 0.4
                            })
                            response = bedrock.invoke_model(modelId="meta.llama3-8b-instruct-v1:0", body=body_payload)
                            response_body = json.loads(response.get("body").read())
                            st.markdown("#### 🤖 Nexus Core Response:")
                            st.success(response_body.get("generation", "No data returned."))
                        except Exception as e:
                            st.error(f"Error communicating with Bedrock Cluster: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            if st.session_state.current_exam is None:
                conn = sqlite3.connect(DB_FILE)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM question_pool WHERE user_id = ? OR user_id = 'GLOBAL_ADMIN'", (current_user,))
                rows = cursor.fetchall()
                conn.close()
                
                if len(rows) > 0:
                    pool = [dict(r) for r in rows]
                    random.shuffle(pool)
                    st.session_state.current_exam = pool[:st.session_state.selected_count]
                    st.session_state.current_index = 0
                    st.session_state.user_answers = {}
                    st.session_state.user_confidence = {}
                    st.session_state.ai_response_cache = {}
                    st.rerun()
                else:
                    st.warning("No questions found tracking within your workspace context scopes.")
                    st.session_state.session_active = False
            else:
                exam = st.session_state.current_exam
                idx = st.session_state.current_index
                mode_setting = st.session_state.selected_mode
                
                if idx > len(exam) - 1 and len(exam) > 0:
                    st.session_state.current_index = len(exam)
                    idx = len(exam)

                if idx < len(exam):
                    q = exam[idx]
                    left_exam_col, right_ai_col = st.columns([5, 4], gap="large")
                    
                    with left_exam_col:
                        st.markdown(f"### Question {idx + 1} of {len(exam)}")
                        st.caption(f"**Syllabus Focus Category:** {q['domain']}")
                        st.markdown(f"<div class='card'><strong>{q['question_text']}</strong></div>", unsafe_allow_html=True)
                        
                        options_map = {"A": q['option_a'], "B": q['option_b'], "C": q['option_c'], "D": q['option_d']}
                        current_selection = st.session_state.user_answers.get(idx, None)
                        
                        choice = st.radio(
                            "Identify target blueprint response path designation:",
                            ["A", "B", "C", "D"],
                            format_func=lambda x: f"{x}: {options_map[x]}",
                            index=None if current_selection is None else ["A", "B", "C", "D"].index(current_selection),
                            key=f"radio_question_{idx}"
                        )
                        if choice and choice != current_selection:
                            st.session_state.user_answers[idx] = choice
                            play_audio_feedback(is_success=(choice == q['correct_option']))

                        st.write("---")
                        saved_conf = st.session_state.user_confidence.get(idx, 0)
                        conf_input = st.slider("Confidence Scale (Must select greater than 0% to proceed):", 0, 100, saved_conf, 5, key=f"confidence_slider_{idx}")
                        st.session_state.user_confidence[idx] = conf_input
                        st.progress(float(conf_input / 100.0))

                        is_next_allowed = (choice is not None) and (conf_input > 0)
                        st.write("")
                        nav1, nav2, _ = st.columns([1, 1, 2])
                        with nav1:
                            if idx > 0:
                                if st.button("⬅️ Previous", use_container_width=True):
                                    st.session_state.current_index -= 1
                                    st.rerun()
                        with nav2:
                            if idx < len(exam) - 1:
                                if st.button("Next Question ➡️", use_container_width=True, disabled=not is_next_allowed):
                                    st.session_state.current_index += 1
                                    st.rerun()
                            else:
                                if st.button("🎓 Terminate & Grade", use_container_width=True, disabled=not is_next_allowed):
                                    st.session_state.current_index = len(exam)
                                    st.rerun()
                        if not is_next_allowed:
                            st.warning("⚠️ You must select an answer choice AND adjust the confidence scale above 0% to proceed.")

                    with right_ai_col:
                        st.markdown("### 🛡️ Core Nexus AI Mentor")
                        if mode_setting == "Practice Mode":
                            if choice:
                                idx_cache_key = f"q_{idx}"
                                if idx_cache_key in st.session_state.ai_response_cache:
                                    st.markdown("<div class='ai-box'>", unsafe_allow_html=True)
                                    st.write(st.session_state.ai_response_cache[idx_cache_key])
                                    st.markdown("</div>", unsafe_allow_html=True)
                                elif "aws" not in st.secrets:
                                    st.markdown("<div class='ai-box-offline'>", unsafe_allow_html=True)
                                    st.write("Cognitive bridge dropped. AWS Secrets schema key matrix not located.")
                                    st.markdown("</div>", unsafe_allow_html=True)
                                else:
                                    try:
                                        with st.spinner("Core Nexus AWS Engine is computing analysis..."):
                                            bedrock = boto3.client(
                                                service_name="bedrock-runtime",
                                                aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
                                                aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"],
                                                region_name=st.secrets["aws"]["AWS_DEFAULT_REGION"]
                                            )
                                            llama_prompt = (
                                                f"You are an expert (ISC)2 Certified in Cybersecurity mentor. Analyze option path context concisely for Domain: {q['domain']}. "
                                                f"Question: {q['question_text']}, Choice Key: {choice}, Correct: {q['correct_option']}. "
                                                f"Rationale: {q['official_rationale']}. Tell the student why their choice is correct or incorrect."
                                            )
                                            body_payload = json.dumps({
                                                "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{llama_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                                                "max_gen_len": 512,
                                                "temperature": 0.4
                                            })
                                            response = bedrock.invoke_model(modelId="meta.llama3-8b-instruct-v1:0", body=body_payload)
                                            output_text = json.loads(response.get("body").read()).get("generation", "No payload processed.")
                                            st.session_state.ai_response_cache[idx_cache_key] = output_text
                                            st.markdown("<div class='ai-box'>", unsafe_allow_html=True)
                                            st.write(output_text)
                                            st.markdown("</div>", unsafe_allow_html=True)
                                    except Exception as e:
                                        st.markdown("<div class='ai-box-offline'>", unsafe_allow_html=True)
                                        st.write(f"Cognitive bridge connection error: {str(e)}")
                                        st.markdown("</div>", unsafe_allow_html=True)
                            else:
                                st.info("💡 *Select an answer choice to engage the interactive AI mentor.*")
                        else:
                            st.caption("🔒 *AI training assistance disabled during formal Exam Mode conditions.*")
                else:
                    st.subheader("📊 Session Processing Complete: System Audit Summary")
                    correct_tally = sum(1 for i, q in enumerate(exam) if st.session_state.user_answers.get(i, None) == q['correct_option'])
                    final_score = int((correct_tally / len(exam)) * 100) if len(exam) > 0 else 0
                    
                    if final_score >= 70:
                        st.balloons()
                        st.success(f"### Final Metric Result Score: {final_score}% — PROVISIONALLY PASSED")
                    else:
                        st.error(f"### Final Metric Result Score: {final_score}% — DOES NOT CONFORM TO PASSMARK")
                    
                    with st.expander("🔍 Review Detailed Answer Key Logs"):
                        for i, q in enumerate(exam):
                            u_ans = st.session_state.user_answers.get(i, 'Unanswered')
                            status_symbol = "✅" if u_ans == q['correct_option'] else "❌"
                            st.markdown(f"**Question {i+1}: {status_symbol} (Confidence: {st.session_state.user_confidence.get(i, 0)}%)**")
                            st.write(q['question_text'])
                            st.write(f"* Your Choice: **{u_ans}** | Correct Key: **{q['correct_option']}**")
                            st.write("---")

                    if st.button("Return to Dashboard Matrix", use_container_width=True):
                        st.session_state.current_exam = None
                        st.session_state.current_index = 0
                        st.session_state.user_answers = {}
                        st.session_state.user_confidence = {}
                        st.session_state.ai_response_cache = {}
                        st.session_state.session_active = False
                        st.session_state.selected_mode = None
                        st.rerun()