-- EduInsights local SQLite schema (tables are populated from included CSV files).
CREATE TABLE IF NOT EXISTS students (
  student_id TEXT PRIMARY KEY, age INTEGER, course_name TEXT, domain TEXT,
  enrollment_date TEXT, attendance_pct REAL, engagement_score REAL,
  average_score REAL, projects_completed INTEGER, learning_status TEXT, fee_status TEXT
);
CREATE TABLE IF NOT EXISTS courses (
  course_name TEXT PRIMARY KEY, domain TEXT, capacity INTEGER, fee_inr INTEGER
);
CREATE TABLE IF NOT EXISTS faculty (
  faculty_id TEXT PRIMARY KEY, faculty_name TEXT, specialization TEXT,
  active_batches INTEGER, sessions_delivered INTEGER, avg_feedback_rating REAL
);
CREATE TABLE IF NOT EXISTS payments (
  payment_date TEXT, amount_inr INTEGER, payment_status TEXT, course_name TEXT
);
CREATE TABLE IF NOT EXISTS feedback (
  feedback_id TEXT PRIMARY KEY, course_name TEXT, feedback_date TEXT,
  feedback_text TEXT, demo_sentiment_label TEXT
);
CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT);
