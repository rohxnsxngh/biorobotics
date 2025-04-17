import serial
import serial.tools.list_ports
import time

def test_serial_port(port_name, baud_rate=115200, timeout=5):
    """
    Test if a port responds as expected
    """
    print(f"Testing port {port_name} at {baud_rate} baud...")
    
    try:
        # Open the serial port
        ser = serial.Serial(port_name, baud_rate, timeout=1)
        print(f"Port {port_name} opened successfully")
        
        # Wait for potential Arduino reset
        time.sleep(2)
        
        # Read any initial data
        initial_data = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if ser.in_waiting:
                new_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                initial_data += new_data
                print(f"Received: {new_data.strip()}")
            
            # If we've received anything, break
            if initial_data:
                print("Received initial data!")
                break
                
            time.sleep(0.1)
        
        # Send test commands
        test_commands = [
            b"TEST\n",
            b"STATUS:1\n",
            b"HELLO\n"
        ]
        
        for cmd in test_commands:
            print(f"Sending: {cmd.decode().strip()}")
            ser.write(cmd)
            time.sleep(1)
            
            response = ""
            if ser.in_waiting:
                response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                print(f"Response: {response.strip()}")
            else:
                print("No response received")
        
        # Close the port
        ser.close()
        print(f"Port {port_name} closed")
        
    except Exception as e:
        print(f"Error on port {port_name}: {str(e)}")
        return False
    
    return True

def list_ports():
    """List all available serial ports"""
    ports = list(serial.tools.list_ports.comports())
    print(f"Found {len(ports)} ports:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
    return ports

def main():
    print("==== Serial Port Tester ====")
    ports = list_ports()
    
    if not ports:
        print("No serial ports found!")
        return
    
    # Ask user which port to test
    try:
        port_index = int(input(f"Enter port number to test (1-{len(ports)}): ")) - 1
        if port_index < 0 or port_index >= len(ports):
            print("Invalid port number!")
            return
            
        port = ports[port_index]
        test_serial_port(port.device)
        
    except ValueError:
        print("Please enter a valid number")

if __name__ == "__main__":
    main()