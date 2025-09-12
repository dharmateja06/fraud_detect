import sqlite3
from datetime import datetime

def init_db():
    """Initialize SQLite database with submissions table."""
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS submissions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT,
                  status TEXT,
                  score REAL,
                  reason TEXT,
                  lat REAL,
                  lon REAL,
                  timestamp TEXT,
                  device TEXT,
                  depth REAL,
                  cluster INTEGER,
                  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def insert_submission(filename: str, status: str, score: float, reason: str, 
                     lat: float, lon: float, timestamp: str, device: str, 
                     depth: float, cluster: int):
    """Insert a submission record into the database."""
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''INSERT INTO submissions (filename, status, score, reason, lat, lon, 
                 timestamp, device, depth, cluster)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (filename, status, score, reason, lat, lon, str(timestamp), device, depth, cluster))
    conn.commit()
    conn.close()

def get_submissions_by_device(device: str):
    """Retrieve all submissions for a given device."""
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM submissions WHERE device = ?", (device,))
    rows = c.fetchall()
    conn.close()
    columns = ["id", "filename", "status", "score", "reason", "lat", "lon", 
               "timestamp", "device", "depth", "cluster", "submitted_at"]
    return [dict(zip(columns, row)) for row in rows]

def get_all_submissions():
    """Retrieve all submissions for review or analysis."""
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM submissions")
    rows = c.fetchall()
    conn.close()
    columns = ["id", "filename", "status", "score", "reason", "lat", "lon", 
               "timestamp", "device", "depth", "cluster", "submitted_at"]
    return [dict(zip(columns, row)) for row in rows]

if __name__ == "__main__":
    # Initialize database when module is run directly
    init_db()