import serial
import time

ser = serial.Serial('COM3', 9600)
time.sleep(2) # wait for arduino reset

angle = input("Enter servo angle (0-100): ")
ser.write(f"{angle}\n".encode())

ser.close()

