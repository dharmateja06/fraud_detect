from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import os
import sqlite3
import logging
import sys
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# Create required directories first
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS submissions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT, status TEXT, score REAL, reason TEXT,
                  lat REAL, lon REAL, timestamp TEXT, device TEXT,
                  depth REAL, cluster INTEGER)''')
    conn.commit()
    conn.close()

# Initialize FastAPI with all static resources
app = FastAPI(debug=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database
init_db()

# Lazy load models and mount static files
# Initialize database
init_db()

# Import verification module - must be after app initialization
from verification import verify_photos

@app.on_event("startup")
async def startup_event():
    """Log successful startup"""
    logger.info("FastAPI application started successfully")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    return HTMLResponse(
        content=f"Internal Server Error: {str(exc)}\n\nTraceback:\n{''.join(traceback.format_tb(exc.__traceback__))}",
        status_code=500
    )

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("static/css", exist_ok=True)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS submissions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT, status TEXT, score REAL, reason TEXT,
                  lat REAL, lon REAL, timestamp TEXT, device TEXT,
                  depth REAL, cluster INTEGER)''')
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
async def get_upload_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/verify_boards/", response_class=HTMLResponse)
async def verify_boards(request: Request, files: List[UploadFile] = File(...)):
    if len(files) < 2 or len(files) > 3:
        return templates.TemplateResponse("results.html", {
            "request": request,
            "error": "Please upload 2-3 photos per board.",
            "results": [],
            "map_url": None
        })

    # Save files and process
    results = []
    for file in files:
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

    # Run verification
    verification_results, map_url = verify_photos([f"uploads/{f.filename}" for f in files])

    # Store in database
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    for result in verification_results:
        c.execute('''INSERT INTO submissions (filename, status, score, reason, lat, lon, timestamp, device, depth, cluster)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (result["file"], result["status"], result["score"], ", ".join(result["reason"]),
                   result["metadata"]["lat"], result["metadata"]["lon"], str(result["metadata"]["timestamp"]),
                   result["metadata"]["device"], result["depth"], result["cluster"]))
    conn.commit()
    conn.close()

    return templates.TemplateResponse("results.html", {
        "request": request,
        "results": verification_results,
        "map_url": map_url,
        "error": None
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)