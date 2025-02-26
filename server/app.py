from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import numpy as np
import cv2
import io
import time
from PIL import Image
import threading

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Global variables to store processed data
latest_frame = None
latest_tag_positions = []
processing_active = False
processing_fps = 0
last_process_time = time.time()
processed_frame = None

@app.route('/process-frame', methods=['POST'])
def process_frame():
    global latest_frame, processing_fps, last_process_time
    
    # Get the base64 image data from the request
    data = request.json
    if not data or 'image' not in data:
        return jsonify({'error': 'No image data provided'}), 400
    
    # Extract the base64 data (remove the data:image/jpeg;base64, prefix)
    img_data = data['image']
    if ',' in img_data:
        img_data = img_data.split(',')[1]
    
    try:
        # Convert base64 to image
        img_bytes = base64.b64decode(img_data)
        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # Update latest frame
        latest_frame = img
        
        # Calculate FPS
        current_time = time.time()
        time_diff = current_time - last_process_time
        if time_diff > 0:
            processing_fps = 1.0 / time_diff
        last_process_time = current_time
        
        # If processing is not active, start it
        if not processing_active:
            start_processing_thread()
        
        return jsonify({
            'status': 'success',
            'frame_received': True,
            'processing_fps': round(processing_fps, 1),
            'tag_positions': latest_tag_positions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Add this function to your app.py file
@app.route('/get-processed-image', methods=['GET'])
def get_processed_image():
    global processed_frame
    
    if processed_frame is None:
        return jsonify({'error': 'No processed frame available'}), 404
    
    try:
        # Convert to JPEG
        _, buffer = cv2.imencode('.jpg', processed_frame)
        
        # Convert to base64
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'image': f'data:image/jpeg;base64,{img_base64}',
            'num_tags': len(latest_tag_positions)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def detect_april_tags(frame):
    """
    Enhanced AprilTag detection with improved preprocessing
    """
    # Copy the frame for display purposes
    display_frame = frame.copy()
    
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply brightness and contrast adjustment
    alpha = 1.5  # Contrast control (1.0 means no change)
    beta = 30    # Brightness control (0 means no change)
    adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(adjusted, (5, 5), 0)
    
    # Apply adaptive thresholding
    thresholded = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Apply morphological operations to clean up
    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(thresholded, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Show preprocessing steps in the debug window
    h, w = frame.shape[:2]
    debug_size = (w//5, h//5)
    
    # Create small versions of each processing step
    small_gray = cv2.resize(gray, debug_size)
    small_adjusted = cv2.resize(adjusted, debug_size)
    small_thresh = cv2.resize(closing, debug_size)
    
    # Convert all to BGR for display
    small_gray_bgr = cv2.cvtColor(small_gray, cv2.COLOR_GRAY2BGR)
    small_adjusted_bgr = cv2.cvtColor(small_adjusted, cv2.COLOR_GRAY2BGR)
    small_thresh_bgr = cv2.cvtColor(small_thresh, cv2.COLOR_GRAY2BGR)
    
    # Place them in the corners of the display frame
    display_frame[10:10+debug_size[1], 10:10+debug_size[0]] = small_gray_bgr
    display_frame[10:10+debug_size[1], 20+debug_size[0]:20+2*debug_size[0]] = small_adjusted_bgr
    display_frame[10:10+debug_size[1], 30+2*debug_size[0]:30+3*debug_size[0]] = small_thresh_bgr
    
    # Add labels for each debug image
    cv2.putText(display_frame, "Gray", (10, 10+debug_size[1]+10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    cv2.putText(display_frame, "Adjusted", (20+debug_size[0], 10+debug_size[1]+10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    cv2.putText(display_frame, "Threshold", (30+2*debug_size[0], 10+debug_size[1]+10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    # Add special handling for white rectangular regions (potential AprilTags)
    detected_tags = []
    tag_id = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Filter out very small or very large contours
        if area < 100 or area > 10000:
            continue
        
        # Get the bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        
        # Calculate aspect ratio
        aspect_ratio = float(w) / h
        
        # If it's approximately square (aspect ratio between 0.8 and 1.2)
        if 0.8 <= aspect_ratio <= 1.2:
            # Draw a green rectangle around it
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Calculate center
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Draw the center
            cv2.circle(display_frame, (center_x, center_y), 5, (0, 0, 255), -1)
            
            # Draw ID
            cv2.putText(display_frame, f"ID: {tag_id}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Create corners array
            corners = [
                [x, y],
                [x+w, y],
                [x+w, y+h],
                [x, y+h]
            ]
            
            # Add to detected tags
            detected_tags.append({
                'id': tag_id,
                'center': (center_x, center_y),
                'corners': corners
            })
            
            tag_id += 1
    
    # Add detection info to frame
    cv2.putText(display_frame, f"Tags: {len(detected_tags)}", (10, h-20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Return the updated frame and detected tags
    return detected_tags, display_frame

def process_frames():
    global latest_frame, latest_tag_positions, processing_active, processed_frame
    
    processing_active = True
    
    while processing_active:
        if latest_frame is not None:
            # Make a copy of the frame to avoid race conditions
            frame = latest_frame.copy()
            
            # Detect AprilTags - note we now get back both tags and the processed frame
            detected_tags, processed_frame = detect_april_tags(frame)
            
            # Update the latest tag positions
            latest_tag_positions = [{'id': tag['id'], 'x': tag['center'][0], 'y': tag['center'][1]} 
                                   for tag in detected_tags]
        
        # Sleep to avoid consuming too much CPU
        time.sleep(0.01)

def start_processing_thread():
    thread = threading.Thread(target=process_frames)
    thread.daemon = True
    thread.start()

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'processing_active': processing_active,
        'processing_fps': round(processing_fps, 1),
        'num_tags_detected': len(latest_tag_positions),
        'tag_positions': latest_tag_positions
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)