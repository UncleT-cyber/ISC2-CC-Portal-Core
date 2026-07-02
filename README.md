# 🛡️ (ISC)² CC Portal Core

An advanced training and examination simulator platform engineered with **Python**, **Streamlit**, **SQLite**, and **AWS Bedrock (Meta Llama 3)** to help learners confidently prepare for the **(ISC)² Certified in Cybersecurity (CC)** entry-level certification.

> **🌐 Live Application:** [https://isc2cctrainingcore.streamlit.app/](https://isc2cctrainingcore.streamlit.app/)

---

## ⚠️ Important Disclaimer
**This project is entirely an independent educational practice platform created exclusively for personal learning and candidate skill assessment purposes. It is NOT affiliated with, endorsed by, sponsored by, or officially associated with (ISC)² in any capacity.** *(ISC)² and Certified in Cybersecurity (CC) are registered trademarks of the International Information System Security Certification Consortium, Inc.*

---

## 📋 Overview

**ISC² CC Portal Core** is a multi-tenant cybersecurity training platform designed to accurately simulate a professional certification prep environment. 

Unlike static quiz apps, this architecture combines stateless UI stability patches, secure cryptographic identity storage, custom user question pools, an on-demand cloud-native AI mentor, timed examination sandboxes, and structural confidence auditing matrices into a unified deployment. 

The system leverages a serverless cloud footprint—decommissioning continuous local hardware runtimes (like EC2 or local Ollama instances) by routing API execution dynamically to serverless engines.

---

## ✨ Features

### 🔐 Secure Authentication & RBAC
* **User Identity Integrity:** Irreversible SHA-256 client password hashing.
* **Gated State Navigation:** Secure session-based authentication nodes that block data cross-pollution.
* **Self-Service Recovery:** Challenge questions backed by asynchronous SMTP email alerts (`smtplib`).
* **Role-Based Access Control (RBAC):** Administrative consoles are cryptographically split from standard user storage pools based on secret target hash matching.

### 👤 Personal User Cockpit
Every registered user accesses an isolated workspace providing:
* **Practice Mode:** A low-stakes training loop with immediate, context-aware AI teardowns.
* **Timed Exam Mode:** A high-fidelity sandbox mimicking strict exam constraints.
* **Personal Question Management:** Create, review, and persist custom domain stems directly inside your database folder without touching core source code.
* **Dual-Metric Progress Matrices:** Tracks raw scores alongside explicit confidence percentages (0-100%).

### 👑 Global Administrator Console
Administrative permissions allow authorized nodes to populate the core global database schema. These questions automatically seed into every active testing profile, blending uniformly with the user's private entries while preserving database isolation.

### ⏱️ Timed Examination Mode
* Enforces strict countdown parameters mapped to chosen length intervals via standalone engine fragments.
* **AI Core Nexus Mentor is completely deactivated** to enforce strict testing realities.
* Comprehensive final scorecard auditing reports indicating PASS/FAIL thresholds (70%).

### 🤖 Cloud-Native AI Learning Assistant
During Practice Mode, the platform acts as an active coach using **AWS Bedrock**:
* Explains complex (ISC)² domain rationale stems.
* Teaches why a specific chosen option is correct or incorrect based on official syllabus pillars.
* Delivers sub-millisecond, on-demand query generations directly over the cloud API.

---

## 🔒 Security Architectures
* **Runtime Data Isolation:** Multi-tenant credential protection using Streamlit encrypted cloud Secrets (`st.secrets`).
* **Protected Namespace Routing:** Outright algorithmic lockout of master admin string inputs on public node registration screens.
* **Transport Guardrails:** Enforces Transport Layer Security (TLS) configuration arrays for all outward SMTP mailing activities.

---

## 🛠️ Technology Stack

* **Frontend UI Matrix:** Streamlit (Python-native web framework with HTML5/CSS3 injection)
* **Database Layer:** SQLite3 (Local serverless relational SQL engine)
* **AI Engine Client:** AWS Bedrock SDK (`boto3`) executing **Meta Llama 3 (`meta.llama3-8b-instruct-v1:0`)**
* **Transport Protocols:** SMTP / Python `smtplib` / MIME Standards
* **Cryptography Unit:** Python `hashlib` (SHA-256 configuration)

---

## 📂 Project Structure

```text
ISC2-CC-Portal-Core/
│
├── app.py                     # Main application engine & logic loop
├── session_manager.py         # JavaScript local storage persistence bridge
├── requirements.txt           # Cloud-native dependency manifest
├── .gitignore                 # Active production directory ignore maps
├── README.md                  # Comprehensive technical documentation
├── questions.json             # Core structural query templates
├── cc_prep.json               # Modular reference arrays
├── isc2_simulator.db          # Active SQLite local relational database
│
└── .streamlit/
    └── secrets.toml           # Local API keys and configurations (Git-ignored)
⚙️ Local Installation & Configuration
1. Clone the Repository
Bash
git clone [https://github.com/UncleT-cyber/ISC2-CC-Portal-Core.git](https://github.com/UncleT-cyber/ISC2-CC-Portal-Core.git)
cd ISC2-CC-Portal-Core
2. Install Dependencies
Bash
pip install -r requirements.txt
3. Configure Local Environmental Secrets
Create a .streamlit/secrets.toml file manually in your root workspace folder. Add the administrative keys, your email SMTP relay properties, and your AWS programmatic keys:

Ini, TOML
ADMIN_HASH_TARGET = "64b7bd3b82736b009e992764f1e967a57fa85bd486a4387d85ef66bb8b6639c4"

[smtp]
SERVER = "smtp.gmail.com"
PORT = 587
USERNAME = "your-distribution-profile@gmail.com"
PASSWORD = "your-secure-app-password"
SENDER_EMAIL = "your-distribution-profile@gmail.com"

[aws]
AWS_ACCESS_KEY_ID = "AKIAIOSXXXXXXEXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPXXXXXXEXAMPLEKEY"
AWS_DEFAULT_REGION = "us-east-1"
⚠️ Note for Production Security: The AWS keys shown above are example templates. In production deployment, real credentials should be placed exclusively inside the Streamlit Cloud Dashboard Secrets field. Never commit actual AWS tokens to public GitHub source repositories.

4. Boot the Framework
Bash
streamlit run app.py
🎓 Verified (ISC)² Exam Domain Alignment
The simulation matrix weights and distributes evaluation strings dynamically across the five core syllabus vectors:

Domain 1: Security Principles

Domain 2: Business Continuity (BC), Disaster Recovery (DR) & Incident Response Concepts

Domain 3: Access Controls Concepts

Domain 4: Network Security

Domain 5: Security Operations

🤝 Contributing
Contributions are welcome! If you have ideas for improving the simulator, resolving performance anomalies, or expanding syllabus functionality:

Fork the repository.

Create your feature branch (git checkout -b feature/AmazingFeature).

Commit your modifications (git commit -m 'Add some AmazingFeature').

Push to the branch (git push origin feature/AmazingFeature).

Open a Pull Request.

👤 Author
Anthony Abah
Cybersecurity Student • Python Developer • Web Systems Enthusiast
🌐 GitHub: https://github.com/UncleT-cyber

📄 License
Distributed under the MIT License. See LICENSE for more information.

Copyright (c) 2026 Anthony Abah
