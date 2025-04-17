// Simple Arduino Serial Echo Test
// This sketch will echo back any data received plus send periodic heartbeats

unsigned long lastHeartbeat = 0;
const unsigned long heartbeatInterval = 2000; // 2 seconds

void setup() {
  // Initialize serial with the same baud rate as your Python script
  Serial.begin(115200);
  
  // Wait a moment for serial to establish
  delay(1000);
  
  // Send initialization messages
  Serial.println("ARDUINO_READY");
  Serial.println("STATUS:READY");
  Serial.println("HELLO:WORLD");
}

void loop() {
  // Echo back any received data immediately
  while (Serial.available() > 0) {
    // Read incoming byte
    char inByte = Serial.read();
    
    // Echo it back
    Serial.write(inByte);
    
    // If we received a complete command (newline), also send a confirmation
    if (inByte == '\n') {
      Serial.println("OK");
      Serial.println("STATUS:OK");
    }
  }
  
  // Send heartbeat messages periodically
  unsigned long currentMillis = millis();
  if (currentMillis - lastHeartbeat >= heartbeatInterval) {
    lastHeartbeat = currentMillis;
    Serial.println("HEARTBEAT");
    Serial.println("STATUS:ALIVE");
  }
}