import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import time

# Simulation time settings
dt = 0.05                    # Time step (seconds)
t_max = 10                   # Total simulation time (seconds)

class FishTailSimulation:
    def __init__(self, root):
        self.root = root
        self.root.title("5-Joint Fish Robot Tail Simulation")
        
        # Set default parameters (matching Arduino patterns)
        self.amplitude = 18.0       # Default amplitude in degrees
        self.frequency = 2.0        # Default frequency in Hz
        self.phase_shift = 45.0     # Default phase shift in degrees
        
        # Number of joints and segment length
        self.num_joints = 5
        self.segment_length = 1.0   # Equal length for all segments
        
        # Joint factors (progressive scaling from head to tail)
        self.joint_factors = [0.6, 0.8, 1.2, 1.3, 1.4]  # Similar to the reference code
        
        # Wave direction (Head to Tail by default)
        self.wave_direction = 1  # 1 for Head->Tail, -1 for Tail->Head
        
        # Data for real-time plotting
        self.joint_angles = np.zeros(self.num_joints)  # Current joint angles
        self.tail_positions = np.zeros((self.num_joints+1, 2))  # Current x,y positions
        
        # Setup time array and storage for angle data over time
        self.time_data = np.arange(0, 2, dt)
        self.angle_data = [np.zeros((len(self.time_data),)) for _ in range(self.num_joints)]
        
        # Frame counter for animation
        self.frame_count = 0
        
        # Animation control
        self.animation_running = True
        
        # Create the main layout
        self.create_layout()
        
        # Start the simulation
        self.update_simulation()
        
    def create_layout(self):
        # Create main frames
        self.left_frame = tk.Frame(self.root, width=300, padx=10, pady=10)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.right_frame = tk.Frame(self.root, padx=10, pady=10)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create control panel in left frame
        self.create_control_panel()
        
        # Create visualization in right frame
        self.create_visualization()
        
    def create_control_panel(self):
        # Title
        title_label = tk.Label(self.left_frame, text="Fish Tail Control Panel", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Amplitude slider
        amp_frame = tk.Frame(self.left_frame)
        amp_frame.pack(fill=tk.X, pady=5)
        
        amp_label = tk.Label(amp_frame, text="Amplitude (deg)", width=15, anchor="w")
        amp_label.pack(side=tk.LEFT)
        
        self.amp_value = tk.Label(amp_frame, text=f"{self.amplitude:.1f}", width=4)
        self.amp_value.pack(side=tk.RIGHT)
        
        self.amp_slider = tk.Scale(self.left_frame, from_=0, to=50, orient=tk.HORIZONTAL, 
                                  resolution=0.1, command=self.update_amplitude)
        self.amp_slider.set(self.amplitude)
        self.amp_slider.pack(fill=tk.X)
        
        # Frequency slider
        freq_frame = tk.Frame(self.left_frame)
        freq_frame.pack(fill=tk.X, pady=5)
        
        freq_label = tk.Label(freq_frame, text="Frequency (Hz)", width=15, anchor="w")
        freq_label.pack(side=tk.LEFT)
        
        self.freq_value = tk.Label(freq_frame, text=f"{self.frequency:.1f}", width=4)
        self.freq_value.pack(side=tk.RIGHT)
        
        self.freq_slider = tk.Scale(self.left_frame, from_=0.1, to=5.0, orient=tk.HORIZONTAL, 
                                   resolution=0.1, command=self.update_frequency)
        self.freq_slider.set(self.frequency)
        self.freq_slider.pack(fill=tk.X)
        
        # Phase shift slider
        phase_frame = tk.Frame(self.left_frame)
        phase_frame.pack(fill=tk.X, pady=5)
        
        phase_label = tk.Label(phase_frame, text="Phase Shift (deg)", width=15, anchor="w")
        phase_label.pack(side=tk.LEFT)
        
        self.phase_value = tk.Label(phase_frame, text=f"{self.phase_shift:.1f}", width=4)
        self.phase_value.pack(side=tk.RIGHT)
        
        self.phase_slider = tk.Scale(self.left_frame, from_=0, to=90, orient=tk.HORIZONTAL, 
                                    resolution=0.1, command=self.update_phase_shift)
        self.phase_slider.set(self.phase_shift)
        self.phase_slider.pack(fill=tk.X)
        
        # Separator
        ttk.Separator(self.left_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Joint factor sliders
        joint_label = tk.Label(self.left_frame, text="Joint Amplitude Factors", font=("Arial", 10, "bold"))
        joint_label.pack(pady=(5, 10))
        
        self.joint_sliders = []
        
        for i in range(self.num_joints):
            joint_frame = tk.Frame(self.left_frame)
            joint_frame.pack(fill=tk.X, pady=2)
            
            joint_name = "Head" if i == 0 else "Tail" if i == self.num_joints-1 else f"{i+1}"
            joint_text = f"Joint {i+1} ({joint_name})"
            
            j_label = tk.Label(joint_frame, text=joint_text, width=15, anchor="w")
            j_label.pack(side=tk.LEFT)
            
            j_value = tk.Label(joint_frame, text=f"{self.joint_factors[i]:.1f}", width=4)
            j_value.pack(side=tk.RIGHT)
            
            j_slider = tk.Scale(self.left_frame, from_=0, to=2.0, orient=tk.HORIZONTAL, 
                               resolution=0.1, command=lambda val, idx=i, val_label=j_value: self.update_joint_factor(val, idx, val_label))
            j_slider.set(self.joint_factors[i])
            j_slider.pack(fill=tk.X)
            
            self.joint_sliders.append((j_slider, j_value))
        
        # Separator
        ttk.Separator(self.left_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Wave direction radio buttons
        direction_label = tk.Label(self.left_frame, text="Wave Direction:", font=("Arial", 10, "bold"))
        direction_label.pack(anchor="w", pady=(5, 5))
        
        self.direction_var = tk.IntVar(value=1)  # Default: Head->Tail
        
        direction_frame = tk.Frame(self.left_frame)
        direction_frame.pack(fill=tk.X)
        
        head_tail_rb = tk.Radiobutton(direction_frame, text="Head→Tail (+1)", variable=self.direction_var, 
                                     value=1, command=self.update_wave_direction)
        head_tail_rb.pack(side=tk.LEFT, padx=5)
        
        tail_head_rb = tk.Radiobutton(direction_frame, text="Tail→Head (-1)", variable=self.direction_var, 
                                     value=-1, command=self.update_wave_direction)
        tail_head_rb.pack(side=tk.LEFT, padx=5)
        
        # Play/Pause Button
        ttk.Separator(self.left_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        self.play_pause_button = tk.Button(self.left_frame, text="Pause", command=self.toggle_animation)
        self.play_pause_button.pack(pady=5)
        
        # Information label
        info_text = f"Segment Length: {self.segment_length} (fixed for all segments)"
        info_label = tk.Label(self.left_frame, text=info_text, relief=tk.RIDGE, pady=5)
        info_label.pack(fill=tk.X, pady=10)
    
    def create_visualization(self):
        # Create figure with two subplots
        self.fig = plt.figure(figsize=(10, 8))
        
        # Top plot: Fish tail visualization (top view)
        self.ax_fish = self.fig.add_subplot(211)
        self.ax_fish.set_aspect('equal')  # Equal aspect ratio for realistic visualization
        self.ax_fish.set_xlim(-1, 6)
        self.ax_fish.set_ylim(-4, 4)
        self.ax_fish.set_title("Fish Robot Tail Simulation (Top View)")
        self.ax_fish.set_xlabel("X")
        self.ax_fish.set_ylabel("Y")
        self.ax_fish.grid(True, linestyle='--', alpha=0.7)
        
        # Create colors for joints (using the reference code's color scheme)
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        # Create a single line for the tail with markers
        self.tail_line, = self.ax_fish.plot([], [], '-', lw=3)
        
        # Create separate markers for each joint to match the colors in the graph below
        self.joint_markers = []
        
        # Only create markers for the joints (not the tail endpoint)
        for i in range(self.num_joints):
            # Use the same color scheme as the graph lines for both markers and segments
            color = self.colors[i]
            # Square marker for first joint, circles for others
            marker = 's' if i == 0 else 'o'
            size = 100 if i == 0 else 80
            point = self.ax_fish.scatter([], [], s=size, c=color, marker=marker, zorder=3)
            self.joint_markers.append(point)
            
        # Create colored line segments between joints
        self.tail_segments = []
        for i in range(self.num_joints):  # Now creating segments for all joints including the last one
            segment, = self.ax_fish.plot([], [], color=self.colors[i], linewidth=3)
            self.tail_segments.append(segment)
        
        # Add direction arrow and label
        self.direction_arrow = self.ax_fish.arrow(0, 0, 0, 0, head_width=0.2, head_length=0.3, 
                                                 fc='red', ec='red', alpha=0)
        
        # Bottom plot: Joint angles over time
        self.ax_angles = self.fig.add_subplot(212)
        self.ax_angles.set_xlim(0, 2)  # Show 2 seconds of motion
        self.ax_angles.set_ylim(-90, 90)  # Expanded range for angles
        self.ax_angles.set_title("Joint Angles Over Time")
        self.ax_angles.set_xlabel("Time (s)")
        self.ax_angles.set_ylabel("Angle (degrees)")
        self.ax_angles.grid(True)
        
        # Create joint angle lines with different colors
        self.joint_lines = []
        labels = [f"Joint {i+1} " + ("(Head)" if i == 0 else "(Tail)" if i == self.num_joints-1 else "") 
                 for i in range(self.num_joints)]
        
        for i in range(self.num_joints):
            line, = self.ax_angles.plot([], [], lw=2, color=self.colors[i], label=labels[i])
            self.joint_lines.append(line)
        
        # Add legend
        self.ax_angles.legend(loc='upper right')
        
        # Time marker in the time-series plot (vertical line)
        self.time_marker, = self.ax_angles.plot([], [], 'k|', markersize=12, markeredgewidth=2)
        
        # Adjust layout and add to tkinter window
        self.fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
    
    # Update functions for sliders
    def update_amplitude(self, val):
        self.amplitude = float(val)
        self.amp_value.config(text=f"{self.amplitude:.1f}")
    
    def update_frequency(self, val):
        self.frequency = float(val)
        self.freq_value.config(text=f"{self.frequency:.1f}")
    
    def update_phase_shift(self, val):
        self.phase_shift = float(val)
        self.phase_value.config(text=f"{self.phase_shift:.1f}")
    
    def update_joint_factor(self, val, idx, value_label):
        self.joint_factors[idx] = float(val)
        value_label.config(text=f"{self.joint_factors[idx]:.1f}")
    
    def update_wave_direction(self):
        self.wave_direction = self.direction_var.get()
    
    def toggle_animation(self):
        self.animation_running = not self.animation_running
        if self.animation_running:
            self.play_pause_button.config(text="Pause")
            self.update_simulation()
        else:
            self.play_pause_button.config(text="Play")
    
    def calculate_joint_angles(self, current_time):
        """Calculate the current joint angles based on continuous time."""
        # Compute angular position for each joint
        omega = 2 * math.pi * self.frequency
        
        # Phase multiplier determines wave direction
        # Negative for head→tail propagation (matches Arduino code)
        phase_multiplier = -1 if self.wave_direction == 1 else 1
        
        # Calculate angles for each joint based on direction and phase shift
        for i in range(self.num_joints):
            # Calculate angle using sine wave with continuous time
            spatial_phase = phase_multiplier * i * math.radians(self.phase_shift)
            angle = self.wave_direction * self.amplitude * self.joint_factors[i] * math.sin(omega * current_time + spatial_phase)
            
            # Store the angle
            self.joint_angles[i] = angle
    
    def calculate_angles_for_timeseries(self):
        """Calculate angles for the time-series plot."""
        # Get the current time
        time = (self.frame_count * dt) % t_max
        
        # Compute the time index for the circular buffer
        time_idx = int((time % 2) / dt)
        
        # Get current parameter values to use for calculations
        amplitude_deg = self.amplitude
        frequency = self.frequency
        phase_shift_rad = math.radians(self.phase_shift)
        direction = self.wave_direction
        
        # Angular frequency
        omega = 2 * math.pi * frequency
        
        # Phase multiplier for wave direction
        phase_multiplier = -1 if direction == 1 else 1
        
        # Calculate the angle for each joint at this time point
        for i in range(self.num_joints):
            spatial_phase = phase_multiplier * i * phase_shift_rad
            angle = direction * amplitude_deg * self.joint_factors[i] * math.sin(omega * time + spatial_phase)
            self.angle_data[i][time_idx] = angle
            
        return time_idx
    
    def calculate_fish_positions(self):
        """Calculate the current positions of the fish joints using forward kinematics."""
        # Reset positions array
        self.tail_positions = np.zeros((self.num_joints+1, 2))
        
        # Head position at the origin
        self.tail_positions[0, 0] = 0  # Head x
        self.tail_positions[0, 1] = 0  # Head y
        
        # Initialize cumulative angle
        total_angle = 0
        
        # Calculate each joint position
        for i in range(self.num_joints):
            # Add this joint's angle to the cumulative angle
            # The angles are already in degrees from the calculation
            total_angle += self.joint_angles[i]
            
            # Convert to radians for trigonometric functions
            theta_rad = math.radians(total_angle)
            
            # Calculate new position using exact segment length
            self.tail_positions[i+1, 0] = self.tail_positions[i, 0] + self.segment_length * math.cos(theta_rad)
            self.tail_positions[i+1, 1] = self.tail_positions[i, 1] + self.segment_length * math.sin(theta_rad)
            
            # Verify segment length and fix if necessary for perfect lengths
            dx = self.tail_positions[i+1, 0] - self.tail_positions[i, 0]
            dy = self.tail_positions[i+1, 1] - self.tail_positions[i, 1]
            actual_length = math.sqrt(dx**2 + dy**2)
            
            # If the length is off by more than a tiny tolerance, fix it
            if abs(actual_length - self.segment_length) > 1e-12:
                # Normalize the direction vector to exact length
                if actual_length > 0:  # Avoid division by zero
                    dx = dx / actual_length * self.segment_length
                    dy = dy / actual_length * self.segment_length
                
                # Update the position with fixed length
                self.tail_positions[i+1, 0] = self.tail_positions[i, 0] + dx
                self.tail_positions[i+1, 1] = self.tail_positions[i, 1] + dy
    
    def update_simulation(self):
        """Update the simulation with current parameters."""
        # Only update if animation is running
        if not self.animation_running:
            return
        
        # Increment frame counter
        self.frame_count += 1
        
        # Get current time
        time = (self.frame_count * dt) % t_max
        
        # Calculate joint angles for the current time
        self.calculate_joint_angles(time)
        self.calculate_fish_positions()
        
        # Calculate angles for time series plot and get current time index
        time_idx = self.calculate_angles_for_timeseries()
        
        # Get positions of all joints and tail endpoint
        x_pos = self.tail_positions[:, 0]
        y_pos = self.tail_positions[:, 1]
        
        # Update all joint markers with matching colors (excluding tail endpoint)
        for i, marker in enumerate(self.joint_markers):
            marker.set_offsets(np.column_stack([x_pos[i], y_pos[i]]))
        
        # Update the colored tail segments (including the last segment)
        for i, segment in enumerate(self.tail_segments):
            segment_x = [x_pos[i], x_pos[i+1]]
            segment_y = [y_pos[i], y_pos[i+1]]
            segment.set_data(segment_x, segment_y)
        
        # Update joint angle plots
        for i, line in enumerate(self.joint_lines):
            line.set_data(self.time_data, self.angle_data[i])
        
        # Update time marker (showing current position in the cycle)
        self.time_marker.set_data([time % 2, time % 2], [-90, 90])
        
        # Redraw the canvas
        self.canvas.draw()
        
        # Schedule the next update using the time step from constants
        self.root.after(int(dt * 1000), self.update_simulation)

if __name__ == "__main__":
    root = tk.Tk()
    app = FishTailSimulation(root)
    root.mainloop()