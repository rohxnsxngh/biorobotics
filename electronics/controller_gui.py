import tkinter as tk
from tkinter import ttk, messagebox
import serial
import time
import math
import threading
import json

class RobotControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Biorobotic Eel Control System")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Serial connection
        self.ser = None
        self.connected = False
        self.lock = threading.Lock()
        
        # Default servo parameters
        self.amplitude = 15.0
        self.frequency = 0.8
        self.phase_shift = 60.0
        self.center_pos = 90.0
        self.rudder_position = 90
        self.servo4_manual_mode = False
        self.servo4_position = 90
        
        # Create frames
        self.create_connection_frame()
        self.create_wave_parameters_frame()
        self.create_rudder_control_frame()
        self.create_visualization_frame()
        
        # Start UI update loop
        self.root.after(100, self.update_ui)
    
    def create_connection_frame(self):
        # Frame for connection settings
        conn_frame = ttk.LabelFrame(self.root, text="Connection Settings")
        conn_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Port selection
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=0, padx=5, pady=5)
        self.port_var = tk.StringVar(value="COM3")
        self.port_entry = ttk.Entry(conn_frame, textvariable=self.port_var, width=15)
        self.port_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Connect button
        self.connect_button = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Status indicator
        self.status_var = tk.StringVar(value="Disconnected")
        ttk.Label(conn_frame, text="Status:").grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(conn_frame, textvariable=self.status_var).grid(row=0, column=4, padx=5, pady=5)
    
    def create_wave_parameters_frame(self):
        # Frame for wave motion parameters
        wave_frame = ttk.LabelFrame(self.root, text="Swimming Motion Parameters")
        wave_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # Amplitude control
        ttk.Label(wave_frame, text="Amplitude:").grid(row=0, column=0, padx=5, pady=5)
        self.amplitude_var = tk.DoubleVar(value=self.amplitude)
        amplitude_scale = ttk.Scale(wave_frame, from_=0, to=45, variable=self.amplitude_var, 
                                    orient="horizontal", length=200)
        amplitude_scale.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(wave_frame, textvariable=self.amplitude_var).grid(row=0, column=2, padx=5, pady=5)
        
        # Frequency control
        ttk.Label(wave_frame, text="Frequency:").grid(row=1, column=0, padx=5, pady=5)
        self.frequency_var = tk.DoubleVar(value=self.frequency)
        frequency_scale = ttk.Scale(wave_frame, from_=0.1, to=2.0, variable=self.frequency_var, 
                                   orient="horizontal", length=200)
        frequency_scale.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(wave_frame, textvariable=self.frequency_var).grid(row=1, column=2, padx=5, pady=5)
        
        # Phase shift control
        ttk.Label(wave_frame, text="Phase Shift:").grid(row=2, column=0, padx=5, pady=5)
        self.phase_shift_var = tk.DoubleVar(value=self.phase_shift)
        phase_shift_scale = ttk.Scale(wave_frame, from_=0, to=180, variable=self.phase_shift_var, 
                                     orient="horizontal", length=200)
        phase_shift_scale.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(wave_frame, textvariable=self.phase_shift_var).grid(row=2, column=2, padx=5, pady=5)
        
        # Apply button
        self.apply_wave_button = ttk.Button(wave_frame, text="Apply Wave Settings", 
                                           command=self.apply_wave_settings)
        self.apply_wave_button.grid(row=3, column=1, padx=5, pady=10)
        
        # Servo4 override controls
        servo4_frame = ttk.LabelFrame(wave_frame, text="Servo 4 Override")
        servo4_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        self.servo4_override_var = tk.BooleanVar(value=False)
        servo4_check = ttk.Checkbutton(servo4_frame, text="Manual Control", 
                                      variable=self.servo4_override_var,
                                      command=self.toggle_servo4_mode)
        servo4_check.grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Label(servo4_frame, text="Position:").grid(row=0, column=1, padx=5, pady=5)
        self.servo4_pos_var = tk.IntVar(value=self.servo4_position)
        servo4_scale = ttk.Scale(servo4_frame, from_=0, to=180, variable=self.servo4_pos_var,
                                orient="horizontal", length=200, command=self.update_servo4)
        servo4_scale.grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(servo4_frame, textvariable=self.servo4_pos_var).grid(row=0, column=3, padx=5, pady=5)
    
    def create_rudder_control_frame(self):
        # Frame for rudder joystick
        rudder_frame = ttk.LabelFrame(self.root, text="Rudder Control")
        rudder_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        
        # Canvas for joystick
        self.joystick_canvas = tk.Canvas(rudder_frame, width=300, height=300, bg="white")
        self.joystick_canvas.grid(row=0, column=0, padx=10, pady=10)
        
        # Draw joystick base
        self.joystick_center_x = 150
        self.joystick_center_y = 150
        self.joystick_radius = 120
        self.joystick_handle_radius = 20
        self.joystick_canvas.create_oval(
            self.joystick_center_x - self.joystick_radius,
            self.joystick_center_y - self.joystick_radius,
            self.joystick_center_x + self.joystick_radius,
            self.joystick_center_y + self.joystick_radius,
            fill="lightgray", outline="gray", width=2
        )
        
        # Draw center marker
        self.joystick_canvas.create_line(
            self.joystick_center_x - 10, self.joystick_center_y,
            self.joystick_center_x + 10, self.joystick_center_y,
            fill="black", width=1
        )
        self.joystick_canvas.create_line(
            self.joystick_center_x, self.joystick_center_y - 10,
            self.joystick_center_x, self.joystick_center_y + 10,
            fill="black", width=1
        )
        
        # Draw joystick handle
        self.joystick_handle = self.joystick_canvas.create_oval(
            self.joystick_center_x - self.joystick_handle_radius,
            self.joystick_center_y - self.joystick_handle_radius,
            self.joystick_center_x + self.joystick_handle_radius,
            self.joystick_center_y + self.joystick_handle_radius,
            fill="red", outline="darkred", width=2
        )
        
        # Bind mouse events
        self.joystick_canvas.bind("<Button-1>", self.joystick_click)
        self.joystick_canvas.bind("<B1-Motion>", self.joystick_drag)
        self.joystick_canvas.bind("<ButtonRelease-1>", self.joystick_release)
        
        # Display current rudder position
        rudder_info_frame = ttk.Frame(rudder_frame)
        rudder_info_frame.grid(row=1, column=0, padx=5, pady=5)
        
        ttk.Label(rudder_info_frame, text="Rudder Position:").grid(row=0, column=0, padx=5, pady=5)
        self.rudder_pos_var = tk.IntVar(value=self.rudder_position)
        ttk.Label(rudder_info_frame, textvariable=self.rudder_pos_var).grid(row=0, column=1, padx=5, pady=5)
        
        # Direction indicator
        ttk.Label(rudder_info_frame, text="Direction:").grid(row=1, column=0, padx=5, pady=5)
        self.direction_var = tk.StringVar(value="Straight")
        ttk.Label(rudder_info_frame, textvariable=self.direction_var).grid(row=1, column=1, padx=5, pady=5)
        
        # Center button
        ttk.Button(rudder_info_frame, text="Center Rudder", 
                  command=self.center_rudder).grid(row=2, column=0, columnspan=2, padx=5, pady=10)
    
    def create_visualization_frame(self):
        # Frame for visualizing servo positions
        viz_frame = ttk.LabelFrame(self.root, text="Servo Visualization")
        viz_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Canvas for visualization
        self.viz_canvas = tk.Canvas(viz_frame, width=780, height=150, bg="white")
        self.viz_canvas.pack(padx=10, pady=10)
        
        # Create servo position indicators
        self.servo_indicators = []
        servo_spacing = 780 / 5
        for i in range(5):
            x = servo_spacing * (i + 0.5)
            
            # Servo label
            self.viz_canvas.create_text(x, 20, text=f"Servo {i+1}")
            
            # Servo position arc background
            self.viz_canvas.create_arc(x-60, 40, x+60, 140, 
                                      start=0, extent=180, 
                                      style="arc", outline="lightgray", width=10)
            
            # Servo position indicator
            indicator = self.viz_canvas.create_arc(x-60, 40, x+60, 140, 
                                                 start=90, extent=0, 
                                                 style="arc", outline="blue", width=10)
            self.servo_indicators.append(indicator)
            
            # Servo position text
            pos_text = self.viz_canvas.create_text(x, 120, text="90°")
            self.servo_indicators.append(pos_text)
    
    def toggle_connection(self):
        if not self.connected:
            try:
                port = self.port_var.get()
                self.ser = serial.Serial(port, 9600, timeout=1)
                time.sleep(2)  # Wait for Arduino reset
                self.connected = True
                self.status_var.set("Connected")
                self.connect_button.configure(text="Disconnect")
                
                # Start the serial reader thread
                self.reader_thread = threading.Thread(target=self.read_from_serial, daemon=True)
                self.reader_thread.start()
                
                messagebox.showinfo("Connection", f"Successfully connected to {port}")
            except serial.SerialException as e:
                messagebox.showerror("Connection Error", str(e))
        else:
            with self.lock:
                if self.ser:
                    self.ser.close()
            self.connected = False
            self.status_var.set("Disconnected")
            self.connect_button.configure(text="Connect")
    
    def read_from_serial(self):
        while self.connected:
            try:
                with self.lock:
                    if self.ser and self.ser.in_waiting:
                        line = self.ser.readline().decode('utf-8').strip()
                        if line:
                            print(f"Arduino: {line}")
            except Exception as e:
                print(f"Serial read error: {e}")
                time.sleep(0.1)
    
    def update_ui(self):
        # Update servo position visualization
        self.update_servo_visualization()
        
        # Schedule the next update
        self.root.after(100, self.update_ui)
    
    def update_servo_visualization(self):
        # Calculate current servo positions based on wave parameters
        t = time.time()
        positions = []
        
        # Convert parameters to radians
        phase_shift_rad = math.radians(self.phase_shift_var.get())
        amplitude = self.amplitude_var.get()
        frequency = self.frequency_var.get()
        omega = 2 * math.pi * frequency
        
        # Calculate positions for each servo
        for i in range(4):
            if i == 3 and self.servo4_override_var.get():
                # Manual override for servo4
                angle = self.servo4_pos_var.get()
            else:
                # Wave pattern
                angle = self.center_pos + amplitude * math.sin(omega * t + i * phase_shift_rad)
            positions.append(angle)
        
        # Add rudder position
        positions.append(self.rudder_position)
        
        # Update visualization
        for i, angle in enumerate(positions):
            # Update position indicator arc
            start_angle = 90
            extent = angle - 90  # Map 0-180 to -90 to +90
            
            self.viz_canvas.itemconfig(
                self.servo_indicators[i*2], 
                start=start_angle, 
                extent=extent
            )
            
            # Update text
            self.viz_canvas.itemconfig(
                self.servo_indicators[i*2+1],
                text=f"{angle:.1f}°"
            )
    
    def apply_wave_settings(self):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Connect to Arduino first")
            return
        
        # Update stored parameters
        self.amplitude = self.amplitude_var.get()
        self.frequency = self.frequency_var.get()
        self.phase_shift = self.phase_shift_var.get()
        
        # Create command to send to Arduino
        command = {
            "command": "wave",
            "amplitude": self.amplitude,
            "frequency": self.frequency,
            "phase_shift": self.phase_shift
        }
        
        self.send_command(command)
    
    def toggle_servo4_mode(self):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Connect to Arduino first")
            return
        
        self.servo4_manual_mode = self.servo4_override_var.get()
        
        if self.servo4_manual_mode:
            # Switch to manual mode
            self.send_command({"command": "S", "angle": self.servo4_pos_var.get()})
        else:
            # Switch back to wave mode
            self.send_command({"command": "W"})
    
    def update_servo4(self, event=None):
        if not self.connected or not self.servo4_override_var.get():
            return
        
        # Get position from slider
        position = self.servo4_pos_var.get()
        self.servo4_position = position
        
        # Send command
        self.send_command({"command": "S", "angle": position})
    
    def joystick_click(self, event):
        # Start joystick movement
        self.update_joystick_position(event.x, event.y)
    
    def joystick_drag(self, event):
        # Continue joystick movement
        self.update_joystick_position(event.x, event.y)
    
    def joystick_release(self, event):
        # End joystick movement
        self.update_joystick_position(event.x, event.y)
    
    def update_joystick_position(self, x, y):
        # Calculate distance from center
        dx = x - self.joystick_center_x
        dy = y - self.joystick_center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Constrain to joystick area
        if distance > self.joystick_radius:
            scale = self.joystick_radius / distance
            dx *= scale
            dy *= scale
            x = self.joystick_center_x + dx
            y = self.joystick_center_y + dy
        
        # Update joystick handle position
        self.joystick_canvas.coords(
            self.joystick_handle,
            x - self.joystick_handle_radius,
            y - self.joystick_handle_radius,
            x + self.joystick_handle_radius,
            y + self.joystick_handle_radius
        )
        
        # Calculate rudder position (only use x-axis)
        # Map x from joystick range to servo range (0-180)
        left_edge = self.joystick_center_x - self.joystick_radius
        right_edge = self.joystick_center_x + self.joystick_radius
        x_normalized = (x - left_edge) / (right_edge - left_edge)
        rudder_position = int(x_normalized * 180)
        
        # Update rudder position
        self.rudder_position = rudder_position
        self.rudder_pos_var.set(rudder_position)
        
        # Update direction text
        if rudder_position < 70:
            direction = "Sharp Left"
        elif rudder_position < 85:
            direction = "Gentle Left"
        elif rudder_position <= 95:
            direction = "Straight"
        elif rudder_position < 110:
            direction = "Gentle Right"
        else:
            direction = "Sharp Right"
        
        self.direction_var.set(direction)
        
        # Send command to Arduino
        self.send_command({"command": "R", "angle": rudder_position})
    
    def center_rudder(self):
        # Reset joystick to center
        self.joystick_canvas.coords(
            self.joystick_handle,
            self.joystick_center_x - self.joystick_handle_radius,
            self.joystick_center_y - self.joystick_handle_radius,
            self.joystick_center_x + self.joystick_handle_radius,
            self.joystick_center_y + self.joystick_handle_radius
        )
        
        # Update rudder position
        self.rudder_position = 90
        self.rudder_pos_var.set(90)
        self.direction_var.set("Straight")
        
        # Send command to Arduino
        self.send_command({"command": "R", "angle": 90})
    
    def send_command(self, command):
        if not self.connected:
            return
        
        try:
            with self.lock:
                cmd_type = command["command"]
                
                if cmd_type == "wave":
                    # Currently not implemented in Arduino code
                    # Would require updating Arduino code to accept these parameters
                    # For now, just print to console
                    print(f"Wave settings: A={command['amplitude']}, F={command['frequency']}, P={command['phase_shift']}")
                
                elif cmd_type == "S":
                    # Servo4 position
                    angle = command["angle"]
                    cmd_str = f"S{angle}\n"
                    self.ser.write(cmd_str.encode())
                
                elif cmd_type == "R":
                    # Rudder position
                    angle = command["angle"]
                    cmd_str = f"R{angle}\n"
                    self.ser.write(cmd_str.encode())
                
                elif cmd_type == "W":
                    # Switch to wave mode
                    self.ser.write(b"W\n")
                
        except Exception as e:
            print(f"Error sending command: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RobotControlGUI(root)
    root.mainloop()