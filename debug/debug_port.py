import serial
import serial.tools.list_ports
import os
import platform
import subprocess
import sys

def list_ports():
    """List all available serial ports"""
    ports = list(serial.tools.list_ports.comports())
    print(f"Found {len(ports)} ports:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
    return ports

def test_port_access(port_name):
    """Test if we can access the specified port"""
    print(f"\nTesting access to {port_name}...")
    try:
        # Try to open the port with a short timeout
        ser = serial.Serial(port_name, 115200, timeout=1)
        ser.close()
        print(f"SUCCESS: Port {port_name} is accessible")
        return True
    except serial.SerialException as e:
        print(f"ERROR: Could not access port {port_name}")
        print(f"Error details: {str(e)}")
        return False

def find_processes_using_port():
    """Find processes that might be using COM ports"""
    print("\nChecking for processes that might be using serial ports...")
    
    system = platform.system()
    if system == "Windows":
        try:
            # On Windows, we can use netstat to find processes using ports
            print("Running Windows port usage check...")
            output = subprocess.check_output("netstat -ano", shell=True).decode('utf-8')
            print("\nNetstat output (look for any process using a COM port):")
            print(output)
            
            print("\nRunning Windows task list for more information...")
            tasks = subprocess.check_output("tasklist", shell=True).decode('utf-8')
            print(tasks)
        except Exception as e:
            print(f"Error running system commands: {str(e)}")
    
    elif system == "Linux":
        try:
            # On Linux, we can check for processes using serial devices
            print("Running Linux port usage check...")
            output = subprocess.check_output("lsof | grep tty", shell=True).decode('utf-8')
            print("\nProcesses using serial ports:")
            print(output)
        except Exception as e:
            print(f"Error running system commands: {str(e)}")
    
    elif system == "Darwin":  # macOS
        try:
            # On macOS, similar approach to Linux
            print("Running macOS port usage check...")
            output = subprocess.check_output("lsof | grep tty", shell=True).decode('utf-8')
            print("\nProcesses using serial ports:")
            print(output)
        except Exception as e:
            print(f"Error running system commands: {str(e)}")
    
    else:
        print(f"Unsupported operating system: {system}")

def main():
    """Main function"""
    print("=== Serial Port Diagnostic Tool ===")
    
    # List all available ports
    ports = list_ports()
    
    if not ports:
        print("No serial ports detected. Make sure your device is connected.")
        return
    
    # Ask which port to test
    port_to_test = None
    while port_to_test is None:
        try:
            if len(ports) == 1:
                choice = input(f"Do you want to test {ports[0].device}? (y/n): ")
                if choice.lower() == 'y':
                    port_to_test = ports[0].device
                else:
                    custom_port = input("Enter the port name to test (e.g., COM3): ")
                    port_to_test = custom_port
            else:
                choice = input("Enter the number of the port to test (or port name directly): ")
                if choice.isdigit() and 1 <= int(choice) <= len(ports):
                    port_to_test = ports[int(choice)-1].device
                else:
                    port_to_test = choice
                    
        except Exception as e:
            print(f"Invalid input: {str(e)}")
    
    # Test access to the port
    access_ok = test_port_access(port_to_test)
    
    # If we couldn't access the port, try to find which process might be using it
    if not access_ok:
        find_processes_using_port()
        
        print("\nTroubleshooting suggestions:")
        print("1. Make sure no other application (like Arduino IDE) has the port open")
        print("2. Check if another instance of your Python script is running")
        print("3. On Windows, check Device Manager to see if the port has any issues")
        print("4. Try unplugging and reconnecting the device")
        print("5. Restart your computer")
        print("6. If using Windows, try running this script as Administrator")

if __name__ == "__main__":
    main()