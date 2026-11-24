from pathlib import Path
import sqlite3
import io
from datetime import date
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
DB = ROOT / 'eduinsights.db'
NAVY = '#071A33'
CYAN = '#00B9E8'
YELLOW = '#FFC928'
WHITE = '#F5F8FC'

st.set_page_config(page_title='EduInsights | EMW', page_icon='🚀', layout='wide', initial_sidebar_state='expanded')
st.markdown(f'''<style>
:root {{ --navy:{NAVY}; --cyan:{CYAN}; --gold:{YELLOW}; }}
.stApp {{ background:#F3F6FA; color:#14263D; }}
[data-testid="stHeader"] {{ background:rgba(243,246,250,.92); }}
[data-testid="stSidebar"] {{ background:linear-gradient(180deg,#071A33 0%,#0A2745 100%); border-right:1px solid #163B5C; }}
[data-testid="stSidebar"] * {{ color:#EAF4FC; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color:#A9C2D8 !important; }}
[data-testid="stSidebar"] hr {{ border-color:#244665; }}
section[data-testid="stMain"] .block-container {{ max-width:1500px; padding-top:1.8rem; padding-bottom:3rem; }}
[data-testid="stMetric"] {{ background:#FFFFFF; border:1px solid #E2EAF2; padding:18px 20px; border-radius:16px; box-shadow:0 5px 18px rgba(18,43,70,.055); }}
[data-testid="stMetricLabel"] p {{ color:#64758B !important; font-size:.84rem; font-weight:650; }}
[data-testid="stMetricValue"] {{ color:#0B2947 !important; font-weight:750; }}
[data-testid="stMetricDelta"] {{ font-size:.8rem; }}
[data-testid="stVerticalBlock"] > div:has(> [data-testid="stPlotlyChart"]) {{ background:#FFFFFF; border:1px solid #E4EBF2; border-radius:16px; padding:12px 12px 4px; box-shadow:0 5px 18px rgba(18,43,70,.04); }}
[data-testid="stDataFrame"], [data-testid="stTable"] {{ border:1px solid #E2EAF2; border-radius:12px; overflow:hidden; }}
.stTabs [data-baseweb="tab-list"] {{ gap:8px; }}
.stTabs [data-baseweb="tab"] {{ background:#E9EFF6; border-radius:10px 10px 0 0; padding:10px 16px; color:#29445F; }}
.stTabs [aria-selected="true"] {{ background:#FFFFFF !important; color:#087FA6 !important; border-bottom:3px solid #00B9E8; }}
.stTextInput input, .stTextArea textarea, .stNumberInput input {{ border-radius:10px; }}
.stSelectbox [data-baseweb="select"] > div, .stMultiSelect [data-baseweb="select"] > div {{ border-radius:10px; }}
div.stButton>button, div.stDownloadButton>button, button[kind="primaryFormSubmit"] {{ border-radius:10px; border:1px solid #0B86AC; font-weight:650; min-height:2.55rem; }}
button[kind="primary"], button[kind="primaryFormSubmit"] {{ background:linear-gradient(100deg,#087FA6,#075777); color:white; }}
.hero {{ background:linear-gradient(112deg,#071A33 0%,#0B3554 62%,#087FA6 100%); border:1px solid #164D70; padding:26px 30px; border-radius:20px; margin-bottom:22px; box-shadow:0 12px 28px rgba(7,26,51,.12); position:relative; overflow:hidden; }}
.hero:after {{ content:''; position:absolute; width:210px; height:210px; right:-55px; top:-95px; border:1px solid rgba(255,255,255,.12); border-radius:50%; box-shadow:0 0 0 24px rgba(255,255,255,.035),0 0 0 48px rgba(255,255,255,.025); }}
.hero h1 {{ margin:0; color:white; font-size:2rem; font-weight:800; letter-spacing:-.035em; }}
.hero p {{ margin:7px 0 0 0; color:#C3DCEB; font-size:.98rem; }}
.nav-group {{ color:#71D6F1; font-size:.69rem; font-weight:800; letter-spacing:.14em; margin:19px 0 8px 3px; }}
[data-testid='stSidebar'] div.stButton > button {{ text-align:left; min-height:2.55rem; border-radius:10px; font-weight:580; background:rgba(255,255,255,.035); border:1px solid rgba(255,255,255,.055); }}
[data-testid='stSidebar'] div.stButton > button:hover {{ background:rgba(0,185,232,.15); border-color:#1685AC; }}
[data-testid='stSidebar'] div.stButton > button[kind='primary'] {{ background:linear-gradient(90deg,#087FA6,#07506F); border:1px solid #27C7EE; color:white; box-shadow:0 5px 18px rgba(0,0,0,.18); }}
h1,h2,h3,h4 {{ color:#102D4A; letter-spacing:-.02em; }}
[data-testid="stAlert"] {{ border-radius:12px; }}
.small-muted {{ color:#64758B; font-size:.9rem; }}
</style>''', unsafe_allow_html=True)


# --- Authentication and self-service registration ---
import hashlib
import hmac
import secrets

def _password_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def _new_password_hash(value: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt.encode(), 180000).hex()
    return f"pbkdf2${salt}${digest}"

def _verify_password(password: str, stored: str) -> bool:
    if stored.startswith("pbkdf2$"):
        _, salt, digest = stored.split("$", 2)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode(), 180000).hex()
        return hmac.compare_digest(candidate, digest)
    return hmac.compare_digest(_password_hash(password), stored)

def _auth_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS user_accounts (
            username TEXT PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
            phone TEXT, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'analyst',
            linked_student_id TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        columns = {row[1] for row in conn.execute("PRAGMA table_info(user_accounts)")}
        if "linked_student_id" not in columns:
            conn.execute("ALTER TABLE user_accounts ADD COLUMN linked_student_id TEXT")

def _preset_users():
    users = {
        "emwadmin": {"password_hash": _password_hash("EMW-Demo-2026!"), "role": "admin",
                     "full_name": "EMW Administrator", "email": "admin@emw-demo.local"},
        "analyst": {"password_hash": _password_hash("Analyst-Demo-2026!"), "role": "analyst",
                    "full_name": "Demo Analyst", "email": "analyst@emw-demo.local"},
    }
    try:
        for username, item in st.secrets.get("users", {}).items():
            users[str(username)] = {"password_hash": str(item["password_hash"]),
                                    "role": str(item.get("role", "analyst")).lower(),
                                    "full_name": str(item.get("full_name", username)),
                                    "email": str(item.get("email", ""))}
    except Exception:
        pass
    return users

def _configured_users():
    users = _preset_users()
    _auth_db()
    with sqlite3.connect(DB) as conn:
        for row in conn.execute("SELECT username,full_name,email,phone,password_hash,role,linked_student_id FROM user_accounts"):
            users.setdefault(row[0], {"full_name": row[1], "email": row[2], "phone": row[3],
                             "password_hash": row[4], "role": row[5], "linked_student_id": row[6]})
    return users

def login_screen():
    left, center, right = st.columns([1, 1.25, 1])
    with center:
        logo = ROOT / "assets" / "emw_logo.png"
        if logo.exists():
            st.image(str(logo), use_container_width=True)
        st.markdown('<div class="hero"><h1>EduInsights <span style="color:#FFC928">/</span> EMW</h1><p>Educational intelligence. Clearer decisions. Better learning experiences.</p></div>', unsafe_allow_html=True)
        tab_login, tab_signup = st.tabs(["Sign in", "Create account"])
        with tab_login:
            st.markdown("### Welcome back")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")
            if submitted:
                record = _configured_users().get(username.strip())
                if record and _verify_password(password, record["password_hash"]):
                    st.session_state.update(authenticated=True, username=username.strip(),
                                            role=record["role"] if record["role"] in ("admin","analyst","student","parent") else "analyst",
                                            full_name=record.get("full_name", username.strip()),
                                            linked_student_id=record.get("linked_student_id"))
                    st.rerun()
                else:
                    st.error("The username or password is incorrect.")
        with tab_signup:
            st.markdown("### Create your workspace account")
            st.caption("Choose Analyst, Student or Parent. Student and Parent accounts require a demo learner ID.")
            with st.form("signup_form"):
                full_name = st.text_input("Full name")
                email = st.text_input("Email address")
                phone = st.text_input("Phone number (optional)")
                new_username = st.text_input("Choose a username")
                account_role = st.selectbox("Account type", ["Analyst", "Student", "Parent"])
                linked_student_id = st.text_input("Learner ID (required for Student/Parent)", placeholder="e.g. EMW-0001")
                new_password = st.text_input("Create password", type="password")
                confirm_password = st.text_input("Confirm password", type="password")
                accepted = st.checkbox("I understand this is a demonstration workspace and will not enter sensitive child data.")
                create = st.form_submit_button("Create account", use_container_width=True, type="primary")
            if create:
                if not all([full_name.strip(), email.strip(), new_username.strip(), new_password]):
                    st.error("Please complete all required fields.")
                elif "@" not in email or "." not in email.rsplit("@",1)[-1]:
                    st.error("Enter a valid email address.")
                elif len(new_username.strip()) < 3 or not new_username.strip().replace("_","").isalnum():
                    st.error("Username must be at least 3 characters and contain only letters, numbers or underscores.")
                elif new_username.strip().casefold() in {name.casefold() for name in _preset_users()}:
                    st.error("That username is reserved.")
                elif account_role in ("Student", "Parent") and linked_student_id.strip() not in set(pd.read_csv(DATA / "students.csv", usecols=["student_id"]).student_id.astype(str)):
                    st.error("Enter an existing demo learner ID.")
                elif len(new_password) < 8:
                    st.error("Use a password with at least 8 characters.")
                elif new_password != confirm_password:
                    st.error("The passwords do not match.")
                elif not accepted:
                    st.error("Please accept the demonstration-workspace notice.")
                else:
                    try:
                        _auth_db()
                        with sqlite3.connect(DB) as conn:
                            conn.execute("INSERT INTO user_accounts(username,full_name,email,phone,password_hash,role,linked_student_id) VALUES(?,?,?,?,?,?,?)",
                                         (new_username.strip(),full_name.strip(),email.strip().lower(),phone.strip(),
                                          _new_password_hash(new_password),account_role.lower(),linked_student_id.strip() if account_role in ("Student", "Parent") else None))
                        st.success("Account created. Switch to Sign in and log in with your new credentials.")
                    except sqlite3.IntegrityError:
                        st.error("That username or email is already registered.")
        st.caption("Authorized demonstration workspace · Do not use real learner or financial data.")

if not st.session_state.get("authenticated", False):
    login_screen()
    st.stop()


@st.cache_data
def load_data():
    return {name:pd.read_csv(DATA/f'{name}.csv') for name in ['students','courses','faculty','payments','feedback']}

def init_db(data):
    with sqlite3.connect(DB) as conn:
        for name, frame in data.items():
            frame.to_sql(name, conn, if_exists='replace', index=False)
        conn.execute('CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT)')
        conn.execute("INSERT OR REPLACE INTO app_meta VALUES ('dataset_type','synthetic demonstration data')")

def money(x): return f'₹{x:,.0f}'

def chart_layout(fig, height=320):
    fig.update_layout(height=height, margin=dict(l=8,r=8,t=35,b=8),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color='#29445F', legend_title_text='')
    fig.update_xaxes(showgrid=False, linecolor='#D5E0EA')
    fig.update_yaxes(gridcolor='#E7EDF4', zerolinecolor='#D5E0EA')
    return fig

data=load_data(); init_db(data)
students,courses,faculty,payments,feedback=(data[k].copy() for k in ['students','courses','faculty','payments','feedback'])
students['enrollment_date']=pd.to_datetime(students.enrollment_date)
payments['payment_date']=pd.to_datetime(payments.payment_date)
feedback['feedback_date']=pd.to_datetime(feedback.feedback_date)

with st.sidebar:
    logo = ROOT / "assets" / "emw_logo.png"
    if logo.exists():
        st.image(str(logo), use_container_width=True)
    st.markdown("### EDUINSIGHTS")
    st.caption("Educational Intelligence Platform")
    page_groups = {
        "OVERVIEW": [("Executive Dashboard","⌂")],
        "LEARNING": [("Student Analytics","▦"),("Attendance & Risk","◷"),("Learner Support","♡")],
        "OPERATIONS": [("Faculty Insights","♙"),("Course Intelligence","◇"),("Finance Analytics","₹")],
        "INSIGHTS & TOOLS": [("Feedback Intelligence","✧"),("AI Recommendations","✦"),("Notifications","♧"),("Reports & Data","▤"),("Data Entry","＋")],
    }
    if st.session_state.get("role") in ("student", "parent"):
        page_groups = {}
    if st.session_state.get("role") in ("admin", "student", "parent"):
        page_groups["PORTAL"] = [("Parent / Student Portal", "⌂")]
    if st.session_state.get("role") == "admin":
        page_groups["ADMINISTRATION"] = [("Admin Console","⚙")]
    st.markdown("#### Workspace")
    allowed_pages = [label for entries in page_groups.values() for label, _ in entries]
    if st.session_state.get("active_page") not in allowed_pages:
        st.session_state["active_page"] = allowed_pages[0]
    for group_name, entries in page_groups.items():
        st.markdown(f'<div class="nav-group">{group_name}</div>', unsafe_allow_html=True)
        for label, glyph in entries:
            selected = st.session_state["active_page"] == label
            if st.button(f"{glyph}   {label}", key=f"nav_{label}",
                         type="primary" if selected else "secondary",
                         use_container_width=True):
                st.session_state["active_page"] = label
                st.rerun()
    page = st.session_state["active_page"]
    st.divider()
    st.caption(f"Signed in: {st.session_state.get('full_name', st.session_state.get('username'))}")
    st.caption(f"Role: {st.session_state.get('role','analyst').title()}")
    if st.button("↪  Sign out", use_container_width=True):
        for key in ("authenticated","username","role","full_name","active_page","linked_student_id"):
            st.session_state.pop(key, None)
        st.rerun()
    st.caption("Demo environment · Synthetic data")

st.markdown('<div class="hero"><h1>EduInsights <span style="color:#FFC928">/</span> EMW</h1><p>Turn learning activity into clear, actionable institutional insights.</p></div>', unsafe_allow_html=True)

# Global filters
if page != "Parent / Student Portal":
    f1,f2,f3=st.columns([1,1,1])
    with f1: domains=st.multiselect('Learning domains', sorted(students.domain.unique()), default=sorted(students.domain.unique()))
    with f2: ages=st.slider('Learner age range',5,17,(5,17))
    with f3: period=st.selectbox('Enrollment window',['All time','Last 12 months','Last 6 months'])
    filtered=students[students.domain.isin(domains)&students.age.between(*ages)].copy()
    if period!='All time':
        days=365 if period=='Last 12 months' else 183
        filtered=filtered[filtered.enrollment_date>=students.enrollment_date.max()-pd.Timedelta(days=days)]

if page=='Executive Dashboard':
    st.subheader('Institution overview')
    paid=payments[payments.payment_status=='Paid'].amount_inr.sum()
    c=st.columns(4)
    c[0].metric('Learners in view',f'{len(filtered):,}')
    c[1].metric('Learning domains',f'{filtered.domain.nunique()}')
    c[2].metric('Avg. attendance',f'{filtered.attendance_pct.mean():.1f}%' if len(filtered) else '—')
    c[3].metric('Collected revenue',money(paid))
    a,b=st.columns([1.5,1])
    with a:
        trend=filtered.assign(month=filtered.enrollment_date.dt.to_period('M').astype(str)).groupby('month').size().reset_index(name='learners')
        st.plotly_chart(chart_layout(px.area(trend,x='month',y='learners',title='Learner enrollment trend',markers=True,color_discrete_sequence=[CYAN])),use_container_width=True)
    with b:
        by=filtered.groupby('domain').size().reset_index(name='learners').sort_values('learners',ascending=True)
        st.plotly_chart(chart_layout(px.bar(by,x='learners',y='domain',orientation='h',title='Learners by domain',color='learners',color_continuous_scale=['#14506C',CYAN])),use_container_width=True)
    a,b=st.columns(2)
    with a:
        status=filtered.learning_status.value_counts().rename_axis('status').reset_index(name='count')
        st.plotly_chart(chart_layout(px.pie(status,names='status',values='count',hole=.58,title='Learner support overview',color_discrete_sequence=[CYAN,YELLOW])),use_container_width=True)
    with b:
        st.plotly_chart(chart_layout(px.scatter(filtered,x='attendance_pct',y='average_score',color='learning_status',size='engagement_score',hover_data=['student_id','domain'],title='Attendance vs learning outcomes',color_discrete_map={'On track':CYAN,'Needs support':YELLOW})),use_container_width=True)
    st.info('Management note: use aggregated trends to plan mentor support, practical sessions and course capacity. Do not use a single metric to judge a learner.')

elif page=='Student Analytics':
    st.subheader('Learner profile & academic outcomes')
    c=st.columns(3); c[0].metric('Average score',f'{filtered.average_score.mean():.1f}/100' if len(filtered) else '—'); c[1].metric('Projects completed',f'{filtered.projects_completed.sum():,}'); c[2].metric('Average engagement',f'{filtered.engagement_score.mean():.1f}/10' if len(filtered) else '—')
    st.plotly_chart(chart_layout(px.box(filtered,x='domain',y='average_score',color='domain',title='Score distribution by learning domain')),use_container_width=True)
    st.dataframe(filtered[['student_id','age','course_name','attendance_pct','average_score','engagement_score','projects_completed','learning_status']],use_container_width=True,hide_index=True)
    st.download_button('Download learner data (CSV)',filtered.to_csv(index=False).encode(),file_name='emw_learner_analytics.csv',mime='text/csv')

elif page=='Attendance & Risk':
    st.subheader('Attendance monitoring & early-support signals')
    low=filtered[filtered.attendance_pct<75]
    c=st.columns(3); c[0].metric('Below 75% attendance',len(low)); c[1].metric('Needs-support flag',int((filtered.learning_status=='Needs support').sum())); c[2].metric('Mean attendance',f'{filtered.attendance_pct.mean():.1f}%' if len(filtered) else '—')
    st.plotly_chart(chart_layout(px.histogram(filtered,x='attendance_pct',nbins=18,color='learning_status',title='Attendance distribution',color_discrete_map={'On track':CYAN,'Needs support':YELLOW})),use_container_width=True)
    st.markdown('#### Demonstration risk model')
    st.caption('A logistic-regression teaching example trained on synthetic records. It is not validated for real-world decisions.')
    try:
        from sklearn.compose import ColumnTransformer
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, roc_auc_score
        features=['attendance_pct','average_score','engagement_score','age','projects_completed']
        X=students[features]; y=(students.learning_status=='Needs support').astype(int)
        Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
        model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,class_weight='balanced'))
        model.fit(Xtr,ytr); probs=model.predict_proba(Xte)[:,1]
        x1,x2=st.columns(2); x1.metric('Holdout accuracy',f'{accuracy_score(yte,probs>=.5):.1%}'); x2.metric('Holdout ROC-AUC',f'{roc_auc_score(yte,probs):.3f}')
        sample=filtered[features].copy()
        if len(sample):
            sample['estimated_support_probability']=model.predict_proba(sample)[:,1].round(3)
            sample=sample.sort_values('estimated_support_probability',ascending=False)
            st.dataframe(sample.head(30),use_container_width=True,hide_index=True)
    except Exception as e: st.warning(f'Model unavailable: {e}')
    st.warning('A high score means “review and offer support”, not a prediction of a child’s future or a basis for exclusion.')

elif page=='Learner Support':
    st.subheader('Learner support & intervention workspace')
    st.caption('Use these signals to prepare a human-reviewed support list. The demo does not contact learners or make automated decisions.')
    support=filtered.copy()
    support['support_reason']=np.select([support.attendance_pct<75, support.average_score<55, support.engagement_score<4], ['Attendance below 75%','Academic score below 55','Low engagement'], default='General mentor check-in')
    support=support[(support.attendance_pct<75)|(support.average_score<55)|(support.engagement_score<4)|(support.learning_status=='Needs support')].copy()
    c=st.columns(3); c[0].metric('Learners for review',len(support)); c[1].metric('Low attendance',int((support.attendance_pct<75).sum())); c[2].metric('Needs-support flag',int((support.learning_status=='Needs support').sum()))
    if len(support):
        st.dataframe(support[['student_id','course_name','domain','attendance_pct','average_score','engagement_score','support_reason']],use_container_width=True,hide_index=True)
        st.download_button('Download mentor review list (CSV)',support[['student_id','course_name','domain','attendance_pct','average_score','engagement_score','support_reason']].to_csv(index=False).encode('utf-8'),file_name='emw_mentor_review_list.csv',mime='text/csv',use_container_width=True)
        if st.button('Prepare mentor review summary',use_container_width=True):
            st.success(f'Review summary prepared for {len(support)} synthetic learner records. Please validate each case with a mentor before taking action.')
            st.write(support['support_reason'].value_counts().rename_axis('Reason').reset_index(name='Learners'))
    else:
        st.success('No learners in the current filter meet the demonstration review thresholds.')

elif page=='Faculty Insights':
    st.subheader('Mentor capacity & learner feedback')
    c=st.columns(3); c[0].metric('Mentors in demo data',len(faculty)); c[1].metric('Sessions delivered',int(faculty.sessions_delivered.sum())); c[2].metric('Mean feedback rating',f'{faculty.avg_feedback_rating.mean():.2f}/5')
    a,b=st.columns(2)
    with a: st.plotly_chart(chart_layout(px.bar(faculty.sort_values('sessions_delivered'),x='sessions_delivered',y='faculty_name',orientation='h',title='Sessions delivered by mentor',color='sessions_delivered',color_continuous_scale=['#14506C',CYAN])),use_container_width=True)
    with b: st.plotly_chart(chart_layout(px.scatter(faculty,x='active_batches',y='avg_feedback_rating',size='sessions_delivered',color='specialization',title='Mentor capacity & feedback')),use_container_width=True)
    st.dataframe(faculty,use_container_width=True,hide_index=True)
    st.caption('Use these aggregates for workload planning and coaching conversations, not as a standalone employee-performance score.')

elif page=='Course Intelligence':
    st.subheader('Programme and domain performance')
    course_stats=students.groupby(['course_name','domain']).agg(learners=('student_id','count'),avg_score=('average_score','mean'),avg_attendance=('attendance_pct','mean'),avg_engagement=('engagement_score','mean')).reset_index()
    course_stats=course_stats.merge(courses[['course_name','capacity','fee_inr']],on='course_name',how='left')
    a,b=st.columns(2)
    with a: st.plotly_chart(chart_layout(px.bar(course_stats.sort_values('learners'),x='learners',y='course_name',orientation='h',title='Enrollment by course',color='learners',color_continuous_scale=['#14506C',CYAN])),use_container_width=True)
    with b: st.plotly_chart(chart_layout(px.scatter(course_stats,x='avg_attendance',y='avg_score',size='learners',color='domain',hover_name='course_name',title='Course attendance vs average score')),use_container_width=True)
    st.dataframe(course_stats.round(1),use_container_width=True,hide_index=True)

elif page=='Finance Analytics':
    st.subheader('Fee collection & revenue trends')
    paid=payments[payments.payment_status=='Paid']; pending=payments[payments.payment_status!='Paid']
    c=st.columns(3); c[0].metric('Collected',money(paid.amount_inr.sum())); c[1].metric('Outstanding / part-paid',money(pending.amount_inr.sum())); c[2].metric('Transactions',f'{len(payments):,}')
    monthly=payments.assign(month=payments.payment_date.dt.to_period('M').astype(str)).groupby(['month','payment_status']).amount_inr.sum().reset_index()
    st.plotly_chart(chart_layout(px.bar(monthly,x='month',y='amount_inr',color='payment_status',title='Monthly payment value',barmode='stack',color_discrete_map={'Paid':CYAN,'Pending':YELLOW,'Part-paid':'#8B9BB0'})),use_container_width=True)
    by=payments.groupby('course_name').amount_inr.sum().reset_index().sort_values('amount_inr',ascending=False)
    st.plotly_chart(chart_layout(px.bar(by,x='course_name',y='amount_inr',title='Payment value by course',color_discrete_sequence=[YELLOW])),use_container_width=True)
    st.download_button('Export finance summary (CSV)',monthly.to_csv(index=False).encode('utf-8'),file_name='emw_finance_summary.csv',mime='text/csv',use_container_width=True)
    st.caption('All payment figures are fictional sample values. Do not use them for accounting or financial reporting.')

elif page=='Feedback Intelligence':
    st.subheader('Voice of learner & parent')
    # Lightweight transparent keyword classifier; avoids external model downloads.
    pos={'great','helpful','enjoys','excellent','practical','clearly','fun','engaging','useful'}
    neg={'changes','often','need','fast','improve','improve.','too'}
    def classify(t):
        words=set(str(t).lower().replace('.','').split()); p=len(words&pos); n=len(words&neg)
        return 'Positive' if p>n else ('Negative' if n>p else 'Neutral')
    feedback['predicted_sentiment']=feedback.feedback_text.map(classify)
    counts=feedback.predicted_sentiment.value_counts().rename_axis('sentiment').reset_index(name='count')
    a,b=st.columns([1,1.5])
    with a: st.plotly_chart(chart_layout(px.pie(counts,names='sentiment',values='count',hole=.55,title='Feedback sentiment mix',color_discrete_sequence=[CYAN,YELLOW,'#8B9BB0'])),use_container_width=True)
    with b:
        domain_feedback=feedback.merge(courses[['course_name','domain']],on='course_name',how='left').groupby(['domain','predicted_sentiment']).size().reset_index(name='count')
        st.plotly_chart(chart_layout(px.bar(domain_feedback,x='domain',y='count',color='predicted_sentiment',barmode='group',title='Feedback themes by domain')),use_container_width=True)
    sentiment_filter=st.multiselect('Filter sentiment', ['Positive','Neutral','Negative'], default=['Positive','Neutral','Negative'])
    feedback_view=feedback[feedback.predicted_sentiment.isin(sentiment_filter)]
    st.dataframe(feedback_view[['feedback_date','course_name','feedback_text','predicted_sentiment']],use_container_width=True,hide_index=True)
    st.download_button('Download filtered feedback analysis (CSV)',feedback_view.to_csv(index=False).encode('utf-8'),file_name='emw_feedback_analysis.csv',mime='text/csv',use_container_width=True)
    st.caption('Sentiment is estimated with a small transparent keyword rule for demonstration. Review original comments before acting.')

elif page=='AI Recommendations':
    st.subheader("AI-assisted learner recommendations")
    st.caption("Explainable rule-based recommendations from the synthetic demo data; not a validated AI model or a substitute for educator judgement.")
    recs = filtered.copy()
    def recommendation(row):
        notes=[]
        if row.attendance_pct < 75: notes.append("Offer an attendance check-in and understand any barriers")
        if row.average_score < 60: notes.append("Offer a short concept review and guided practice")
        if row.engagement_score < 5: notes.append("Ask about learning interests and try a hands-on activity")
        if row.projects_completed < 2: notes.append("Suggest a small, achievable project milestone")
        return " · ".join(notes) if notes else "Continue current learning plan and celebrate progress"
    recs["Suggested next step"] = recs.apply(recommendation, axis=1)
    st.dataframe(recs[["student_id","course_name","attendance_pct","average_score","engagement_score","Suggested next step"]], use_container_width=True, hide_index=True)
    st.download_button("Export recommendations (CSV)", recs.to_csv(index=False).encode("utf-8"), file_name="emw_support_recommendations.csv", mime="text/csv")
    st.info("Review each learner's circumstances with a qualified mentor before taking action. Do not use these suggestions to rank, penalize or exclude learners.")

elif page=='Notifications':
    st.subheader("Notifications & follow-up centre")
    notices=[]
    for _, row in filtered.iterrows():
        if row.attendance_pct < 75:
            notices.append({"Priority":"Review","Learner":row.student_id,"Notification":"Attendance is below 75% — consider a supportive check-in."})
        if row.average_score < 55:
            notices.append({"Priority":"Review","Learner":row.student_id,"Notification":"Recent learning score suggests a concept-review conversation."})
    pending = payments[payments.payment_status != "Paid"]
    for _, row in pending.iterrows():
        notices.append({"Priority":"Finance","Learner":"—","Notification":f"Pending/part-paid demo fee for {row.course_name}: ₹{row.amount_inr:,.0f}."})
    if notices:
        notice_df=pd.DataFrame(notices)
        st.metric("Items requiring review", len(notice_df))
        priority=st.multiselect("Filter notification type", sorted(notice_df.Priority.unique()), default=sorted(notice_df.Priority.unique()))
        st.dataframe(notice_df[notice_df.Priority.isin(priority)], use_container_width=True, hide_index=True)
        st.download_button("Download notification list", notice_df.to_csv(index=False).encode(), file_name="emw_notifications.csv", mime="text/csv")
    else:
        st.success("No notifications for the current filters.")
    st.caption("Notifications are generated from the sample data at page load. This prototype does not send email, SMS or push alerts.")

elif page=='Parent / Student Portal':
    role=st.session_state.get("role")
    if role not in ("admin","student","parent"):
        st.error("This area is available to student/parent accounts and administrators.")
        st.stop()
    st.subheader("Parent & Student Learning Portal")
    link_id=st.session_state.get("linked_student_id")
    if role == "admin":
        link_id=st.selectbox("Preview learner", students.student_id.astype(str).tolist())
    if not link_id:
        st.warning("This account is not linked to a learner record. Sign out and register a Student or Parent account using the learner ID provided by the institution.")
    else:
        own=students[students.student_id.astype(str)==str(link_id)]
        if own.empty:
            st.error("No learner record matches this ID in the demo dataset. Check the ID with the administrator.")
        else:
            learner=own.iloc[0]
            c=st.columns(4)
            c[0].metric("Attendance", f"{learner.attendance_pct:.1f}%")
            c[1].metric("Learning score", f"{learner.average_score:.1f}/100")
            c[2].metric("Engagement", f"{learner.engagement_score:.1f}/10")
            c[3].metric("Projects", int(learner.projects_completed))
            st.markdown("#### Learning profile")
            st.write(f"**Learner ID:** {learner.student_id}  ·  **Course:** {learner.course_name}  ·  **Domain:** {learner.domain}")
            st.markdown("#### Suggested learning actions")
            actions=[]
            if learner.attendance_pct < 75: actions.append("Discuss attendance barriers with the mentor.")
            if learner.average_score < 60: actions.append("Ask the mentor for a focused revision activity.")
            if learner.engagement_score < 5: actions.append("Explore a practical activity connected to the learner's interests.")
            if not actions: actions.append("Keep practising and share completed projects with the mentor.")
            for action in actions: st.write("• " + action)
            st.info("This is a read-only demonstration portal using fictional learner data. It is not a secure production parent/student record system.")

elif page=='Reports & Data':
    st.subheader('Reports, exports & data dictionary')
    st.markdown('Export the current filtered learner dataset or inspect the sample tables used by the dashboard.')
    st.download_button('Download complete demo dataset (students)',students.to_csv(index=False).encode(),file_name='emw_students_demo.csv',mime='text/csv')
    st.download_button('Download payments demo data',payments.to_csv(index=False).encode(),file_name='emw_payments_demo.csv',mime='text/csv')
    st.download_button('Download feedback demo data',feedback.to_csv(index=False).encode(),file_name='emw_feedback_demo.csv',mime='text/csv')
    if st.button('Generate institutional data summary',use_container_width=True):
        summary=(f"EduInsights / EMW — Demo Data Summary\n\nLearners: {len(students)}\nCourses: {len(courses)}\nFaculty records: {len(faculty)}\nPayment records: {len(payments)}\nFeedback records: {len(feedback)}\n\nAll records are synthetic demonstration data.\n")
        st.download_button('Download generated summary (TXT)',summary.encode('utf-8'),file_name='emw_demo_summary.txt',mime='text/plain',key='download_summary')
    st.markdown("#### Multi-format institutional report")
    report_frames={"Learners":filtered,"Courses":courses,"Faculty":faculty,"Payments":payments,"Feedback":feedback}
    excel_buffer=io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        for sheet, frame in report_frames.items():
            frame.to_excel(writer, sheet_name=sheet[:31], index=False)
    st.download_button("Download Excel workbook (.xlsx)", excel_buffer.getvalue(), file_name="EduInsights_EMW_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        pdf_buffer=io.BytesIO()
        doc=SimpleDocTemplate(pdf_buffer, pagesize=A4)
        styles=getSampleStyleSheet()
        story=[Paragraph("EduInsights / EMW — Institutional Demo Report", styles["Title"]), Spacer(1,12),
               Paragraph("Synthetic demonstration data only. Not actual EMW records and not for operational decisions.", styles["BodyText"]), Spacer(1,12)]
        rows=[["Dataset","Records","Fields"]]+[[name,len(frame),len(frame.columns)] for name,frame in report_frames.items()]
        table=Table(rows, repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0B3554")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.5,colors.grey),("PADDING",(0,0),(-1,-1),7)]))
        story.extend([table,Spacer(1,14),Paragraph(f"Learners in current filter: {len(filtered)}",styles["BodyText"]),Paragraph(f"Average attendance: {filtered.attendance_pct.mean():.1f}%" if len(filtered) else "Average attendance: N/A",styles["BodyText"])])
        doc.build(story)
        st.download_button("Download PDF summary (.pdf)",pdf_buffer.getvalue(),file_name="EduInsights_EMW_Summary.pdf",mime="application/pdf")
    except Exception as exc:
        st.warning(f"PDF export is unavailable: {exc}")

    st.markdown('#### Data dictionary')
    st.dataframe(pd.DataFrame([
      ['students','One synthetic learner record per row','Attendance, score, engagement, course and support flag'],
      ['courses','One row per EMW learning domain/course','Domain, capacity and indicative demo fee'],
      ['faculty','Synthetic mentor workload summary','Batches, sessions and aggregated feedback rating'],
      ['payments','Synthetic payment transactions','Date, amount and payment status'],
      ['feedback','Synthetic learner/parent comments','Comment text and demo sentiment label']
    ],columns=['Table','Grain','Key fields']),use_container_width=True,hide_index=True)
    st.markdown('#### Database')
    st.code('SQLite database: eduinsights.db\nTables: students, courses, faculty, payments, feedback, app_meta',language='text')
    st.caption('The database is rebuilt from the included CSV demo files when the app starts. Back up and replace this process before production use.')

elif page=='Data Entry':
    st.subheader("Data Entry & Record Management")
    st.caption("Add demonstration records to the local CSV datasets. These records persist when you restart the app.")
    tab_student, tab_feedback, tab_faculty, tab_course, tab_payment = st.tabs(
        ["Learner", "Feedback", "Faculty", "Course", "Payment"])
    def append_record(table_name, record):
        file_path = DATA / f"{table_name}.csv"
        old = pd.read_csv(file_path)
        updated = pd.concat([old, pd.DataFrame([record])], ignore_index=True)
        updated.to_csv(file_path, index=False)
        st.cache_data.clear()
        st.success(f"{table_name.title()} record saved.")
    with tab_student:
        with st.form("add_student"):
            a,b = st.columns(2)
            sid = a.text_input("Learner ID", placeholder="EMW-NEW01")
            age = b.number_input("Age", min_value=5, max_value=17, value=10)
            course = st.selectbox("Course", courses.course_name.tolist())
            attendance = st.slider("Attendance (%)",0,100,85)
            score = st.slider("Average score",0,100,75)
            engagement = st.slider("Engagement score",1.0,10.0,7.0)
            projects = st.number_input("Projects completed",0,100,1)
            enroll = st.date_input("Enrollment date")
            save_student = st.form_submit_button("Save learner", type="primary")
        if save_student:
            if not sid.strip(): st.error("Learner ID is required.")
            elif sid.strip() in students.student_id.astype(str).values: st.error("That learner ID already exists.")
            else:
                course_row = courses[courses.course_name == course].iloc[0]
                append_record("students", {"student_id":sid.strip(),"age":int(age),"course_name":course,
                    "domain":course_row.domain,"enrollment_date":str(enroll),"attendance_pct":attendance,
                    "engagement_score":engagement,"average_score":score,"projects_completed":int(projects),
                    "learning_status":"Needs support" if attendance < 65 or score < 50 else "On track",
                    "fee_status":"Pending"})
    with tab_feedback:
        with st.form("add_feedback"):
            fc = st.selectbox("Course", courses.course_name.tolist(), key="fb_course")
            fdate = st.date_input("Feedback date", key="fb_date")
            ftext = st.text_area("Feedback details", placeholder="Enter feedback...")
            save_feedback = st.form_submit_button("Save feedback", type="primary")
        if save_feedback:
            if not ftext.strip(): st.error("Feedback text is required.")
            else:
                oldfb = pd.read_csv(DATA/"feedback.csv")
                append_record("feedback", {"feedback_id":f"FDB-{len(oldfb)+1:04d}","course_name":fc,
                    "feedback_date":str(fdate),"feedback_text":ftext.strip(),"demo_sentiment_label":"Unreviewed"})
    with tab_faculty:
        with st.form("add_faculty"):
            fid = st.text_input("Faculty ID",placeholder="FAC-NEW01")
            fname = st.text_input("Faculty name")
            spec = st.selectbox("Specialization", sorted(courses.domain.unique()))
            batches = st.number_input("Active batches",0,100,1)
            sessions = st.number_input("Sessions delivered",0,10000,0)
            rating = st.slider("Average feedback rating",1.0,5.0,4.0)
            save_faculty = st.form_submit_button("Save faculty",type="primary")
        if save_faculty:
            if not fid.strip() or not fname.strip(): st.error("Faculty ID and name are required.")
            elif fid.strip() in faculty.faculty_id.astype(str).values: st.error("Faculty ID already exists.")
            else: append_record("faculty",{"faculty_id":fid.strip(),"faculty_name":fname.strip(),"specialization":spec,
                "active_batches":int(batches),"sessions_delivered":int(sessions),"avg_feedback_rating":rating})
    with tab_course:
        with st.form("add_course"):
            cname = st.text_input("Course name")
            domain = st.selectbox("Learning domain",sorted(students.domain.unique()))
            capacity = st.number_input("Capacity",1,10000,30)
            fee = st.number_input("Course fee (₹)",0,1000000,8000,step=500)
            save_course = st.form_submit_button("Save course",type="primary")
        if save_course:
            if not cname.strip(): st.error("Course name is required.")
            elif cname.strip() in courses.course_name.astype(str).values: st.error("Course already exists.")
            else: append_record("courses",{"course_name":cname.strip(),"domain":domain,"capacity":int(capacity),"fee_inr":int(fee)})
    with tab_payment:
        with st.form("add_payment"):
            pdate = st.date_input("Payment date",key="payment_date")
            pcourse = st.selectbox("Course",courses.course_name.tolist(),key="payment_course")
            amount = st.number_input("Amount (₹)",0,1000000,5000,step=500)
            status = st.selectbox("Payment status",["Paid","Pending","Part-paid"])
            save_payment = st.form_submit_button("Save payment",type="primary")
        if save_payment:
            append_record("payments",{"payment_date":str(pdate),"amount_inr":int(amount),
                "payment_status":status,"course_name":pcourse})
    st.info("This is a local prototype using CSV files. Back up your data folder before editing, and do not enter personally identifiable information about children.")

elif page=='Admin Console':
    if st.session_state.get('role') != 'admin':
        st.error('Administrator access is required for this page.')
        st.stop()
    st.subheader('Administrator workspace')
    st.caption('Administrative controls for this demonstration build.')
    a,b,c=st.columns(3)
    a.metric('Workspace role','Administrator')
    b.metric('Data source','Synthetic CSV files')
    c.metric('Database','SQLite')
    st.markdown('#### Data governance checklist')
    st.info('Before using real EMW information: obtain written authorization, use approved accounts, minimize child data, configure secure hosting, define retention rules and verify access permissions.')
    st.markdown('#### Dataset inventory')
    inventory=[]
    for name,frame in data.items(): inventory.append({'Dataset':name.title(),'Rows':len(frame),'Columns':len(frame.columns),'Source':'Synthetic demonstration data'})
    st.dataframe(pd.DataFrame(inventory),use_container_width=True,hide_index=True)
    st.markdown('#### Data integrity check')
    if st.button('Run data integrity check',use_container_width=True):
        checks=[]
        for name,frame in data.items():
            checks.append({'Dataset':name.title(),'Rows':len(frame),'Missing cells':int(frame.isna().sum().sum()),'Duplicate rows':int(frame.duplicated().sum()),'Status':'Review' if frame.isna().sum().sum() or frame.duplicated().sum() else 'Passed'})
        st.dataframe(pd.DataFrame(checks),use_container_width=True,hide_index=True)
        st.success('Integrity check completed on the included synthetic CSV files.')
    st.markdown('#### Deployment status')
    st.warning('Local prototype mode. Configure unique credentials in Streamlit secrets and deploy behind HTTPS before sharing beyond a controlled demo.')
    with sqlite3.connect(':memory:') as snapshot:
        for name, frame in data.items():
            frame.to_sql(name, snapshot, index=False)
        snapshot_bytes = "\n".join(snapshot.iterdump()).encode("utf-8")
    st.download_button('Download demo data snapshot', snapshot_bytes, file_name='eduinsights_demo.sql', mime='text/plain')

st.divider()
st.markdown('<div class="small-muted">EduInsights for EMW · Demonstration build · Data is synthetic · Not for decisions about real children, staff or finances.</div>',unsafe_allow_html=True)
