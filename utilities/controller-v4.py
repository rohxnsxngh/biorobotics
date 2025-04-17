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
url = 'http://192.168.4.2:4747/video'
cap = cv2.VideoCapture(url)

# Camera parameters
fx, fy = 800, 800
cx, cy = 320, 240
camera_params = [fx, fy, cx, cy]
tag_size = 0.05  # 5cm - adjust to your actual tag size

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

# Target path information
target_start = (0, 0)
target_end = (20, 0)  # This will be dynamically updated based on the actual tag distance

# Shared data between threads
shared_data = {
    'robot_pos': None,
    'robot_theta': 0,
    'target_pos': target_end,
    'origin_pos': target_start,
    'x_axis_length': 0,
    'running': True,
    'update_simulation': False,
    'scale_changed': False
}

# Function to calculate a complete trajectory simulation from current position
def simulate_trajectory(start_pos, start_theta, target_pos):
    # Simulation parameters
    num_steps = 200
    
    # Create arrays to store the trajectory
    trajectory_x = [start_pos[0]]
    trajectory_y = [start_pos[1]]
    
    # Initial state
    state = {
        'x': start_pos[0],
        'y': start_pos[1],
        'theta': start_theta,
        'v': 0
    }
    
    # PID memory for simulation
    integral_theta = 0
    integral_speed = 0
    prev_theta_error = 0
    prev_speed_error = 0
    
    # Simulation loop
    for i in range(num_steps):
        # Compute desired direction vector (from robot to target)
        dx = target_pos[0] - state['x']
        dy = target_pos[1] - state['y']
        desired_theta = np.arctan2(dy, dx)
        
        # Compute lookahead points for heading control
        lookahead_x1 = state['x'] + lookahead_distance * np.cos(state['theta'])
        lookahead_y1 = state['y'] + lookahead_distance * np.sin(state['theta'])
        lookahead_x2 = state['x'] + lookahead_distance * np.cos(desired_theta)
        lookahead_y2 = state['y'] + lookahead_distance * np.sin(desired_theta)
        
        # Compute theta error (difference between current and desired heading)
        theta_error = np.arctan2(np.sin(desired_theta - state['theta']), np.cos(desired_theta - state['theta']))
        
        # Distance to target
        distance_to_target = np.sqrt(dx**2 + dy**2)
        
        # If we're close to the target, we're done
        if distance_to_target < 0.1:
            break
            
        # Speed error (distance to target, projected on heading direction)
        speed_error = distance_to_target * np.cos(desired_theta - state['theta'])
        
        # Heading PID
        integral_theta += theta_error * dt
        derivative_theta = (theta_error - prev_theta_error) / dt
        rudder_angle = Kp_theta * theta_error + Ki_theta * integral_theta + Kd_theta * derivative_theta
        rudder_angle = np.clip(rudder_angle, -max_steering, max_steering)
        prev_theta_error = theta_error
        
        # Speed PID
        integral_speed += speed_error * dt
        derivative_speed = (speed_error - prev_speed_error) / dt
        tail_amplitude = Kp_speed * speed_error + Ki_speed * integral_speed + Kd_speed * derivative_speed
        tail_amplitude = np.clip(tail_amplitude, 0, max_tail_amplitude)
        prev_speed_error = speed_error
        
        # Calculate forward thrust
        u_t = k_t * tail_amplitude**2
        
        # Update state using the bicycle model
        state['v'] = min(max(u_t, 0), 1.5)
        state['x'] += state['v'] * np.cos(state['theta']) * dt
        state['y'] += state['v'] * np.sin(state['theta']) * dt
        state['theta'] += (state['v'] / L) * np.tan(rudder_angle) * dt
        
        # Store trajectory
        trajectory_x.append(state['x'])
        trajectory_y.append(state['y'])
    
    return trajectory_x, trajectory_y

# Function to run the Matplotlib visualization in a separate thread
def run_simulation_window():
    # Create Tkinter window for simulation
    sim_root = tk.Tk()
    sim_root.title("Robot Trajectory Simulation")
    sim_root.geometry("800x600")
    
    # Create matplotlib figure
    fig = plt.Figure(figsize=(10, 8), dpi=100)
    ax = fig.add_subplot(111)
    
    # Add the plot to the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=sim_root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    # Control panel frame
    control_frame = tk.Frame(sim_root)
    control_frame.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Control information labels
    position_label = tk.Label(control_frame, text="Robot Position: (0.00, 0.00)")
    position_label.pack(side=tk.LEFT, padx=10)
    
    distance_label = tk.Label(control_frame, text="Tag 0 to Tag 5: 0.00 m")
    distance_label.pack(side=tk.LEFT, padx=10)
    
    # Create plots for ideal path and current position
    ideal_line, = ax.plot([], [], 'k--', label='Ideal Path')
    robot_point, = ax.plot([], [], 'go', markersize=10, label='Current Position')
    target_point, = ax.plot([], [], 'rx', markersize=10, label='Target')
    
    # Variable to store the current simulated trajectory
    simulation_line, = ax.plot([], [], 'b-', linewidth=2, label='Simulated Trajectory')
    
    # Set labels and grid
    ax.set_xlabel('X Position (m)')
    ax.set_ylabel('Y Position (m)')
    ax.set_title('Robot Trajectory using PID and Lookahead Control')
    ax.grid(True)
    ax.legend(loc='upper right')
    
    # Initial axis limits - will be updated when we get actual measurements
    ax.set_xlim(-5, 25)
    ax.set_ylim(-8, 8)
    ax.set_aspect('equal')
    
    # Function to update the simulation plot
    def update_simulation_plot():
        if not shared_data['running']:
            sim_root.quit()
            return
            
        robot_pos = shared_data.get('robot_pos')
        target_pos = shared_data.get('target_pos', target_end)
        origin_pos = shared_data.get('origin_pos', target_start)
        robot_theta = shared_data.get('robot_theta', 0)
        x_axis_length = shared_data.get('x_axis_length', 0)
        
        # Update distance label
        distance_label.config(text=f"Tag 0 to Tag 5: {x_axis_length:.2f} m")
        
        # Update axis limits if the scale changed
        if shared_data.get('scale_changed', False):
            # Calculate appropriate axis limits
            if x_axis_length > 0:
                x_margin = x_axis_length * 0.25  # 25% margin on each side
                y_margin = x_axis_length * 0.4   # Use same scale for y
                
                ax.set_xlim(-x_margin, x_axis_length + x_margin)
                ax.set_ylim(-y_margin, y_margin)
                
                # Update plot title to reflect the actual scale
                ax.set_title(f'Robot Trajectory (Scale: {x_axis_length:.2f}m between tags)')
                
                shared_data['scale_changed'] = False
        
        # Update position label if we have a robot position
        if robot_pos:
            position_label.config(text=f"Robot Position: ({robot_pos[0]:.2f}, {robot_pos[1]:.2f})")
        
        # Update ideal path
        ideal_line.set_data([origin_pos[0], target_pos[0]], [origin_pos[1], target_pos[1]])
        
        # Update robot and target positions
        if robot_pos:
            robot_point.set_data([robot_pos[0]], [robot_pos[1]])
            target_point.set_data([target_pos[0]], [target_pos[1]])
            
            # Simulate trajectory if requested
            if shared_data.get('update_simulation', False):
                sim_x, sim_y = simulate_trajectory(robot_pos, robot_theta, target_pos)
                simulation_line.set_data(sim_x, sim_y)
                shared_data['update_simulation'] = False
                
                # Calculate y-axis padding based on the simulation results
                if len(sim_y) > 0:
                    y_min = min(min(sim_y) - 1, -4)
                    y_max = max(max(sim_y) + 1, 4)
                    
                    # Don't let the y limits be too extreme
                    y_range = max(y_max - y_min, x_axis_length * 0.5)
                    y_center = (y_min + y_max) / 2
                    
                    # Set y limits with proper centering and scale
                    ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
        
        # Draw the canvas
        canvas.draw()
        
        # Schedule the next update
        sim_root.after(100, update_simulation_plot)
    
    # Start the update loop
    sim_root.after(100, update_simulation_plot)
    
    # Run the Tkinter event loop
    sim_root.mainloop()

# Start the visualization thread
viz_thread = Thread(target=run_simulation_window)
viz_thread.daemon = True
viz_thread.start()

# Track last position to detect movement
last_robot_pos = None
position_change_threshold = 0.1  # meters

# Variable to track the last measured x-axis length
last_x_axis_length = 0

# Main loop for AprilTag detection
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
            if r.tag_id in [0, 4, 5]:  # We only need tags 0, 4, and 5 now
                target_tags[r.tag_id] = r
        
        # Display how many of our target tags were found
        cv2.putText(frame, f"Target tags found: {len(target_tags)}/{3}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (0, 255, 255), 2)
        
        # Draw detection results
        tag_colors = [(0, 0, 255), (255, 0, 255), (0, 255, 255)]  # Colors for tags 0, 4, 5
        for tag_id, r in target_tags.items():
            # Get the index for the color
            color_idx = 0 if tag_id == 0 else 1 if tag_id == 4 else 2
            
            # Extract tag corners and center
            pts = r.corners.astype(np.int32).reshape((-1, 1, 2))
            center = np.mean(pts, axis=0).astype(int)[0]
            
            # Draw tag outline with specific color based on ID
            color = tag_colors[color_idx]
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
                
                # Check if the axis length has changed significantly
                if abs(x_axis_length - last_x_axis_length) > 0.05:  # 5cm threshold
                    shared_data['scale_changed'] = True
                    last_x_axis_length = x_axis_length
                
                shared_data['x_axis_length'] = x_axis_length
                
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
                
                # Update shared origin and target positions based on coordinate system
                shared_data['origin_pos'] = (0, 0)
                shared_data['target_pos'] = (x_axis_length, 0)  # Target is at the end of our x-axis
        
        # Initialize robot position 
        robot_pos = None
        robot_theta = 0
        
        # Calculate positions in new coordinate system if established
        if new_coordinate_system and 4 in target_tags:
            tag4 = target_tags[4]
            tag_pos = tag4.pose_t.reshape(3)
            
            # Vector from origin (tag 0) to current tag
            rel_pos = tag_pos - coord_system['origin']
            
            # Project onto our new coordinate system
            x_coord = np.dot(rel_pos, coord_system['x_axis'])
            y_coord = np.dot(rel_pos, coord_system['y_axis'])
            
            # Get center of tag in image
            center = np.mean(tag4.corners, axis=0).astype(int)
            
            # Display the coordinates in our new system
            cv2.putText(frame, f"Robot: ({x_coord:.2f}, {y_coord:.2f})m", 
                        (center[0] + 15, center[1] + 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, (255, 255, 255), 2)
            
            # Store robot position
            robot_pos = (x_coord, y_coord)
            
            # Calculate robot orientation (theta)
            rot_matrix = cv2.Rodrigues(tag4.pose_R)[0]
            yaw = np.arctan2(rot_matrix[1, 0], rot_matrix[0, 0])
            
            # Transform to our coordinate system
            robot_heading_vec = np.array([np.cos(yaw), np.sin(yaw), 0])
            robot_heading_x = np.dot(robot_heading_vec, coord_system['x_axis'])
            robot_heading_y = np.dot(robot_heading_vec, coord_system['y_axis'])
            robot_theta = np.arctan2(robot_heading_y, robot_heading_x)
            
            # Draw robot heading vector
            heading_length = 0.5  # in meters
            head_x = center[0] + int(heading_length * 100 * np.cos(robot_theta))
            head_y = center[1] + int(heading_length * 100 * np.sin(robot_theta))
            cv2.arrowedLine(frame, tuple(center), (head_x, head_y), (0, 255, 0), 2)
            
            # Update shared data
            shared_data['robot_pos'] = robot_pos
            shared_data['robot_theta'] = robot_theta
            
            # Check if the position has changed significantly
            if last_robot_pos:
                distance_moved = np.sqrt((robot_pos[0] - last_robot_pos[0])**2 + (robot_pos[1] - last_robot_pos[1])**2)
                if distance_moved > position_change_threshold:
                    # Position changed significantly, trigger a new simulation
                    shared_data['update_simulation'] = True
                    last_robot_pos = robot_pos
            else:
                # First detection, trigger a simulation
                shared_data['update_simulation'] = True
                last_robot_pos = robot_pos
            
            # Add message about simulation
            cv2.putText(frame, "Simulating trajectory in separate window", 
                        (10, frame.shape[0] - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, (0, 255, 0), 2)
        
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