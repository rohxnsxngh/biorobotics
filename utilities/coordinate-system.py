import cv2
import numpy as np
from pupil_apriltags import Detector

# Initialize AprilTag detector
detector = Detector(families='tag36h11',
                    nthreads=1,
                    quad_decimate=1.0,
                    quad_sigma=0.0,
                    refine_edges=1,
                    decode_sharpening=0.25,
                    debug=0)

# Replace with your phone's IP address and port
url = 'http://172.26.46.85:4747/video'
cap = cv2.VideoCapture(url)

# Camera parameters
fx, fy = 800, 800
cx, cy = 320, 240
camera_params = [fx, fy, cx, cy]
tag_size = 0.05  # 5cm - adjust to your actual tag size

# Define the sequential connections we want to measure
# This creates a chain: 0→1→2→3
sequential_pairs = [(0, 1), (1, 2), (2, 3)]

# Add coordinate system reference line
# Define the new base coordinate system between tag 0 and tag 5
coordinate_system_pair = (0, 5)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect AprilTags
    results = detector.detect(gray, estimate_tag_pose=True, camera_params=camera_params, tag_size=tag_size)
    
    # Filter for our tags and organize by ID
    target_tags = {}
    for r in results:
        if r.tag_id in [0, 1, 2, 3, 4, 5]:
            target_tags[r.tag_id] = r
    
    # Display how many of our target tags were found
    cv2.putText(frame, f"Target tags found: {len(target_tags)}/{6}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (0, 255, 255), 2)
    
    # Draw detection results
    tag_colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0), (255, 0, 255), (0, 255, 255)]  # Colors for tags 0,1,2,3,4,5
    for tag_id, r in target_tags.items():
        # Extract tag corners and center
        pts = r.corners.astype(np.int32).reshape((-1, 1, 2))
        center = np.mean(pts, axis=0).astype(int)[0]
        
        # Draw tag outline with specific color based on ID
        color = tag_colors[tag_id] if tag_id < len(tag_colors) else (255, 255, 255)
        cv2.polylines(frame, [pts], True, color, 2)
        
        # Draw tag ID
        cv2.putText(frame, f"ID: {r.tag_id}", 
                    (center[0], center[1]), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, color, 2)
        
        # Draw center point
        cv2.circle(frame, (center[0], center[1]), 3, color, -1)
    
    # Establish new coordinate system if tags 0 and 5 are visible
    new_coordinate_system = False
    if 0 in target_tags and 5 in target_tags:
        tag0 = target_tags[0]
        tag5 = target_tags[5]
        
        # Get centers
        center0 = np.mean(tag0.corners, axis=0).astype(int)
        center5 = np.mean(tag5.corners, axis=0).astype(int)
        
        # Draw thicker line to represent the X-axis of new coordinate system
        cv2.line(frame, tuple(center0), tuple(center5), (0, 0, 0), 3)  # Thick black line
        cv2.line(frame, tuple(center0), tuple(center5), (255, 255, 255), 1)  # White overlay
        
        # Calculate 3D distance if pose information is available
        if hasattr(tag0, 'pose_t') and hasattr(tag5, 'pose_t') and tag0.pose_t is not None and tag5.pose_t is not None:
            # Extract 3D positions
            pos0 = tag0.pose_t.reshape(3)
            pos5 = tag5.pose_t.reshape(3)
            
            # Calculate 3D Euclidean distance - this is our X-axis length
            x_axis_length = np.linalg.norm(pos5 - pos0)
            
            # Calculate unit vector from tag0 to tag5 (X-axis direction)
            x_axis_dir = (pos5 - pos0) / x_axis_length
            
            # Create a Y-axis direction perpendicular to X-axis and camera Z
            z_axis = np.array([0, 0, 1])
            y_axis_dir = np.cross(z_axis, x_axis_dir)
            y_axis_dir = y_axis_dir / np.linalg.norm(y_axis_dir)
            
            # Display coordinate system information
            cv2.putText(frame, f"X-axis length: {x_axis_length:.3f}m", 
                        (int((center0[0] + center5[0]) / 2), int((center0[1] + center5[1]) / 2) - 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, (255, 255, 255), 2)
            
            new_coordinate_system = True
    
    # Calculate distances between the sequential pairs
    distances = []
    for id1, id2 in sequential_pairs:
        if id1 in target_tags and id2 in target_tags:
            tag1 = target_tags[id1]
            tag2 = target_tags[id2]
            
            # Get centers
            center1 = np.mean(tag1.corners, axis=0).astype(int)
            center2 = np.mean(tag2.corners, axis=0).astype(int)
            
            # Draw line between centers
            cv2.line(frame, tuple(center1), tuple(center2), (255, 165, 0), 2)
            
            # Calculate 3D distance if pose information is available
            if hasattr(tag1, 'pose_t') and hasattr(tag2, 'pose_t') and tag1.pose_t is not None and tag2.pose_t is not None:
                # Extract 3D positions
                pos1 = tag1.pose_t.reshape(3)
                pos2 = tag2.pose_t.reshape(3)
                
                # Calculate 3D Euclidean distance
                dist_3d = np.linalg.norm(pos1 - pos2)
                distances.append((id1, id2, dist_3d))
                
                # Calculate midpoint for text
                mid_x = int((center1[0] + center2[0]) / 2)
                mid_y = int((center1[1] + center2[1]) / 2)
                
                # Display distance information
                cv2.putText(frame, f"{id1}->{id2}: {dist_3d:.3f}m", 
                            (mid_x, mid_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.5, (0, 165, 255), 2)
    
    # Display total length of the chain if all sequential measurements are available
    if len(distances) == len(sequential_pairs):
        total_length = sum(dist for _, _, dist in distances)
        cv2.putText(frame, f"Total length: {total_length:.3f}m", 
                    (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (255, 255, 255), 2)
    
    # Calculate deviation from straight line if we have at least 3 tags in sequence
    if len(distances) >= 2:
        # Check if we have 3 consecutive tags
        consecutive_tags = []
        for i in range(len(sequential_pairs) - 1):
            if sequential_pairs[i][1] == sequential_pairs[i+1][0]:
                if sequential_pairs[i][0] in target_tags and sequential_pairs[i][1] in target_tags and sequential_pairs[i+1][1] in target_tags:
                    consecutive_tags.append((sequential_pairs[i][0], sequential_pairs[i][1], sequential_pairs[i+1][1]))
        
        # Calculate alignment for each triplet of consecutive tags
        for id1, id2, id3 in consecutive_tags:
            center1 = np.mean(target_tags[id1].corners, axis=0)
            center2 = np.mean(target_tags[id2].corners, axis=0)
            center3 = np.mean(target_tags[id3].corners, axis=0)
            
            # Calculate vectors between centers
            v12 = center2 - center1
            v23 = center3 - center2
            
            # Normalize vectors
            v12_norm = v12 / np.linalg.norm(v12)
            v23_norm = v23 / np.linalg.norm(v23)
            
            # Calculate dot product (1.0 means perfectly aligned)
            alignment = np.dot(v12_norm, v23_norm)
            
            # Calculate angle in degrees (0° means perfectly aligned)
            angle = np.arccos(np.clip(alignment, -1.0, 1.0)) * 180 / np.pi
            
            # Display alignment information
            cv2.putText(frame, f"Alignment {id1}-{id2}-{id3}: {angle:.1f}°", 
                        (10, 90 + 30 * (id1)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, (255, 255, 0), 2)
            
            # Display status
            if angle < 5:  # Less than 5 degrees deviation
                status = "Aligned"
                color = (0, 255, 0)
            elif angle < 15:
                status = "Slight deviation"
                color = (0, 255, 255)
            else:
                status = "Misaligned"
                color = (0, 0, 255)
                
            cv2.putText(frame, f"Status: {status}", 
                        (250, 90 + 30 * (id1)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, color, 2)
    
    # Calculate and display positions in new coordinate system if established
    if new_coordinate_system:
        # Reference positions
        tag0_pos = target_tags[0].pose_t.reshape(3)
        tag5_pos = target_tags[5].pose_t.reshape(3)
        
        # Create X-axis direction vector (unit vector)
        x_axis = (tag5_pos - tag0_pos) / np.linalg.norm(tag5_pos - tag0_pos)
        
        # Y-axis is perpendicular to X-axis and camera Z-axis
        z_axis = np.array([0, 0, 1])
        y_axis = np.cross(z_axis, x_axis)
        y_axis = y_axis / np.linalg.norm(y_axis)
        
        # Display new coordinates for tags 1-4
        for tag_id in range(1, 5):
            if tag_id in target_tags:
                tag_pos = target_tags[tag_id].pose_t.reshape(3)
                
                # Vector from origin (tag 0) to current tag
                rel_pos = tag_pos - tag0_pos
                
                # Project onto our new coordinate system
                x_coord = np.dot(rel_pos, x_axis)
                y_coord = np.dot(rel_pos, y_axis)
                
                # Display the coordinates in our new system
                center = np.mean(target_tags[tag_id].corners, axis=0).astype(int)
                cv2.putText(frame, f"({x_coord:.3f}, {y_coord:.3f})m", 
                            (center[0] + 15, center[1] + 15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.5, (255, 255, 255), 2)
    
    # Display the frame
    cv2.imshow('AprilTag with Custom Coordinate System', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()