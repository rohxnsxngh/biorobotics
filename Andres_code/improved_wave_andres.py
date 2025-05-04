# Improved visualization sim.py
import numpy as np
import matplotlib
# Force matplotlib to use TkAgg backend and configure it before importing pyplot
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import math

# === TAIL CONFIGURATION ===
num_joints = 6  # Increased to 6 joints
link_length = 1.0  # Each segment is 1 unit long

# === SIMULATION SETTINGS ===
dt = 0.05                     # Time step (seconds)
t_max = 10                    # Total simulation time (seconds)
t = np.arange(0, t_max, dt)  # Time array

# === INITIAL PARAMETERS === (matching the Arduino code)
amplitude_deg = 25.0
frequency = 1.0
phase_shift_deg = 30.0  # Reduced as in updated Arduino code
# Progressive amplitude scaling from head to tail
constant1 = 0.2
constant2 = 0.4
constant3 = 0.6
constant4 = 0.8
constant5 = 1.0
constant6 = 1.2
# Direction control
direction_multiplier = 1  # +1 for head->tail (forward swimming)

# === CREATE TKINTER GUI FOR SLIDERS ===
root = tk.Tk()
root.title("Fish Robot Wave Parameter Controls")

# Tkinter variables
amp_var = tk.DoubleVar(value=amplitude_deg)
freq_var = tk.DoubleVar(value=frequency)
phase_var = tk.DoubleVar(value=phase_shift_deg)
c1_var = tk.DoubleVar(value=constant1)
c2_var = tk.DoubleVar(value=constant2)
c3_var = tk.DoubleVar(value=constant3)
c4_var = tk.DoubleVar(value=constant4)
c5_var = tk.DoubleVar(value=constant5)
c6_var = tk.DoubleVar(value=constant6)
dir_var = tk.IntVar(value=direction_multiplier)

# Slider frame
slider_frame = tk.Frame(root)
slider_frame.pack(side=tk.LEFT, padx=10, pady=10)

# Function to create sliders easily
def create_slider(label, var, frm, to, row, resolution=0.1):
    tk.Label(slider_frame, text=label).grid(row=row, column=0, sticky='w')
    tk.Scale(slider_frame, variable=var, from_=frm, to=to, resolution=resolution,
             orient='horizontal', length=200).grid(row=row, column=1)

create_slider("Amplitude (deg)", amp_var, 0, 90, 0)
create_slider("Frequency (Hz)", freq_var, 0.1, 5.0, 1)
create_slider("Phase Shift (deg)", phase_var, 0, 180, 2)
create_slider("Joint 1 (Head)", c1_var, 0.0, 2.0, 3)
create_slider("Joint 2", c2_var, 0.0, 2.0, 4)
create_slider("Joint 3", c3_var, 0.0, 2.0, 5)
create_slider("Joint 4", c4_var, 0.0, 2.0, 6)
create_slider("Joint 5", c5_var, 0.0, 2.0, 7)
create_slider("Joint 6 (Tail)", c6_var, 0.0, 2.0, 8)

# Direction control with radio buttons
dir_frame = tk.Frame(slider_frame)
dir_frame.grid(row=9, columnspan=2, pady=10)
tk.Label(dir_frame, text="Wave Direction:").pack(side=tk.LEFT)
tk.Radiobutton(dir_frame, text="Head→Tail (+1)", variable=dir_var, value=1).pack(side=tk.LEFT)
tk.Radiobutton(dir_frame, text="Tail→Head (-1)", variable=dir_var, value=-1).pack(side=tk.LEFT)

# === FIGURE SETUP ===
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# Top view of fish (main visualization)
ax1.set_aspect('equal')
ax1.set_xlim(-1, 7)  # Adjusted for 6 segments
ax1.set_ylim(-4, 4)
ax1.set_title("Fish Robot Tail Simulation (Top View)")
ax1.set_xlabel("X")
ax1.set_ylabel("Y")
tail_line, = ax1.plot([], [], 'bo-', lw=3, markersize=8)
# Add head marker
head_marker, = ax1.plot([], [], 'rs', markersize=12)  # Red square for head
# Direction arrow (initialize as empty, will update later)
direction_arrow = ax1.arrow(0, 0, 0, 0, head_width=0.2, head_length=0.3, fc='red', ec='red')
ax1.text(6, 3, "← Forward", fontsize=12, color='red')

# Time-series view of joint angles
ax2.set_xlim(0, 2)  # Show 2 seconds of motion
ax2.set_ylim(-90, 90)
ax2.set_title("Joint Angles Over Time")
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Angle (degrees)")
ax2.grid(True)

# One line per joint for the time series
angle_lines = []
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
labels = ['Joint 1 (Head)', 'Joint 2', 'Joint 3', 'Joint 4', 'Joint 5', 'Joint 6 (Tail)']
for i in range(num_joints):
    line, = ax2.plot([], [], lw=2, color=colors[i], label=labels[i])
    angle_lines.append(line)
ax2.legend(loc='upper right')

# Time marker in the time-series plot
time_marker, = ax2.plot([], [], 'k|', markersize=12, markeredgewidth=2)

# Data storage for time series
time_data = np.arange(0, 2, dt)
angle_data = [np.zeros((len(time_data),)) for _ in range(num_joints)]

plt.tight_layout()

# Embed Matplotlib in Tkinter window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
canvas.draw()

# Add info frame if needed
info_frame = tk.Frame(slider_frame)
info_frame.grid(row=10, columnspan=2, pady=10)

# === ANIMATION FUNCTION ===
frame_count = 0
animation_running = True

def update():
    global frame_count
    if not animation_running:
        return
    
    time = frame_count * dt % t_max
    frame_count += 1
    
    # Get real-time values from sliders
    amplitude_rad = math.radians(amp_var.get())
    frequency = freq_var.get()
    phase_shift_rad = math.radians(phase_var.get())
    c1 = c1_var.get()
    c2 = c2_var.get()
    c3 = c3_var.get()
    c4 = c4_var.get()
    c5 = c5_var.get()
    c6 = c6_var.get()
    direction = dir_var.get()
    
    # Compute angular position of each joint
    omega = 2 * math.pi * frequency
    
    # Key change: negative phase shift for head→tail wave propagation
    # when direction = 1 (matches Arduino code)
    phase_multiplier = -1 if direction == 1 else 1
    
    angle1 = c1 * direction * amplitude_rad * math.sin(omega * time)
    angle2 = c2 * direction * amplitude_rad * math.sin(omega * time + phase_multiplier * 1 * phase_shift_rad)
    angle3 = c3 * direction * amplitude_rad * math.sin(omega * time + phase_multiplier * 2 * phase_shift_rad)
    angle4 = c4 * direction * amplitude_rad * math.sin(omega * time + phase_multiplier * 3 * phase_shift_rad)
    angle5 = c5 * direction * amplitude_rad * math.sin(omega * time + phase_multiplier * 4 * phase_shift_rad)
    angle6 = c6 * direction * amplitude_rad * math.sin(omega * time + phase_multiplier * 5 * phase_shift_rad)

    angles = [angle1, angle2, angle3, angle4, angle5, angle6]
    
    # Store angles for time series (in degrees)
    time_idx = int((time % 2) / dt)
    for i, angle in enumerate(angles):
        angle_data[i][time_idx] = math.degrees(angle)

    # Forward kinematics to calculate joint positions
    x = [0]
    y = [0]
    total_angle = 0
    for angle in angles:
        total_angle += angle
        x.append(x[-1] + link_length * np.cos(total_angle))
        y.append(y[-1] + link_length * np.sin(total_angle))

    # Update tail line
    tail_line.set_data(x, y)
    
    # Update head marker
    head_marker.set_data([x[0]], [y[0]])
    
    # Update time series
    for i, line in enumerate(angle_lines):
        line.set_data(time_data, angle_data[i])
    
    # Update time marker
    time_marker.set_data([time % 2, time % 2], [-90, 90])
    
    # Redraw canvas
    canvas.draw()
    
    # Schedule the next update using tkinter's after method
    root.after(int(dt * 1000), update)

# Add play/pause button
def toggle_animation():
    global animation_running
    animation_running = not animation_running
    if animation_running:
        play_pause_button.config(text="Pause")
        update()
    else:
        play_pause_button.config(text="Play")

play_pause_button = tk.Button(info_frame, text="Pause", command=toggle_animation)
play_pause_button.pack(pady=5)

# Start the animation
update()

# Start the Tkinter main loop
root.mainloop()