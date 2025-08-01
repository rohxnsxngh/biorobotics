import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
import math
import time

class FishTailSimulation:
    def __init__(self, root):
        self.root = root
        self.root.title("Fish Robot Tail Simulation")
        
        # Set default parameters
        self.amplitude = 18.0  # Default amplitude in degrees
        self.frequency = 2.0   # Default frequency in Hz
        self.phase_shift = 45.0  # Default phase shift in degrees
        
        # Joint factors (relative amplitude multipliers)
        self.joint_factors = [0.6, 0.8, 1.2, 1.3, 1.4]
        
        # Wave direction (Head to Tail by default)
        self.wave_direction = 0  # 1 for Head->Tail, -1 for Tail->Head
        
        # Data for plotting
        self.num_joints = 5
        self.joint_angles = np.zeros(self.num_joints)  # Current joint angles
        
        # Fixed time points for plotting (0 to 2 seconds)
        self.history_length = 100
        self.time_points = np.linspace(0, 2, self.history_length)
        
        # Fish tail parameters
        self.segment_length = 1  # Fixed length for all segments
        self.tail_positions = np.zeros((self.num_joints+1, 2))  # Current x,y positions
        
        # Start time for continuous wave motion
        self.start_time = time.time()
        
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
        title_label = tk.Label(self.left_frame, text="Control Panel", font=("Arial", 12, "bold"))
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
        
        # Frequency slider with expanded range
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
        joint_label = tk.Label(self.left_frame, text="Joint Factors", font=("Arial", 10, "bold"))
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
    
    def create_visualization(self):
        # Create figure with two subplots (2 rows, 1 column)
        self.fig = plt.figure(figsize=(8, 8))
        
        # Top plot: Fish tail visualization
        self.ax_fish = self.fig.add_subplot(211)
        self.ax_fish.set_xlim(-1, 6)
        self.ax_fish.set_ylim(-4, 4)
        self.ax_fish.set_title("Fish Robot Tail Simulation (Top View)")
        self.ax_fish.set_xlabel("X")
        self.ax_fish.set_ylabel("Y")
        
        # Add grid for better visual reference
        self.ax_fish.grid(True, linestyle='--', alpha=0.7)
        
        # Add a text displaying segment length info
        self.ax_fish.text(
            0.02, 0.98, 
            f"Segment Length: {self.segment_length}",
            transform=self.ax_fish.transAxes,
            verticalalignment='top',
            horizontalalignment='left',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray')
        )
        
        # Create initial tail segments with colored markers to match bottom graph
        # Create separate line segments for each joint to maintain exact length
        self.tail_segments = []
        colors = ['blue', 'orange', 'green', 'red', 'purple']
        
        for i in range(self.num_joints):
            segment, = self.ax_fish.plot([], [], color=colors[i], linewidth=2)
            self.tail_segments.append(segment)
        
        # Create separate scatter plots for each joint with matching colors
        self.joint_markers = []
        for i in range(self.num_joints + 1):
            # Use the joint color for internal joints, red for head
            color = 'red' if i == 0 else colors[i-1]
            # Use square marker for head, circles for joints
            marker = 's' if i == 0 else 'o'
            # Make head and tail slightly larger
            size = 100 if i == 0 or i == self.num_joints else 80
            point = self.ax_fish.scatter([], [], s=size, c=color, marker=marker)
            self.joint_markers.append(point)
        
        # The head marker is the first joint marker
        self.head_marker = self.joint_markers[0]
        
        # Bottom plot: Joint angles over time
        self.ax_angles = self.fig.add_subplot(212)
        self.ax_angles.set_xlim(0, 2)
        self.ax_angles.set_ylim(-75, 75)
        self.ax_angles.set_title("Joint Angles Over Time")
        self.ax_angles.set_xlabel("Time (s)")
        self.ax_angles.set_ylabel("Angle (degrees)")
        
        # Create joint angle lines with different colors
        self.joint_lines = []
        labels = [f"Joint {i+1} " + ("(Head)" if i == 0 else "(Tail)" if i == self.num_joints-1 else "") 
                 for i in range(self.num_joints)]
        
        for i in range(self.num_joints):
            line, = self.ax_angles.plot([], [], color=colors[i], label=labels[i])
            self.joint_lines.append(line)
        
        # Add legend
        self.ax_angles.legend(loc='upper right')
        
        # Add time marker line
        self.time_marker, = self.ax_angles.plot([0, 0], [-75, 75], 'k-', alpha=0.5)
        
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
    
    def calculate_joint_angles(self, current_time):
        """Calculate the current joint angles based on continuous time."""
        for i in range(self.num_joints):
            # Calculate phase based on joint position and direction
            spatial_phase = self.wave_direction * i * math.radians(self.phase_shift)
            
            # Calculate angle using sine wave with continuous time
            # This ensures no discontinuity at any point
            time_phase = 2 * math.pi * self.frequency * current_time
            angle = self.amplitude * self.joint_factors[i] * math.sin(time_phase + spatial_phase)
            
            # Store the angle
            self.joint_angles[i] = angle
    
    def calculate_theoretical_angles(self):
        """Calculate theoretical angle curves for the plot (not actual angles)."""
        # Get current time
        current_time = time.time() - self.start_time
        
        # Calculate where in the cycle we are (0 to 2π)
        cycle_phase = 2 * math.pi * self.frequency * (current_time % (1/self.frequency))
        
        # For each joint, calculate a complete cycle of angles starting from current phase
        angles = np.zeros((self.num_joints, len(self.time_points)))
        for i in range(self.num_joints):
            # Spatial phase for this joint
            spatial_phase = self.wave_direction * i * math.radians(self.phase_shift)
            
            # Calculate one complete cycle of the sine wave
            for t_idx, t in enumerate(self.time_points):
                # Map time points to phase values (0 to 2π)
                phase = 2 * math.pi * t / 2  # Map 0-2s to 0-2π
                # Offset by current phase to make smooth scrolling
                total_phase = phase + cycle_phase + spatial_phase
                # Calculate angle
                angles[i, t_idx] = self.amplitude * self.joint_factors[i] * math.sin(total_phase)
        
        return angles
    
    def calculate_fish_positions(self):
        """Calculate the current positions of the fish joints."""
        # Reset positions array
        self.tail_positions = np.zeros((self.num_joints+1, 2))
        
        # Head position at the origin
        self.tail_positions[0, 0] = 0  # Head x
        self.tail_positions[0, 1] = 0  # Head y
        
        # Initialize cumulative angle (relative to horizontal)
        theta = 0
        
        # Calculate each joint position
        for i in range(self.num_joints):
            if i == 0:
                # First joint - use its angle directly
                theta = self.joint_angles[i]
            else:
                # Add this joint's angle to get the new orientation
                theta += self.joint_angles[i]
            
            # Convert angle to radians
            theta_rad = math.radians(theta)
            
            # Get previous joint position
            prev_x = self.tail_positions[i, 0]
            prev_y = self.tail_positions[i, 1]
            
            # Calculate exact new position using polar coordinates
            next_x = prev_x + self.segment_length * math.cos(theta_rad)
            next_y = prev_y + self.segment_length * math.sin(theta_rad)
            
            # Store the new joint position
            self.tail_positions[i+1, 0] = next_x
            self.tail_positions[i+1, 1] = next_y
            
            # Verify segment length and fix if necessary
            dx = self.tail_positions[i+1, 0] - self.tail_positions[i, 0]
            dy = self.tail_positions[i+1, 1] - self.tail_positions[i, 1]
            actual_length = math.sqrt(dx**2 + dy**2)
            
            # If the length is off by more than a tiny tolerance, fix it
            if abs(actual_length - self.segment_length) > 1e-12:
                # Normalize the direction vector
                if actual_length > 0:  # Avoid division by zero
                    dx = dx / actual_length * self.segment_length
                    dy = dy / actual_length * self.segment_length
                
                # Update the position with fixed length
                self.tail_positions[i+1, 0] = self.tail_positions[i, 0] + dx
                self.tail_positions[i+1, 1] = self.tail_positions[i, 1] + dy
    
    def update_simulation(self):
        """Update the simulation with current parameters for continuous motion."""
        # Get current time
        current_time = time.time() - self.start_time
        
        # Calculate joint angles and positions for the current time
        self.calculate_joint_angles(current_time)
        self.calculate_fish_positions()
        
        # Calculate theoretical angle curves for plotting
        theoretical_angles = self.calculate_theoretical_angles()
        
        # Update the segment lines individually
        x_pos = self.tail_positions[:, 0]
        y_pos = self.tail_positions[:, 1]
        
        # Update each segment separately to maintain exact length
        for i in range(self.num_joints):
            segment_x = [x_pos[i], x_pos[i+1]]
            segment_y = [y_pos[i], y_pos[i+1]]
            self.tail_segments[i].set_data(segment_x, segment_y)
            
            # Double-check segment length
            dx = x_pos[i+1] - x_pos[i]
            dy = y_pos[i+1] - y_pos[i]
            length = math.sqrt(dx**2 + dy**2)
            
            # This should never happen given our calculations, but just in case
            if abs(length - self.segment_length) > 1e-9:
                print(f"Warning: Segment {i+1} length = {length:.6f}, expected {self.segment_length}")
        
        # Update all joint markers
        for i, marker in enumerate(self.joint_markers):
            marker.set_offsets([x_pos[i], y_pos[i]])
        
        # Update joint angle plots with theoretical curves
        for i in range(self.num_joints):
            self.joint_lines[i].set_data(self.time_points, theoretical_angles[i])
        
        # Update time marker - show current position in the cycle
        # Calculate where in the 2-second display we are
        display_time = (current_time * self.frequency) % 2
        self.time_marker.set_data([display_time, display_time], [-75, 75])
        
        # Redraw the canvas
        self.canvas.draw()
        
        # Schedule the next update
        self.root.after(16, self.update_simulation)

if __name__ == "__main__":
    root = tk.Tk()
    app = FishTailSimulation(root)
    root.mainloop()