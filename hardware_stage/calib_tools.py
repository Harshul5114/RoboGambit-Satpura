import requests
import serial
import time
import math
import json
import numpy as np
import cv2

# --- CONFIG ---
ARM_IP = "192.168.4.1"
SERIAL_PORT = "COM3"  # Adjust for your laptop
ARM_PORT = "COM4"  # Adjust for your laptop
BAUD_RATE = 115200

# Try to connect to Magnet
try:
    magnet_ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Magnet Serial Connected.")
except:
    magnet_ser = None
    print("Magnet Serial NOT connected. Check COM port.")

try:
    arm_serial = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)
    print("Arm Serial Connected.")
except:
    arm_serial = None
    print("Arm Serial NOT connected. Check COM port.")


def send_arm_cmd(command: str):
    """Send command and wait for the robot's feedback."""
    print(f"Sending command: {command}")
    
    # 1. Clear the buffer so we don't read old messages
    arm_serial.reset_input_buffer() 
    
    # 2. Send the command
    arm_serial.write((command + '\n').encode())
    
    # 3. Read the response (Blocking)
    # The arm usually responds with a JSON line
    response = arm_serial.readline().decode('utf-8').strip()
    
    print(f"Robot says: {response}")
    return response

def get_feedback():
    """Gets current x, y, z, s, e from T:105."""
    data = send_arm_cmd({"T": 105})
    if data:
        return data.get('x'), data.get('y'), data.get('z'), data.get('s'), data.get('e')
    return None, None, None, None, None

# --- TASK 1: THE CALIBRATOR ---
def run_calibration():
    """Manual collection of the 4 corner coordinates."""
    results = {}
    corners = [21, 22, 23, 24]
    print("\n--- 4-CORNER CALIBRATION ---")
    print("Manually jog the arm to each ArUco marker center at Z_GRIP height.")
    
    for cid in corners:
        input(f"\nMove arm to ArUco ID {cid}. Press Enter when centered...")
        x, y, z, s, e = get_feedback()
        if x is not None:
            results[cid] = (x, y)
            print(f"Captured ID {cid}: X={x}, Y={y} (z={z})")
        else:
            print("Failed to get feedback! Check connection.")
    
    print("\n--- COPY THESE INTO YOUR main_2.py ---")
    print(f"ROBOT_REALITY = {results}")
    return results

# --- TASK 2: MAGNET TEST ---
def toggle_magnet(state):
    """Sends 1 to turn on, 0 to turn off via Serial."""
    if magnet_ser:
        cmd = "1" if state else "0"
        magnet_ser.write(cmd.encode())
        print(f"Magnet {'ON' if state else 'OFF'}")
    else:
        print("Magnet serial not available.")

# --- TASK 3: SMOOTH MOVE TEST ---
def test_linear_path(target_x, target_y, target_z, steps=20):
    """Tests the 1041 non-dipping straight line movement."""
    curr_x, curr_y, curr_z, s, e = get_feedback()
    if curr_x is None: return

    print(f"Starting linear move to {target_x}, {target_y}...")
    
    for i in range(1, steps + 1):
        # Linear Interpolation
        next_x = curr_x + (target_x - curr_x) * (i / steps)
        next_y = curr_y + (target_y - curr_y) * (i / steps)
        next_z = curr_z + (target_z - curr_z) * (i / steps)
        
        # Calculate t to keep level: Hand angle = PI - (Shoulder + Elbow)
        # Note: This is an approximation based on the RoArm geometry
        _, _, _, s_curr, e_curr = get_feedback()
        t_val = 3.14159 - (s_curr + e_curr)
        
        cmd = {"T": 1041, "x": round(next_x, 2), "y": round(next_y, 2), 
               "z": round(next_z, 2), "t": round(t_val, 2)}
        send_arm_cmd(cmd)
        time.sleep(0.05) # Adjust for smoothness

# --- TASK 4: HOMOGRAPHY VALIDATOR (Run this after collecting data) ---
def check_homography(robot_data):
    """Checks if your captured points make a logical square."""
    # Board world points (from your perception.py)
    world_pts = np.array([[212.5, 212.5], [212.5, -212.5], 
                          [-212.5, -212.5], [-212.5, 212.5]], dtype=np.float32)
    # Robot points from your calibration
    rob_pts = np.array([robot_data[21], robot_data[22], 
                        robot_data[23], robot_data[24]], dtype=np.float32)
    
    H, _ = cv2.findHomography(world_pts, rob_pts)
    print("\nHomography Matrix calculated successfully.")
    return H

if __name__ == "__main__":
    while True:
        print("\n1. Calibrate Corners\n2. Toggle Magnet ON\n3. Toggle Magnet OFF\n4. Test Move to (300, 0, 120)\n5. Exit")
        choice = input("Select task: ")
        if choice == '1': run_calibration()
        elif choice == '2': toggle_magnet(True)
        elif choice == '3': toggle_magnet(False)
        elif choice == '4': test_linear_path(300, 0, 120)
        elif choice == '5': break