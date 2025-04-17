# Python server script
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Store the latest commands
current_command = {
    "x": 0.0,
    "y": 0.0,
    "distance": 0.5
}

@app.route('/', methods=['GET'])
def get_command():
    """Endpoint for Arduino to fetch the latest command"""
    return jsonify(current_command)

@app.route('/set', methods=['GET', 'POST'])
def set_command():
    """Endpoint to set a new command"""
    global current_command
    
    if request.method == 'POST':
        data = request.json
        if data and 'x' in data and 'y' in data:
            current_command['x'] = data['x']
            current_command['y'] = data['y']
            if 'distance' in data:
                current_command['distance'] = data['distance']
            return jsonify({"status": "ok"})
    
    # If GET or invalid POST
    return jsonify(current_command)

@app.route('/control', methods=['GET'])
def control_page():
    """Simple web interface for controlling the robot"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Arduino Robot Control</title>
        <style>
            #joystick { 
                width: 300px; 
                height: 300px; 
                background: #eee; 
                border: 1px solid #999;
                position: relative;
            }
            #handle {
                width: 30px;
                height: 30px;
                background: blue;
                border-radius: 50%;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                cursor: pointer;
            }
            #distance {
                width: 300px;
                margin-top: 20px;
            }
            #status {
                margin-top: 20px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <h1>Arduino Robot Control</h1>
        <div id="joystick"><div id="handle"></div></div>
        <div>
            <label for="distance">Distance: <span id="distanceValue">0.5</span></label>
            <input type="range" id="distance" min="0.1" max="1.0" step="0.05" value="0.5">
        </div>
        <div id="status">Status: Ready</div>
        
        <script>
            const joystick = document.getElementById('joystick');
            const handle = document.getElementById('handle');
            const distanceSlider = document.getElementById('distance');
            const distanceValue = document.getElementById('distanceValue');
            const status = document.getElementById('status');
            
            let isDragging = false;
            let x = 0, y = 0;
            
            joystick.addEventListener('mousedown', (e) => {
                isDragging = true;
                updatePosition(e);
            });
            
            document.addEventListener('mousemove', (e) => {
                if (isDragging) updatePosition(e);
            });
            
            document.addEventListener('mouseup', () => {
                isDragging = false;
            });
            
            distanceSlider.addEventListener('input', () => {
                distanceValue.textContent = distanceSlider.value;
                sendData();
            });
            
            function updatePosition(e) {
                const rect = joystick.getBoundingClientRect();
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                // Calculate position relative to center
                let posX = e.clientX - rect.left - centerX;
                let posY = e.clientY - rect.top - centerY;
                
                // Constrain to joystick boundaries (circular)
                const radius = Math.min(rect.width, rect.height) / 2 - 15;
                const distance = Math.sqrt(posX * posX + posY * posY);
                
                if (distance > radius) {
                    posX = (posX / distance) * radius;
                    posY = (posY / distance) * radius;
                }
                
                // Update handle position
                handle.style.left = `${centerX + posX}px`;
                handle.style.top = `${centerY + posY}px`;
                
                // Calculate normalized values (-0.5 to 0.5)
                x = posX / radius / 2;
                y = -posY / radius / 2; // Invert Y axis
                
                sendData();
            }
            
            function sendData() {
                const data = {
                    x: x,
                    y: y,
                    distance: parseFloat(distanceSlider.value)
                };
                
                fetch('/set', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(data => {
                    status.textContent = `Status: Sent (x=${x.toFixed(2)}, y=${y.toFixed(2)}, dist=${distanceSlider.value})`;
                })
                .catch(error => {
                    status.textContent = `Status: Error: ${error}`;
                });
            }
            
            // Reset handle to center
            handle.style.left = '50%';
            handle.style.top = '50%';
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("Starting server on port 5000")
    print("Arduino should connect to: http://YOUR_COMPUTER_IP:5000")
    print("Control interface available at: http://localhost:5000/control")
    app.run(host='0.0.0.0', port=5000)