"""Create clearly synthetic demonstration data for EduInsights EMW."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)
rng = np.random.default_rng(42)

courses = [
    ('Robotics Foundations', 'Robotics', 40, 8500),
    ('Coding & AI Explorers', 'Coding & AI', 55, 9000),
    ('Space Science Lab', 'Space Science', 35, 7800),
    ('Biotechnology Basics', 'Biotechnology', 30, 8200),
    ('Agritech Innovation', 'Agritech', 25, 7600),
    ('Marine Technology', 'Marine Tech', 22, 8000),
    ('Automobile Technology', 'Automobile Tech', 28, 8400),
    ('Digital Fabrication', 'Fabrication', 32, 8800),
    ('Civil & Infrastructure Tech', 'Civil & Infra', 24, 7900),
]
course_df = pd.DataFrame(courses, columns=['course_name','domain','capacity','fee_inr'])
course_df.to_csv(DATA/'courses.csv', index=False)

n=520
ids=[f'EMW-{i:04d}' for i in range(1,n+1)]
course_idx=rng.integers(0,len(courses),n)
age=rng.integers(5,18,n)
attendance=np.clip(rng.normal(82,13,n),35,100).round(1)
engagement=np.clip(rng.normal(7.2,1.7,n),1,10).round(1)
score=np.clip(0.48*attendance+3.4*engagement+rng.normal(5,10,n),20,100).round(1)
# Demo-only outcome label, used for a teaching example model.
risk=((attendance<65)&(score<58)) | ((attendance<52)&(engagement<5.5))
student_df=pd.DataFrame({
 'student_id':ids,'age':age,'course_name':[courses[i][0] for i in course_idx],
 'domain':[courses[i][1] for i in course_idx],
 'enrollment_date':pd.to_datetime('2025-01-01')+pd.to_timedelta(rng.integers(0,660,n),unit='D'),
 'attendance_pct':attendance,'engagement_score':engagement,'average_score':score,
 'projects_completed':rng.integers(0,9,n),'learning_status':np.where(risk,'Needs support','On track'),
 'fee_status':rng.choice(['Paid','Pending','Part-paid'],n,p=[.72,.18,.10])
})
student_df['enrollment_date']=student_df['enrollment_date'].dt.strftime('%Y-%m-%d')
student_df.to_csv(DATA/'students.csv',index=False)

faculty=pd.DataFrame({
 'faculty_id':[f'FAC-{i:03d}' for i in range(1,19)],
 'faculty_name':[f'Instructor {i:02d}' for i in range(1,19)],
 'specialization':rng.choice([c[1] for c in courses],18),
 'active_batches':rng.integers(1,6,18),
 'sessions_delivered':rng.integers(12,95,18),
 'avg_feedback_rating':np.round(rng.uniform(3.6,5,18),1)
})
faculty.to_csv(DATA/'faculty.csv',index=False)

months=pd.date_range('2025-01-01','2026-11-01',freq='MS')
rev=[]
for d in months:
    for _ in range(int(rng.integers(16,35))):
        rev.append({'payment_date':d+pd.Timedelta(days=int(rng.integers(0,27))),
                    'amount_inr':int(rng.choice([2500,3500,4500,6000,7800,8500,9000])),
                    'payment_status':rng.choice(['Paid','Pending','Part-paid'],p=[.78,.15,.07]),
                    'course_name':rng.choice(course_df.course_name)})
revenue=pd.DataFrame(rev)
revenue['payment_date']=pd.to_datetime(revenue.payment_date).dt.strftime('%Y-%m-%d')
revenue.to_csv(DATA/'payments.csv',index=False)

positive=['Great hands-on projects and helpful mentors.','My child enjoys the robotics sessions.','Excellent practical learning experience.','The instructor explains concepts clearly.','Fun and engaging class with useful activities.']
negative=['The schedule changes too often.','Need more time for practical projects.','The class pace is sometimes too fast.','Communication about sessions can improve.']
neutral=['The course content is interesting.','We attended the scheduled session.','The project materials were provided.']
feedback=[]
for i in range(260):
    sentiment=rng.choice(['Positive','Negative','Neutral'],p=[.62,.2,.18])
    msg=rng.choice({'Positive':positive,'Negative':negative,'Neutral':neutral}[sentiment])
    feedback.append({'feedback_id':f'FDB-{i+1:04d}','course_name':rng.choice(course_df.course_name),
                     'feedback_date':(pd.Timestamp('2025-01-01')+pd.Timedelta(days=int(rng.integers(0,680)))).strftime('%Y-%m-%d'),
                     'feedback_text':msg,'demo_sentiment_label':sentiment})
pd.DataFrame(feedback).to_csv(DATA/'feedback.csv',index=False)
print('Synthetic demo datasets created in', DATA)
