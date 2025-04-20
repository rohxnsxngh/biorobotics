#include <Servo.h>
#include <math.h>

// Create servo objects
Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;
Servo servo5;  // New rudder servo

// === USER-TUNABLE PARAMETERS ===
const float amplitude = 15.0;        // Degrees (0-90 is safe range for most servos)
const float frequency = 0.8;         // Hz (cycles per second)
const float phaseShiftDeg = 60.0;    // Degrees phase shift between servos

// === INTERNAL SETTINGS ===
const float centerPos = 90.0;        // Center position (neutral angle)
const unsigned long updateDelay = 20; // ms between updates
const float pi = 3.14159265;

// Timer variable
unsigned long previousMillis = 0;
float timeSeconds = 0.0;

// Flag to control default wave vs serial input mode
bool useSerialControl = false;
int servo4Target = 90;  // Default position for servo4 when using serial
int rudderPosition = 90; // Default center position for rudder (servo5)

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Attach servos to pins
  servo1.attach(3);
  servo2.attach(5);
  servo3.attach(6);
  servo4.attach(9);  // Part of swimming motion
  servo5.attach(10); // Rudder for steering
  
  // Initialize rudder to center position
  servo5.write(rudderPosition);
}

void loop() {
  // Check for serial commands
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    
    // Parse the command
    if (input.startsWith("S")) {
      // Manual servo4 control (S90 sets to 90 degrees)
      servo4Target = input.substring(1).toInt();
      
      // Constrain to valid range
      servo4Target = constrain(servo4Target, 0, 180);
      
      // Switch to serial control mode
      useSerialControl = true;
      
      // Acknowledge receipt
      Serial.print("Servo4 set to: ");
      Serial.println(servo4Target);
    } 
    else if (input.startsWith("R")) {
      // Rudder control (R90 sets rudder to 90 degrees - center position)
      rudderPosition = input.substring(1).toInt();
      
      // Constrain to valid range
      rudderPosition = constrain(rudderPosition, 0, 180);
      
      // Set the rudder position
      servo5.write(rudderPosition);
      
      // Acknowledge receipt
      Serial.print("Rudder set to: ");
      Serial.println(rudderPosition);
    }
    else if (input.startsWith("W")) {
      // Switch back to wave mode
      useSerialControl = false;
      Serial.println("Wave mode activated");
    }
  }

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
    
    // Servo4 either follows wave pattern or uses serial input
    float angle4;
    if (useSerialControl) {
      angle4 = servo4Target;  // Use the target set by serial
    } else {
      angle4 = centerPos + amplitude * sin(omega * timeSeconds + 3 * phaseShiftRad);
    }

    // Write angles to swimming servos
    servo1.write((int)angle1);
    servo2.write((int)angle2);
    servo3.write((int)angle3);
    servo4.write((int)angle4);
    
    // Note: We don't need to set servo5 here as it's set when a command is received
  }
}