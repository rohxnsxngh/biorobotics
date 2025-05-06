import cv2
import numpy as np
from pupil_apriltags import Detector
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Initialize AprilTag detector
detector = Detector(families='tag36h11',
                    nthreads=1,
                    quad_decimate=1.0,
                    quad_sigma=0.0,
                    refine_edges=1,
                    decode_sharpening=0.25,
                    debug=0)

# Camera setup
cap = cv2.VideoCapture(1)  # Try index 1 for external camera

# Check if the camera is opened successfully
if not cap.isOpened():
    print("Failed to open camera at index 1, trying index 0...")
    cap = cv2.VideoCapture(0)  # Try index 0 for built-in camera

if not cap.isOpened():
    print("Failed to open camera. Please check your USB connection.")
    exit()

# Camera parameters
fx, fy = 1280, 720  # These should match your camera's resolution if possible
cx, cy = 640, 360   # Half of the resolution values above
camera_params = [fx, fy, cx, cy]
tag_size = 0.05  # 5cm - adjust to your actual tag size

# Function to create AprilTag position visualization
def create_apriltag_position_plot(tag_positions, origin_pos=(0, 0)):
    # Create figure and axes
    fig = Figure(figsize=(8, 6), dpi=100)  # Larger figure size
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    
    # Plot each tag position
    for tag_id, position in tag_positions.items():
        if tag_id == 0:  # Start point
            # Apply offset to tag 0
            adjusted_position = (position[0], position[1] - 0.05)
            ax.scatter(adjusted_position[0], adjusted_position[1], color='g', marker='o', s=100, label='Start (Tag 0)')
        elif tag_id == 7:  # End point
            # Apply offset to tag 7
            adjusted_position = (position[0], position[1] - 0.05)
            ax.scatter(adjusted_position[0], adjusted_position[1], color='r', marker='x', s=100, label='End (Tag 7)')
        elif tag_id == 1:  # Tag 1 as yellow triangle
            ax.scatter(position[0], position[1], color='yellow', marker='^', s=120, label='Tag 1')
            ax.text(position[0]+0.01, position[1]+0.01, f"{tag_id}", fontsize=9)
        else:  # Other tags
            ax.scatter(position[0], position[1], color='b', marker='.', s=80)
            ax.text(position[0]+0.01, position[1]+0.01, f"{tag_id}", fontsize=9)
    
    # Draw connections between tags if they exist in specific order
    connection_pairs = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
    for start_id, end_id in connection_pairs:
        if start_id in tag_positions and end_id in tag_positions:
            start_pos = tag_positions[start_id]
            end_pos = tag_positions[end_id]
            ax.plot([start_pos[0], end_pos[0]], [start_pos[1], end_pos[1]], 'k--', alpha=0.5)
    
    # Set labels and grid
    ax.set_xlabel('X Position (m)')
    ax.set_ylabel('Y Position (m)')
    ax.set_title('AprilTag Positions')
    ax.grid(True)
    
    # Set axis limits as requested
    ax.set_xlim(-0.25, 0.5)
    ax.set_ylim(0.35, -0.15)  # Reversed Y-axis (high to low)
    
    # Add legend only if we have start and end points
    if 0 in tag_positions or 7 in tag_positions:
        ax.legend(loc='upper right')
    
    # Ensure aspect ratio is equal
    ax.set_aspect('equal')
    
    # Convert plot to OpenCV image
    canvas.draw()
    plot_image = np.array(canvas.renderer.buffer_rgba())
    plot_image = cv2.cvtColor(plot_image, cv2.COLOR_RGBA2BGR)
    
    return plot_image

# Main loop to capture video feed
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame.")
        break
    
    # Convert to grayscale for AprilTag detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect AprilTags
    results = detector.detect(gray, estimate_tag_pose=True, camera_params=camera_params, tag_size=tag_size)
    
    # Process detection results
    target_tags = {}
    for r in results:
        if r.tag_id in [0, 1, 2, 3, 4, 5, 6, 7]:
            target_tags[r.tag_id] = r
    
    # Display the number of detected target tags
    cv2.putText(frame, f"Target tags found: {len(target_tags)}/{8}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (0, 255, 255), 2)
    
    # Draw detection results
    tag_colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), 
                 (255, 255, 0), (255, 0, 255), (0, 255, 255), (128, 128, 128), (255, 255, 255)]
    
    tag_centers = {}
    tag_positions = {}  # Store 3D positions for plotting
    
    for tag_id, r in target_tags.items():
        pts = r.corners.astype(np.int32).reshape((-1, 1, 2))
        center = np.mean(pts, axis=0).astype(int)[0]
        tag_centers[tag_id] = center
        color = tag_colors[tag_id] if tag_id < len(tag_colors) else (255, 255, 255)
        cv2.polylines(frame, [pts], True, color, 2)
        cv2.putText(frame, f"ID: {r.tag_id}", 
                    (center[0], center[1]), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, color, 2)
        cv2.circle(frame, (center[0], center[1]), 3, color, -1)
        
        # Store tag positions for plot
        if hasattr(r, 'pose_t') and r.pose_t is not None:
            tag_pos = r.pose_t.reshape(3)
            tag_positions[tag_id] = (tag_pos[0], tag_pos[1])  # Store x,y coordinates
    
    # Draw connections between tags
    connection_pairs = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
    for start_id, end_id in connection_pairs:
        if start_id in tag_centers and end_id in tag_centers:
            start_center = tag_centers[start_id]
            end_center = tag_centers[end_id]
            cv2.line(frame, tuple(start_center), tuple(end_center), (255, 255, 0), 3)  # Yellow
    
    # Handling coordinate system
    if 0 in target_tags and 7 in target_tags:
        tag0 = target_tags[0]
        tag7 = target_tags[7]
        
        center0 = np.mean(tag0.corners, axis=0).astype(int)
        center7 = np.mean(tag7.corners, axis=0).astype(int)
        
        cv2.line(frame, tuple(center0), tuple(center7), (0, 0, 0), 3)  # Thick black line
        cv2.line(frame, tuple(center0), tuple(center7), (255, 255, 255), 1)  # White overlay
        
        if hasattr(tag0, 'pose_t') and hasattr(tag7, 'pose_t') and tag0.pose_t is not None and tag7.pose_t is not None:
            pos0 = tag0.pose_t.reshape(3)
            pos7 = tag7.pose_t.reshape(3)
            x_axis_length = np.linalg.norm(pos7 - pos0)
            
            x_axis_dir = (pos7 - pos0) / x_axis_length
            z_axis = np.array([0, 0, 1])
            y_axis_dir = np.cross(z_axis, x_axis_dir)
            y_axis_dir = y_axis_dir / np.linalg.norm(y_axis_dir)
            
            cv2.putText(frame, f"X-axis length: {x_axis_length:.3f}m", 
                        (int((center0[0] + center7[0]) / 2), int((center0[1] + center7[1]) / 2) - 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, (255, 255, 255), 2)
            
            coord_system = {
                'origin': pos0,  
                'x_axis': x_axis_dir,
                'y_axis': y_axis_dir,
                'z_axis': np.cross(x_axis_dir, y_axis_dir)
            }
    
    # Create and display AprilTag position plot if we have any positions
    if tag_positions:
        plot_img = create_apriltag_position_plot(tag_positions)
        plot_h, plot_w = plot_img.shape[:2]
        
        # Create a larger plot area - use 40% of the camera frame height
        desired_height = frame.shape[0] * 0.4
        scale = desired_height / plot_h
        plot_img = cv2.resize(plot_img, (int(plot_w * scale), int(plot_h * scale)))
        plot_h, plot_w = plot_img.shape[:2]
        
        # Create a separate window for the plot instead of overlaying it
        cv2.imshow("AprilTag Positions", plot_img)
    
    # Show the frame
    cv2.imshow("Camera Feed", frame)
    
    # Break the loop on 'q' press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()