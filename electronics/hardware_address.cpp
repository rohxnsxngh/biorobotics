#include <WiFiS3.h>

void setup() {
  Serial.begin(9600);

  // Wait a bit for the Serial Monitor to connect
  delay(1000); 
  Serial.println("Starting...");

  // Check if WiFi module is available
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    while (true);
  }

  byte mac[6];
  WiFi.macAddress(mac);

  Serial.print("MAC address: ");
  for (int i = 0; i < 6; i++) {
    if (mac[i] < 0x10) Serial.print("0");
    Serial.print(mac[i], HEX);
    if (i < 5) Serial.print(":");
  }
  Serial.println();
}

void loop() {
  // Nothing to do
}
