This code creates a standalone WiFi access point with the Arduino. Here's how to use it:

Upload this code to your Arduino Uno R4 WiFi
Once uploaded, the Arduino will create a WiFi network named "ArduinoRobot"
Connect to this network from your laptop using the password "robotcontrol"
Open your web browser and navigate to http://192.168.4.1
You should see a virtual joystick interface that you can use to control your robot's servos

The interface includes:

A circular joystick to control X/Y coordinates
A slider to adjust the "distance" parameter
A status display showing the current commands