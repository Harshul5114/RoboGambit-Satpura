import time
import json
import math
import serial
import numpy as np

# Import YOUR existing logic
import main_2 
import perception

# --- PHYSICAL OVERRIDES ---
main_2.TESTING = False 
# Ports as defined by your GameMaster
ser_arm = serial.Serial("COM8", baudrate=115200, timeout=1) 
ser_mag = serial.Serial("COM7", baudrate=115200, timeout=1) 

def get_serial_feedback():
    """Requests current position (X, Y, Z) via Serial."""
    ser_arm.reset_input_buffer()
    ser_arm.write(b'{"T":105}\n')
    line = ser_arm.readline().decode('utf-8').strip()
    try:
        data = json.loads(line)
        return data.get('x'), data.get('y'), data.get('z')
    except:
        return None, None, None

def jog_arm():
    """Moves the arm using WASD (XY) and RF (Z) keys."""
    step = 5.0 # mm per keypress
    print("\n--- JOG MODE ACTIVE ---")
    print("W/S: X +/- | A/D: Y +/- | R/F: Z +/- | ENTER: Save & Next")
    
    while True:
        curr_x, curr_y, curr_z = get_serial_feedback()
        if curr_x is None:
            print("Error: Lost connection to arm.")
            break
            
        print(f"\rCurrent Pos: X={curr_x:.1f}, Y={curr_y:.1f}, Z={curr_z:.1f}", end="")
        
        key = input(" Move > ").lower()
        if key == '': break # Enter pressed
        
        nx, ny, nz = curr_x, curr_y, curr_z
        if key == 'w': nx += step
        elif key == 's': nx -= step
        elif key == 'a': ny += step
        elif key == 'd': ny -= step
        elif key == 'r': nz += step
        elif key == 'f': nz -= step
        
        # Move command using your arm's protocol (T:104 is blocking coordinate move)
        move_cmd = json.dumps({"T": 104, "x": nx, "y": ny, "z": nz, "t": 3.14}) + "\n"
        ser_arm.write(move_cmd.encode())
        time.sleep(0.1) # Small delay for serial processing

def run_calibration_test():
    print("\n--- SIDE-PLACEMENT CALIBRATION WITH JOGGING ---")
    print("Point of View: Look at the CAMERA screen.")
    
    points = [
        ("TOP-LEFT (R0,C0)", "TL"),
        ("TOP-RIGHT (R0,C5)", "TR"),
        ("BOTTOM-LEFT (R5,C0)", "BL"),
        ("BOTTOM-RIGHT (R5,C5)", "BR")
    ]
    
    results = {}
    for label, key in points:
        print(f"\n[TARGET: {label}]")
        jog_arm() # This opens the WASD controls
        
        x, y, z = get_serial_feedback()
        if x is not None:
            results[key] = (x, y, z)
            print(f"\nCaptured {key}: X={x}, Y={y}, Z={z}")
        else:
            print("\nError: Could not read feedback!")
    
    print("\n--- FINAL CALIBRATION DATA ---")
    print("Paste these into your main_2.py constants:")
    for k, v in results.items():
        print(f"CORNER_{k} = ({v[0]:.2f}, {v[1]:.2f})  # Z={v[2]:.2f}")

# --- KEEPING YOUR OTHER TESTS ---

def run_magnet_test():
    print("Testing Magnet on COM7...")
    ser_mag.write(b'1'); time.sleep(2); ser_mag.write(b'0')
    print("Magnet Cycle Complete.")

def run_perception_test():
    sock = perception.init_perception()
    board, _ = perception.get_stable_board(sock, stability_required=5)
    if board is not None: print(board)
    sock.close()

if __name__ == "__main__":
    while True:
        print("\n[1] Test Magnet (COM7)")
        print("[2] Calibrate with WASDRF Jogging")
        print("[3] Test Perception")
        print("[4] Exit")
        
        choice = input("Select Test: ")
        if choice == '1': run_magnet_test()
        elif choice == '2': run_calibration_test()
        elif choice == '3': run_perception_test()
        elif choice == '4': break