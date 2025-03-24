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

# Replace with your phone's IP address and port
url = 'http://172.26.46.85:4747/video'
cap = cv2.VideoCapture(url)

# Camera parameters
fx, fy = 800, 800
cx, cy = 320, 240
camera_params = [fx, fy, cx, cy]
tag_size = 0.05  # 5cm - adjust to your actual tag size

# Define the sequential connections we want to measure
sequential_pairs = [(0, 1), (1, 2), (2, 3)]

# Define the coordinate system reference
coordinate_system_pair = (0, 5)

# PID Controller Parameters from the trajectory calculation function
dt = 0.1
L = 1.0  # Distance from rudder to tail force
k_t = 1.0
max_steering = np.deg2rad(30)
max_tail_amplitude = 1.5
lookahead_distance = 1.5

# PID Gains
Kp_theta = 3.0
Ki_theta = 0.5
Kd_theta = 1.0
Kp_speed = 1.2
Ki_speed = 0.1
Kd_speed = 0.6

# PID memory
integral_theta = 0
integral_speed = 0
prev_theta_error = 0
prev_speed_error = 0

# Robot state
robot_state = {
    'x': 0,
    'y': 0,
    'theta': 0,
    'v': 0
}

# Trajectory points
trajectory_x = []
trajectory_y = []
max_trajectory_points = 100  # Maximum number of points to keep in trajectory

# Function to calculate control signals
def calculate_control_step(robot_pos, target_pos, current_state, dt, integral_theta, integral_speed, prev_theta_error, prev_speed_error):
    # Extract positions
    robot_x, robot_y = robot_pos
    target_x, target_y = target_pos
    
    # Compute desired direction vector (from robot to target)
    dx = target_x - robot_x
    dy = target_y - robot_y
    desired_theta = np.arctan2(dy, dx)
    
    # Normalize angles
    current_theta = current_state['theta']
    
    # Compute lookahead points for heading control
    lookahead_x1 = robot_x + lookahead_distance * np.cos(current_theta)
    lookahead_y1 = robot_y + lookahead_distance * np.sin(current_theta)
    lookahead_x2 = robot_x + lookahead_distance * np.cos(desired_theta)
    lookahead_y2 = robot_y + lookahead_distance * np.sin(desired_theta)
    
    # Compute theta error (difference between current and desired heading)
    theta_error = np.arctan2(np.sin(desired_theta - current_theta), np.cos(desired_theta - current_theta))
    
    # Speed error (distance to target, projected on heading direction)
    distance_to_target = np.sqrt(dx**2 + dy**2)
    speed_error = distance_to_target * np.cos(desired_theta - current_theta)
    
    # Heading PID
    integral_theta += theta_error * dt
    derivative_theta = (theta_error - prev_theta_error) / dt
    rudder_angle = Kp_theta * theta_error + Ki_theta * integral_theta + Kd_theta * derivative_theta
    rudder_angle = np.clip(rudder_angle, -max_steering, max_steering)
    
    # Speed PID
    integral_speed += speed_error * dt
    derivative_speed = (speed_error - prev_speed_error) / dt
    tail_amplitude = Kp_speed * speed_error + Ki_speed * integral_speed + Kd_speed * derivative_speed
    tail_amplitude = np.clip(tail_amplitude, 0, max_tail_amplitude)
    
    # Calculate forward thrust
    u_t = k_t * tail_amplitude**2
    
    # Return control signals and updated PID memory
    return rudder_angle, tail_amplitude, u_t, integral_theta, integral_speed, theta_error, speed_error

# Function to create a trajectory visualization
def create_trajectory_plot(robot_pos, target_pos, trajectory_x, trajectory_y, origin_pos=(0,0)):
    # Create figure and axes
    fig = Figure(figsize=(4, 3), dpi=100)
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    
    # Plot trajectory
    if len(trajectory_x) > 1:
        ax.plot(trajectory_x, trajectory_y, 'b-', linewidth=2)
    
    # Plot robot position
    ax.scatter(robot_pos[0], robot_pos[1], color='g', marker='o', s=100, label='Robot')
    
    # Plot target position
    ax.scatter(target_pos[0], target_pos[1], color='r', marker='x', s=100, label='Target')
    
    # Plot origin
    ax.scatter(origin_pos[0], origin_pos[1], color='k', marker='+', s=100, label='Origin')
    
    # Draw line from origin to target to show ideal path
    ax.plot([origin_pos[0], target_pos[0]], [origin_pos[1], target_pos[1]], 'k--', alpha=0.5)
    
    # Set labels and grid
    ax.set_xlabel('X Position (m)')
    ax.set_ylabel('Y Position (m)')
    ax.set_title('Robot Trajectory')
    ax.grid(True)
    ax.legend(loc='upper right')
    
    # Ensure aspect ratio is equal
    ax.set_aspect('equal')
    
    # Convert plot to OpenCV image
    canvas.draw()
    plot_image = np.array(canvas.renderer.buffer_rgba())
    plot_image = cv2.cvtColor(plot_image, cv2.COLOR_RGBA2BGR)
    
    return plot_image

# Main loop
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
    
    # Check if we have our coordinate system reference tags
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
            
            # Create coordinate transformation data
            coord_system = {
                'origin': pos0,
                'x_axis': x_axis_dir,
                'y_axis': y_axis_dir,
                'z_axis': np.cross(x_axis_dir, y_axis_dir)
            }
    
    # Initialize robot position and target
    robot_pos = None
    origin_pos = (0, 0)
    target_pos = (20, 0)  # Default target position at 20 meters along X-axis
    
    # Calculate positions in new coordinate system if established
    if new_coordinate_system:
        # Reference positions
        origin_pos = (0, 0)  # Tag 0 is our origin
        
        # Calculate positions of all tags in our new coordinate system
        for tag_id, tag in target_tags.items():
            tag_pos = tag.pose_t.reshape(3)
            
            # Vector from origin (tag 0) to current tag
            rel_pos = tag_pos - coord_system['origin']
            
            # Project onto our new coordinate system
            x_coord = np.dot(rel_pos, coord_system['x_axis'])
            y_coord = np.dot(rel_pos, coord_system['y_axis'])
            
            # Display the coordinates in our new system
            center = np.mean(tag.corners, axis=0).astype(int)
            cv2.putText(frame, f"({x_coord:.2f}, {y_coord:.2f})m", 
                        (center[0] + 15, center[1] + 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, (255, 255, 255), 2)
            
            # Store robot position (tag 4)
            if tag_id == 4:
                robot_pos = (x_coord, y_coord)
                
                # Calculate robot orientation (theta)
                # We need to extract orientation from the tag pose
                rot_matrix = cv2.Rodrigues(tag.pose_R)[0]
                yaw = np.arctan2(rot_matrix[1, 0], rot_matrix[0, 0])
                
                # Transform to our coordinate system
                robot_heading_vec = np.array([np.cos(yaw), np.sin(yaw), 0])
                robot_heading_x = np.dot(robot_heading_vec, coord_system['x_axis'])
                robot_heading_y = np.dot(robot_heading_vec, coord_system['y_axis'])
                robot_theta = np.arctan2(robot_heading_y, robot_heading_x)
                
                # Update robot state
                robot_state['x'] = x_coord
                robot_state['y'] = y_coord
                robot_state['theta'] = robot_theta
                
                # Add point to trajectory
                trajectory_x.append(x_coord)
                trajectory_y.append(y_coord)
                
                # Limit trajectory size
                if len(trajectory_x) > max_trajectory_points:
                    trajectory_x.pop(0)
                    trajectory_y.pop(0)
                
                # Draw robot heading vector
                heading_length = 0.5  # in meters
                head_x = center[0] + int(heading_length * 100 * np.cos(robot_theta))
                head_y = center[1] + int(heading_length * 100 * np.sin(robot_theta))
                cv2.arrowedLine(frame, tuple(center), (head_x, head_y), (0, 255, 0), 2)
    
    # Calculate and display control signals if we have robot position
    if robot_pos is not None and new_coordinate_system:
        # Calculate control step
        rudder_angle, tail_amplitude, thrust, integral_theta, integral_speed, theta_error, speed_error = calculate_control_step(
            robot_pos, target_pos, robot_state, dt, integral_theta, integral_speed, prev_theta_error, prev_speed_error)
        
        # Update PID memory
        prev_theta_error = theta_error
        prev_speed_error = speed_error
        
        # Display control signals
        info_y = 390
        cv2.putText(frame, f"Robot: ({robot_pos[0]:.2f}, {robot_pos[1]:.2f})m", 
                    (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        info_y += 20
        cv2.putText(frame, f"Target: ({target_pos[0]:.2f}, {target_pos[1]:.2f})m", 
                    (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        info_y += 20
        cv2.putText(frame, f"Heading error: {np.degrees(theta_error):.1f}°", 
                    (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        info_y += 20
        cv2.putText(frame, f"Rudder angle: {np.degrees(rudder_angle):.1f}°", 
                    (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        info_y += 20
        cv2.putText(frame, f"Tail amplitude: {tail_amplitude:.2f}", 
                    (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        info_y += 20
        cv2.putText(frame, f"Thrust: {thrust:.2f}", 
                    (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Create and display trajectory plot
        if len(trajectory_x) > 0:
            plot_img = create_trajectory_plot(robot_pos, target_pos, trajectory_x, trajectory_y)
            plot_h, plot_w = plot_img.shape[:2]
            
            # Scale if necessary
            max_height = 240
            if plot_h > max_height:
                scale = max_height / plot_h
                plot_img = cv2.resize(plot_img, (int(plot_w * scale), int(plot_h * scale)))
            
            # Insert plot into the frame
            h, w = plot_img.shape[:2]
            frame[frame.shape[0]-h:frame.shape[0], frame.shape[1]-w:frame.shape[1]] = plot_img
    
    # Display the frame
    cv2.imshow('AprilTag Navigation System', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()