import requests
import json
import time
import argparse
from math import sin, cos

def send_data(ip_address, x, y, distance=0.5):
    """Send data to Arduino server"""
    url = f"http://{ip_address}:80"
    data = {
        "x": x,
        "y": y,
        "distance": distance
    }
    
    try:
        response = requests.post(url, json=data, timeout=2)
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"Response: {response_data}")
                return True
            except json.JSONDecodeError:
                print(f"Received response, but couldn't parse JSON: {response.text}")
                return True
        else:
            print(f"Error: Status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Send control data to Arduino robot')
    parser.add_argument('ip', help='IP address of the Arduino')
    parser.add_argument('--mode', choices=['manual', 'circle', 'sine'], default='manual',
                        help='Control mode: manual (single value), circle (continuous circle pattern), sine (oscillating pattern)')
    parser.add_argument('--x', type=float, default=0.0, help='X position (-0.5 to 0.5)')
    parser.add_argument('--y', type=float, default=0.0, help='Y position (-0.5 to 0.5)')
    parser.add_argument('--distance', type=float, default=0.5, help='Distance value (0.1 to 1.0)')
    parser.add_argument('--duration', type=int, default=30, help='Duration in seconds for automatic modes')
    
    args = parser.parse_args()
    
    if args.mode == 'manual':
        print(f"Sending single data point: x={args.x}, y={args.y}, distance={args.distance}")
        send_data(args.ip, args.x, args.y, args.distance)
    
    elif args.mode == 'circle':
        print(f"Starting circle pattern for {args.duration} seconds...")
        start_time = time.time()
        
        while time.time() - start_time < args.duration:
            # Calculate position on a circle
            t = (time.time() - start_time) / 5  # Complete a circle every 5 seconds
            x = 0.4 * cos(t * 6.28)  # Radius of 0.4 in x direction
            y = 0.4 * sin(t * 6.28)  # Radius of 0.4 in y direction
            
            # Gradually decrease distance over time to increase amplitude
            elapsed = time.time() - start_time
            distance = max(0.1, args.distance - (elapsed / args.duration) * 0.3)
            
            success = send_data(args.ip, x, y, distance)
            if not success:
                print("Connection lost. Retrying...")
                time.sleep(1)
            else:
                time.sleep(0.1)  # Send updates 10 times per second
    
    elif args.mode == 'sine':
        print(f"Starting sine pattern for {args.duration} seconds...")
        start_time = time.time()
        
        while time.time() - start_time < args.duration:
            # Calculate oscillating x position
            t = (time.time() - start_time)
            x = 0.4 * sin(t)  # Oscillate x between -0.4 and 0.4
            y = 0.3 * sin(t * 2)  # Oscillate y at double frequency
            
            # Vary distance
            distance = 0.5 + 0.3 * sin(t / 3)  # Oscillate distance between 0.2 and 0.8
            
            success = send_data(args.ip, x, y, distance)
            if not success:
                print("Connection lost. Retrying...")
                time.sleep(1)
            else:
                time.sleep(0.1)
    
    print("Done.")

if __name__ == "__main__":
    main()
    
# python debug_hotspot.py 172.20.10.6 --mode sine --duration 10