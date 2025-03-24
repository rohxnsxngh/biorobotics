import cv2
import numpy as np
from pupil_apriltags import Detector
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from threading import Thread
import time

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

# PID Controller Parameters
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

# Shared data between threads
shared_data = {
    'robot_pos': None,
    'target_pos': (20, 0),
    'origin_pos': (0, 0),
    'trajectory_x': [],
    'trajectory_y': [],
    'rudder_angle': 0,
    'tail_amplitude': 0,
    'thrust': 0,
    'heading_error': 0,
    'running': True
}

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

# Function to run the Matplotlib visualization in a separate thread
def run_visualization():
    # Create Tkinter window
    root = tk.Tk()
    root.title("Robot Trajectory Visualization")
    root.geometry("800x600")
    
    # Create matplotlib figure
    fig = plt.Figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Add the plot to the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    # Control panel frame
    control_frame = tk.Frame(root)
    control_frame.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Control information labels
    heading_label = tk.Label(control_frame, text="Heading Error: 0.0°")
    heading_label.pack(side=tk.LEFT, padx=10)
    
    rudder_label = tk.Label(control_frame, text="Rudder: 0.0°")
    rudder_label.pack(side=tk.LEFT, padx=10)
    
    tail_label = tk.Label(control_frame, text="Tail: 0.0")
    tail_label.pack(side=tk.LEFT, padx=10)
    
    thrust_label = tk.Label(control_frame, text="Thrust: 0.0")
    thrust_label.pack(side=tk.LEFT, padx=10)
    
    position_label = tk.Label(control_frame, text="Position: (0.00, 0.00)")
    position_label.pack(side=tk.LEFT, padx=10)
    
    # Function to update the plot
    def update_plot():
        if not shared_data['running']:
            root.quit()
            return
            
        # Clear the axis
        ax.clear()
        
        # Get latest data
        robot_pos = shared_data['robot_pos']
        target_pos = shared_data['target_pos']
        origin_pos = shared_data['origin_pos']
        trajectory_x = shared_data['trajectory_x'].copy()
        trajectory_y = shared_data['trajectory_y'].copy()
        
        # Update control information
        if robot_pos:
            heading_label.config(text=f"Heading Error: {np.degrees(shared_data['heading_error']):.1f}°")
            rudder_label.config(text=f"Rudder: {np.degrees(shared_data['rudder_angle']):.1f}°")
            tail_label.config(text=f"Tail: {shared_data['tail_amplitude']:.2f}")
            thrust_label.config(text=f"Thrust: {shared_data['thrust']:.2f}")
            position_label.config(text=f"Position: ({robot_pos[0]:.2f}, {robot_pos[1]:.2f})")
        
        # Plot trajectory if we have data
        if robot_pos and len(trajectory_x) > 1:
            # Plot the trajectory
            ax.plot(trajectory_x, trajectory_y, 'b-', linewidth=2)
            
            # Plot robot position
            ax.scatter(robot_pos[0], robot_pos[1], color='g', marker='o', s=100, label='Robot')
            
            # Plot target position
            ax.scatter(target_pos[0], target_pos[1], color='r', marker='x', s=100, label='Target')
            
            # Plot origin
            ax.scatter(origin_pos[0], origin_pos[1], color='k', marker='+', s=100, label='Origin')
            
            # Draw line from origin to target to show ideal path
            ax.plot([origin_pos[0], target_pos[0]], [origin_pos[1], target_pos[1]], 'k--', alpha=0.5)
            
            # Add robot heading arrow
            if robot_pos and 'theta' in robot_state:
                arrow_length = 0.5
                dx = arrow_length * np.cos(robot_state['theta'])
                dy = arrow_length * np.sin(robot_state['theta'])
                ax.arrow(robot_pos[0], robot_pos[1], dx, dy, 
                         head_width=0.2, head_length=0.3, fc='g', ec='g')
            
            # Set labels and grid
            ax.set_xlabel('X Position (m)')
            ax.set_ylabel('Y Position (m)')
            ax.set_title('Robot Trajectory')
            ax.grid(True)
            ax.legend(loc='upper right')
            
            # Set limits with some padding
            max_x = max(max(trajectory_x + [target_pos[0]]) + 2, 25)
            min_x = min(min(trajectory_x + [origin_pos[0]]) - 2, -5)
            max_y = max(max(trajectory_y + [target_pos[1]]) + 2, 5)
            min_y = min(min(trajectory_y + [origin_pos[1]]) - 2, -5)
            
            ax.set_xlim(min_x, max_x)
            ax.set_ylim(min_y, max_y)
            
            # Ensure aspect ratio is equal
            ax.set_aspect('equal')
        
        # Draw the canvas
        canvas.draw()
        
        # Schedule the next update
        root.after(100, update_plot)
    
    # Start the update loop
    root.after(100, update_plot)
    
    # Run the Tkinter event loop
    root.mainloop()

# Start the visualization thread
viz_thread = Thread(target=run_visualization)
viz_thread.daemon = True
viz_thread.start()

# Main loop for AprilTag detection and control
try:
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
                    shared_data['trajectory_x'].append(x_coord)
                    shared_data['trajectory_y'].append(y_coord)
                    
                    # Limit trajectory size
                    if len(shared_data['trajectory_x']) > max_trajectory_points:
                        shared_data['trajectory_x'].pop(0)
                        shared_data['trajectory_y'].pop(0)
                    
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
            
            # Update shared data for visualization thread
            shared_data['robot_pos'] = robot_pos
            shared_data['target_pos'] = target_pos
            shared_data['origin_pos'] = origin_pos
            shared_data['rudder_angle'] = rudder_angle
            shared_data['tail_amplitude'] = tail_amplitude
            shared_data['thrust'] = thrust
            shared_data['heading_error'] = theta_error
        
        # Display the frame
        cv2.imshow('AprilTag Navigation System', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    # Cleanup
    shared_data['running'] = False
    cap.release()
    cv2.destroyAllWindows()
    
    # Give visualization thread time to close
    time.sleep(0.5)