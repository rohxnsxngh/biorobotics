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

# Define the coordinate system reference - using tags 0 and 2
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

# Function to calculate heading from tag corners
def calculate_heading_from_corners(corners, coord_system):
    """Calculate heading based on the tag's corner orientation."""
    # AprilTag corners are ordered: top-left, top-right, bottom-right, bottom-left
    # We'll use the vector from center to front (top edge midpoint) to determine heading
    
    # Calculate center point
    center = np.mean(corners, axis=0)
    
    # Calculate the midpoint of the top edge (front of the tag)
    front_midpoint = (corners[0] + corners[1]) / 2
    
    # Vector from center to front in camera coordinates
    heading_vector = front_midpoint - center
    
    # Normalize the vector
    heading_vector = heading_vector / np.linalg.norm(heading_vector)
    
    # Project this vector onto our coordinate system
    # Add a z-coordinate of 0 for 3D projection
    heading_vector_3d = np.array([heading_vector[0], heading_vector[1], 0])
    
    # Project onto custom coordinate system
    heading_x = np.dot(heading_vector_3d, coord_system['x_axis'])
    heading_y = np.dot(heading_vector_3d, coord_system['y_axis'])
    
    # Calculate the heading angle in our coordinate system
    theta = np.arctan2(heading_y, heading_x)
    
    return theta, heading_vector

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
            theta_deg = np.rad2deg(shared_data.get('robot_theta', 0))
            position_label.config(text=f"Robot Position: X={robot_pos[0]:.3f}, Y={robot_pos[1]:.3f}, Heading={theta_deg:.1f}°")
        
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
                
                # Format data to send - X, Y coordinates and heading
                x, y = shared_data['robot_pos']
                theta = shared_data['robot_theta']
                theta_deg = np.rad2deg(theta)
                
                # Calculate distance to target (using the x-axis length as our target)
                x_axis_length = shared_data.get('x_axis_length', 0)
                distance_to_target = x_axis_length - x if x_axis_length > 0 else 0
                
                # Data packet with position and heading
                data = {
                    'x': round(x, 3),
                    'y': round(y, 3),
                    'theta': round(theta_deg, 1),
                    'distance': round(distance_to_target, 3)
                }
                
                # Send to Arduino
                if send_to_arduino(data):
                    shared_data['last_sent_data'] = f"X: {data['x']}, Y: {data['y']}, Theta: {data['theta']}°, Dist: {data['distance']}m"
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
        
        # Filter for tags 0, 1, and 2
        target_tags = {}
        for r in results:
            if r.tag_id in [0, 1, 2]:  # Only need tags 0, 1, and 2
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
        
        # Colors for tags 0, 1, 2
        tag_colors = [(0, 0, 255), (0, 255, 0), (255, 0, 255)]  # Red, Green, Magenta
        
        # Draw detected tags
        for tag_id, r in target_tags.items():
            # Extract tag corners and center
            pts = r.corners.astype(np.int32).reshape((-1, 1, 2))
            center = np.mean(pts, axis=0).astype(int)[0]
            
            # Draw tag outline with specific color based on ID
            color = tag_colors[tag_id]
            cv2.polylines(frame, [pts], True, color, 2)
            
            # Draw tag ID
            cv2.putText(frame, f"ID: {r.tag_id}", 
                        (center[0], center[1]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, color, 2)
            
            # Draw center point
            cv2.circle(frame, (center[0], center[1]), 3, color, -1)
            
            # Number the corners (for debugging)
            for i, corner in enumerate(r.corners.astype(np.int32)):
                cv2.putText(frame, str(i), 
                           (corner[0], corner[1]), 
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           0.4, (255, 255, 0), 1)
        
        # Check if we have our coordinate system reference tags (0 and 2)
        new_coordinate_system = False
        if 0 in target_tags and 2 in target_tags:
            tag0 = target_tags[0]
            tag2 = target_tags[2]
            
            # Get centers
            center0 = np.mean(tag0.corners, axis=0).astype(int)
            center2 = np.mean(tag2.corners, axis=0).astype(int)
            
            # Draw line to represent the X-axis of coordinate system
            cv2.line(frame, tuple(center0), tuple(center2), (0, 0, 0), 3)  # Thick black line
            cv2.line(frame, tuple(center0), tuple(center2), (255, 255, 255), 1)  # White overlay
            
            # Calculate 3D distance if pose information is available
            if hasattr(tag0, 'pose_t') and hasattr(tag2, 'pose_t') and tag0.pose_t is not None and tag2.pose_t is not None:
                # Extract 3D positions
                pos0 = tag0.pose_t.reshape(3)
                pos2 = tag2.pose_t.reshape(3)
                
                # Calculate 3D Euclidean distance - this is our X-axis length
                x_axis_length = np.linalg.norm(pos2 - pos0)
                
                # Update shared data
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
        
        # Calculate robot position and heading if coordinate system established and tag 1 is visible
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
            
            # Calculate heading using corners method
            theta, heading_vector = calculate_heading_from_corners(tag1.corners, coord_system)
            theta_deg = np.rad2deg(theta)
            
            # Draw heading vector (direction the tag is facing)
            # Convert heading vector to pixels for visualization
            scale_factor = 50
            head_x = center[0] + int(heading_vector[0] * scale_factor)
            head_y = center[1] + int(heading_vector[1] * scale_factor)
            cv2.arrowedLine(frame, tuple(center), (head_x, head_y), (0, 255, 0), 2)
            
            # Draw the top edge (front) of the tag
            front_midpoint = ((tag1.corners[0][0] + tag1.corners[1][0])/2, 
                              (tag1.corners[0][1] + tag1.corners[1][1])/2)
            front_midpoint = (int(front_midpoint[0]), int(front_midpoint[1]))
            cv2.circle(frame, front_midpoint, 5, (255, 255, 0), -1)
            
            # Display the coordinates and heading in our new system
            cv2.putText(frame, f"Robot: ({x_coord:.2f}, {y_coord:.2f})m, {theta_deg:.1f}°", 
                        (center[0] + 15, center[1] + 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, (255, 255, 255), 2)
            
            # Store robot position and heading
            shared_data['robot_pos'] = (x_coord, y_coord)
            shared_data['robot_theta'] = theta
            
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