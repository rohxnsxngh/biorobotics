#include <Servo.h>
#include <math.h>
#include <ArduinoJson.h>
#include <WiFiS3.h>

// Create servo objects
Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;

// === USER-TUNABLE PARAMETERS ===
float amplitude = 15.0;     // Degrees (0-90 is safe range for most servos)
float frequency = 0.8;      // Hz (cycles per second)
float phaseShiftDeg = 60.0; // Degrees phase shift between servos

// === INTERNAL SETTINGS ===
const float centerPos = 90.0;         // Center position (neutral angle)
const unsigned long updateDelay = 20; // ms between updates
const float pi = 3.14159265;

// Variables to store received data
float robot_x = 0;
float robot_y = 0;
float distance = 0;

// Counter to track number of messages received
unsigned long msg_count = 0;

// Timer variables
unsigned long previousMillis = 0;
float timeSeconds = 0.0;

// Flag to track if we've received data and should run motors
bool dataReceived = false;

// Timeout for data (stop motors if no new data for this long)
const unsigned long dataTimeout = 2000; // milliseconds
unsigned long lastDataTime = 0;

// CMU WiFi settings
char ssid[] = "CMU-DEVICE"; // CMU network SSID
char pass[] = "";           // Your network password (leave empty if using MAC registration)

// Network configuration - using the static IP that was registered
IPAddress ip(172, 21, 25, 132);     // The IP address assigned to your device
IPAddress gateway(172, 21, 25, 1);  // Default gateway (may need adjustment)
IPAddress subnet(255, 255, 255, 0); // Subnet mask (may need adjustment)
IPAddress dns(8, 8, 8, 8);          // DNS server (may need adjustment)

int status = WL_IDLE_STATUS;
WiFiServer server(80); // Create a server at port 80
WiFiClient client;     // Client object for handling connections

// MAC address that you registered
byte mac[] = {0x64, 0xE8, 0x33, 0x6A, 0x02, 0x60}; // Based on your registration

void setup()
{
    Serial.begin(9600);
    while (!Serial)
        ;

    Serial.println("Starting WiFi setup...");

    byte mac[] = {0x64, 0xE8, 0x33, 0x6A, 0x02, 0x60};
    IPAddress ip(172, 21, 25, 132);
    IPAddress gateway(172, 21, 25, 1);
    IPAddress subnet(255, 255, 255, 0);
    IPAddress dns(8, 8, 8, 8);

    delay(1000);
    WiFi.macAddress(mac); // Optional, depending on board
    WiFi.config(ip, dns, gateway, subnet);

    char ssid[] = "CMU-DEVICE";
    char pass[] = ""; // No password for MAC-auth

    Serial.print("Connecting to ");
    Serial.println(ssid);

    int status = WiFi.begin(ssid, pass);
    int attempts = 0;
    while (status != WL_CONNECTED && attempts < 15)
    {
        delay(1000);
        Serial.print(".");
        status = WiFi.status();
        attempts++;
    }

    if (status == WL_CONNECTED)
    {
        Serial.println("\nConnected!");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());
    }
    else
    {
        Serial.println("\nFailed to connect.");
        Serial.print("Status: ");
        Serial.println(status);
    }
}

void printMacAddress()
{
    byte mac[6];
    WiFi.macAddress(mac);
    for (int i = 0; i < 5; i++)
    {
        if (mac[i] < 16)
            Serial.print("0");
        Serial.print(mac[i], HEX);
        Serial.print(":");
    }
    if (mac[5] < 16)
        Serial.print("0");
    Serial.println(mac[5], HEX);
}

void loop()
{
    // Check if we're still connected to WiFi
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("WiFi connection lost - attempting to reconnect");
        status = WiFi.begin(ssid, pass);
        delay(5000); // Wait for reconnection
        return;
    }

    // First, check if there's any client connection
    if (!client || !client.connected())
    {
        // Try to get a client
        client = server.available();
        if (client)
        {
            Serial.println("New client connected");
        }
    }

    // Check if data is available to read
    if (client && client.connected() && client.available())
    {
        // Allocate the JSON document
        StaticJsonDocument<200> doc;

        // Read the JSON document from the WiFi client
        DeserializationError error = deserializeJson(doc, client);

        // Test if parsing succeeded
        if (error)
        {
            Serial.print("deserializeJson() failed: ");
            Serial.println(error.c_str());
            // Clear buffer
            while (client.available())
            {
                client.read();
            }
            return;
        }

        // Extract values
        if (doc.containsKey("x") && doc.containsKey("y"))
        {
            robot_x = doc["x"];
            robot_y = doc["y"];

            // Check for distance value
            if (doc.containsKey("distance"))
            {
                distance = doc["distance"];
            }

            // Increment message counter
            msg_count++;

            // Debug output
            Serial.print("MSG #");
            Serial.print(msg_count);
            Serial.print(": Position(");
            Serial.print(robot_x, 3);
            Serial.print(", ");
            Serial.print(robot_y, 3);
            Serial.print(")");

            // Include distance if available
            if (doc.containsKey("distance"))
            {
                Serial.print(", Dist=");
                Serial.print(distance, 3);
                Serial.println("m");
            }
            else
            {
                Serial.println();
            }

            // Send confirmation back to client
            if (client && client.connected())
            {
                StaticJsonDocument<200> respDoc;
                respDoc["status"] = "ok";
                respDoc["msg_count"] = msg_count;
                respDoc["x"] = robot_x;
                respDoc["y"] = robot_y;
                respDoc["distance"] = distance;

                serializeJson(respDoc, client);
                client.println(); // End with a newline
            }

            // Set flag that we've received data
            if (!dataReceived)
            {
                Serial.println("First data received - Motors activated");
                dataReceived = true;
            }

            // Update data timeout tracker
            lastDataTime = millis();

            // Adjust servo parameters based on position data
            adjustServoParameters();
        }
    }

    // Check for data timeout
    if (dataReceived && (millis() - lastDataTime > dataTimeout))
    {
        Serial.println("Data timeout - Motors disabled");
        dataReceived = false;

        // Return servos to center position
        servo1.write(centerPos);
        servo2.write(centerPos);
        servo3.write(centerPos);
        servo4.write(centerPos);
    }

    // Only run the servo control logic if we've received data
    if (dataReceived)
    {
        updateServos();
    }

    // Send a heartbeat message every 5 seconds (debug only)
    static unsigned long last_heartbeat = 0;
    if (millis() - last_heartbeat > 5000)
    {
        Serial.print("Arduino heartbeat - Motors ");
        Serial.println(dataReceived ? "active" : "disabled, waiting for data");
        last_heartbeat = millis();
    }
}

void adjustServoParameters()
{
    // Adjust amplitude based on distance
    // Closer objects (smaller distance) = larger amplitude
    if (distance > 0)
    {
        // Map distance to amplitude: closer = more movement
        // Assuming maximum expected distance is 1.0m
        amplitude = map(distance * 100, 0, 100, 40, 5);
        amplitude = constrain(amplitude, 5, 40);
    }

    // Adjust frequency based on x-position
    // Map x position to frequency range
    frequency = map(robot_x * 100, -50, 50, 0.5 * 100, 2.0 * 100) / 100.0;
    frequency = constrain(frequency, 0.5, 2.0);

    // Adjust phase shift based on y-position
    // Map y position to phase shift range
    phaseShiftDeg = map(robot_y * 100, -50, 50, 30, 90);
    phaseShiftDeg = constrain(phaseShiftDeg, 30, 90);
}

void updateServos()
{
    unsigned long currentMillis = millis();

    if (currentMillis - previousMillis >= updateDelay)
    {
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
        float angle4 = centerPos + amplitude * sin(omega * timeSeconds + 3 * phaseShiftRad);

        // Write angles to servos
        servo1.write((int)angle1);
        servo2.write((int)angle2);
        servo3.write((int)angle3);
        servo4.write((int)angle4);
    }
}