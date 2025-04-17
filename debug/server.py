import subprocess
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import serial
import serial.tools.list_ports
import asyncio
import uvicorn
import json
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import platform
import time

# FastAPI app
app = FastAPI(title="Snake Robot Controller")

# Serial connection parameters
BAUD_RATE = 115200
arduino_serial = None

# Snake robot parameters
class SnakeParams(BaseModel):
    steer: Optional[float] = None
    amplitude: Optional[float] = None
    frequency: Optional[float] = None
    phase_shift: Optional[float] = None

# Current state
current_state = {
    "steer": 0.0,
    "amplitude": 15.0,
    "frequency": 0.8,
    "phase_shift": 60.0,
    "connected": False,
    "port": None,
    "last_error": None,
    "debug_info": []
}

def add_debug_info(message):
    """Add debug information to the current state"""
    timestamp = time.strftime("%H:%M:%S")
    debug_message = f"[{timestamp}] {message}"
    print(debug_message)
    current_state["debug_info"].append(debug_message)
    # Keep only the last 20 debug messages
    if len(current_state["debug_info"]) > 20:
        current_state["debug_info"] = current_state["debug_info"][-20:]

def force_close_port(port_name: str) -> Dict[str, Any]:
    """Attempt to forcibly close a port that might be in use by another process"""
    system = platform.system()
    result = {"success": False, "message": ""}
    
    try:
        if system == "Windows":
            # On Windows, try to forcibly close the port
            # Get the port number (e.g., COM3 -> 3)
            port_num = ''.join(filter(str.isdigit, port_name))
            if port_num:
                # Mode.com is a Windows tool that can help reset COM ports
                subprocess.run(f"mode.com {port_name} BAUD=115200 PARITY=n DATA=8 STOP=1", 
                              shell=True, check=False, capture_output=True)
                result["success"] = True
                result["message"] = f"Attempted to reset {port_name} using mode.com"
        else:
            # For Linux and macOS, we might need to kill processes using the port
            # This is more complex and potentially dangerous, so we'll just suggest it
            result["success"] = False
            result["message"] = f"Manual intervention needed on {system}: Please check processes using the port"
    
    except Exception as e:
        result["success"] = False
        result["message"] = f"Error trying to force close port: {str(e)}"
    
    return result

async def find_arduino(force_reset: bool = False):
    """Find Arduino port by trying available ports"""
    add_debug_info("Searching for Arduino...")
    ports = list(serial.tools.list_ports.comports())
    add_debug_info(f"Found {len(ports)} ports: {', '.join([p.device for p in ports])}")
    
    for port in ports:
        try:
            # If the port was previously giving a permission error and force_reset is True
            if force_reset:
                result = force_close_port(port.device)
                add_debug_info(f"Port reset attempt: {result['message']}")
                await asyncio.sleep(1)  # Wait after reset attempt
            
            add_debug_info(f"Trying to connect to {port.device}...")
            ser = serial.Serial(port.device, BAUD_RATE, timeout=1)
            await asyncio.sleep(2)  # Wait for Arduino to reset
            
            # Clear any startup messages
            if ser.in_waiting:
                startup_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                add_debug_info(f"Cleared startup buffer: {startup_data.strip()}")
            ser.reset_input_buffer()
            
            # Try multiple commands to check if Arduino is responsive
            test_commands = [
                b"STATUS:1\n",
                b"STATUS\n",
                b"HELLO\n"
            ]
            
            found = False
            for cmd in test_commands:
                add_debug_info(f"Sending command: {cmd.decode().strip()}")
                ser.write(cmd)
                await asyncio.sleep(0.5)  # Longer wait time
                
                response = ""
                if ser.in_waiting:
                    response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    add_debug_info(f"Received response: {response.strip()}")
                    
                    # More lenient check - any response is better than none
                    if response:
                        add_debug_info(f"Arduino found on {port.device}, response: {response.strip()}")
                        return ser, port.device
                else:
                    add_debug_info(f"No response to {cmd.decode().strip()}")
            
            add_debug_info(f"No valid response from {port.device}, closing...")
            ser.close()
            
        except (serial.SerialException, OSError) as e:
            error_msg = f"Error on {port.device}: {str(e)}"
            add_debug_info(error_msg)
            if "PermissionError" in str(e) or "Access is denied" in str(e):
                current_state["last_error"] = f"Permission error on {port.device}: {str(e)}"
            continue
    
    add_debug_info("Arduino not found on any port")
    return None, None

@app.on_event("startup")
async def startup_event():
    global arduino_serial, current_state
    add_debug_info("Server starting up")
    arduino_serial, port = await find_arduino()
    if arduino_serial:
        current_state["connected"] = True
        current_state["port"] = port
        add_debug_info(f"Arduino automatically connected on {port}")
    else:
        add_debug_info("Arduino not found during startup. Please connect manually.")

@app.on_event("shutdown")
async def shutdown_event():
    if arduino_serial:
        arduino_serial.close()
        add_debug_info("Arduino disconnected during shutdown")

@app.get("/api/ports", response_model=List[str])
async def list_ports():
    """List available serial ports"""
    ports = [port.device for port in serial.tools.list_ports.comports()]
    add_debug_info(f"Port list requested: {ports}")
    return ports

@app.post("/api/connect/{port}")
async def connect_port(port: str):
    """Connect to a specific port"""
    global arduino_serial, current_state
    
    add_debug_info(f"Attempting to connect to {port}")
    
    if arduino_serial:
        arduino_serial.close()
        current_state["connected"] = False
        add_debug_info("Closed previous connection")
    
    try:
        add_debug_info(f"Opening serial port {port} at {BAUD_RATE} baud")
        arduino_serial = serial.Serial(port, BAUD_RATE, timeout=1)
        await asyncio.sleep(2)  # Wait for Arduino to reset
        
        # Clear buffer and log any initial data
        if arduino_serial.in_waiting:
            initial_data = arduino_serial.read(arduino_serial.in_waiting).decode('utf-8', errors='ignore')
            add_debug_info(f"Initial data from Arduino: {initial_data.strip()}")
        
        arduino_serial.reset_input_buffer()
        
        # Try multiple commands
        test_commands = [
            b"STATUS:1\n",
            b"STATUS\n",
            b"HELLO\n"
        ]
        
        for cmd in test_commands:
            add_debug_info(f"Sending command: {cmd.decode().strip()}")
            arduino_serial.write(cmd)
            await asyncio.sleep(0.5)
            
            response = ""
            if arduino_serial.in_waiting:
                response = arduino_serial.read(arduino_serial.in_waiting).decode('utf-8', errors='ignore')
                add_debug_info(f"Received response: {response.strip()}")
                
                # More lenient check - any response might indicate success
                if response:
                    current_state["connected"] = True
                    current_state["port"] = port
                    add_debug_info(f"Connection successful to {port}")
                    return {"status": "connected", "port": port, "response": response.strip()}
        
        # If we get here, connection failed despite getting a port
        add_debug_info(f"Device on {port} did not respond to any command")
        arduino_serial.close()
        arduino_serial = None
        return {"status": "failed", "message": "Device did not respond to any command", "debug_info": current_state["debug_info"]}
        
    except serial.SerialException as e:
        error_msg = f"Serial exception: {str(e)}"
        add_debug_info(error_msg)
        return {"status": "error", "message": error_msg, "debug_info": current_state["debug_info"]}

@app.get("/api/status")
async def get_status():
    """Get current robot status"""
    return current_state

@app.post("/api/control")
async def control_robot(params: SnakeParams):
    """Send control commands to the robot"""
    global arduino_serial, current_state
    
    if not arduino_serial or not current_state["connected"]:
        raise HTTPException(status_code=400, detail="Arduino not connected")
    
    # Update parameters that were specified
    if params.steer is not None:
        cmd = f"STEER:{params.steer}\n".encode()
        add_debug_info(f"Sending: {cmd.decode().strip()}")
        arduino_serial.write(cmd)
        current_state["steer"] = params.steer
    
    if params.amplitude is not None:
        cmd = f"AMP:{params.amplitude}\n".encode()
        add_debug_info(f"Sending: {cmd.decode().strip()}")
        arduino_serial.write(cmd)
        current_state["amplitude"] = params.amplitude
    
    if params.frequency is not None:
        cmd = f"FREQ:{params.frequency}\n".encode()
        add_debug_info(f"Sending: {cmd.decode().strip()}")
        arduino_serial.write(cmd)
        current_state["frequency"] = params.frequency
    
    if params.phase_shift is not None:
        cmd = f"PHASE:{params.phase_shift}\n".encode()
        add_debug_info(f"Sending: {cmd.decode().strip()}")
        arduino_serial.write(cmd)
        current_state["phase_shift"] = params.phase_shift
    
    # Read response if available
    await asyncio.sleep(0.02)  # Brief delay for Arduino to respond
    response = ""
    
    if arduino_serial.in_waiting:
        response = arduino_serial.read(arduino_serial.in_waiting).decode('utf-8', errors='ignore')
        add_debug_info(f"Received response: {response.strip()}")
    
    return {
        "status": "ok",
        "state": current_state,
        "response": response if response else "No response"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time control and updates"""
    await websocket.accept()
    add_debug_info("WebSocket client connected")
    
    try:
        while True:
            # Receive and process WebSocket messages
            data = await websocket.receive_text()
            try:
                params = json.loads(data)
                
                # Handle joystick input
                if "x" in params and "y" in params:
                    # Convert joystick x position to steering angle
                    steer_value = params["x"] * 30.0  # Scale to ±30 degrees
                    
                    # Only update if Arduino is connected
                    if arduino_serial and current_state["connected"]:
                        arduino_serial.write(f"STEER:{steer_value}\n".encode())
                        current_state["steer"] = steer_value
                        
                        # Also adjust frequency based on y position
                        if "y" in params:
                            y_value = params["y"]
                            if abs(y_value) > 0.05:  # Apply small dead zone
                                # Map y from -0.5..0.5 to frequency range 0.3..1.5
                                freq = 0.8 + y_value * 1.4
                                freq = max(0.3, min(1.5, freq))  # Clamp to safe range
                                arduino_serial.write(f"FREQ:{freq}\n".encode())
                                current_state["frequency"] = freq
                    
                    # Send updated state back to client
                    await websocket.send_json({
                        "status": "ok",
                        "state": current_state
                    })
                
            except json.JSONDecodeError:
                add_debug_info(f"Invalid JSON received: {data}")
                await websocket.send_json({"status": "error", "message": "Invalid JSON"})
            
    except Exception as e:
        error_msg = f"WebSocket error: {e}"
        add_debug_info(error_msg)

# Serve the HTML interface with updated debug display
@app.get("/", response_class=HTMLResponse)
async def get_html():
    """Serve the control interface HTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Snake Robot Control</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 0;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
            }
            #connection-panel {
                margin-bottom: 20px;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
            #joystick-container {
                width: 300px;
                height: 300px;
                background-color: #eee;
                border-radius: 50%;
                position: relative;
                margin: 0 auto 30px auto;
                touch-action: none;
            }
            #joystick-handle {
                width: 60px;
                height: 60px;
                background-color: #007bff;
                border-radius: 50%;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                touch-action: none;
            }
            .control-panel {
                text-align: left;
                margin: 15px auto;
                max-width: 300px;
            }
            .slider {
                width: 100%;
                margin: 10px 0;
            }
            .status {
                color: green;
                font-weight: bold;
            }
            .disconnected {
                color: red;
            }
            label {
                display: block;
                margin: 5px 0;
            }
            select, button {
                padding: 8px;
                margin: 5px;
            }
            .status-display {
                font-family: monospace;
                text-align: left;
                border: 1px solid #ccc;
                padding: 10px;
                margin-top: 20px;
                font-size: 14px;
                height: 200px;
                overflow-y: auto;
                background-color: #f9f9f9;
            }
            .debug-button {
                margin-top: 10px;
                background-color: #f0ad4e;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                cursor: pointer;
            }
            .debug-button:hover {
                background-color: #ec971f;
            }
        </style>
    </head>
    <body>
        <h1>Snake Robot Control</h1>
        
        <div id="connection-panel">
            <div>
                <select id="port-select">
                    <option value="">Select port</option>
                </select>
                <button id="refresh-ports">Refresh Ports</button>
                <button id="connect-button">Connect</button>
                <button id="force-connect-button" class="debug-button">Force Connect</button>
            </div>
            <div id="connection-status">Status: <span class="disconnected">Disconnected</span></div>
        </div>
        
        <div id="joystick-container">
            <div id="joystick-handle"></div>
        </div>
        
        <div class="control-panel">
            <label>
                Amplitude: <span id="amplitude-value">15</span>°
                <input type="range" id="amplitude-slider" class="slider" min="5" max="30" value="15">
            </label>
            
            <label>
                Frequency: <span id="frequency-value">0.8</span> Hz
                <input type="range" id="frequency-slider" class="slider" min="0.2" max="2.0" step="0.1" value="0.8">
            </label>
            
            <label>
                Phase Shift: <span id="phase-value">60</span>°
                <input type="range" id="phase-slider" class="slider" min="30" max="90" step="5" value="60">
            </label>
        </div>
        
        <div class="status-display" id="status-display">Ready to connect...</div>
        <button id="clear-log" class="debug-button">Clear Log</button>
        <button id="refresh-status" class="debug-button">Refresh Status</button>
        
        <script>
            // DOM Elements
            const portSelect = document.getElementById('port-select');
            const refreshButton = document.getElementById('refresh-ports');
            const connectButton = document.getElementById('connect-button');
            const forceConnectButton = document.getElementById('force-connect-button');
            const connectionStatus = document.getElementById('connection-status');
            const joystickContainer = document.getElementById('joystick-container');
            const joystickHandle = document.getElementById('joystick-handle');
            const amplitudeSlider = document.getElementById('amplitude-slider');
            const frequencySlider = document.getElementById('frequency-slider');
            const phaseSlider = document.getElementById('phase-slider');
            const amplitudeValue = document.getElementById('amplitude-value');
            const frequencyValue = document.getElementById('frequency-value');
            const phaseValue = document.getElementById('phase-value');
            const statusDisplay = document.getElementById('status-display');
            const clearLogButton = document.getElementById('clear-log');
            const refreshStatusButton = document.getElementById('refresh-status');
            
            // State variables
            let connected = false;
            let joystickActive = false;
            let wsConnection = null;
            
            // Handle WebSocket connection
            function connectWebSocket() {
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
                
                wsConnection = new WebSocket(wsUrl);
                
                wsConnection.onopen = function() {
                    console.log('WebSocket connected');
                    addStatus('WebSocket connected');
                };
                
                wsConnection.onclose = function() {
                    console.log('WebSocket disconnected');
                    addStatus('WebSocket disconnected');
                };
                
                wsConnection.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.state) {
                        updateUIFromState(data.state);
                    }
                };
                
                wsConnection.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    addStatus('WebSocket error: ' + error);
                };
            }
            
            // Connect WebSocket on page load
            connectWebSocket();
            
            // Update UI from state
            function updateUIFromState(state) {
                if (state.connected !== connected) {
                    connected = state.connected;
                    connectionStatus.innerHTML = 'Status: ' + 
                        (connected ? 
                         '<span class="status">Connected to ' + state.port + '</span>' : 
                         '<span class="disconnected">Disconnected</span>');
                }
                
                // Only update sliders if not being dragged
                if (!amplitudeSlider.matches(':active')) {
                    amplitudeSlider.value = state.amplitude;
                    amplitudeValue.textContent = state.amplitude.toFixed(1);
                }
                
                if (!frequencySlider.matches(':active')) {
                    frequencySlider.value = state.frequency;
                    frequencyValue.textContent = state.frequency.toFixed(1);
                }
                
                if (!phaseSlider.matches(':active')) {
                    phaseSlider.value = state.phase_shift;
                    phaseValue.textContent = state.phase_shift.toFixed(1);
                }
                
                // Update debug info if available
                if (state.debug_info && state.debug_info.length > 0) {
                    // Only update if there's new info
                    if (statusDisplay.innerHTML.split('<br>').length - 1 < state.debug_info.length) {
                        statusDisplay.innerHTML = state.debug_info.join('<br>');
                        statusDisplay.scrollTop = statusDisplay.scrollHeight;
                    }
                }
            }
            
            // Fetch available ports
            async function fetchPorts() {
                try {
                    const response = await fetch('/api/ports');
                    const ports = await response.json();
                    
                    // Clear existing options
                    portSelect.innerHTML = '<option value="">Select port</option>';
                    
                    // Add port options
                    ports.forEach(port => {
                        const option = document.createElement('option');
                        option.value = port;
                        option.textContent = port;
                        portSelect.appendChild(option);
                    });
                    
                    addStatus(`Found ${ports.length} ports`);
                } catch (error) {
                    console.error('Error fetching ports:', error);
                    addStatus('Error fetching ports: ' + error.message);
                }
            }
            
            // Connect to selected port
            async function connectToPort(forceConnect = false) {
                const port = portSelect.value;
                if (!port) {
                    alert('Please select a port');
                    return;
                }
                
                try {
                    const url = forceConnect 
                        ? `/api/connect/${port}?force=true` 
                        : `/api/connect/${port}`;
                    
                    const response = await fetch(url, { method: 'POST' });
                    const result = await response.json();
                    
                    if (result.status === 'connected') {
                        connected = true;
                        connectionStatus.innerHTML = `Status: <span class="status">Connected to ${port}</span>`;
                        addStatus(`Connected to ${port}`);
                        
                        // Display debug info if available
                        if (result.debug_info) {
                            statusDisplay.innerHTML = result.debug_info.join('<br>');
                            statusDisplay.scrollTop = statusDisplay.scrollHeight;
                        }
                        
                        // Fetch current status
                        fetchStatus();
                    } else {
                        if (result.debug_info) {
                            statusDisplay.innerHTML = result.debug_info.join('<br>');
                            statusDisplay.scrollTop = statusDisplay.scrollHeight;
                        }
                        addStatus(`Connection failed: ${result.message}`);
                    }
                } catch (error) {
                    console.error('Error connecting:', error);
                    addStatus('Error connecting: ' + error.message);
                }
            }
            
            // Fetch current status
            async function fetchStatus() {
                try {
                    const response = await fetch('/api/status');
                    const status = await response.json();
                    updateUIFromState(status);
                } catch (error) {
                    console.error('Error fetching status:', error);
                    addStatus('Error fetching status: ' + error.message);
                }
            }
            
            // Send control command
            async function sendControl(params) {
                try {
                    const response = await fetch('/api/control', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(params)
                    });
                    
                    const result = await response.json();
                    if (result.response && result.response !== 'No response') {
                        addStatus(result.response);
                    }
                } catch (error) {
                    console.error('Error sending control:', error);
                    addStatus('Error sending control: ' + error.message);
                }
            }
            
            // Joystick control
            function handleJoystick(event) {
                if (!joystickActive || !connected) return;
                
                // Prevent scrolling on touch devices
                if (event.cancelable) event.preventDefault();
                
                // Get joystick container dimensions
                const rect = joystickContainer.getBoundingClientRect();
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                // Get touch/mouse position
                let pointerX, pointerY;
                if (event.type.includes('touch')) {
                    pointerX = event.touches[0].clientX - rect.left;
                    pointerY = event.touches[0].clientY - rect.top;
                } else {
                    pointerX = event.clientX - rect.left;
                    pointerY = event.clientY - rect.top;
                }
                
                // Calculate displacement from center
                let dx = pointerX - centerX;
                let dy = pointerY - centerY;
                
                // Limit to joystick radius
                const radius = Math.min(centerX, centerY) - 30;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance > radius) {
                    dx = dx * (radius / distance);
                    dy = dy * (radius / distance);
                }
                
                // Update handle position
                joystickHandle.style.left = `${centerX + dx}px`;
                joystickHandle.style.top = `${centerY + dy}px`;
                
                // Calculate normalized values (-1 to 1)
                const x = dx / radius;
                const y = -dy / radius;  // Invert Y axis
                
                // Send via WebSocket for faster response
                if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
                    wsConnection.send(JSON.stringify({ x, y }));
                }
            }
            
            function resetJoystick() {
                joystickActive = false;
                joystickHandle.style.left = '50%';
                joystickHandle.style.top = '50%';
                
                // Send zero command via WebSocket
                if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
                    wsConnection.send(JSON.stringify({ x: 0, y: 0 }));
                }
            }
            
            // Add status message
            function addStatus(message) {
                const now = new Date();
                const time = now.toLocaleTimeString();
                statusDisplay.innerHTML += `[${time}] ${message}<br>`;
                statusDisplay.scrollTop = statusDisplay.scrollHeight;
            }
            
            // Event listeners
            refreshButton.addEventListener('click', fetchPorts);
            connectButton.addEventListener('click', () => connectToPort(false));
            forceConnectButton.addEventListener('click', () => connectToPort(true));
            clearLogButton.addEventListener('click', () => {
                statusDisplay.innerHTML = 'Log cleared.<br>';
            });
            refreshStatusButton.addEventListener('click', fetchStatus);
            
            // Joystick events
            joystickContainer.addEventListener('mousedown', (e) => {
                joystickActive = true;
                handleJoystick(e);
            });
            
            joystickContainer.addEventListener('touchstart', (e) => {
                joystickActive = true;
                handleJoystick(e);
            }, { passive: false });
            
            document.addEventListener('mousemove', (e) => {
                if (joystickActive) handleJoystick(e);
            });
            
            document.addEventListener('touchmove', (e) => {
                if (joystickActive) handleJoystick(e);
            }, { passive: false });
            
            document.addEventListener('mouseup', resetJoystick);
            document.addEventListener('touchend', resetJoystick);
            
            // Slider events
            amplitudeSlider.addEventListener('input', () => {
                const value = parseFloat(amplitudeSlider.value);
                amplitudeValue.textContent = value;
                sendControl({ amplitude: value });
            });
            
            frequencySlider.addEventListener('input', () => {
                const value = parseFloat(frequencySlider.value);
                frequencyValue.textContent = value;
                sendControl({ frequency: value });
            });
            
            phaseSlider.addEventListener('input', () => {
                const value = parseFloat(phaseSlider.value);
                phaseValue.textContent = value;
                sendControl({ phase_shift: value });
            });
            
            // Initial setup
            fetchPorts();
            fetchStatus();
            
            // Regularly fetch status to update debug info
            setInterval(fetchStatus, 2000);
            
            // Reconnect WebSocket if it closes
            setInterval(() => {
                if (wsConnection && wsConnection.readyState === WebSocket.CLOSED) {
                    connectWebSocket();
                }
            }, 5000);
        </script>
    </body>
    </html>
    """

# Run the server
if __name__ == "__main__":
    print("Starting Snake Robot Control Server")
    print("-----------------------------------")
    print("1. Connect Arduino via USB")
    print("2. Open http://localhost:8000 in browser")
    print("3. Select the correct port and connect")
    print("4. Use joystick to control the snake robot")
    print("-----------------------------------")
    uvicorn.run(app, host="0.0.0.0", port=8000)