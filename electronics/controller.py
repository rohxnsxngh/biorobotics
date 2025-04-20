import serial
import time

def main():
    # Configure the serial connection
    try:
        # Update the port to match your Arduino's port
        # Common examples: 'COM3' (Windows), '/dev/ttyUSB0' (Linux), '/dev/cu.usbmodem14101' (Mac)
        ser = serial.Serial('COM3', 9600, timeout=1)
        print("Connected to Arduino")
        time.sleep(2)  # Wait for Arduino to reset
    except serial.SerialException:
        print("Error: Could not open serial port. Check connection and port name.")
        return

    try:
        while True:
            print("\nRobot Control Options:")
            print("1. Set swimming servo angle (0-180)")
            print("2. Set rudder position (0-180)")
            print("3. Return to wave pattern")
            print("4. Exit")
            
            choice = input("Enter option (1-4): ")
            
            if choice == '1':
                try:
                    angle = int(input("Enter swimming servo angle (0-180): "))
                    if 0 <= angle <= 180:
                        command = f"S{angle}\n"
                        ser.write(command.encode())
                        # Read acknowledgment
                        response = ser.readline().decode().strip()
                        print(f"Arduino response: {response}")
                    else:
                        print("Error: Angle must be between 0 and 180")
                except ValueError:
                    print("Error: Please enter a valid number")
            
            elif choice == '2':
                try:
                    angle = int(input("Enter rudder angle (0-180, 90 is center): "))
                    if 0 <= angle <= 180:
                        # Convert to rudder command
                        command = f"R{angle}\n"
                        ser.write(command.encode())
                        # Read acknowledgment
                        response = ser.readline().decode().strip()
                        print(f"Arduino response: {response}")
                        
                        # Give steering guidance based on angle
                        if angle < 70:
                            print("Steering: Sharp left turn")
                        elif angle < 85:
                            print("Steering: Gentle left turn")
                        elif angle <= 95:
                            print("Steering: Going straight")
                        elif angle < 110:
                            print("Steering: Gentle right turn")
                        else:
                            print("Steering: Sharp right turn")
                    else:
                        print("Error: Angle must be between 0 and 180")
                except ValueError:
                    print("Error: Please enter a valid number")
            
            elif choice == '3':
                ser.write(b"W\n")
                response = ser.readline().decode().strip()
                print(f"Arduino response: {response}")
            
            elif choice == '4':
                print("Exiting program")
                break
            
            else:
                print("Invalid option. Please try again.")
                
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    finally:
        ser.close()
        print("Serial connection closed")

if __name__ == "__main__":
    main()