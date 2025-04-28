import cv2
import numpy as np
from pupil_apriltags import Detector
import csv
import datetime

# Initialize AprilTag detector
detector = Detector(families='tag36h11',
                    nthreads=1,
                    quad_decimate=1.0,
                    quad_sigma=0.0,
                    refine_edges=1,
                    decode_sharpening=0.25,
                    debug=0)

# Connect to USB camera
cap = cv2.VideoCapture(1)  # Try index 1 first for USB connection

# If camera index 1 doesn't work, try index 0
if not cap.isOpened():
    print("Failed to open camera at index 1, trying index 0...")
    cap = cv2.VideoCapture(0)

# If both failed, let user know
if not cap.isOpened():
    print("Failed to open camera. Please check your USB connection.")
    exit()

# Camera parameters - using the same as in the original script
fx, fy = 1280, 720
cx, cy = 640, 360
camera_params = [fx, fy, cx, cy]
tag_size = 0.05  # 5cm - adjust to your actual tag size

# Create CSV file with timestamp in filename
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"apriltag1_track_{timestamp}.csv"

with open(csv_filename, 'w', newline='') as csvfile:
    # Create CSV writer
    csv_writer = csv.writer(csvfile)
    
    # Write header
    csv_writer.writerow(['Timestamp', 'Tag_ID', 'u', 'v', 'x', 'y', 'z'])
    
    # Main loop
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect AprilTags
        results = detector.detect(gray, estimate_tag_pose=True, camera_params=camera_params, tag_size=tag_size)
        
        # Current timestamp for this frame
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Flag to track if we found tag 1
        tag1_found = False
        
        # Look specifically for tag ID 1
        for r in results:
            if r.tag_id == 1:
                tag1_found = True
                
                # Extract tag center (u,v coordinates in the image)
                center = np.mean(r.corners, axis=0)
                u, v = center
                
                # Get 3D position if available
                x, y, z = 0, 0, 0
                if hasattr(r, 'pose_t') and r.pose_t is not None:
                    x, y, z = r.pose_t.reshape(3)
                
                # Write to CSV
                csv_writer.writerow([current_time, r.tag_id, u, v, x, y, z])
                csvfile.flush()  # Make sure data is written immediately
                
                # Display that we found and saved tag 1
                print(f"Tag 1 detected at ({u:.2f}, {v:.2f}) - Data saved to {csv_filename}")
                
                # Draw detection on frame
                pts = r.corners.astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
                center_point = tuple(center.astype(int))
                cv2.circle(frame, center_point, 5, (0, 255, 0), -1)
                cv2.putText(frame, f"ID: 1 ({u:.1f}, {v:.1f})", 
                           (center_point[0] + 10, center_point[1]), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                break  # Found tag 1, no need to process others
        
        # Display status on frame
        if tag1_found:
            status_text = "Tag 1 DETECTED - Saving data"
            status_color = (0, 255, 0)  # Green
        else:
            status_text = "Waiting for Tag 1..."
            status_color = (0, 0, 255)  # Red
        
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.7, status_color, 2)
        cv2.putText(frame, f"Recording to: {csv_filename}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Display the frame
        cv2.imshow('AprilTag 1 Tracker', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
print(f"Tracking complete. Data saved to {csv_filename}")