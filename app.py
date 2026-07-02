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
from google import genai

# =====================================================================
# 1. CRYPTOGRAPHIC SECURITY & CONFIGURATION MATRIX
# =====================================================================
DEFAULT_FALLBACK_HASH = "64b7bd3b82736b009e992764f1e967a57fa85bd486a4387d85ef66bb8b6639c4"

def get_admin_hash_target():
    """Retrieves target admin hash from production secrets, falling back to repository default."""
    return st.secrets.get("ADMIN_HASH_TARGET", DEFAULT_FALLBACK_HASH)

def verify_is_admin(input_username):
    hashed_input = hashlib.sha256(input_username.strip().encode()).hexdigest()
    return hashed_input == get_admin_hash_target()

def hash_password(plain_text_pass):
    return hashlib.sha256(plain_text_pass.strip().encode()).hexdigest()

def send_smtp_email(recipient_email, subject, html_content):
    """Securely transmits outbound notification emails using system secrets configuration."""
    smtp_config = st.secrets.get("smtp", {})
    if not smtp_config:
        st.warning("SMTP configurations are not live. Email notifications are currently offline.")
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
    except Exception as e:
        print(f"Mail delivery subsystem quiet bypass: {str(e)}")
        return False

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

ai_client = None
if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)

# =====================================================================
# 2. DATABASE REPOSITORY SETUP WITH EMAIL SCHEMA UPGRADES
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
# 3. STREAMLIT CONFIGURATION & SESSION STATE SYNC
# =====================================================================
st.set_page_config(page_title="(ISC)² CC Simulator Engine", page_icon="🛡️", layout="wide")

# Persistent Login Handler via Browser LocalStorage
def init_browser_session_sync():
    if st.session_state.get("authenticated_user") is not None:
        return

    # Render hidden JavaScript bridge to inspect localStorage keys
    storage_bridge = components.html(
        """
        <script>
            const savedUser = localStorage.getItem("isc2_cc_session_user");
            const savedAdmin = localStorage.getItem("isc2_cc_session_admin");
            if (savedUser && savedAdmin) {
                window.parent.postMessage({
                    type: "streamlit:setComponentValue",
                    value: JSON.stringify({username: savedUser, is_admin: savedAdmin === "true"})
                }, "*");
            }
        </script>
        """,
        height=0
    )
    
    if storage_bridge:
        try:
            stored_data = json.loads(storage_bridge)
            st.session_state.is_admin = stored_data["is_admin"]
            st.session_state.authenticated_user = stored_data["username"]
            st.rerun()
        except Exception:
            pass

init_browser_session_sync()

if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "current_exam" not in st.session_state:
    st.session_state.current_exam = None
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "user_confidence" not in st.session_state:
    st.session_state.user_confidence = {}
if "exam_end_timestamp" not in st.session_state:
    st.session_state.exam_end_timestamp = None
if "session_active" not in st.session_state:
    st.session_state.session_active = False
if "selected_count" not in st.session_state:
    st.session_state.selected_count = 20
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = None

st.markdown("""
    <style>
    .isc2-header { color: #15803d; font-weight: 800; font-size: 2.6rem; text-align: center; margin-bottom: 0.2rem; }
    .isc2-subheader { color: #475569; font-size: 1rem; text-align: center; font-weight: 600; margin-bottom: 2rem; letter-spacing: 1px; }
    .card { background-color: #ffffff; padding: 1.8rem; border-radius: 8px; border-top: 5px solid #15803d; box-shadow: 0 4px 10px rgba(0,0,0,0.06); color: #1e293b; margin-bottom: 1rem; }
    .ai-box { background-color: #f8fafc; padding: 1.5rem; border-radius: 8px; border-left: 5px solid #0284c7; box-shadow: 0 2px 8px rgba(0,0,0,0.04); color: #0f172a; }
    .login-box { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); border-top: 6px solid #15803d; max-width: 650px; margin: 0 auto; }
    .dashboard-box { background: white; padding: 2.5rem; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.05); border-top: 6px solid #15803d; max-width: 800px; margin: 2rem auto; }
    .timer-critical { background-color: #fef2f2; border: 1px solid #fee2e2; color: #dc2626; padding: 1rem; border-radius: 8px; font-weight: 800; text-align: center; font-size: 1.3rem; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 4. AUTHENTICATION HUB (SIGN IN / SIGN UP / RESET)
# =====================================================================
if st.session_state.authenticated_user is None:
    st.markdown("<div class='isc2-header'>🛡️ (ISC)² CC Portal Core</div>", unsafe_allow_html=True)
    st.markdown("<div class='isc2-subheader'>Official Certified in Cybersecurity Training Sandbox</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    
    auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Sign In", "📝 Create Account", "🔄 Reset Password"])
    
    # ---- TAB 1: USER LOGIN ----
    with auth_tab1:
        st.markdown("### Profile Authentication Entry")
        login_user = st.text_input("Username Identifier:", key="login_u_box").strip().upper()
        login_pass = st.text_input("Access Password:", type="password", key="login_p_box")
        
        if st.button("🔑 Access System Dashboard", use_container_width=True, key="btn_signin"):
            if not login_user or not login_pass:
                st.error("Please enter both parameters to authenticate access nodes.")
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT password_hash FROM user_registry WHERE username = ?", (login_user,))
                row = cursor.fetchone()
                conn.close()
                
                if row and row[0] == hash_password(login_pass):
                    is_admin_flag = verify_is_admin(login_user)
                    resolved_user = "PLATFORM_ADMIN" if is_admin_flag else login_user
                    
                    # Inject JavaScript to save configuration strings to browser local storage
                    components.html(
                        f"""
                        <script>
                            localStorage.setItem("isc2_cc_session_user", "{resolved_user}");
                            localStorage.setItem("isc2_cc_session_admin", "{str(is_admin_flag).lower()}");
                            window.parent.location.reload();
                        </script>
                        """,
                        height=0
                    )
                    
                    st.session_state.is_admin = is_admin_flag
                    st.session_state.authenticated_user = resolved_user
                    st.rerun()
                else:
                    st.error("Access verification handshake dropped: Invalid Credentials.")

    # ---- TAB 2: REGISTRATION & PROTECTIONS ----
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
                st.error("All configuration identity fields must be fully populated.")
            elif input_user_hash == current_target_hash or reg_user == "SUPER_SECRET_ADMIN_PORTAL":
                st.error("Operation Denied: This administrative identity string namespace is reserved exclusively.")
            elif "@" not in reg_email or "." not in reg_email:
                st.error("Please provide a syntactically valid email address structure.")
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM user_registry WHERE username = ?", (reg_user,))
                if cursor.fetchone():
                    st.error("Identity conflict detected. This username key has already been issued.")
                    conn.close()
                else:
                    cursor.execute("""
                        INSERT INTO user_registry (username, candidate_email, password_hash, recovery_question, recovery_answer_hash)
                        VALUES (?, ?, ?, ?, ?)
                    """, (reg_user, reg_email, hash_password(reg_pass), recovery_q, hash_password(recovery_a)))
                    conn.commit()
                    conn.close()
                    
                    welcome_html = f"""
                    <div style="font-family: Arial, sans-serif; border-top: 5px solid #15803d; padding: 20px;">
                        <h2 style="color: #15803d;">🛡️ (ISC)² CC Training Simulator</h2>
                        <p>Hello <strong>{reg_user}</strong>,</p>
                        <p>Your portal sandbox profile account is now active. Welcome to our testing ecosystem!</p>
                        <p>Keep an eye on this inbox for future security updates and system masterclass announcements.</p>
                    </div>
                    """
                    send_smtp_email(reg_email, "Account Activated - (ISC)2 Engine Sandbox", welcome_html)
                    st.success(f"✨ Registration Completed! Welcome to the portal as {reg_user}.")

    # ---- TAB 3: SELF-SERVICE RESET (QUESTION GATED ONLY) ----
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
                        st.error("Both the security challenge answer and your new password entry must be filled out.")
                    else:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute("SELECT recovery_answer_hash FROM user_registry WHERE username = ?", (reset_user,))
                        true_answer_hash = cursor.fetchone()[0]
                        
                        if true_answer_hash == hash_password(answer_attempt):
                            cursor.execute("UPDATE user_registry SET password_hash = ? WHERE username = ?", (hash_password(new_pass_entry), reset_user))
                            conn.commit()
                            conn.close()
                            
                            alert_html = f"""
                            <div style="font-family: Arial, sans-serif; border-top: 5px solid #eab308; padding: 20px;">
                                <h3 style="color: #854d0e;">⚠️ Security Matrix Account Notice</h3>
                                <p>Hello <strong>{reset_user}</strong>,</p>
                                <p>The access credentials tied to your sandbox profile were successfully modified via Security Question Validation.</p>
                                <p>If you did not execute this parameters shift, please escalate immediately to system network ops.</p>
                            </div>
                            """
                            send_smtp_email(registered_email, "Security Alert: Passcode Modified", alert_html)
                            st.success("🔒 Security details updated successfully on-screen! You can now toggle to 'Sign In'.")
                        else:
                            st.error("Verification failure. Security challenge response mismatch.")
                            conn.close()
            else:
                st.error("The specified profile string target does not exist in our active directories.")
                
    st.markdown("</div>", unsafe_allow_html=True)

else:
    # =====================================================================
    # 5. POST-AUTHENTICATION ENVIRONMENT (SIDEBAR & ROOT DATA)
    # =====================================================================
    current_user = st.session_state.authenticated_user
    is_admin_session = st.session_state.is_admin
    
    st.sidebar.title(f"👤 Node: {current_user}")
    if st.session_state.session_active:
        st.sidebar.markdown(f"Environment: **{st.session_state.selected_mode}**")
        st.sidebar.markdown(f"Allocation Target: **{st.session_state.selected_count} Items**")
    
    app_mode = st.sidebar.radio("Console Navigation Matrix", ["Run Practice Exam", "Admin Content Manager"])
    
    if st.sidebar.button("Log Out / Exit Portal Context", use_container_width=True):
        # Wipe browser memory cache clean upon explicit exit request
        components.html(
            """
            <script>
                localStorage.removeItem("isc2_cc_session_user");
                localStorage.removeItem("isc2_cc_session_admin");
                window.parent.location.reload();
            </script>
            """,
            height=0
        )
        st.session_state.authenticated_user = None
        st.session_state.is_admin = False
        st.session_state.current_exam = None
        st.session_state.session_active = False
        st.session_state.selected_mode = None
        st.rerun()

    # =====================================================================
    # 6. MANAGEMENT TERMINAL (ADMIN)
    # =====================================================================
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

    # =====================================================================
    # 7. LIVE EXAMINATION ENVIRONMENT & WELCOME DASHBOARD
    # =====================================================================
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
                if st.button("📖 Launch Practice Session lounge", use_container_width=True):
                    st.session_state.selected_count = chosen_q_count
                    st.session_state.selected_mode = "Practice Mode"
                    st.session_state.session_active = True
                    st.rerun()
            with col_dash_e:
                if st.button("⚡ Launch High-Fidelity Examination Sandbox", use_container_width=True):
                    st.session_state.selected_count = chosen_q_count
                    st.session_state.selected_mode = "Exam Mode"
                    st.session_state.session_active = True
                    st.session_state.exam_end_timestamp = time.time() + (chosen_q_count * 62)
                    st.rerun()
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
                    st.rerun()
                else:
                    st.warning("No questions found matching this environment.")
                    st.session_state.session_active = False
            
            else:
                exam = st.session_state.current_exam
                idx = st.session_state.current_index
                mode_setting = st.session_state.selected_mode
                
                if mode_setting == "Exam Mode" and idx < len(exam):
                    @st.fragment(run_every=1.0)
                    def render_active_countdown_clock():
                        time_left = int(st.session_state.exam_end_timestamp - time.time())
                        if time_left <= 0:
                            st.session_state.current_index = len(exam)
                            st.rerun()
                        else:
                            m, s = divmod(time_left, 60)
                            st.markdown(f"<div class='timer-critical'>⏳ TIME REMAINING: {m:02d}:{s:02d}</div>", unsafe_allow_html=True)
                    render_active_countdown_clock()

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
                        
                        if choice:
                            st.session_state.user_answers[idx] = choice

                        st.write("---")
                        
                        saved_conf = st.session_state.user_confidence.get(idx, 0)
                        conf_input = st.slider(
                            "Metrics Assessment Retention Confidence Scale (Must select greater than 0% to proceed):", 
                            0, 100, saved_conf, 5,
                            key=f"confidence_slider_{idx}"
                        )
                        st.session_state.user_confidence[idx] = conf_input
                        st.progress(conf_input / 100)

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
                            st.warning("⚠️ **(ISC)² System Gating Notice:** You must select an answer choice AND adjust the confidence scale above 0% before the system unlocks the next question.")

                    with right_ai_col:
                        st.markdown("### 🤖 Live Gemini Instructor Coach")
                        if mode_setting == "Practice Mode":
                          if choice:
                            st.markdown("<div class='ai-box'>", unsafe_allow_html=True)
                            
                            gemini_analysis_prompt = f"""
                            You are an elite (ISC)² Certified in Cybersecurity (CC) trainer.
                            Analyze this item context. RESPOND IMMEDIATELY AND CONCISELY (max 150 words).
                            Domain: {q['domain']}
                            Question: {q['question_text']}
                            Choices: A: {q['option_a']}, B: {q['option_b']}, C: {q['option_c']}, D: {q['option_d']}
                            Selected Option Key: {choice}
                            Correct Target Key: {q['correct_option']}
                            Syllabus Note: {q['official_rationale']}
                            
                            State right away if correct or incorrect, why, and a 2-sentence domain takeaway.
                            """
                            
                            if ai_client:
                                try:
                                    response_stream = ai_client.models.generate_content_stream(
                                        model='gemini-2.5-flash',
                                        contents=gemini_analysis_prompt
                                    )
                                    st.write_stream(chunk.text for chunk in response_stream)
                                except Exception as e:
                                    st.error(f"Stream generation dropped: {str(e)}")
                            else:
                                st.warning("API key missing from workspace secrets layout configurations.")
                                
                            st.markdown("</div>", unsafe_allow_html=True)
                          else:
                            st.info("💡 *Select an answer choice on the left to activate the Gemini Instructor coaching terminal instantly without lagging or scrolling.*")
                        else:
                            st.caption("🔒 *AI coaching engine deactivated during high-fidelity exam mode simulations.*")
                else:
                    # =====================================================================
                    # 8. GRADING METRICS EVALUATION AUDIT CONSOLE
                    # =====================================================================
                    st.subheader("📊 Session Processing Complete: System Audit Summary")
                    correct_tally = 0
                    for i, q in enumerate(exam):
                        if st.session_state.user_answers.get(i, None) == q['correct_option']:
                            correct_tally += 1
                            
                    final_score = int((correct_tally / len(exam)) * 100) if len(exam) > 0 else 0
                    
                    if final_score >= 70:
                        st.balloons()
                        st.success(f"### Final Metric Result Score: {final_score}% — PROVISIONALLY PASSED")
                    else:
                        st.error(f"### Final Metric Result Score: {final_score}% — DOES NOT CONFORM TO PASSMARK")
                    
                    with st.expander("🔍 Review Detailed Answer Key Logs + AI Explanations"):
                        for i, q in enumerate(exam):
                            u_ans = st.session_state.user_answers.get(i, 'Unanswered')
                            is_correct = u_ans == q['correct_option']
                            status_symbol = "✅" if is_correct else "❌"
                            st.markdown(f"**Question {i+1}: {status_symbol} (Confidence: {st.session_state.user_confidence.get(i, 0)}%)**")
                            st.write(q['question_text'])
                            st.write(f"* Your Choice: **{u_ans}** | Correct Key: **{q['correct_option']}**")
                            st.write("---")

                    if st.button("Return to Dashboard", use_container_width=True):
                        st.session_state.current_exam = None
                        st.session_state.current_index = 0
                        st.session_state.user_answers = {}
                        st.session_state.user_confidence = {}
                        st.session_state.session_active = False
                        st.session_state.selected_mode = None
                        st.rerun()