// Arduino sketch to receive position and heading data from Python
// and echo it back for communication testing

#include <ArduinoJson.h>

// Variables to store received data
float robot_x = 0;
float robot_y = 0;
float robot_theta = 0;  // Heading angle in degrees
float distance = 0;

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
  Serial.println("Arduino ready for position and heading tracking");
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
    if (doc.containsKey("x") && doc.containsKey("y")) {
      robot_x = doc["x"];
      robot_y = doc["y"];
      
      // Get heading angle if available
      if (doc.containsKey("theta")) {
        robot_theta = doc["theta"];
      }
      
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
      Serial.print("), Heading=");
      Serial.print(robot_theta, 1);
      Serial.print("°");
      
      // Include distance if available
      if (doc.containsKey("distance")) {
        Serial.print(", Dist=");
        Serial.print(distance, 3);
        Serial.println("m");
      } else {
        Serial.println();
      }
      
      // You could add more processing here to respond to the position and heading
      // For example, calculate navigation commands, print direction indicators, etc.
    }
  }
  
  // Send a heartbeat message every 5 seconds
  static unsigned long last_heartbeat = 0;
  if (millis() - last_heartbeat > 5000) {
    Serial.println("Arduino heartbeat - still listening");
    last_heartbeat = millis();
  }
}