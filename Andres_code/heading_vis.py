import tkinter as tk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import sys

# ------------------------- Simulation Parameters -------------------------
dt = 0.1                        # Time step (seconds)
num_steps = 200                 # Total time steps (increased to ensure path end is reached)
L = 1.0                         # Distance from rudder to tail force
k_t = 1.0                       # Tail thrust coefficient
max_steering = math.radians(30) # Max rudder deflection (radians)
max_tail_amplitude = 1.5        # Max tail amplitude
lookahead_distance = 1.5        # Lookahead distance for heading control

# PID Gains (heading)
Kp_theta = 3.0
Ki_theta = 0.1
Kd_theta = 0.8

# PID Gains (speed)
Kp_speed = 1.2
Ki_speed = 0.1
Kd_speed = 0.6

# Desired path: from origin to (20,0)
origin = (0, 0)
end = (20, 0)

# ------------------------- Initial State & Trajectory -------------------------
state = {
    'x': 0,
    'y': np.random.uniform(-3, 3),  # Random y in [-3,3]
    'theta': 0,   # initial heading (radians)
    'v': 0        # velocity
}
rudder_angle = 0        # initial rudder angle (radians)
tail_amplitude = 0      # initial tail amplitude
time_elapsed = 0
disturbance_force = 0   # Initial disturbance force
apply_disturbance = False  # Flag to control when disturbance is applied

trajectory = np.zeros((2, num_steps))  # 2 x num_steps trajectory array

# Arrays to store servo angles and corresponding PWM values
# Modified to accommodate an additional tail servo (6 servos total now)
servo_angle_log = np.zeros((6, num_steps))
servo_pwm_log = np.zeros((6, num_steps))

# ------------------------- PID Memory -------------------------
integral_theta = 0
integral_speed = 0
prev_theta_error = 0
prev_speed_error = 0

# ------------------------- Controller Functions -------------------------
def compute_errors(state):
    x, y, theta = state['x'], state['y'], state['theta']
    lookahead_x1 = x + lookahead_distance * np.cos(theta)
    lookahead_y1 = y + lookahead_distance * np.sin(theta)
    lookahead_x2 = x + lookahead_distance
    lookahead_y2 = 0
    theta_1 = np.arctan2(lookahead_y1 - y, lookahead_x1 - x)
    theta_2 = np.arctan2(lookahead_y2 - y, lookahead_x2 - x)
    e_theta = theta_2 - theta_1
    total_time = num_steps * dt
    desired_x = origin[0] + (end[0] - origin[0]) * (time_elapsed / total_time)
    e_v = desired_x - x
    return e_theta, e_v, (lookahead_x1, lookahead_y1), (lookahead_x2, lookahead_y2)

def run_pid_controllers(state):
    global integral_theta, integral_speed, prev_theta_error, prev_speed_error, dt
    e_theta, e_v, ray1, ray2 = compute_errors(state)
    integral_theta += e_theta * dt
    derivative_theta = (e_theta - prev_theta_error) / dt
    rudder = Kp_theta * e_theta + Ki_theta * integral_theta + Kd_theta * derivative_theta
    rudder = np.clip(rudder, -max_steering, max_steering)
    prev_theta_error = e_theta
    integral_speed += e_v * dt
    derivative_speed = (e_v - prev_speed_error) / dt
    tail_amp = Kp_speed * e_v + Ki_speed * integral_speed + Kd_speed * derivative_speed
    tail_amp = np.clip(tail_amp, 0, max_tail_amplitude)
    prev_speed_error = e_v
    return rudder, tail_amp, ray1, ray2

def update_state(state, rudder, tail_amp, disturbance_force):
    # Apply the base motion model
    u_t = k_t * tail_amp**2
    state['v'] = np.clip(u_t, 0, 1.5)
    state['x'] += state['v'] * np.cos(state['theta']) * dt
    
    # Apply the disturbance force to the y-position only if active
    y_disturbance = disturbance_force * dt if apply_disturbance else 0
    state['y'] += state['v'] * np.sin(state['theta']) * dt + y_disturbance
    
    # The disturbance doesn't directly affect theta, but the PID controller will 
    # adjust the rudder to compensate for the y-displacement
    state['theta'] += (state['v'] / L) * np.tan(rudder) * dt
    
    return state

# ------------------------- GUI Setup -------------------------
root = tk.Tk()
root.title("Fish Robot Simulation")

def on_ctrl_c(event):
    root.destroy()
    sys.exit()
root.bind("<Control-c>", on_ctrl_c)

top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
middle_frame = tk.Frame(root)  # New frame for disturbance control
middle_frame.pack(fill=tk.BOTH)
bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

fig, ax = plt.subplots(figsize=(8, 4))
ax.set_xlim(-2, 22)
ax.set_ylim(-5, 5)
ax.set_title("Map View: Robot Trajectory")
ax.set_xlabel("X Position")
ax.set_ylabel("Y Position")
ax.plot([origin[0], end[0]], [origin[1], end[1]], 'k--', linewidth=2, label="Ideal Path")

# Create fish-like shape with circle body and line tail segments
fish_radius = 0.3  # Circle radius for fish body
body_circle = plt.Circle((0, 0), fish_radius, color='b', fill=True)
ax.add_patch(body_circle)

# Create tail as connected line segments - make tail longer
num_tail_segments = 5
tail_length = 2.0  # Increased total tail length from 1.2 to 2.0
segment_length = tail_length / num_tail_segments

# Create line objects for tail segments
tail_segments = []
for i in range(num_tail_segments):
    # Calculate positions for start and end of segment
    x_start = -i * segment_length
    x_end = -(i+1) * segment_length
    # Create line segment (starts with a straight horizontal line)
    segment = plt.Line2D([x_start, x_end], [0, 0], lw=4-i*0.5, color='b')  # Decreasing width
    tail_segments.append(segment)
    ax.add_line(segment)

# Group all patches for easier transformation
robot_patches = [body_circle] + tail_segments

traj_line, = ax.plot([], [], 'r-', linewidth=1.5, label="Trajectory")
ax.legend()

canvas = FigureCanvasTkAgg(fig, master=top_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
canvas.draw()

# ------------------------- Disturbance Control -------------------------
disturbance_frame = tk.Frame(middle_frame, padx=10, pady=10)
disturbance_frame.pack(fill=tk.X)

disturbance_label = tk.Label(disturbance_frame, text="Disturbance Force:", font=("Arial", 12))
disturbance_label.pack(side=tk.LEFT, padx=10)

def update_disturbance(val):
    global disturbance_force
    disturbance_force = float(val)
    disturbance_value_label.config(text=f"Value: {disturbance_force:.2f}")

# Slider for disturbance control (-1.0 to 1.0)
disturbance_slider = tk.Scale(disturbance_frame, from_=-1.0, to=1.0, resolution=0.1, 
                           orient=tk.HORIZONTAL, length=400, command=update_disturbance)
disturbance_slider.set(0)  # Initialize at 0
disturbance_slider.pack(side=tk.LEFT, padx=10)

# Label to display current disturbance value
disturbance_value_label = tk.Label(disturbance_frame, text="Value: 0.00", font=("Arial", 12))
disturbance_value_label.pack(side=tk.LEFT, padx=10)

# Add a button to apply a single disturbance pulse and then reset
def apply_disturbance_pulse():
    global apply_disturbance, disturbance_force
    
    # Apply the disturbance for 1 second
    apply_disturbance = True
    
    # Schedule to reset after 1 second
    root.after(1000, lambda: reset_disturbance())
    
    # Disable the button temporarily while disturbance is active
    disturbance_button.config(state=tk.DISABLED, bg="red", text="Applying...")
    
def reset_disturbance():
    global apply_disturbance, disturbance_force
    
    # Turn off disturbance
    apply_disturbance = False
    
    # Reset slider and force value
    disturbance_slider.set(0)
    disturbance_force = 0
    update_disturbance(0)
    
    # Re-enable the button
    disturbance_button.config(state=tk.NORMAL, bg="SystemButtonFace", text="Apply Disturbance")

disturbance_button = tk.Button(disturbance_frame, text="Apply Disturbance", 
                             command=apply_disturbance_pulse, font=("Arial", 12))
disturbance_button.pack(side=tk.LEFT, padx=20)

# ------------------------- Servo Visualization -------------------------
servo_canvas = tk.Canvas(bottom_frame, width=1000, height=300, bg="white")
servo_canvas.pack(fill=tk.BOTH, expand=True)
servo_canvas.create_text(500, 20, text="Servo Simulation", font=("Arial", 16), fill="black")

# Modified to include an additional tail segment
servo_order = ["tail1", "tail2", "tail3", "tail4", "tail5", "head"]
servo_data = []
dial_radius = 60
dial_line_length = 40
servo_spacing = 1000 // 7  # Adjusted spacing for 6 servos

# Creating 6 servos instead of 5
for i in range(6):
    dial_center_x = servo_spacing * (i + 1)
    dial_center_y = 150

    # adding circle at base (smaller)
    servo_canvas.create_oval(
        dial_center_x - 15, dial_center_y - 15, 
        dial_center_x + 15, dial_center_y + 15, 
        fill="lightgray", outline="black"
    )

    # Make lines face backwards (180 degrees offset)
    line_id = servo_canvas.create_line(dial_center_x, dial_center_y, 
                                       dial_center_x - dial_line_length, dial_center_y, width=3, fill="blue")
    servo_data.append({
        "center_x": dial_center_x,
        "center_y": dial_center_y,
        "line": line_id
    })

servo_text_ids = {}
for i, key in enumerate(servo_order):
    pos = servo_data[i]
    text_id = servo_canvas.create_text(pos["center_x"], pos["center_y"] - dial_radius - 10,
                                       text=f"{key}: 0", font=("Arial", 14), fill="black")
    servo_text_ids[key] = text_id

def update_servo(angle, servo_index):
    servo = servo_data[servo_index]
    # Add 180 degrees (π radians) to make the servo face backwards
    radians = math.radians(angle) + math.pi
    cx, cy = servo["center_x"], servo["center_y"]
    x2 = cx + dial_line_length * math.cos(radians)
    y2 = cy + dial_line_length * math.sin(radians)
    servo_canvas.coords(servo["line"], cx, cy, x2, y2)
    key = servo_order[servo_index]
    servo_canvas.itemconfig(servo_text_ids[key], text=f"{key}: {angle:.1f}")

# ------------------------- Simulation Loop -------------------------
current_step = 0

def simulation_step():
    global state, time_elapsed, current_step, trajectory, dt, disturbance_force
    # Run simulation continuously by resetting when reaching end or boundary
    if state['x'] >= end[0]:
        # Reset position but keep other state variables
        state['x'] = 0
        state['y'] = np.random.uniform(-3, 3)
        state['theta'] = 0
        state['v'] = 0
        # Clear trajectory
        trajectory = np.zeros((2, num_steps))
        current_step = 0
        time_elapsed = 0
    
    # Run the simulation step
    rudder, tail_amp, ray1, ray2 = run_pid_controllers(state)
    state_updated = update_state(state, rudder, tail_amp, disturbance_force)
    state.update(state_updated)
    
    # Update trajectory data for plotting
    if current_step < num_steps:
        trajectory[:, current_step] = [state['x'], state['y']]
    
    # Calculate tail amplitude in degrees
    tail_amp_deg = (tail_amp / max_tail_amplitude) * 60
    
    # Update fish body position
    body_circle.center = (state['x'], state['y'])
    
    # Rotation for fish orientation
    theta = state['theta']
    
    # Update tail segments (as lines)
    prev_x, prev_y = state['x'], state['y']
    
    for i, segment in enumerate(tail_segments):
        # Base position calculation
        segment_length = tail_length / num_tail_segments
        
        # Calculate wave pattern with increasing amplitude toward tail end
        wave_factor = tail_amp_deg * (i + 1) / num_tail_segments * 0.02  # Increased wave factor
        angle_offset = math.sin(2 * math.pi * 2 * (current_step * dt) + math.radians(45 * i)) * wave_factor
        
        # Calculate endpoint of this segment
        total_angle = theta + angle_offset
        dx = segment_length * math.cos(total_angle - math.pi)  # Point backward
        dy = segment_length * math.sin(total_angle - math.pi)
        
        # Update segment coordinates
        segment.set_xdata([prev_x, prev_x + dx])
        segment.set_ydata([prev_y, prev_y + dy])
        
        # The end of this segment becomes the start of the next
        prev_x += dx
        prev_y += dy
    
    # Update trajectory line
    if current_step < num_steps:
        traj_line.set_data(trajectory[0, :current_step+1], trajectory[1, :current_step+1])
    
    canvas.draw()
    
    # Update servos and store angles
    angles_this_step = []

    # Updated to handle 5 tail segments instead of 4
    for i in range(5):
        # Calculate angle for visualization
        angle = tail_amp_deg * math.sin(2 * math.pi * 2 * (current_step * dt) + math.radians(45 * i))  
        update_servo(angle, i)
        angles_this_step.append(angle)

    head_angle = math.degrees(rudder)
    update_servo(head_angle, 5)
    angles_this_step.append(head_angle)

    # Store angles and PWM values
    if current_step < num_steps:
        for i in range(6):
            servo_angle_log[i, current_step] = angles_this_step[i]
            servo_pwm_log[i, current_step] = 1500 + (angles_this_step[i] / 90.0) * 500

    # Increment step counter
    globals()['current_step'] = (current_step + 1) % num_steps  # Use modulo to wrap around
    globals()['time_elapsed'] += dt
    
    # Continue simulation indefinitely
    root.after(int(dt*1000), simulation_step)

try:
    simulation_step()
    root.mainloop()
except KeyboardInterrupt:
    print("Simulation terminated by user.")
    sys.exit()