/*
 * D646WH Motor Control with Arduino
 * 
 * This sketch allows control of a D646WH servo motor using an Arduino.
 * The D646WH is a high-torque digital servo motor commonly used in robotics applications.
 */

 void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    Serial.println("Echo: " + input);
  }
}
