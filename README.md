# 🛡️ ISC² CC Portal Core

An advanced training and examination platform built with **Python**, **Streamlit**, **SQLite**, and **Google Gemini AI** to help learners prepare for the **ISC² Certified in Cybersecurity (CC)** certification.

> **🌐 Live Application:** [https://isc2cctrainingcore.streamlit.app/](https://isc2cctrainingcore.streamlit.app/)

---

## 📋 Overview

**ISC² CC Portal Core** is a complete cybersecurity training platform designed to simulate a realistic certification preparation environment.

Unlike traditional quiz applications, the platform combines secure authentication, role-based administration, customizable question banks, AI-assisted tutoring, timed examinations, confidence tracking, and performance evaluation into a single application.

The system was built to be extensible, allowing both learners and administrators to continuously expand the available question database without modifying the application source code.

---

## ✨ Features

### 🔐 Secure Authentication
* **User Registration & Integrity:** Secure SHA-256 password hashing.
* **Gated Access:** Login authentication with stateful tracking.
* **Self-Service Recovery:** Password recovery using security questions.
* **Transactional Mail:** Automated SMTP email notifications.
* **Session Protections:** Strict session-based authentication nodes.

### 👤 Personal User Dashboard
Every registered user has access to a customized cockpit featuring:
* **Practice Mode:** Low-stakes training sandbox with immediate feedback.
* **Timed Exam Mode:** High-fidelity simulation mimicking actual exam constraints.
* **Personal Question Bank:** Tracking for custom domain content.
* **AI Tutor:** Instant integration with real-time feedback loops.
* **Performance Summary:** Breakdown of scored categories.
* **Confidence Tracking:** Dual-metric analytical progression metadata.

### 📝 Personal Question Management
Each user can create and maintain their own private examination database. Users can explicitly define:
* Question Stem Text
* Options Structure (A, B, C, D)
* Correct Answer Designation
* Official Rationale Context

These questions are stored privately and automatically become part of that specific user's future practice sessions and examinations.

### 👑 Global Administrator Console
The platform includes a secure administrator role decoupled from source control. Administrator capabilities include:
* Publish global questions to the core schema.
* Create shared examination content arrays.
* Manage the platform-wide question repository.

*Global questions are automatically available to every registered user while preserving each user's personal question bank.*

### 📚 Hybrid Question Engine
Each examination session intelligently combines:
* Global administrator questions.
* User-created private questions.

Questions are uniquely shuffled before every session, ensuring an organic, non-repeating examination experience.

### 🎯 Practice Mode
Practice Mode provides immediate learning support:
* Instant answer validation loops.
* Display of official rationale metadata.
* Context-aware AI explanations via dynamic processing.
* Domain-focused learning categorization.
* Dynamic confidence tracking metrics.

### ⏱️ Timed Examination Mode
Exam Mode simulates a strict, production-level certification environment:
* Real-time breakdown countdown timer via standalone fragments.
* AI Instructor coaching completely disabled.
* Randomized pool selection routines.
* Automatic schema grading mechanics.
* Comprehensive final scorecard reports.

### 🤖 Gemini AI Learning Assistant
During Practice Mode, Google Gemini acts as an on-demand coach:
* Concept definitions and modular breakdowns.
* Option choice reasoning.
* Domain reinforcement exercises.
* Cybersecurity exam-prep tutoring.

This transforms the simulator from a static testing bank into an interactive learning framework.

### 📊 Confidence Tracking
Each submitted answer records the learner's self-assessed confidence level, storing:
* Selected answer choices.
* Confidence percentages (0-100%).
* Final scoring matrices.

This empowers learners to identify systemic gaps and topics requiring additional target study.

### 📧 Email Notifications
SMTP integration supports:
* Multi-styled onboarding welcome emails.
* Password reset alerts and access changes.
* System security modification notices.

---

## 🔒 Security Features

* **Cryptographic Identity Protection:** Full SHA-256 password hashing.
* **Decoupled Architecture:** Configurable administrator identity targets.
* **Runtime Isolation:** Secure Streamlit Secrets (`st.secrets`) engine deployment.
* **Secure SMTP Gating:** Transport Layer Security (TLS) configuration arrays.
* **Session Isolation:** Robust state constraints preventing data cross-pollution.
* **Protected Namespace:** Algorithmic lockout of the master admin username string on public nodes.
* **Role-Based Access Control (RBAC):** True database-level permission separation.

---

## 🛠️ Technology Stack

* **Frontend/UI:** Streamlit (Python-native web application framework)
* **Database Relational Layer:** SQLite3 (Serverless SQL relational database)
* **AI Engine Client:** Google GenAI SDK (`gemini-2.5-flash`)
* **Transport Protocols:** SMTP / Python `smtplib` / MIME Standards
* **Cryptography Unit:** Python `hashlib` (SHA-256 implementation)
* **State Engines:** Streamlit Session State & Component Fragments
* **Interface Modifiers:** HTML5 / CSS3 injection styling

---

## 📂 Project Structure

```text
ISC2-CC-Portal-Core/
│
├── app.py                     # Main application script & logic
├── requirements.txt           # Live platform dependency manifests
├── .gitignore                 # Production ignore maps
├── README.md                  # Comprehensive portfolio documentation
├── questions.json             # Core structural query templates
├── cc_prep.json               # Modular reference arrays
├── isc2_simulator.db          # Active SQLite local relational database
│
├── .streamlit/
│   └── secrets.toml           # Local API keys and configurations (Git-ignored)
│
└── templates/                 # Auxiliary structural UI wrappers
⚙️ Local Installation & Configuration
1. Clone the Repository
Bash
git clone [https://github.com/UncleT-cyber/ISC2-CC-Portal-Core.git](https://github.com/UncleT-cyber/ISC2-CC-Portal-Core.git)
cd ISC2-CC-Portal-Core
2. Install Dependencies
Bash
pip install -r requirements.txt
3. Configure Local Environmental Secrets
Sensitive credentials are intentionally separated from the source code. The .streamlit/secrets.toml file is ignored by Git and must be created manually in your root workspace directory before starting the application.

Create .streamlit/secrets.toml and populate it with your local properties:

Ini, TOML
GEMINI_API_KEY = "your-gemini-api-key"

# Optional administrator override
# Replace with the SHA-256 hash of your preferred admin username.
# If omitted, the application uses its built-in fallback administrator hash.
ADMIN_HASH_TARGET = "your-admin-username-sha256-hash"

[smtp]
SERVER = "smtp.resend.com"
PORT = 587
USERNAME = "resend"
PASSWORD = "your-resend-api-key"
SENDER_EMAIL = "your_verified_sender@example.com"
4. Run the Application
Bash
streamlit run app.py
🔑 Administrator Identity Configuration
The application natively supports custom administrator configurations without altering a single line of core Python code.

Default Behavior
If ADMIN_HASH_TARGET is omitted from your local secrets.toml, the application defaults to an internal cryptographic fallback hash string. The corresponding administrative namespace is completely protected and blocked from standard creation through the public registration interface.

Creating Your Custom Administrator Identity
Developers running their own local copy can easily mount an alternate master administrator account:

Pick an arbitrary admin username string (e.g., MY_DEV_ADMIN).

Generate its corresponding SHA-256 hash.

Map that hash inside your local .streamlit/secrets.toml file:

Ini, TOML
ADMIN_HASH_TARGET = "your-generated-sha256-hash"
Start the application framework.

Head to the Create Account page and register that exact username.

Login normally. The pipeline instantly identifies the hash parity and assigns your account full administrative privileges.

📸 Screenshots
Login & Registration Interface: <img width="1270" height="835" alt="image" src="https://github.com/user-attachments/assets/fbbfc8d5-524b-410c-b8b8-1944dfa8d908" />
User Dashboard Cockpit: <img width="1279" height="851" alt="image" src="https://github.com/user-attachments/assets/7be21b2e-a562-4c63-b1f0-33ccef682cad" />
🗺️ Future Roadmap
Planned structural improvements include:

Multi-tiered Logic: Multi-tiered question difficulty logic configurations.

Domain Analytics: Granular domain-by-domain proficiency metrics analytics.

Performance Cockpits: Centralized student visual performance metrics dashboards.

Gamification Elements: Competitive interactive learning leaderboards.

Reporting Services: On-demand PDF examination certificate summary generation.

Data Integration Arrays: Bulk CSV question schema dataset import/export tools.

Database Infrastructure Scale: Enterprise PostgreSQL cloud database support.

Advanced Access Protection: Multi-Factor Authentication (MFA) sign-in security flows.

Taxonomy Frameworks: Dynamic question taxonomy and hashtag index mapping.

Rich Context Testing: Rich multimedia/image-based scenario questions.

Enterprise Supervision: Dedicated instructor tracking portals and analytical panels.

🤝 Contributing
Contributions are welcome! If you have ideas for improving the simulator, resolving performance anomalies, or expanding syllabus functionality:

Fork the repository.

Create your feature branch (git checkout -b feature/AmazingFeature).

Commit your modifications (git commit -m 'Add some AmazingFeature').

Push to the branch (git push origin feature/AmazingFeature).

Open a Pull Request.

⚠️ Disclaimer
This project is an independent educational practice platform created exclusively for learning and candidate skill assessment purposes. It is not affiliated with, endorsed by, sponsored by, or officially associated with ISC².

ISC² and Certified in Cybersecurity (CC) are registered trademarks of ISC².

👤 Author
Anthony Abah

Cybersecurity Student • Python Developer • Web Systems Enthusiast

🌐 GitHub: https://github.com/UncleT-cyber

📄 License
Distributed under the MIT License. See LICENSE for more information.

Copyright (c) 2026 Anthony Abah
