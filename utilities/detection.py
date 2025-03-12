import cv2
import numpy as np
from pupil_apriltags import Detector

# Initialize AprilTag detector
# You can try different tag families if 'tag36h11' isn't working
detector = Detector(families='tag25h9', 
                    nthreads=1,
                    quad_decimate=1.0,  # Try 2.0 for better performance
                    quad_sigma=0.0,
                    refine_edges=1,
                    decode_sharpening=0.25,
                    debug=0)

# Replace with your phone's IP address and port
url = 'http://172.26.65.246:4747/video'
cap = cv2.VideoCapture(url)

# Placeholder camera parameters - these don't affect detection, only pose estimation
fx, fy = 800, 800
cx, cy = 320, 240
camera_params = [fx, fy, cx, cy]
tag_size = 0.05  # 5cm

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Add frame counter and dimensions for debugging
    frame_count += 1
    height, width = gray.shape
    cv2.putText(frame, f"Frame: {frame_count} Size: {width}x{height}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (0, 255, 255), 2)
    
    # Detect AprilTags
    results = detector.detect(gray, estimate_tag_pose=True, camera_params=camera_params, tag_size=tag_size)
    
    # Add detection count
    cv2.putText(frame, f"Tags detected: {len(results)}", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (0, 255, 255), 2)
    
    # Draw detection results
    for r in results:
        # Extract tag corners
        pts = r.corners.astype(np.int32).reshape((-1, 1, 2))
        
        # Draw tag outline
        cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
        
        # Draw tag ID
        center = np.mean(pts, axis=0).astype(int)
        cv2.putText(frame, f"ID: {r.tag_id}", 
                    tuple(center[0]), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, (0, 0, 255), 2)
        
        # Print debug info about the detection
        print(f"Detected tag ID: {r.tag_id}, Center: {center}, Corners: {r.corners}")
        
        # Calculate and display distance
        if hasattr(r, 'pose_t') and r.pose_t is not None:
            # The third element of pose_t is the Z distance (in meters)
            distance = r.pose_t[2][0]
            cv2.putText(frame, f"Dist: {distance:.2f}m", 
                        (center[0][0], center[0][1] + 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, (255, 0, 0), 2)
    
    # Display the frame
    cv2.imshow('AprilTag Detection', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()