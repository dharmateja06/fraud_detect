# Image Guard AI

**Image Guard AI** is a web-based system that verifies the authenticity of any fake images by giving a score.  
It ensures that submitted photos are **genuine, untampered, and truly captured from distinct physical locations**.  
The system leverages **deep learning (EfficientNet with Keras)**, **computer vision**, **metadata analysis**, **OCR**, **clustering**, and **fraud scoring** to provide a reliable detection solution.

---

## Features
- **Deep Learning Authenticity Check**  
  Uses **EfficientNet (Keras + TensorFlow)** to detect image tampering.  
- **Metadata & EXIF Analysis**  
  Extracts device info, timestamps, and GPS data for validation.  
- **OCR (Optical Character Recognition)**  
  Reads and compares text from the board using **Tesseract OCR**.  
- **Depth & Image Analysis**  
  Evaluates scene depth and pixel-level features using **OpenCV + NumPy**.  
- **Clustering for Location Verification**  
  Groups images by visual/metadata similarity with **scikit-learn**.  
- **Fraud Scoring System**  
  Scores each image as **Authentic**, **Tampered**, or **Verification Failed**.  
- **Database Integration**  
  Stores results in **SQLite** (via SQLAlchemy).  
- **Results Dashboard**  
  Displays uploaded images, verification status, analysis results, and map links for geotagged photos.  

---

## Tech Stack

### Core Frameworks & Languages
- **Python 3.9+**
- **FastAPI** → Backend API framework  
- **HTML, CSS, Jinja2** → Frontend templates  
- **SQLite** → Database  

### Deep Learning & AI
- **Keras** → Model handling  
- **TensorFlow** → Backend engine  
- **EfficientNet** → Pretrained CNN for image authenticity detection  

### Computer Vision & Image Processing
- **OpenCV** → Image analysis & preprocessing  
- **Pillow (PIL)** → Image handling  
- **NumPy** → Numerical computations  

### OCR & Metadata
- **pytesseract** → OCR (text extraction)  
- **piexif / exifread** → Metadata & EXIF handling  

### Machine Learning / Clustering
- **scikit-learn** → Clustering, similarity checks  

### Utilities
- **uvicorn** → ASGI server for FastAPI  
- **sqlalchemy** → ORM for database operations  
- **python-multipart** → File uploads  
- **jinja2** → Template rendering  

---

## Python Package List
Your `requirements.txt` should include (with versions as per your environment):

```txt
fastapi
uvicorn
sqlalchemy
python-multipart
jinja2

numpy
opencv-python
pillow

tensorflow
keras
efficientnet

scikit-learn
pytesseract
exifread
piexif
