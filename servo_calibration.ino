#include <Servo.h>

// Joint Servos
Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;
Servo servo5;

// Rudder Servo
Servo servo6;

// === USER SETTINGS ===
const int positions[] = {30, 90, 150};               // Servo angles
const unsigned long intervals[] = {2000, 6000, 2000}; // Time at each angle in ms
const int numPositions = sizeof(positions) / sizeof(positions[0]);

// === INTERNAL STATE ===
int currentPositionIndex = 0;
unsigned long previousMillis = 0;


/////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////
/////////////////////// CALIBRATION ANGLE   /////////////////////////////
                        int angle = 90;
/////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////



void setup() {
  // Attach servos to pins
  servo1.attach(3);
  servo2.attach(5);
  servo3.attach(6);
  servo4.attach(9);
  servo5.attach(10);

  servo6.attach(11);

  // Start serial monitor for debugging
  Serial.begin(9600);
  delay(500); // Let Serial settle

  // Set initial position
  int angle = positions[currentPositionIndex];
  moveAllServos(angle);
  Serial.print("Starting at angle: ");
  Serial.println(angle);
}

void loop() {
  unsigned long currentMillis = millis();
  moveAllServos(angle);

//   if (currentMillis - previousMillis >= intervals[currentPositionIndex]) {
//     previousMillis = currentMillis;
//     // Move to the next position
//     currentPositionIndex = (currentPositionIndex + 1) % numPositions;
//     int angle = positions[currentPositionIndex];
//     moveAllServos(angle);
//     Serial.print("Moved to angle: ");
//     Serial.print(angle);
//     Serial.print(" (Duration: ");
//     Serial.print(intervals[currentPositionIndex]);
//     Serial.println(" ms)");
//   }
}

void moveAllServos(int angle) {
  servo1.write(angle);
  servo2.write(angle);
  servo3.write(angle);
  servo4.write(angle);
  servo5.write(angle);
  servo6.write(angle);
}
