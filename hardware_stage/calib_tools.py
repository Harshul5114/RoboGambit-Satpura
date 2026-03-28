import time
import json
import math
import serial
import numpy as np

# Import YOUR existing logic
import main_2 
import perception

# --- PHYSICAL OVERRIDES (Adjusted for Serial) ---
main_2.TESTING = False 
# Use the GameMaster's Serial Setup
ser_arm = serial.Serial("COM4", baudrate=115200, timeout=1) # The Arm
ser_mag = serial.Serial("COM3", baudrate=115200, timeout=1) # The Magnet

def get_serial_feedback():
    """YOUR updated feedback logic for Serial."""
    ser_arm.reset_input_buffer()
    ser_arm.write(b'{"T":105}\n')
    line = ser_arm.readline().decode('utf-8').strip()
    try:
        data = json.loads(line)
        return data.get('x'), data.get('y'), data.get('z')
    except:
        return None, None, None

# --- THE TEST MENU ---

def run_magnet_test():
    print("Testing Magnet on COM3...")
    ser_mag.write(b'1')
    time.sleep(2)
    ser_mag.write(b'0')
    print("Magnet Cycle Complete.")

def run_calibration_test():
    print("\n--- SIDE-PLACEMENT CALIBRATION ---")
    print("Point of View: Look at the CAMERA screen.")
    # We map Row/Col (Camera) to Robot X/Y (Serial)
    points = [
        ("TOP-LEFT (R0,C0)", "TL"),
        ("TOP-RIGHT (R0,C5)", "TR"),
        ("BOTTOM-LEFT (R5,C0)", "BL"),
        ("BOTTOM-RIGHT (R5,C5)", "BR")
    ]
    
    results = {}
    for label, key in points:
        input(f"Move arm to {label} center, touch the board, then press Enter...")
        x, y, z = get_serial_feedback()
        if x is not None:
            results[key] = (x, y, z)
            print(f"Stored {key}: X={x}, Y={y}, Z={z}")
        else:
            print("Error: No serial response from Arm!")
    
    print("\n--- COPY THESE TO main_2.py ---")
    for k, v in results.items():
        print(f"CORNER_{k} = {v[:2]}  # Z={v[2]}")

def run_perception_test():
    print("Testing Camera Connection...")
    # This calls your exact stable board logic
    sock = perception.init_perception()
    board, poses = perception.get_stable_board(sock, stability_required=5)
    if board is not None:
        print("Camera Success! Board detected:")
        print(board)
    sock.close()

def run_movement_test():
    print("Testing your linear_move_to logic...")
    # This uses YOUR function from main_2.py
    # Moving to a safe center point
    target_x, target_y = 300, 0
    print(f"Moving to {target_x}, {target_y} at height 120")
    main_2.linear_move_to(target_x, target_y, 120, math.pi, steps=30)

if __name__ == "__main__":
    while True:
        print("\n[1] Test Magnet (COM3)")
        print("[2] Calibrate 4 Corners (Capture Robot X,Y,Z)")
        print("[3] Test Perception (Socket)")
        print("[4] Test Your linear_move_to (COM4)")
        print("[5] Exit")
        
        choice = input("Select Test: ")
        if choice == '1': run_magnet_test()
        elif choice == '2': run_calibration_test()
        elif choice == '3': run_perception_test()
        elif choice == '4': run_movement_test()
        elif choice == '5': break