# EduInsights for EMW — Educational Intelligence Platform

A runnable Streamlit analytics application branded for **EMW (Edutainal Maverick World)**. It brings learner, attendance, course, mentor-capacity, finance and feedback analytics into one demonstration workspace.

> **Important:** The included data is synthetic and generated for demonstration. It is not EMW's actual student, staff, customer, attendance, feedback or financial data. The app is a prototype, not a production student-information system. Do not enter identifiable information about children.

## Why this project fits the brand

The EMW brand artwork supplied for this project presents future-ready learning domains such as Robotics, Coding & AI, Space Science, Biotechnology, Agritech, Marine Tech, Automobile Tech, Fabrication and Civil & Infrastructure Tech, and emphasizes hands-on learning, real-world projects and expert mentors. The dashboard uses those domains as its sample course taxonomy and adopts the supplied navy, cyan and yellow visual identity.

The internship certificate image in the user's materials identifies the host organization as **Edutainal Ventures** and describes internship activities across computer science and robotics-based curriculum development, website/app development, digital marketing and mentoring young learners. The application is therefore framed as an educational-operations analytics prototype for the EMW learning brand; it does not claim the user was assigned a particular internal EMW analytics project.

## Features

- Executive overview with enrollment, attendance, revenue and learner-support indicators.
- Student analytics with age/domain filters, outcomes, engagement and CSV export.
- Attendance monitoring and a sample logistic-regression support-signal model.
- Mentor workload and aggregate feedback insights.
- Course/domain enrollment and outcome comparisons.
- Fee collection and payment trend charts using fictional values.
- Feedback sentiment demonstration using transparent keyword rules.
- SQLite database created from the included CSV tables.
- Sign-up screen with validated registration, persistent local accounts, analyst/student/parent account types and optional learner-ID linking.
- Modern grouped sidebar navigation with active-page highlighting.
- AI-assisted, explainable support suggestions based on simple rules; not a validated predictive model.
- Notifications centre for attendance, learning-support and pending-fee review items; notifications are in-app only.
- Read-only parent/student portal for a linked synthetic learner record.
- Multi-sheet Excel export and PDF institutional summary report.
- Data Entry workspace with forms for learners, feedback, faculty, courses and payments; entries are saved to local CSV files.
- EMW logo artwork extracted from the supplied booth design reference.

## Authentication and roles

The local demo includes two convenience accounts so the app can be explored immediately. New accounts can also be created using the **Create account** tab. Registrants may choose Analyst, Student or Parent; Student/Parent accounts must provide a learner ID. Admin privileges are never self-assigned:

| Role | Username | Demo password |
|---|---|---|
| Administrator | `emwadmin` | `EMW-Demo-2026!` |
| Analyst | `analyst` | `Analyst-Demo-2026!` |

These are **public demo credentials, not secure production credentials**. Change them before any shared deployment. The administrator sees the Admin Console. Student/Parent accounts see a read-only portal for their linked learner ID. This prototype does not implement verified guardianship, institutional approval, or production-grade privacy controls.

For Streamlit deployment, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, generate unique SHA-256 password hashes, and add the values through the hosting provider's secrets manager. Never commit `secrets.toml`. Example hash command:

```bash
python -c "import hashlib; print(hashlib.sha256(b'YOUR_STRONG_PASSWORD').hexdigest())"
```

New local registrations are stored in the SQLite `user_accounts` table using PBKDF2-SHA256 password hashes. The two built-in demo accounts remain SHA-256 compatibility examples. The login layer is still a prototype access gate, not a substitute for enterprise identity, verified parent-child relationships, account approval, rate limiting, session controls, HTTPS, audit logging or a security review. The Data Entry page appends records to local CSVs; back up the `data/` folder before editing.

## Run locally

Install Python 3.10 or newer and open a terminal in the extracted project folder.

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

**macOS or Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Open http://localhost:8501. Sign in as Administrator to explore every page, or register a Student or Parent account with the sample learner ID `EMW-0001`. Student and Parent accounts open directly to their linked learner's read-only portal.

## Deployment

### Streamlit Community Cloud
1. Push this folder to a private GitHub repository after removing any local secrets or database files.
2. Create a Streamlit Community Cloud app pointing to `app.py`.
3. Add the `[users.<username>]` entries from `.streamlit/secrets.toml.example` in the app's Secrets settings, using unique password hashes and roles (`admin` or `analyst`).
4. Deploy and verify access using separate admin and analyst accounts.

### Docker
A `Dockerfile` is included. Build and run with:

```bash
docker build -t eduinsights-emw .
docker run --rm -p 8501:8501 eduinsights-emw
```

Supply production credentials through a secure secrets mechanism; do not bake them into the image. Persist the SQLite database only if you deliberately configure a persistent volume and review the data lifecycle.

## Project structure

```text
eduinsights_emw/
├── app.py                  # Streamlit application and dashboard pages
├── generate_data.py        # Rebuilds the synthetic sample data
├── requirements.txt
├── README.md
├── assets/
│   └── emw_logo.png        # Logo crop from supplied EMW brand artwork
├── data/
│   ├── students.csv
│   ├── courses.csv
│   ├── faculty.csv
│   ├── payments.csv
│   └── feedback.csv
└── EMW_2_0_RELEASE_NOTES.md
```

## Data and model notes

- `generate_data.py` creates reproducible synthetic data with a fixed random seed.
- The risk model is trained on synthetic records and reports a holdout accuracy and ROC-AUC for educational demonstration only. It is not validated for real-world prediction.
- A support flag is a prompt to review context and offer help, never a label to deny access or penalize a learner.
- Faculty metrics are aggregate planning indicators, not employee ratings.
- Finance data is fictional and must not be used for accounting.
- The feedback classifier is a simple keyword baseline, not a trained language model. AI-assisted recommendations are transparent threshold-based suggestions and must be reviewed by a mentor. Notifications are generated in-app only; no email, SMS or push messages are sent. PDF/Excel reports contain demo data and should not be treated as official institutional records.

## Production hardening checklist

Before any real deployment: obtain written authorization from EMW; confirm the official data dictionary and logo usage; replace demo data with approved, minimized data; add role-based access control and strong authentication; encrypt data in transit and at rest; define retention/deletion rules; add audit logging; validate accessibility; review applicable child-data/privacy requirements; add backups and monitoring; independently validate models for bias and reliability; and obtain human review for all interventions. Do not upload children's personal data to an unapproved service.

## Brand assets and source note

The EMW mark in `assets/emw_logo.png` is cropped from the EMW exhibition-stall artwork present in the user's ChatGPT Library. It is included as a visual brand reference, not represented as a vector master or official brand-kit file. The broader company/internship context is reflected in the report; contact details and certificate signatures are intentionally not copied into the app.


## EMW 2.1 UI refresh
- Refined light dashboard canvas with a deep-navy EMW sidebar and cyan/gold brand accents.
- Improved page hierarchy, typography, navigation states, KPI cards, charts, tables, forms and buttons.
- Updated Plotly chart styling for the light dashboard theme.
- Runs locally with Streamlit; start using `streamlit run app.py`.
