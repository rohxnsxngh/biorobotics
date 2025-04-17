#include <Servo.h>
#include <math.h>
#include <ArduinoJson.h>
#include <WiFiS3.h>

// Create servo objects
Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;

// === USER-TUNABLE PARAMETERS ===
float amplitude = 15.0;        // Degrees (0-90 is safe range for most servos)
float frequency = 0.8;         // Hz (cycles per second)
float phaseShiftDeg = 60.0;    // Degrees phase shift between servos

// === INTERNAL SETTINGS ===
const float centerPos = 90.0;        // Center position (neutral angle)
const unsigned long updateDelay = 20; // ms between updates
const float pi = 3.14159265;

// Variables to store received data
float robot_x = 0;
float robot_y = 0;
float distance = 0;

// Counter to track number of messages received
unsigned long msg_count = 0;

// Timer variables
unsigned long previousMillis = 0;
float timeSeconds = 0.0;

// Flag to track if we've received data and should run motors
bool dataReceived = false;

// Timeout for data (stop motors if no new data for this long)
const unsigned long dataTimeout = 2000; // milliseconds
unsigned long lastDataTime = 0;

// AP WiFi settings
char ssid[] = "ArduinoRobot";  // AP SSID
char pass[] = "robotcontrol";   // AP password - at least 8 chars

// Server on port 80
WiFiServer server(80);
WiFiClient client;

void setup() {
  // Initialize serial communication for debugging
  Serial.begin(9600);
  while (!Serial);
  
  // Attach servos to pins
  servo1.attach(3);
  servo2.attach(5);
  servo3.attach(6);
  servo4.attach(9);
  
  // Initialize servos to center position
  servo1.write(centerPos);
  servo2.write(centerPos);
  servo3.write(centerPos);
  servo4.write(centerPos);
  
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

  // Create open network
  int status = WiFi.beginAP(ssid, pass);
  
  if (status != WL_AP_LISTENING) {
    Serial.println("Creating access point failed");
    while (true); // Don't continue
  }
  
  delay(5000); // Wait for AP to start
  
  // Start the server
  server.begin();
  
  Serial.println("Access point created!");
  Serial.println("To control the robot:");
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
  }
  
  // Only run the servo control logic if we've received data
  if (dataReceived) {
    updateServos();
  }
  
  // Send a heartbeat message every 5 seconds
  static unsigned long last_heartbeat = 0;
  if (millis() - last_heartbeat > 5000) {
    Serial.print("Arduino heartbeat - Motors ");
    Serial.println(dataReceived ? "active" : "disabled, waiting for data");
    last_heartbeat = millis();

    // Print network information
    Serial.print("AP IP Address: ");
    Serial.println(WiFi.localIP());
    
    // Print connection status
    Serial.println("AP is running");
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
            
            if (doc.containsKey("distance")) {
              distance = doc["distance"];
            }
            
            // Increment message counter
            msg_count++;
            
            // Debug output
            Serial.print("MSG #");
            Serial.print(msg_count);
            Serial.print(": Position(");
            Serial.print(robot_x, 3);
            Serial.print(", ");
            Serial.print(robot_y, 3);
            Serial.print(")");
            
            if (doc.containsKey("distance")) {
              Serial.print(", Dist=");
              Serial.print(distance, 3);
              Serial.println("m");
            } else {
              Serial.println();
            }
            
            // Set flag that we've received data
            if (!dataReceived) {
              Serial.println("First data received - Motors activated");
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
            respDoc["distance"] = distance;
            
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
        
        // Send a complete web page with JavaScript controller
        client.println("<!DOCTYPE HTML>");
        client.println("<html>");
        client.println("<head>");
        client.println("<title>Arduino Robot Control</title>");
        client.println("<meta name='viewport' content='width=device-width, initial-scale=1'>");
        client.println("<style>");
        client.println("body { font-family: Arial; text-align: center; margin: 0px auto; padding: 20px; }");
        client.println(".container { display: flex; flex-direction: column; align-items: center; }");
        client.println("#joystick { width: 300px; height: 300px; background: #eee; border-radius: 50%; position: relative; }");
        client.println("#handle { width: 50px; height: 50px; background: #007bff; border-radius: 50%; position: absolute; cursor: pointer; transform: translate(-50%, -50%); }");
        client.println(".slider-container { width: 300px; margin: 20px 0; }");
        client.println(".slider { width: 100%; }");
        client.println("#status { margin-top: 20px; padding: 10px; border: 1px solid #ddd; width: 300px; font-family: monospace; }");
        client.println("</style>");
        client.println("</head>");
        client.println("<body>");
        client.println("<h1>Arduino Robot Control</h1>");
        client.println("<div class='container'>");
        client.println("  <div id='joystick'><div id='handle'></div></div>");
        client.println("  <div class='slider-container'>");
        client.println("    <label for='distance'>Distance: <span id='distanceValue'>0.5</span></label>");
        client.println("    <input type='range' id='distance' class='slider' min='0.1' max='1.0' step='0.05' value='0.5'>");
        client.println("  </div>");
        client.println("  <div id='status'>Ready to control robot</div>");
        client.println("</div>");
        
        client.println("<script>");
        client.println("const joystick = document.getElementById('joystick');");
        client.println("const handle = document.getElementById('handle');");
        client.println("const distanceSlider = document.getElementById('distance');");
        client.println("const distanceValue = document.getElementById('distanceValue');");
        client.println("const status = document.getElementById('status');");
        
        client.println("// Center the handle initially");
        client.println("handle.style.left = '50%';");
        client.println("handle.style.top = '50%';");
        
        client.println("let isDragging = false;");
        client.println("let x = 0, y = 0;");
        client.println("let intervalId = null;");
        
        client.println("// Touch and mouse events for the joystick");
        client.println("joystick.addEventListener('mousedown', startDrag);");
        client.println("joystick.addEventListener('touchstart', handleTouch);");
        client.println("document.addEventListener('mousemove', moveDrag);");
        client.println("document.addEventListener('touchmove', handleTouch);");
        client.println("document.addEventListener('mouseup', endDrag);");
        client.println("document.addEventListener('touchend', endDrag);");
        client.println("distanceSlider.addEventListener('input', updateDistance);");
        
        client.println("function startDrag(e) {");
        client.println("  isDragging = true;");
        client.println("  updatePosition(e);");
        client.println("  // Start sending data regularly");
        client.println("  if (intervalId === null) {");
        client.println("    intervalId = setInterval(sendData, 200);");
        client.println("  }");
        client.println("}");
        
        client.println("function handleTouch(e) {");
        client.println("  e.preventDefault();");
        client.println("  if (e.type === 'touchstart') {");
        client.println("    isDragging = true;");
        client.println("    if (intervalId === null) {");
        client.println("      intervalId = setInterval(sendData, 200);");
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
        client.println("}");
        
        client.println("function updateDistance() {");
        client.println("  distanceValue.textContent = distanceSlider.value;");
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
        client.println("}");
        
        client.println("function sendData() {");
        client.println("  const data = {");
        client.println("    x: parseFloat(x.toFixed(3)),");
        client.println("    y: parseFloat(y.toFixed(3)),");
        client.println("    distance: parseFloat(distanceSlider.value)");
        client.println("  };");
        
        client.println("  fetch('/api/control', {");
        client.println("    method: 'POST',");
        client.println("    headers: { 'Content-Type': 'application/json' },");
        client.println("    body: JSON.stringify(data)");
        client.println("  })");
        client.println("  .then(response => response.json())");
        client.println("  .then(data => {");
        client.println("    status.textContent = `Sent: x=${data.x.toFixed(2)}, y=${data.y.toFixed(2)}, dist=${data.distance.toFixed(2)}`;");
        client.println("  })");
        client.println("  .catch(error => {");
        client.println("    status.textContent = `Error: ${error.message}`;");
        client.println("  });");
        client.println("}");
        
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
  // Adjust amplitude based on distance
  // Closer objects (smaller distance) = larger amplitude
  if (distance > 0) {
    // Map distance to amplitude: closer = more movement
    // Assuming maximum expected distance is 1.0m
    amplitude = map(distance * 100, 0, 100, 40, 5);
    amplitude = constrain(amplitude, 5, 40);
  }
  
  // Adjust frequency based on x-position
  // Map x position to frequency range
  frequency = map(robot_x * 100, -50, 50, 0.5 * 100, 2.0 * 100) / 100.0;
  frequency = constrain(frequency, 0.5, 2.0);
  
  // Adjust phase shift based on y-position
  // Map y position to phase shift range
  phaseShiftDeg = map(robot_y * 100, -50, 50, 30, 90);
  phaseShiftDeg = constrain(phaseShiftDeg, 30, 90);
}

void updateServos() {
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= updateDelay) {
    previousMillis = currentMillis;
   
    // Time in seconds
    timeSeconds += updateDelay / 1000.0;

    // Convert phase shift to radians
    float phaseShiftRad = radians(phaseShiftDeg);

    // Angular frequency
    float omega = 2 * pi * frequency;

    // Calculate target angles
    float angle1 = centerPos + amplitude * sin(omega * timeSeconds);
    float angle2 = centerPos + amplitude * sin(omega * timeSeconds + phaseShiftRad);
    float angle3 = centerPos + amplitude * sin(omega * timeSeconds + 2 * phaseShiftRad);
    float angle4 = centerPos + amplitude * sin(omega * timeSeconds + 3 * phaseShiftRad);

    // Write angles to servos
    servo1.write((int)angle1);
    servo2.write((int)angle2);
    servo3.write((int)angle3);
    servo4.write((int)angle4);
  }
}