# Improved controller visual sim.py
import tkinter as tk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import sys

# ------------------------- Simulation Parameters -------------------------
dt = 0.05                       # Time step (seconds) - Faster simulation (half the time step)
num_steps = 300                # Total time steps (increased to ensure path end is reached)
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

trajectory = np.zeros((2, num_steps))  # 2 x num_steps trajectory array

# Arrays to store servo angles and corresponding PWM values
servo_angle_log = np.zeros((5, num_steps))
servo_pwm_log = np.zeros((5, num_steps))

# ------------------------- PID Memory -------------------------
integral_theta = 0
integral_speed = 0
prev_theta_error = 0
prev_speed_error = 0

# ------------------------- Controller Functions -------------------------
def compute_errors(state):
    """
    Compute lookahead-based heading error and speed error.
    """
    x, y, theta = state['x'], state['y'], state['theta']
    
    # Ray 1: in the direction the robot is currently facing
    lookahead_x1 = x + lookahead_distance * np.cos(theta)
    lookahead_y1 = y + lookahead_distance * np.sin(theta)
    
    # Ray 2: same length, aimed directly horizontally (desired y = 0)
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
    """
    Compute rudder angle and tail amplitude using PID controllers.
    """
    global integral_theta, integral_speed, prev_theta_error, prev_speed_error, dt
    e_theta, e_v, ray1, ray2 = compute_errors(state)
    
    # Heading PID
    integral_theta += e_theta * dt
    derivative_theta = (e_theta - prev_theta_error) / dt
    rudder = Kp_theta * e_theta + Ki_theta * integral_theta + Kd_theta * derivative_theta
    rudder = np.clip(rudder, -max_steering, max_steering)
    prev_theta_error = e_theta
    
    # Speed PID
    integral_speed += e_v * dt
    derivative_speed = (e_v - prev_speed_error) / dt
    tail_amp = Kp_speed * e_v + Ki_speed * integral_speed + Kd_speed * derivative_speed
    tail_amp = np.clip(tail_amp, 0, max_tail_amplitude)
    prev_speed_error = e_v
    
    return rudder, tail_amp, ray1, ray2

def update_state(state, rudder, tail_amp):
    """
    Update the robot state using a bicycle model.
    """
    u_t = k_t * tail_amp**2
    state['v'] = np.clip(u_t, 0, 1.5)
    state['x'] += state['v'] * np.cos(state['theta']) * dt
    state['y'] += state['v'] * np.sin(state['theta']) * dt
    state['theta'] += (state['v'] / L) * np.tan(rudder) * dt
    return state

# ------------------------- GUI Setup -------------------------
root = tk.Tk()
root.title("Fish Robot Simulation")

# Bind Ctrl+C to close the simulation
def on_ctrl_c(event):
    root.destroy()
    sys.exit()
root.bind("<Control-c>", on_ctrl_c)

top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

# ----- Top Section: Map View (Matplotlib) -----
fig, ax = plt.subplots(figsize=(8, 4))
ax.set_xlim(-2, 22)
ax.set_ylim(-5, 5)
ax.set_title("Map View: Robot Trajectory")
ax.set_xlabel("X Position")
ax.set_ylabel("Y Position")
ax.plot([origin[0], end[0]], [origin[1], end[1]], 'k--', linewidth=2, label="Ideal Path")

# Define robot shape with articulated segments
head_size = 0.6
segment_length = 0.5
segment_width = 0.4
num_segments = 4  # Number of tail segments

# Create head (square)
head = plt.Rectangle((-head_size/2, -head_size/2), head_size, head_size, 
                     color='blue', alpha=0.8)
ax.add_patch(head)

# Create tail segments (rectangles)
tail_segments = []
for i in range(num_segments):
    segment = plt.Rectangle((-head_size/2-(i+1)*segment_length, -segment_width/2), 
                           segment_length, segment_width, 
                           color='blue', alpha=0.7 - i*0.1)  # Decreasing alpha for fade effect
    ax.add_patch(segment)
    tail_segments.append(segment)

# Arrays to store segment angles and positions
segment_angles = [0] * num_segments
segment_positions = [(0, 0)] * num_segments

# Initialize plots for trajectory and look-ahead rays
traj_line, = ax.plot([], [], 'r-', linewidth=1.5, label="Trajectory")
ray1_line, = ax.plot([], [], 'g-', linewidth=1.5, label="Current Direction") # Green ray (current heading)
ray2_line, = ax.plot([], [], 'm-', linewidth=1.5, label="Target Direction")   # Magenta ray (desired heading)

ax.legend()

canvas = FigureCanvasTkAgg(fig, master=top_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
canvas.draw()

# ----- Bottom Section: Servo Simulation (Tkinter Canvas) -----
servo_canvas = tk.Canvas(bottom_frame, width=1000, height=300, bg="white")
servo_canvas.pack(fill=tk.BOTH, expand=True)
servo_canvas.create_text(500, 20, text="Servo Simulation", font=("Arial", 16))

# Create servo dials: We want the tail servos on the left and the head servo on the right.
# We'll define five servo dials; we'll label them with the order: tail1, tail2, tail3, tail4, head.
servo_order = ["tail1", "tail2", "tail3", "tail4", "head"]
servo_data = []
dial_radius = 60
dial_line_length = 40
servo_spacing = 1000 // 6  # Divide canvas width into 6 parts

# Create servo dials
for i in range(5):
    dial_center_x = servo_spacing * (i + 1)
    dial_center_y = 150  # vertical center
    line_id = servo_canvas.create_line(dial_center_x, dial_center_y, 
                                         dial_center_x + dial_line_length, dial_center_y, width=2)
    servo_data.append({
        "center_x": dial_center_x,
        "center_y": dial_center_y,
        "line": line_id
    })

# Create text labels for each servo with increased font size.
servo_text_ids = {}
for i, key in enumerate(servo_order):
    pos = servo_data[i]
    text_id = servo_canvas.create_text(pos["center_x"], pos["center_y"] - dial_radius - 10,
                                         text=f"{key}: 0", font=("Arial", 14))
    servo_text_ids[key] = text_id

def update_servo(angle, servo_index):
    """Update the dial line for a specific servo based on angle (in degrees)."""
    servo = servo_data[servo_index]
    radians = math.radians(angle)
    cx, cy = servo["center_x"], servo["center_y"]
    x2 = cx + dial_line_length * math.cos(radians)
    y2 = cy - dial_line_length * math.sin(radians)
    servo_canvas.coords(servo["line"], cx, cy, x2, y2)
    # Also update the corresponding text label.
    key = servo_order[servo_index]
    servo_canvas.itemconfig(servo_text_ids[key], text=f"{key}: {angle:.1f}")

# ------------------------- Simulation Loop -------------------------
current_step = 0

def simulation_step():
    global state, time_elapsed, current_step, trajectory, dt
    if current_step < num_steps and state['x'] < end[0]:
        rudder, tail_amp, ray1, ray2 = run_pid_controllers(state)
        state_updated = update_state(state, rudder, tail_amp)
        state.update(state_updated)
        trajectory[:, current_step] = [state['x'], state['y']]
        
        # Update robot visualization (head and tail segments)
        # Update head position and orientation
        head_transform = matplotlib.transforms.Affine2D().rotate(state['theta']).translate(state['x'], state['y'])
        head.set_transform(head_transform + ax.transData)
        
        # Update tail segments with sinusoidal motion
        tail_amp_rad = tail_amp * 0.3 # Use the tail amplitude from controller
        wave_freq = 3.0  # Wave frequency parameter
        
        for i, segment in enumerate(tail_segments):
            # Calculate phase shift based on segment position (propagating wave)
            phase_shift = -i * np.pi / 4  # Progressive phase shift for wave effect
            
            # Calculate segment angle relative to heading
            # This creates a sinusoidal wave that propagates along the tail
            segment_angle = tail_amp_rad * np.sin(wave_freq * time_elapsed + phase_shift)
            
            # Position depends on previous segments
            if i == 0:
                # First segment connects to the head
                prev_x = state['x'] - head_size/2 * np.cos(state['theta'])
                prev_y = state['y'] - head_size/2 * np.sin(state['theta'])
                prev_angle = state['theta']
            else:
                # Other segments connect to the previous segment
                prev_x = segment_positions[i-1][0] - segment_length * np.cos(segment_angles[i-1])
                prev_y = segment_positions[i-1][1] - segment_length * np.sin(segment_angles[i-1])
                prev_angle = segment_angles[i-1]
            
            # Total angle for this segment is heading + accumulated wave motion
            segment_total_angle = prev_angle + segment_angle
            segment_angles[i] = segment_total_angle
            
            # Store segment position (at its front end)
            segment_positions[i] = (prev_x, prev_y)
            
            # Apply transformation
            segment_transform = matplotlib.transforms.Affine2D().rotate(segment_total_angle).translate(prev_x, prev_y)
            segment.set_transform(segment_transform + ax.transData)
        
        # Update trajectory and lookahead rays
        traj_line.set_data(trajectory[0, :current_step+1], trajectory[1, :current_step+1])
        ray1_line.set_data([state['x'], ray1[0]], [state['y'], ray1[1]])  # Current heading ray
        ray2_line.set_data([state['x'], ray2[0]], [state['y'], ray2[1]])  # Desired heading ray
        
        canvas.draw()
        
        # Update bottom view: Servo Simulation.
        # For tail servos (indices 0 to 3): map tail_amp to an amplitude in degrees (e.g., 0 to 60 degrees)
        tail_amp_deg = (tail_amp / max_tail_amplitude) * 60
        angles_this_step = []
        
        # Use a sine wave with phase shifts for tail servos
        for i in range(4):
            angle = tail_amp_deg * math.sin(2 * math.pi * 0.05 * (current_step * dt) + math.radians(45 * i))
            update_servo(angle, i)
            angles_this_step.append(angle)
            
        # For head servo (index 4): use the rudder angle (in degrees)
        head_angle = math.degrees(rudder)
        update_servo(head_angle, 4)
        angles_this_step.append(head_angle)
        
        # Store servo angles and PWM values
        for i in range(5):
            servo_angle_log[i, current_step] = angles_this_step[i]
            servo_pwm_log[i, current_step] = 1500 + (angles_this_step[i] / 90.0) * 500
        
        current_step_inc = current_step + 1
        globals()['current_step'] = current_step_inc
        globals()['time_elapsed'] += dt
        root.after(int(dt*500), simulation_step)  # Half the delay for 2x speed
    else:
        print("Trajectory calculated!")
        print("Final position: x={:.2f}, y={:.2f}".format(state['x'], state['y']))
        
        # Print the servo angle and PWM logs (only showing first and last 3 steps)
        np.set_printoptions(precision=1, suppress=True)
        print("\n--- Servo Angle Log (degrees) ---")
        if current_step > 6:
            print("First 3 steps:")
            print(servo_angle_log[:, :3])
            print("Last 3 steps:")
            print(servo_angle_log[:, current_step-3:current_step])
        else:
            print(servo_angle_log[:, :current_step])
            
        print("\n--- Servo PWM Log (microseconds) ---")
        if current_step > 6:
            print("First 3 steps:")
            print(servo_pwm_log[:, :3])
            print("Last 3 steps:")
            print(servo_pwm_log[:, current_step-3:current_step])
        else:
            print(servo_pwm_log[:, :current_step])

try:
    simulation_step()
    root.mainloop()
except KeyboardInterrupt:
    print("Simulation terminated by user.")
    sys.exit()