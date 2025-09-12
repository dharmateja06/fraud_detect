app_content = '''from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import os
import sqlite3
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# Create required directories first
os.makedirs('static', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# Initialize FastAPI with all static resources
app = FastAPI(debug=True)
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

# Initialize database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute(\'\'\'CREATE TABLE IF NOT EXISTS submissions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT, status TEXT, score REAL, reason TEXT,
                  lat REAL, lon REAL, timestamp TEXT, device TEXT,
                  depth REAL, cluster INTEGER)\'\'\')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Import verification module - must be after app initialization
from verification import verify_photos

@app.on_event('startup')
async def startup_event():
    """Log successful startup"""
    logger.info('FastAPI application started successfully')

@app.get('/', response_class=HTMLResponse)
async def get_upload_form(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.post('/verify_boards/', response_class=HTMLResponse)
async def verify_boards(request: Request, files: List[UploadFile] = File(...)):
    if len(files) < 2 or len(files) > 3:
        return templates.TemplateResponse('results.html', {
            'request': request,
            'error': 'Please upload 2-3 photos per board.',
            'results': [],
            'map_url': None
        })

    try:
        # Save uploaded files
        saved_paths = []
        for file in files:
            file_path = os.path.join('uploads', file.filename)
            with open(file_path, 'wb') as buffer:
                content = await file.read()
                buffer.write(content)
            saved_paths.append(file_path)

        # Run verification
        verification_results, map_url = verify_photos(saved_paths)

        # Store results in database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        for result in verification_results:
            metadata = result['metadata']
            c.execute(\'\'\'INSERT INTO submissions 
                        (filename, status, score, reason, lat, lon, timestamp, 
                         device, depth, cluster)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\'\'\',
                     (result['file'], result['status'], 
                      result.get('score', 0.0),  # Use get() with default value
                      ', '.join(result['reason']),
                      metadata['lat'], metadata['lon'],
                      metadata['timestamp'].isoformat() if metadata['timestamp'] else None,
                      metadata['device'], result['depth'], result['cluster']))
        conn.commit()
        conn.close()

        return templates.TemplateResponse('results.html', {
            'request': request,
            'results': verification_results,
            'map_url': map_url,
            'error': None
        })

    except Exception as e:
        logger.error(f'Error processing upload: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return templates.TemplateResponse('results.html', {
            'request': request,
            'error': f'Error processing upload: {str(e)}',
            'results': [],
            'map_url': None
        })

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
'''

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_content)