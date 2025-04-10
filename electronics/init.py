import serial
import time

arduino = serial.Serial(port='COM3', baudrate=9600, timeout=1)
time.sleep(2)  # wait for connection to establish

try:
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            print(f"Arduino says: {line}")
except KeyboardInterrupt:
    print("Exiting...")
finally:
    arduino.close()
