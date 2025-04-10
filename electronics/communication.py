import cv2
import numpy as np
from pupil_apriltags import Detector
import tkinter as tk
from threading import Thread
import time
import serial
import json

# Serial communication setup
SERIAL_PORT = 'COM3'  # Change to your Arduino port
BAUD_RATE = 9600
arduino = None

def initialize_arduino():
    global arduino
    try:
        arduino = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for connection to establish
        print(f"Connected to Arduino on {SERIAL_PORT}")
        return True
    except Exception as e:
        print(f"Failed to connect to Arduino: {e}")
        return False

# Function to send data to Arduino
def send_to_arduino(data_dict):
    if arduino is None or not arduino.is_open:
        return False
    
    # Convert dict to JSON string
    json_data = json.dumps(data_dict)
    
    # Add newline for Arduino parsing
    message = json_data + "\n"
    
    try:
        arduino.write(message.encode('utf-8'))
        return True
    except Exception as e:
        print(f"Error sending data to Arduino: {e}")
        return False

# Function to read from Arduino
def read_from_arduino():
    if arduino is None or not arduino.is_open:
        return None
    
    if arduino.in_waiting > 0:
        try:
            line = arduino.readline().decode('utf-8').strip()
            return line
        except Exception as e:
            print(f"Error reading from Arduino: {e}")
    
    return None

# Initialize AprilTag detector
detector = Detector(families='tag36h11',
                    nthreads=1,
                    quad_decimate=1.0,
                    quad_sigma=0.0,
                    refine_edges=1,
                    decode_sharpening=0.25,
                    debug=0)

# Replace with your phone's IP address and port or use 0 for webcam
url = 'http://172.26.0.244:4747/video'
# Uncomment the line below to use webcam
# cap = cv2.VideoCapture(0)
cap = cv2.VideoCapture(url)

# Camera parameters
fx, fy = 800, 800
cx, cy = 320, 240
camera_params = [fx, fy, cx, cy]
tag_size = 0.05  # 5cm - adjust to your actual tag size

# Define the coordinate system reference - MODIFIED: Now using tags 0 and 2
coordinate_system_pair = (0, 2)

# Shared data between threads
shared_data = {
    'robot_pos': None,
    'robot_theta': 0,
    'x_axis_length': 0,
    'running': True,
    'arduino_connected': False,
    'arduino_response': None,
    'last_sent_data': None,
    'send_interval': 0.5,  # Send data every 0.5 seconds
    'last_send_time': 0
}

# Function to run the simple status window
def run_status_window():
    # Create Tkinter window for status
    status_root = tk.Tk()
    status_root.title("Arduino Communication Status")
    status_root.geometry("600x200")
    
    # Create main frame
    main_frame = tk.Frame(status_root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Create labels for status information
    title_label = tk.Label(main_frame, text="Arduino Communication Monitor", font=("Arial", 14, "bold"))
    title_label.pack(pady=(0, 20))
    
    position_label = tk.Label(main_frame, text="Robot Position: Not detected", font=("Arial", 12))
    position_label.pack(pady=5)
    
    connection_label = tk.Label(main_frame, text="Arduino: Not Connected", fg="red", font=("Arial", 12))
    connection_label.pack(pady=5)
    
    sent_label = tk.Label(main_frame, text="Last Sent: None", font=("Arial", 12))
    sent_label.pack(pady=5)
    
    response_label = tk.Label(main_frame, text="Response: None", font=("Arial", 12))
    response_label.pack(pady=5)
    
    # Auto-connect to Arduino
    def auto_connect_arduino():
        if initialize_arduino():
            shared_data['arduino_connected'] = True
            connection_label.config(text="Arduino: Connected", fg="green")
            print("Arduino connected automatically")
        else:
            print("Failed to auto-connect to Arduino")
    
    # Schedule auto-connect after 2 seconds
    status_root.after(2000, auto_connect_arduino)
    
    # Function to update status information
    def update_status():
        if not shared_data['running']:
            status_root.quit()
            return
        
        # Update position info
        robot_pos = shared_data.get('robot_pos')
        if robot_pos:
            position_label.config(text=f"Robot Position: X={robot_pos[0]:.3f}, Y={robot_pos[1]:.3f}, "
                                      f"Theta={np.rad2deg(shared_data.get('robot_theta', 0)):.1f}°")
        
        # Update connection status
        if shared_data.get('arduino_connected', False):
            connection_label.config(text="Arduino: Connected", fg="green")
        else:
            connection_label.config(text="Arduino: Not Connected", fg="red")
        
        # Update sent data
        last_sent = shared_data.get('last_sent_data')
        if last_sent:
            sent_label.config(text=f"Last Sent: {last_sent}")
        
        # Update received data
        response = shared_data.get('arduino_response')
        if response:
            response_label.config(text=f"Response: {response}")
        
        # Schedule next update
        status_root.after(100, update_status)
    
    # Start the update loop
    status_root.after(100, update_status)
    
    # Run the Tkinter event loop
    status_root.mainloop()

# Thread function to handle Arduino communication
def arduino_communication_thread():
    last_time = time.time()
    
    while shared_data['running']:
        current_time = time.time()
        
        # Only proceed if Arduino is connected
        if shared_data.get('arduino_connected', False) and arduino and arduino.is_open:
            # Read from Arduino
            response = read_from_arduino()
            if response:
                shared_data['arduino_response'] = response
                print(f"Arduino says: {response}")  # Print to console as well
            
            # Send data to Arduino if we have position data and enough time has passed
            if (current_time - last_time > shared_data['send_interval'] and 
                shared_data.get('robot_pos') is not None):
                
                # Format data to send
                x, y = shared_data['robot_pos']
                theta = shared_data['robot_theta']
                
                # Convert to degrees for easier Arduino handling
                theta_deg = np.rad2deg(theta)
                
                # Calculate distance to target (using the x-axis length as our target)
                distance_to_target = shared_data.get('x_axis_length', 0) - x
                
                # Calculate angle to target (assuming target is at x-axis)
                angle_to_target = np.arctan2(-y, distance_to_target)
                rel_angle = np.arctan2(np.sin(angle_to_target - theta), np.cos(angle_to_target - theta))
                rel_angle_deg = np.rad2deg(rel_angle)
                
                # Enhanced data packet with more navigation-related information
                data = {
                    'x': round(x, 3),
                    'y': round(y, 3),
                    'theta': round(theta_deg, 2),
                    'distance': round(distance_to_target, 3),
                    'rel_angle': round(rel_angle_deg, 2)
                }
                
                # Send to Arduino
                if send_to_arduino(data):
                    shared_data['last_sent_data'] = f"X: {data['x']}, Y: {data['y']}, Theta: {data['theta']}°, Dist: {data['distance']}m, Angle: {data['rel_angle']}°"
                    last_time = current_time
                    print(f"Sent to Arduino: {shared_data['last_sent_data']}")  # Print to console
        
        # Sleep to prevent high CPU usage
        time.sleep(0.1)

# Start the status window thread
status_thread = Thread(target=run_status_window)
status_thread.daemon = True
status_thread.start()

# Start the Arduino communication thread
arduino_thread = Thread(target=arduino_communication_thread)
arduino_thread.daemon = True
arduino_thread.start()

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
        
        # MODIFIED: Now filtering for tags 0, 1, and 2
        target_tags = {}
        for r in results:
            if r.tag_id in [0, 1, 2]:  # We only need tags 0, 1, and 2 now
                target_tags[r.tag_id] = r
        
        # Display how many of our target tags were found
        cv2.putText(frame, f"Target tags found: {len(target_tags)}/{3}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (0, 255, 255), 2)
        
        # Display Arduino connection status
        arduino_status = "Connected" if shared_data.get('arduino_connected', False) else "Not Connected"
        arduino_color = (0, 255, 0) if shared_data.get('arduino_connected', False) else (0, 0, 255)
        cv2.putText(frame, f"Arduino: {arduino_status}", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, arduino_color, 2)
        
        # MODIFIED: Updated colors for tags 0, 1, 2
        tag_colors = [(0, 0, 255), (0, 255, 0), (255, 0, 255)]  # Colors for tags 0, 1, 2
        for tag_id, r in target_tags.items():
            # Get the index for the color
            color_idx = tag_id  # Direct mapping since we're using tags 0, 1, 2
            
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
        
        # MODIFIED: Check if we have our coordinate system reference tags (0 and 2)
        new_coordinate_system = False
        if 0 in target_tags and 2 in target_tags:
            tag0 = target_tags[0]
            tag2 = target_tags[2]
            
            # Get centers
            center0 = np.mean(tag0.corners, axis=0).astype(int)
            center2 = np.mean(tag2.corners, axis=0).astype(int)
            
            # Draw thicker line to represent the X-axis of new coordinate system
            cv2.line(frame, tuple(center0), tuple(center2), (0, 0, 0), 3)  # Thick black line
            cv2.line(frame, tuple(center0), tuple(center2), (255, 255, 255), 1)  # White overlay
            
            # Calculate 3D distance if pose information is available
            if hasattr(tag0, 'pose_t') and hasattr(tag2, 'pose_t') and tag0.pose_t is not None and tag2.pose_t is not None:
                # Extract 3D positions
                pos0 = tag0.pose_t.reshape(3)
                pos2 = tag2.pose_t.reshape(3)
                
                # Calculate 3D Euclidean distance - this is our X-axis length
                x_axis_length = np.linalg.norm(pos2 - pos0)
                
                # Check if the axis length has changed significantly
                if abs(x_axis_length - last_x_axis_length) > 0.05:  # 5cm threshold
                    last_x_axis_length = x_axis_length
                
                shared_data['x_axis_length'] = x_axis_length
                
                # Calculate unit vector from tag0 to tag2 (X-axis direction)
                x_axis_dir = (pos2 - pos0) / x_axis_length
                
                # Create a Y-axis direction perpendicular to X-axis and camera Z
                z_axis = np.array([0, 0, 1])
                y_axis_dir = np.cross(z_axis, x_axis_dir)
                y_axis_dir = y_axis_dir / np.linalg.norm(y_axis_dir)
                
                # Display coordinate system information
                cv2.putText(frame, f"X-axis length: {x_axis_length:.3f}m", 
                            (int((center0[0] + center2[0]) / 2), int((center0[1] + center2[1]) / 2) - 15), 
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
        
        # Initialize robot position 
        robot_pos = None
        robot_theta = 0
        
        # MODIFIED: Calculate positions in new coordinate system if established and tag 1 is visible
        if new_coordinate_system and 1 in target_tags:
            tag1 = target_tags[1]
            tag_pos = tag1.pose_t.reshape(3)
            
            # Vector from origin (tag 0) to current tag
            rel_pos = tag_pos - coord_system['origin']
            
            # Project onto our new coordinate system
            x_coord = np.dot(rel_pos, coord_system['x_axis'])
            y_coord = np.dot(rel_pos, coord_system['y_axis'])
            
            # Get center of tag in image
            center = np.mean(tag1.corners, axis=0).astype(int)
            
            # Display the coordinates in our new system
            cv2.putText(frame, f"Robot: ({x_coord:.2f}, {y_coord:.2f})m", 
                        (center[0] + 15, center[1] + 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, (255, 255, 255), 2)
            
            # Store robot position
            robot_pos = (x_coord, y_coord)
            
            # Calculate robot orientation (theta)
            rot_matrix = cv2.Rodrigues(tag1.pose_R)[0]
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
            
            # Display latest Arduino response if available
            arduino_response = shared_data.get('arduino_response')
            if arduino_response:
                cv2.putText(frame, f"Arduino: {arduino_response[:40]}", 
                            (10, frame.shape[0] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.6, (255, 165, 0), 2)
        
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
    
    # Close Arduino connection if open
    if arduino and arduino.is_open:
        arduino.close()
        print("Arduino connection closed")
    
    # Give threads time to close
    time.sleep(0.5)