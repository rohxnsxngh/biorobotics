// Arduino client code
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

// Timing for data polling
const unsigned long dataPollInterval = 200; // poll server every 200ms
unsigned long lastPollTime = 0;

// Timeout for data (stop motors if no new data for this long)
const unsigned long dataTimeout = 2000; // milliseconds
unsigned long lastDataTime = 0;

// Hotspot WiFi settings
char ssid[] = "Rohans iPhone";  // Hotspot SSID
char pass[] = "66VncAnc#";      // Hotspot password

// Server where control app is running
char serverAddress[] = "192.168.X.X";  // REPLACE WITH YOUR COMPUTER'S IP
int serverPort = 5000;

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
  
  // Connect to WiFi
  Serial.println("Attempting to connect to WiFi...");
  
  // Check for the WiFi module
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // Don't continue
    while (true);
  }
  
  // Print firmware version
  Serial.print("WiFi firmware version: ");
  Serial.println(WiFi.firmwareVersion());
  
  // Connect to hotspot
  int status = WiFi.begin(ssid, pass);
  int attempts = 0;
  
  while (status != WL_CONNECTED && attempts < 10) {
    delay(1000);
    Serial.print(".");
    status = WiFi.status();
    attempts++;
  }
  
  if (status == WL_CONNECTED) {
    Serial.println("\nConnected to hotspot!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength (RSSI): ");
    Serial.println(WiFi.RSSI());
    Serial.println("Motors disabled until data received");
  } else {
    Serial.println("\nFailed to connect to WiFi.");
    Serial.print("WiFi status code: ");
    Serial.println(status);
  }
}

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost - attempting to reconnect");
    WiFi.begin(ssid, pass);
    delay(5000);
    return;
  }
  
  // Poll for new data on a regular interval
  unsigned long currentMillis = millis();
  if (currentMillis - lastPollTime >= dataPollInterval) {
    lastPollTime = currentMillis;
    pollForData();
  }
  
  // Check for data timeout - disable motors if no data received for a while
  if (dataReceived && (currentMillis - lastDataTime > dataTimeout)) {
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
  if (currentMillis - last_heartbeat > 5000) {
    Serial.print("Arduino heartbeat - Motors ");
    Serial.println(dataReceived ? "active" : "disabled, waiting for data");
    last_heartbeat = currentMillis;

    // Print network information
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  }
}

void pollForData() {
  Serial.println("Polling for data...");
  
  if (!client.connected()) {
    Serial.print("Connecting to server at ");
    Serial.print(serverAddress);
    Serial.print(":");
    Serial.println(serverPort);
    
    if (client.connect(serverAddress, serverPort)) {
      Serial.println("Connected to server");
    } else {
      Serial.println("Connection to server failed");
      return;
    }
  }
  
  // Make a HTTP request
  client.println("GET / HTTP/1.1");
  client.print("Host: ");
  client.print(serverAddress);
  client.print(":");
  client.println(serverPort);
  client.println("Connection: keep-alive");
  client.println();
  
  // Wait for response
  unsigned long timeout = millis();
  while (client.available() == 0) {
    if (millis() - timeout > 5000) {
      Serial.println(">>> Client Timeout !");
      client.stop();
      return;
    }
  }
  
  // Skip HTTP headers
  char endOfHeaders[] = "\r\n\r\n";
  if (!client.find(endOfHeaders)) {
    Serial.println("Invalid response");
    return;
  }
  
  // Allocate the JSON document
  StaticJsonDocument<200> doc;
  
  // Parse JSON
  DeserializationError error = deserializeJson(doc, client);
  
  // Check for parsing errors
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Extract values
  if (doc.containsKey("x") && doc.containsKey("y")) {
    robot_x = doc["x"];
    robot_y = doc["y"];
    
    // Check for distance value
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
    
    // Include distance if available
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