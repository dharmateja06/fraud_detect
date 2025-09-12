from typing import List
import numpy as np
import torch
import cv2
from PIL import Image
from exif import Image as ExifImage
from sklearn.cluster import DBSCAN
from haversine import haversine
import folium
from datetime import datetime
import os

# Initialize model variables
midas = None
transform = None

def init_midas():
    """Initialize MiDaS model lazily on first use"""
    global midas, transform
    if midas is None:
        try:
            midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
            midas.eval()
            transform = torch.hub.load("intel-isl/MiDaS", "transforms").small_transform
        except Exception as e:
            print(f"Error loading MiDaS model: {str(e)}")
            raise

def extract_exif_metadata(image_path: str):
    """Extract geolocation, timestamp, and device from EXIF."""
    try:
        with open(image_path, "rb") as img_file:
            img = ExifImage(img_file)
            lat = img.get("gps_latitude", None)
            lon = img.get("gps_longitude", None)
            timestamp = img.get("datetime", None)
            device = img.get("model", None)
            if lat and lon:
                lat = float(lat[0]) + lat[1]/60 + lat[2]/3600
                lon = float(lon[0]) + lon[1]/60 + lon[2]/3600
            if timestamp:
                timestamp = datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
            return {"lat": lat, "lon": lon, "timestamp": timestamp, "device": device}
    except:
        return {"lat": None, "lon": None, "timestamp": None, "device": None}

def compute_depth(image_path: str):
    """Estimate camera-to-board distance using MiDaS."""
    try:
        # Initialize model if needed
        if midas is None:
            init_midas()
            
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Unable to read image")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        input_batch = transform(img).unsqueeze(0)
        with torch.no_grad():
            depth = midas(input_batch)
            depth = torch.nn.functional.interpolate(
                depth.unsqueeze(1), size=img.shape[:2], mode="bicubic"
            ).squeeze()
        return float(depth.mean().item())
    except Exception as e:
        print(f"Error computing depth: {str(e)}")
        # On failure return a safe default depth and let higher-level logic
        # penalize but not crash the whole request
        return 0.0

def cluster_geolocations(locations: List[tuple]):
    """Cluster geolocations using DBSCAN."""
    if not locations:
        return []
    db = DBSCAN(eps=10/6371e3, min_samples=1, metric="haversine").fit(np.radians(locations))
    return db.labels_

def verify_photos(file_paths: List[str]):
    """Verify photos for fraud detection."""
    results = []
    locations = []
    depths = []
    timestamps = []
    devices = []

    # Process each photo
    for file_path in file_paths:
        try:
            reasons = []
            score = 1.0
            
            # Extract metadata
            metadata = extract_exif_metadata(file_path)
            
            # Compute depth first as it doesn't depend on metadata
            depth = compute_depth(file_path)
            
            # Check geolocation
            if metadata["lat"] is not None and metadata["lon"] is not None:
                locations.append((metadata["lat"], metadata["lon"]))
            else:
                reasons.append("Missing geolocation")
                score *= 0.5  # Reduce score but don't immediately fail
                
            # Store data
            if metadata["timestamp"]:
                timestamps.append(metadata["timestamp"])
            if metadata["device"]:
                devices.append(metadata["device"])
                
            # Create initial result
            result = {
                "file": os.path.basename(file_path),
                "status": None,  # Will be set later
                "score": score,
                "reason": reasons,
                "metadata": metadata,
                "depth": depth,
                "cluster": -1  # Will be updated if geolocation exists
            }
            results.append(result)
        except Exception as e:
            # Capture file-level errors as a result entry so one bad image
            # doesn't cause a 500 for the whole request.
            results.append({
                "file": os.path.basename(file_path),
                "status": "Error",
                "score": 0.0,
                "reason": [f"Processing error: {str(e)}"],
                "metadata": {"lat": None, "lon": None, "timestamp": None, "device": None},
                "depth": 0.0,
                "cluster": -1
            })

    # Cluster geolocations if we have any
    if locations:
        clusters = cluster_geolocations(locations)
        loc_index = 0
        for result in results:
            if result["metadata"]["lat"] is not None and result["metadata"]["lon"] is not None:
                if loc_index < len(clusters):
                    result["cluster"] = int(clusters[loc_index])
                loc_index += 1

    # Fraud detection
    for i, result in enumerate(results):
        if "status" in result:
            continue
        score = 1.0
        reason = []

        # Object Detection (mock; replace with YOLOv9)
        score *= 0.9
        # Manipulation Check (mock; replace with XceptionNet)
        score *= 0.95
        # Background Check (mock; replace with ResNet-18)
        score *= 0.95

        # Spatial Analysis
        cluster = result["cluster"]
        cluster_photos = [r for r in results if r["cluster"] == cluster]
        if len(cluster_photos) > 2:
            score *= 0.6
            reason.append("Excessive photos in 10m cluster")

        # Depth check
        for other in cluster_photos:
            if other["file"] != result["file"]:
                depth_diff = abs(result["depth"] - other["depth"])
                if depth_diff < 2.0:
                    score *= 0.7
                    reason.append("Similar depth in cluster")

        # Temporal check
        for other in cluster_photos:
            if other["file"] != result["file"] and other["metadata"]["timestamp"] and result["metadata"]["timestamp"]:
                time_diff = abs((other["metadata"]["timestamp"] - result["metadata"]["timestamp"]).total_seconds())
                if time_diff < 15:
                    score *= 0.6
                    reason.append("Photos taken too quickly")

        # Device check
        if sum(1 for r in cluster_photos if r["metadata"]["device"] == result["metadata"]["device"]) > 2:
            score *= 0.7
            reason.append("Multiple submissions from same device")

        # Image analysis
        try:
            img = Image.open(file_paths[i])
            # Check image quality
            if img.size[0] < 800 or img.size[1] < 800:
                score *= 0.8
                reason.append("Low resolution image")
            # Check if image was edited
            if "Software" in img.info:
                score *= 0.7
                reason.append("Image edited with software")
        except Exception as e:
            score *= 0.5
            reason.append("Error analyzing image")

        # Final verdict
        result["score"] = score
        if score > 0.7:  # Lowered threshold since geo might be missing
            result["status"] = "Real"
        elif score > 0.4:
            result["status"] = "Review"
        else:
            result["status"] = "Fake"
        result["reason"] = reason if reason else ["Passed"]

    # Generate map for photos with locations
    map_url = None
    if locations:
        m = folium.Map(location=[locations[0][0], locations[0][1]], zoom_start=15)
        loc_index = 0
        for result in results:
            if result["metadata"]["lat"] is not None and result["metadata"]["lon"] is not None:
                folium.Marker(
                    [result["metadata"]["lat"], result["metadata"]["lon"]], 
                    popup=f"{result['status']}: {', '.join(result['reason'])}"
                ).add_to(m)
                loc_index += 1
        map_url = "static/map.html"
        m.save(map_url)

    return results, map_url