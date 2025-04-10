// Arduino sketch to receive location and orientation data from Python
// and echo it back as confirmation

#include <ArduinoJson.h>

// Variables to store received data
float robot_x = 0;
float robot_y = 0;
float robot_theta = 0;
float distance = 0;
float rel_angle = 0;

// Counter to track number of messages received
unsigned long msg_count = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Wait for serial port to connect
  while (!Serial) {
    ; // wait for serial port to connect
  }
  
  // Send startup message
  Serial.println("Arduino ready for communication");
  Serial.println("Waiting for data from Python...");
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
    if (doc.containsKey("x") && doc.containsKey("y") && doc.containsKey("theta")) {
      robot_x = doc["x"];
      robot_y = doc["y"];
      robot_theta = doc["theta"];
      
      // Check for additional navigation data
      if (doc.containsKey("distance")) {
        distance = doc["distance"];
      }
      
      if (doc.containsKey("rel_angle")) {
        rel_angle = doc["rel_angle"];
      }
      
      // Increment message counter
      msg_count++;
      
      // Send confirmation back to Python
      Serial.print("MSG #");
      Serial.print(msg_count);
      Serial.print(": X=");
      Serial.print(robot_x, 3);
      Serial.print(", Y=");
      Serial.print(robot_y, 3);
      Serial.print(", Theta=");
      Serial.print(robot_theta, 1);
      
      // Include additional data if available
      if (doc.containsKey("distance") && doc.containsKey("rel_angle")) {
        Serial.print(", Dist=");
        Serial.print(distance, 3);
        Serial.print("m, Angle=");
        Serial.print(rel_angle, 1);
        Serial.println("°");
      } else {
        Serial.println("°");
      }
    }
  }
  
  // Send a heartbeat message every 5 seconds
  static unsigned long last_heartbeat = 0;
  if (millis() - last_heartbeat > 5000) {
    Serial.println("Arduino heartbeat - still listening");
    last_heartbeat = millis();
  }
}