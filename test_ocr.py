from PIL import Image
import pytesseract
import os
import cv2
import numpy as np

# Set Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
    # Read image using opencv
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to preprocess the image
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Apply dilation to connect text components
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    gray = cv2.dilate(gray, kernel, iterations=1)
    
    # Write the grayscale image to disk as temporary file
    cv2.imwrite("temp_processed.png", gray)
    
    # Return the preprocessed image path
    return "temp_processed.png"

def test_ocr(image_path):
    print(f"\nTesting OCR on: {os.path.basename(image_path)}")
    try:
        # Preprocess the image
        processed_image_path = preprocess_image(image_path)
        
        # Open the preprocessed image
        img = Image.open(processed_image_path)
        
        # Configure OCR settings
        custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
        
        # Perform OCR with custom configuration
        text = pytesseract.image_to_string(img, config=custom_config)
        
        print("Detected text:")
        print("-" * 40)
        print(text.strip())
        print("-" * 40)
        
        # Get bounding boxes with confidence scores
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        print("\nDetailed OCR data:")
        n_boxes = len(data['text'])
        print(f"Number of text segments found: {n_boxes}")
        
        # Print segments with high confidence
        print("\nHigh confidence text segments:")
        for i in range(n_boxes):
            if float(data['conf'][i]) > 60:  # Only show text with confidence > 60%
                text = data['text'][i]
                conf = data['conf'][i]
                if text.strip():  # Only print non-empty text
                    print(f"Text: {text}, Confidence: {conf}%")
        
        # Cleanup
        os.remove(processed_image_path)
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")

# Test with all images from the uploads directory
for image_name in os.listdir("uploads"):
    if image_name.lower().endswith(('.png', '.jpg', '.jpeg')):
        image_path = os.path.join("uploads", image_name)
        test_ocr(image_path)