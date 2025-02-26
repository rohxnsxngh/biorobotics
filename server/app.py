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
    global latest_frame
    
    if latest_frame is None:
        return jsonify({'error': 'No frame available'}), 404
    
    try:
        # Make a copy of the frame
        frame = latest_frame.copy()
        
        # Detect AprilTags and draw them on the frame
        detected_tags = detect_april_tags(frame)
        
        # Draw the detections on the frame
        for tag in detected_tags:
            # Draw tag perimeter
            corners = np.array(tag['corners'], np.int32)
            corners = corners.reshape((-1, 1, 2))
            cv2.polylines(frame, [corners], True, (0, 255, 0), 2)
            
            # Draw tag center
            center = tag['center']
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
            
            # Put tag ID
            cv2.putText(frame, f"ID: {tag['id']}", 
                       (center[0] + 10, center[1] + 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Add debug info to the image
        cv2.putText(frame, f"FPS: {round(processing_fps, 1)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Tags: {len(detected_tags)}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Convert to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        
        # Convert to base64
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'image': f'data:image/jpeg;base64,{img_base64}',
            'num_tags': len(detected_tags)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def detect_april_tags(frame):
    """
    Process the frame to detect AprilTags with improved detection
    This is a placeholder for actual AprilTag detection
    """
    # Convert to grayscale for tag detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding to better handle varying lighting conditions
    thresholded = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Basic morphological operations to clean up the image
    kernel = np.ones((3, 3), np.uint8)
    thresholded = cv2.morphologyEx(thresholded, cv2.MORPH_OPEN, kernel)
    thresholded = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)
    
    # Draw the thresholded image in a corner for debugging
    h, w = frame.shape[:2]
    small_thresh = cv2.resize(thresholded, (w//4, h//4))
    frame[10:10+h//4, 10:10+w//4] = cv2.cvtColor(small_thresh, cv2.COLOR_GRAY2BGR)
    
    # Find contours
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Detected tags
    detected_tags = []
    
    # Process each contour
    for i, contour in enumerate(contours):
        # Filter small contours
        if cv2.contourArea(contour) < 100:
            continue
            
        # Find the approximate polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # If it has 4 corners, it might be a tag
        if len(approx) == 4:
            # Get the corners in the right order
            corners = approx.reshape(-1, 2)
            
            # Calculate center
            center_x = int(np.mean(corners[:, 0]))
            center_y = int(np.mean(corners[:, 1]))
            
            # Add to detected tags
            detected_tags.append({
                'id': i,
                'center': (center_x, center_y),
                'corners': corners.tolist()
            })
    
    return detected_tags

def process_frames():
    global latest_frame, latest_tag_positions, processing_active
    
    processing_active = True
    
    while processing_active:
        if latest_frame is not None:
            # Make a copy of the frame to avoid race conditions
            frame = latest_frame.copy()
            
            # Detect AprilTags
            detected_tags = detect_april_tags(frame)
            
            # Draw the detections on the frame
            for tag in detected_tags:
                # Draw tag perimeter
                corners = np.array(tag['corners'], np.int32)
                corners = corners.reshape((-1, 1, 2))
                cv2.polylines(frame, [corners], True, (0, 255, 0), 2)
                
                # Draw tag center
                center = tag['center']
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
                
                # Put tag ID
                cv2.putText(frame, f"ID: {tag['id']}", 
                           (center[0] + 10, center[1] + 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Display the processed frame (optional)
            cv2.imshow('Processed Frame', frame)
            cv2.waitKey(1)
            
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