#include <Servo.h>

Servo myServo;


void setup() {
	Serial.begin(9600);
	myServo.attach(3);
}

void loop() {
	if (Serial.available()) {
		int angle = Serial.parseInt();
		if (angle >= 0 && angle <= 180) {
			myServo.write(angle);
		}
	}
}
