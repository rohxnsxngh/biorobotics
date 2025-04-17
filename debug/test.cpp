#include <Servo.h>
#include <math.h>

// Create servo objects for snake segments
Servo servo1;  // Head/steering segment
Servo servo2;  // Body segment 1
Servo servo3;  // Body segment 2
Servo servo4;  // Body segment 3
Servo servo5;  // Tail segment (pin 11)

// === MOTION PARAMETERS ===
float amplitude = 15.0;        // Amplitude of oscillation (0-30 degrees)
float frequency = 0.8;         // Frequency in Hz (cycles per second)
float phaseShiftDeg = 60.0;    // Phase shift between segments (degrees)
float steeringAngle = 0.0;     // Steering angle offset for head segment

// === CONSTANTS ===
const float centerPos = 90.0;     // Center position (degrees)
const unsigned long updateDelay = 5;  // Servo update delay (milliseconds)
const float pi = 3.14159265;

// === TIMING VARIABLES ===
unsigned long previousMillis = 0;
float timeSeconds = 0.0;

// === SERIAL COMMUNICATION ===
String inputString = "";         // String to hold incoming data
boolean stringComplete = false;  // Whether the string is complete
const long serialBaudRate = 115200;

void setup() {
  // Initialize serial communication
  Serial.begin(serialBaudRate);
  inputString.reserve(200);  // Reserve space for serial commands
  
  // Attach servos to pins
  servo1.attach(3);  // Head/steering
  servo2.attach(5);  // Body segment 1
  servo3.attach(6);  // Body segment 2
  servo4.attach(9);  // Body segment 3
  servo5.attach(11); // Tail segment
  
  // Initialize servos to center position
  servo1.write(centerPos);
  servo2.write(centerPos);
  servo3.write(centerPos);
  servo4.write(centerPos);
  servo5.write(centerPos);
  
  // Send ready status - Add a delay to make sure it's sent after serial is ready
  delay(1000);  // Wait 1 second for serial to stabilize
  Serial.println("SNAKE_READY");
  Serial.println("STATUS:READY");  // Send a simple STATUS response that the Python script can recognize
}

void loop() {
  // Parse serial commands if available
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
  
  // Update servo positions - ALWAYS running for smooth motion
  updateServos();
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    
    // Add character to input buffer
    if (inChar != '\n') {
      inputString += inChar;
    }
    // End of command
    else {
      stringComplete = true;
    }
  }
}

void processCommand(String command) {
  // Debug echo - always respond to any command
  Serial.print("RECEIVED:");
  Serial.println(command);
  
  // Special case for STATUS command with any value
  if (command.startsWith("STATUS")) {
    sendStatus();
    return;
  }
  
  // For other commands, use the PARAM:VALUE format
  int separatorIndex = command.indexOf(':');
  
  if (separatorIndex != -1) {
    String param = command.substring(0, separatorIndex);
    float value = command.substring(separatorIndex + 1).toFloat();
    
    // Process parameters
    if (param == "STEER") {
      steeringAngle = value;
      Serial.println("STEER:" + String(steeringAngle));
    }
    else if (param == "AMP") {
      amplitude = value;
      Serial.println("AMP:" + String(amplitude));
    }
    else if (param == "FREQ") {
      frequency = value;
      Serial.println("FREQ:" + String(frequency));
    }
    else if (param == "PHASE") {
      phaseShiftDeg = value;
      Serial.println("PHASE:" + String(phaseShiftDeg));
    }
    else if (param == "HELLO") {
      // Simple handshake command
      Serial.println("HELLO:OK");
    }
  }
  else {
    // Command without a colon - respond to basic commands
    if (command == "HELLO") {
      Serial.println("HELLO:OK");
    }
  }
}

void sendStatus() {
  // Send a simple STATUS response first for compatibility
  Serial.println("STATUS:OK");
  
  // Then send the detailed JSON response
  String statusMsg = "STATUS_DETAILS:{";
  statusMsg += "\"steer\":" + String(steeringAngle) + ",";
  statusMsg += "\"amp\":" + String(amplitude) + ",";
  statusMsg += "\"freq\":" + String(frequency) + ",";
  statusMsg += "\"phase\":" + String(phaseShiftDeg);
  statusMsg += "}";
  
  Serial.println(statusMsg);
}

void updateServos() {
  unsigned long currentMillis = millis();
  
  // Only update at the specified interval
  if (currentMillis - previousMillis >= updateDelay) {
    previousMillis = currentMillis;
    
    // Update time counter
    timeSeconds += updateDelay / 1000.0;
    
    // Calculate wave parameters
    float omega = 2 * pi * frequency;
    float phaseShiftRad = radians(phaseShiftDeg);
    
    // Head segment only uses steering offset, not sine wave
    float angle1 = centerPos + steeringAngle;
    
    // Body segments follow pure sine wave pattern
    float angle2 = centerPos + amplitude * sin(omega * timeSeconds);
    float angle3 = centerPos + amplitude * sin(omega * timeSeconds + phaseShiftRad);
    float angle4 = centerPos + amplitude * sin(omega * timeSeconds + 2 * phaseShiftRad);
    float angle5 = centerPos + amplitude * sin(omega * timeSeconds + 3 * phaseShiftRad);
    
    // Safety limits
    angle1 = constrain(angle1, centerPos - 30, centerPos + 30);
    angle2 = constrain(angle2, centerPos - 30, centerPos + 30);
    angle3 = constrain(angle3, centerPos - 30, centerPos + 30);
    angle4 = constrain(angle4, centerPos - 30, centerPos + 30);
    angle5 = constrain(angle5, centerPos - 30, centerPos + 30);
    
    // Write to servos - DIRECT WRITES for maximum responsiveness
    servo1.write(angle1);
    servo2.write(angle2);
    servo3.write(angle3);
    servo4.write(angle4);
    servo5.write(angle5);
  }
}