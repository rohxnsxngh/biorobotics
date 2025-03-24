/*
 * D646WH Motor Control with Arduino
 * 
 * This sketch allows control of a D646WH servo motor using an Arduino.
 * The D646WH is a high-torque digital servo motor commonly used in robotics applications.
 */

//  arduino c:\_dev\biorobotics\electronics\init.c
 #include <Servo.h>

 // Create a servo object
 Servo d646whServo;
 
 // Define the pin to which the servo signal wire is connected
 const int servoPin = 9;  // Connect to one of the Arduino's PWM pins
 
 // Define variables for motor control
 int angle = 90;          // Initial position (middle)
 const int minAngle = 0;  // Minimum angle
 const int maxAngle = 180; // Maximum angle
 
 void setup() {
   // Attach the servo to the specified pin
   d646whServo.attach(servoPin);
   
   // Initialize serial communication for debugging and control
   Serial.begin(9600);
   Serial.println("D646WH Motor Control Ready");
   Serial.println("Enter angle (0-180) or commands:");
   Serial.println("'l' - move left");
   Serial.println("'r' - move right");
   Serial.println("'c' - center");
   
   // Center the servo at startup
   d646whServo.write(angle);
   delay(1000);  // Give the servo time to reach the position
 }
 
 void loop() {
   // Check if commands are available from Serial
   if (Serial.available() > 0) {
     String input = Serial.readStringUntil('\n');
     
     // Process the input
     if (input == "l") {
       // Move left by 10 degrees
       angle = constrain(angle - 10, minAngle, maxAngle);
       Serial.print("Moving left to angle: ");
       Serial.println(angle);
     } 
     else if (input == "r") {
       // Move right by 10 degrees
       angle = constrain(angle + 10, minAngle, maxAngle);
       Serial.print("Moving right to angle: ");
       Serial.println(angle);
     } 
     else if (input == "c") {
       // Center the servo
       angle = 90;
       Serial.println("Centering servo to 90 degrees");
     } 
     else {
       // Try to parse as a direct angle
       int newAngle = input.toInt();
       if (newAngle >= minAngle && newAngle <= maxAngle) {
         angle = newAngle;
         Serial.print("Moving to angle: ");
         Serial.println(angle);
       } else {
         Serial.println("Invalid input. Enter angle (0-180) or 'l', 'r', 'c'");
       }
     }
     
     // Move the servo to the new position
     d646whServo.write(angle);
     delay(100);  // Small delay to allow the servo to start moving
   }
 }