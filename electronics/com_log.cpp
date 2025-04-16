#include <Servo.h>
#include <math.h>
#include <ArduinoJson.h>

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

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
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
  
  // Wait for serial port to connect
  while (!Serial) {
    ; // wait for serial port to connect
  }
  
  // Send startup message
  Serial.println("Arduino ready for position and heading tracking");
  Serial.println("Motors disabled until data received from Python");
}

void loop() {
  // Check if data is available to read
  if (Serial.available() > 0) {
    // Allocate the JSON document
    StaticJsonDocument<200> doc;
    
    // Read the JSON document from the Serial
    DeserializationError error = deserializeJson(doc, Serial);
    
    // Test if parsing succeeded
    if (error) {
      Serial.print("deserializeJson() failed: ");
      Serial.println(error.c_str());
      // Clear serial buffer
      while (Serial.available() > 0) {
        Serial.read();
      }
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
      
      // Send confirmation back to Python
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
  
  // Check for data timeout
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
    if (dataReceived) {
      Serial.println("Arduino heartbeat - Motors active");
    } else {
      Serial.println("Arduino heartbeat - Motors disabled, waiting for data");
    }
    last_heartbeat = millis();
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