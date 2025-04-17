#include <Servo.h>
#include <math.h>
#include <ArduinoJson.h>
#include <WiFiS3.h>

// Create servo objects for snake segments
Servo servo1;  // Head segment (for steering)
Servo servo2;  // Body segment 1
Servo servo3;  // Body segment 2
Servo servo4;  // Body segment 3
Servo servo5;  // Body segment 4 (connected to pin 11)

// === USER-TUNABLE PARAMETERS ===
float amplitude = 25.0;        // Maximum angle for undulation (0-50 is safe)
float frequency = 0.8;         // Hz (cycles per second)
float phaseShiftDeg = 60.0;    // Degrees phase shift between segments
float steeringAngle = 0.0;     // Steering offset angle for head segment

// === INTERNAL SETTINGS ===
const float centerPos = 90.0;     // Center position (neutral angle)
const unsigned long updateDelay = 10; // ms between updates (reduced for less lag)
const float pi = 3.14159265;

// Tuning parameters for responsiveness
const float steeringGain = 1.5;    // Multiplier for steering sensitivity
const float frequencyGain = 3.0;   // Multiplier for frequency response
const float lowPassFilter = 0.8;   // Value between 0-1, lower = smoother but more lag

// Previous values for smooth transitions
float prevSteeringAngle = 0.0;
float prevAmplitude = 25.0;
float prevFrequency = 0.8;
float prevPhaseShift = 60.0;

// Variables to store received data
float robot_x = 0;           // Horizontal joystick position (-0.5 to 0.5)
float robot_y = 0;           // Vertical joystick position (-0.5 to 0.5)
float target_heading = 0;    // Target heading in degrees
float distance = 0;          // Distance from target

// Counter to track number of messages received
unsigned long msg_count = 0;

// Timer variables
unsigned long previousMillis = 0;
float timeSeconds = 0.0;

// Flag to track if we've received data and should run motors
bool dataReceived = false;

// Timeout for data (stop motors if no new data for this long)
const unsigned long dataTimeout = 1000; // milliseconds
unsigned long lastDataTime = 0;

// AP WiFi settings
char ssid[] = "SnakeRobot";   // AP SSID
char pass[] = "robotcontrol"; // AP password - at least 8 chars

// Server on port 80
WiFiServer server(80);
WiFiClient client;

void setup() {
  // Initialize serial communication for debugging
  Serial.begin(115200);  // Increased baud rate for faster communication
  
  // Attach servos to pins
  servo1.attach(3);  // Head/steering segment
  servo2.attach(5);  // Body segment 1
  servo3.attach(6);  // Body segment 2
  servo4.attach(9);  // Body segment 3
  servo5.attach(11); // Body segment 4
  
  // Initialize servos to center position
  servo1.write(centerPos);
  servo2.write(centerPos);
  servo3.write(centerPos);
  servo4.write(centerPos);
  servo5.write(centerPos);
  
  // Create access point
  Serial.println("Creating WiFi access point...");
  
  // Check for the WiFi module
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // Don't continue
    while (true);
  }
  
  // Print firmware version
  Serial.print("WiFi firmware version: ");
  Serial.println(WiFi.firmwareVersion());
  
  // Create AP
  Serial.print("Creating access point named: ");
  Serial.println(ssid);

  // Create network
  int status = WiFi.beginAP(ssid, pass);
  
  if (status != WL_AP_LISTENING) {
    Serial.println("Creating access point failed");
    while (true); // Don't continue
  }
  
  delay(5000); // Wait for AP to start
  
  // Start the server
  server.begin();
  
  Serial.println("Access point created!");
  Serial.println("To control the snake robot:");
  Serial.println("1. Connect to the WiFi network named: " + String(ssid));
  Serial.println("2. Use password: " + String(pass));
  Serial.println("3. Open a web browser and go to: http://192.168.4.1");
  
  // Print the IP address
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
  
  Serial.println("Motors disabled until data received");
}

void loop() {
  // Check if we're still in AP mode
  if (WiFi.status() != WL_AP_LISTENING && WiFi.status() != WL_AP_CONNECTED) {
    Serial.println("AP mode stopped - attempting to restart");
    WiFi.beginAP(ssid, pass);
    delay(5000);
    return;
  }
  
  // Handle any client connections
  handleClient();
  
  // Check for data timeout - disable motors if no data received for a while
  if (dataReceived && (millis() - lastDataTime > dataTimeout)) {
    Serial.println("Data timeout - Motors disabled");
    dataReceived = false;
    
    // Return servos to center position
    servo1.write(centerPos);
    servo2.write(centerPos);
    servo3.write(centerPos);
    servo4.write(centerPos);
    servo5.write(centerPos);
  }
  
  // Only run the servo control logic if we've received data
  if (dataReceived) {
    updateServos();
  }
  
  // Send a heartbeat message every 5 seconds
  static unsigned long last_heartbeat = 0;
  if (millis() - last_heartbeat > 5000) {
    Serial.print("Snake robot heartbeat - Motors ");
    Serial.println(dataReceived ? "active" : "disabled, waiting for data");
    last_heartbeat = millis();

    // Print network information
    Serial.print("AP IP Address: ");
    Serial.println(WiFi.localIP());
    
    // Print current parameters if active
    if (dataReceived) {
      Serial.print("Current settings - Amplitude: ");
      Serial.print(amplitude);
      Serial.print(", Frequency: ");
      Serial.print(frequency);
      Serial.print(", PhaseShift: ");
      Serial.print(phaseShiftDeg);
      Serial.print(", Steering: ");
      Serial.println(steeringAngle);
    }
  }
}

void handleClient() {
  // Check if client is connected
  if (!client || !client.connected()) {
    client = server.available();
    if (client) {
      Serial.println("New client connected");
      
      // Read the first line of the request
      String request = client.readStringUntil('\r');
      client.flush();
      
      // Check for JSON data (POST request)
      if (request.indexOf("POST /api/") != -1) {
        // Skip HTTP headers
        while (client.available() && client.readStringUntil('\n') != "\r");
        
        // Process JSON data
        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, client);
        
        if (!error) {
          if (doc.containsKey("x") && doc.containsKey("y")) {
            robot_x = doc["x"];
            robot_y = doc["y"];
            
            // Update target heading based on x position (steering)
            target_heading = robot_x * 60.0; // Map -0.5 to 0.5 to -30 to 30 degrees
            
            if (doc.containsKey("distance")) {
              distance = doc["distance"];
            }
            
            // Increment message counter
            msg_count++;
            
            // Debug output (only every 10th message to reduce serial overhead)
            if (msg_count % 10 == 0) {
              Serial.print("MSG #");
              Serial.print(msg_count);
              Serial.print(": X=");
              Serial.print(robot_x, 2);
              Serial.print(", Y=");
              Serial.print(robot_y, 2);
              Serial.print(", Heading=");
              Serial.print(target_heading, 1);
              Serial.print("°, Distance=");
              Serial.println(distance, 2);
            }
            
            // Set flag that we've received data
            if (!dataReceived) {
              Serial.println("First data received - Snake activated");
              dataReceived = true;
            }
            
            // Update data timeout tracker
            lastDataTime = millis();
            
            // Adjust servo parameters based on position data
            adjustServoParameters();
            
            // Send confirmation
            client.println("HTTP/1.1 200 OK");
            client.println("Content-Type: application/json");
            client.println("Access-Control-Allow-Origin: *");
            client.println("Connection: close");
            client.println();
            
            // Send JSON response
            StaticJsonDocument<200> respDoc;
            respDoc["status"] = "ok";
            respDoc["msg_count"] = msg_count;
            respDoc["x"] = robot_x;
            respDoc["y"] = robot_y;
            respDoc["heading"] = target_heading;
            respDoc["distance"] = distance;
            respDoc["amplitude"] = amplitude;
            respDoc["frequency"] = frequency;
            
            serializeJson(respDoc, client);
          }
        }
      }
      // Send HTML if it's a GET request for the root
      else if (request.indexOf("GET / ") != -1 || request.indexOf("GET /index.html") != -1) {
        client.println("HTTP/1.1 200 OK");
        client.println("Content-Type: text/html");
        client.println("Connection: close");
        client.println();
        
        // Send a complete web page with JavaScript controller and snake robot simulation
        client.println("<!DOCTYPE HTML>");
        client.println("<html>");
        client.println("<head>");
        client.println("<title>Snake Robot Control</title>");
        client.println("<meta name='viewport' content='width=device-width, initial-scale=1'>");
        client.println("<style>");
        client.println("body { font-family: Arial; text-align: center; margin: 0px auto; padding: 20px; }");
        client.println(".container { display: flex; flex-direction: column; align-items: center; }");
        client.println("#joystick { width: 300px; height: 300px; background: #eee; border-radius: 50%; position: relative; }");
        client.println("#handle { width: 50px; height: 50px; background: #007bff; border-radius: 50%; position: absolute; cursor: pointer; transform: translate(-50%, -50%); }");
        client.println(".slider-container { width: 300px; margin: 20px 0; }");
        client.println(".slider { width: 100%; }");
        client.println("#status { margin-top: 20px; padding: 10px; border: 1px solid #ddd; width: 300px; font-family: monospace; height: 80px; overflow-y: auto; text-align: left; }");
        
        // New styles for the snake simulation
        client.println("#snake-simulation { width: 100%; max-width: 500px; height: 120px; position: relative; margin: 20px auto; border: 1px solid #ddd; background: #f9f9f9; overflow: hidden; }");
        client.println(".segment { width: 35px; height: 20px; background: #007bff; position: absolute; border-radius: 10px; }");
        client.println("#head { background: #ff6b00; }");
        client.println(".line { position: absolute; height: 1px; background: #ff9800; top: 60px; left: 0; right: 0; }");
        client.println("#start, #end { position: absolute; font-weight: bold; font-size: 12px; }");
        client.println("#start { right: 10px; top: 5px; }");
        client.println("#end { left: 10px; top: 5px; }");
        
        client.println("</style>");
        client.println("</head>");
        client.println("<body>");
        client.println("<h1>Snake Robot Control</h1>");
        client.println("<h3>Servo-based Fish Locomotion</h3>");
        client.println("<div class='container'>");
        client.println("  <div id='joystick'><div id='handle'></div></div>");
        client.println("  <div class='slider-container'>");
        client.println("    <label for='amplitude'>Amplitude: <span id='amplitudeValue'>25</span> degrees</label>");
        client.println("    <input type='range' id='amplitude' class='slider' min='5' max='50' step='1' value='25'>");
        client.println("  </div>");
        client.println("  <div class='slider-container'>");
        client.println("    <label for='frequency'>Frequency: <span id='frequencyValue'>0.8</span> Hz</label>");
        client.println("    <input type='range' id='frequency' class='slider' min='0.2' max='2.0' step='0.1' value='0.8'>");
        client.println("  </div>");
        client.println("  <div class='slider-container'>");
        client.println("    <label for='phaseShift'>Phase Shift: <span id='phaseShiftValue'>60</span> degrees</label>");
        client.println("    <input type='range' id='phaseShift' class='slider' min='30' max='90' step='5' value='60'>");
        client.println("  </div>");
        client.println("  <div id='status'>Ready to control snake robot</div>");
        
        // Add snake simulation
        client.println("  <h3>Live Simulation</h3>");
        client.println("  <div id='snake-simulation'>");
        client.println("    <div class='line'></div>");
        client.println("    <div id='head' class='segment'></div>");
        client.println("    <div id='segment1' class='segment'></div>");
        client.println("    <div id='segment2' class='segment'></div>");
        client.println("    <div id='segment3' class='segment'></div>");
        client.println("    <div id='segment4' class='segment'></div>");
        client.println("    <div id='start'>START</div>");
        client.println("    <div id='end'>END</div>");
        client.println("  </div>");
        
        client.println("</div>");
        
        client.println("<script>");
        client.println("const joystick = document.getElementById('joystick');");
        client.println("const handle = document.getElementById('handle');");
        client.println("const amplitudeSlider = document.getElementById('amplitude');");
        client.println("const amplitudeValue = document.getElementById('amplitudeValue');");
        client.println("const frequencySlider = document.getElementById('frequency');");
        client.println("const frequencyValue = document.getElementById('frequencyValue');");
        client.println("const phaseShiftSlider = document.getElementById('phaseShift');");
        client.println("const phaseShiftValue = document.getElementById('phaseShiftValue');");
        client.println("const status = document.getElementById('status');");
        
        // Snake simulation elements
        client.println("const segments = [");
        client.println("  document.getElementById('head'),");
        client.println("  document.getElementById('segment1'),");
        client.println("  document.getElementById('segment2'),");
        client.println("  document.getElementById('segment3'),");
        client.println("  document.getElementById('segment4')");
        client.println("];");
        
        // Variables for simulation
        client.println("let simAmplitude = 25;");
        client.println("let simFrequency = 0.8;");
        client.println("let simPhaseShift = 60;");
        client.println("let simHeading = 0;");
        client.println("let simTime = 0;");
        client.println("let simRunning = false;");
        client.println("let lastUpdate = Date.now();");
        client.println("let baseX = 250;  // Middle of simulation area");
        
        client.println("// Center the handle initially");
        client.println("handle.style.left = '50%';");
        client.println("handle.style.top = '50%';");
        
        client.println("let isDragging = false;");
        client.println("let x = 0, y = 0;");
        client.println("let intervalId = null;");
        client.println("let simulationId = null;");
        client.println("let lastSendTime = 0;  // To throttle data sending");
        
        // Touch and mouse events for the joystick
        client.println("joystick.addEventListener('mousedown', startDrag);");
        client.println("joystick.addEventListener('touchstart', handleTouch);");
        client.println("document.addEventListener('mousemove', moveDrag);");
        client.println("document.addEventListener('touchmove', handleTouch);");
        client.println("document.addEventListener('mouseup', endDrag);");
        client.println("document.addEventListener('touchend', endDrag);");
        
        // Slider event listeners
        client.println("amplitudeSlider.addEventListener('input', updateAmplitude);");
        client.println("frequencySlider.addEventListener('input', updateFrequency);");
        client.println("phaseShiftSlider.addEventListener('input', updatePhaseShift);");
        
        client.println("function startDrag(e) {");
        client.println("  isDragging = true;");
        client.println("  updatePosition(e);");
        client.println("  // Start sending data regularly");
        client.println("  if (intervalId === null) {");
        client.println("    intervalId = setInterval(sendData, 50);"); // Increased frequency to 50ms for responsiveness
        client.println("  }");
        client.println("  // Start the simulation");
        client.println("  if (simulationId === null) {");
        client.println("    simRunning = true;");
        client.println("    lastUpdate = Date.now();");
        client.println("    simulationId = requestAnimationFrame(updateSimulation);");
        client.println("  }");
        client.println("}");
        
        client.println("function handleTouch(e) {");
        client.println("  e.preventDefault();");
        client.println("  if (e.type === 'touchstart') {");
        client.println("    isDragging = true;");
        client.println("    if (intervalId === null) {");
        client.println("      intervalId = setInterval(sendData, 50);"); // 50ms for more responsiveness
        client.println("    }");
        client.println("    // Start the simulation");
        client.println("    if (simulationId === null) {");
        client.println("      simRunning = true;");
        client.println("      lastUpdate = Date.now();");
        client.println("      simulationId = requestAnimationFrame(updateSimulation);");
        client.println("    }");
        client.println("  }");
        client.println("  if (isDragging && e.touches && e.touches[0]) {");
        client.println("    updatePosition(e.touches[0]);");
        client.println("  }");
        client.println("}");
        
        client.println("function moveDrag(e) {");
        client.println("  if (isDragging) {");
        client.println("    updatePosition(e);");
        client.println("  }");
        client.println("}");
        
        client.println("function endDrag() {");
        client.println("  isDragging = false;");
        client.println("  // Return handle to center");
        client.println("  handle.style.left = '50%';");
        client.println("  handle.style.top = '50%';");
        client.println("  x = 0;");
        client.println("  y = 0;");
        client.println("  sendData();");
        client.println("  // Stop the interval");
        client.println("  clearInterval(intervalId);");
        client.println("  intervalId = null;");
        client.println("  // Don't stop the simulation, let it continue showing the robot");
        client.println("}");
        
        client.println("function updateAmplitude() {");
        client.println("  simAmplitude = parseInt(amplitudeSlider.value);");
        client.println("  amplitudeValue.textContent = simAmplitude;");
        client.println("  sendData();");
        client.println("}");
        
        client.println("function updateFrequency() {");
        client.println("  simFrequency = parseFloat(frequencySlider.value);");
        client.println("  frequencyValue.textContent = simFrequency;");
        client.println("  sendData();");
        client.println("}");
        
        client.println("function updatePhaseShift() {");
        client.println("  simPhaseShift = parseInt(phaseShiftSlider.value);");
        client.println("  phaseShiftValue.textContent = simPhaseShift;");
        client.println("  sendData();");
        client.println("}");
        
        client.println("function updatePosition(e) {");
        client.println("  const rect = joystick.getBoundingClientRect();");
        client.println("  const centerX = rect.width / 2;");
        client.println("  const centerY = rect.height / 2;");
        
        client.println("  // Calculate position relative to center");
        client.println("  let posX = e.clientX - rect.left - centerX;");
        client.println("  let posY = e.clientY - rect.top - centerY;");
        
        client.println("  // Constrain to joystick boundaries (circular)");
        client.println("  const radius = Math.min(rect.width, rect.height) / 2 - 25;");
        client.println("  const distance = Math.sqrt(posX * posX + posY * posY);");
        
        client.println("  if (distance > radius) {");
        client.println("    posX = (posX / distance) * radius;");
        client.println("    posY = (posY / distance) * radius;");
        client.println("  }");
        
        client.println("  // Update handle position");
        client.println("  handle.style.left = `${centerX + posX}px`;");
        client.println("  handle.style.top = `${centerY + posY}px`;");
        
        client.println("  // Calculate normalized values (-0.5 to 0.5)");
        client.println("  x = posX / radius / 2;");
        client.println("  y = -posY / radius / 2; // Invert Y axis to match robot coordinates");
        client.println("  ");
        client.println("  // Update simulation parameters");
        client.println("  simHeading = x * 60; // Convert x to heading angle (-30 to 30 deg)");
        client.println("  ");
        client.println("  // Throttle updates to prevent overloading");
        client.println("  const now = Date.now();");
        client.println("  if (now - lastSendTime > 50) { // 50ms throttle");
        client.println("    sendData();");
        client.println("    lastSendTime = now;");
        client.println("  }");
        client.println("}");
        
        client.println("function updateSimulation() {");
        client.println("  if (!simRunning) return;");
        
        client.println("  const now = Date.now();");
        client.println("  const deltaT = (now - lastUpdate) / 1000; // Time in seconds");
        client.println("  lastUpdate = now;");
        
        client.println("  simTime += deltaT;");
        client.println("  const pi = Math.PI;");
        client.println("  const omega = 2 * pi * simFrequency;");
        client.println("  const phaseShiftRad = simPhaseShift * pi / 180;");
        
        client.println("  // Keep the simulation container width updated");
        client.println("  const containerWidth = document.getElementById('snake-simulation').offsetWidth;");
        client.println("  baseX = containerWidth / 2; // Center point");
        
        client.println("  // Calculate positions for each segment");
        client.println("  const segmentSpacing = 40; // Distance between segments");
        client.println("  const centerY = 60; // Vertical center of simulation area");
        
        client.println("  for (let i = 0; i < segments.length; i++) {");
        client.println("    // Calculate offset position along the sine wave");
        client.println("    const xOffset = i * segmentSpacing;");
        client.println("    const wavePos = simTime * simFrequency - (i * phaseShiftRad / (2 * pi));");
        client.println("    ");
        client.println("    // Add steering for the head segment (i=0)");
        client.println("    let extraSteering = 0;");
        client.println("    if (i === 0) {");
        client.println("      extraSteering = simHeading;");
        client.println("    }");
        
        client.println("    // Calculate wave amplitude at this position");
        client.println("    const angle = omega * simTime - i * phaseShiftRad;");
        client.println("    const yWave = simAmplitude * Math.sin(angle);");
        
        client.println("    // Position on screen");
        client.println("    const xPos = baseX - xOffset;");
        client.println("    const yPos = centerY - yWave;");
        
        client.println("    // Apply rotation to simulate the snake's bending body");
        client.println("    const segment = segments[i];");
        client.println("    const rotation = Math.atan2(Math.cos(angle) * simAmplitude, segmentSpacing) * 180 / pi;");
        
        client.println("    // Apply position and rotation");
        client.println("    segment.style.left = `${xPos - 15}px`; // Center the segment (width/2)");
        client.println("    segment.style.top = `${yPos - 10}px`; // Center the segment (height/2)");
        client.println("    segment.style.transform = `rotate(${rotation + extraSteering}deg)`;");
        client.println("  }");
        
        client.println("  // Continue simulation");
        client.println("  simulationId = requestAnimationFrame(updateSimulation);");
        client.println("}");
        
        client.println("function sendData() {");
        client.println("  const data = {");
        client.println("    x: parseFloat(x.toFixed(3)),");
        client.println("    y: parseFloat(y.toFixed(3)),");
        client.println("    amplitude: simAmplitude,");
        client.println("    frequency: simFrequency,");
        client.println("    phaseShift: simPhaseShift");
        client.println("  };");
        
        client.println("  fetch('/api/control', {");
        client.println("    method: 'POST',");
        client.println("    headers: { 'Content-Type': 'application/json' },");
        client.println("    body: JSON.stringify(data)");
        client.println("  })");
        client.println("  .then(response => response.json())");
        client.println("  .then(data => {");
        client.println("    // Update status with a timestamp to see responsiveness");
        client.println("    const now = new Date();");
        client.println("    const time = now.getHours().toString().padStart(2, '0') + ':' +");
        client.println("                now.getMinutes().toString().padStart(2, '0') + ':' +");
        client.println("                now.getSeconds().toString().padStart(2, '0') + '.' +");
        client.println("                now.getMilliseconds().toString().padStart(3, '0');");
        client.println("    status.innerHTML = `[${time}] x=${data.x.toFixed(2)}, y=${data.y.toFixed(2)}, heading=${data.heading.toFixed(1)}°<br>Amp=${data.amplitude.toFixed(1)}, Freq=${data.frequency.toFixed(1)}, Phase=${data.phaseShift}°`;");
        client.println("  })");
        client.println("  .catch(error => {");
        client.println("    status.innerHTML += `<br>Error: ${error.message}`;");
        client.println("  });");
        client.println("}");
        
        client.println("// Initialize the simulation");
        client.println("function initSimulation() {");
        client.println("  simRunning = true;");
        client.println("  lastUpdate = Date.now();");
        client.println("  requestAnimationFrame(updateSimulation);");
        client.println("}");
        
        client.println("// Start simulation when page loads");
        client.println("window.addEventListener('load', initSimulation);");
        
        client.println("</script>");
        client.println("</body>");
        client.println("</html>");
      }
      
      // Give the client time to receive the response
      delay(10);
      client.stop();
    }
  }
}

void adjustServoParameters() {
  // Use low-pass filtering for smoother transitions
  
  // Update steering angle with low-pass filter
  steeringAngle = prevSteeringAngle * lowPassFilter + 
                 (target_heading * steeringGain) * (1.0 - lowPassFilter);
  prevSteeringAngle = steeringAngle;
  
  // Adjust frequency based on y-position (forward speed control)
  // Positive y = forward movement = higher frequency
  float targetFreq = map(robot_y * 100, -50, 50, 0.2 * 100, 2.0 * 100) / 100.0;
  targetFreq = constrain(targetFreq, 0.2, 2.0);
  
  frequency = prevFrequency * lowPassFilter + targetFreq * (1.0 - lowPassFilter);
  prevFrequency = frequency;
  
  // Allow client to directly set amplitude and phase shift if provided
  if (client && client.available()) {
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, client);
    
    if (!error) {
      if (doc.containsKey("amplitude")) {
        float targetAmp = doc["amplitude"];
        amplitude = prevAmplitude * lowPassFilter + targetAmp * (1.0 - lowPassFilter);
        prevAmplitude = amplitude;
      }
      
      if (doc.containsKey("phaseShift")) {
        float targetPhase = doc["phaseShift"];
        phaseShiftDeg = prevPhaseShift * lowPassFilter + targetPhase * (1.0 - lowPassFilter);
        prevPhaseShift = phaseShiftDeg;
      }
      
      if (doc.containsKey("frequency")) {
        float targetFreq = doc["frequency"];
        frequency = prevFrequency * lowPassFilter + targetFreq * (1.0 - lowPassFilter);
        prevFrequency = frequency;
      }
    }
  }
  
  // Constrain all parameters to safe ranges
  amplitude = constrain(amplitude, 5, 50);
  frequency = constrain(frequency, 0.2, 2.0);
  phaseShiftDeg = constrain(phaseShiftDeg, 30, 90);
  steeringAngle = constrain(steeringAngle, -30, 30);
}