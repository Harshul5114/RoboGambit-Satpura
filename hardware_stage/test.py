import time
import math
from main_2 import (
    linear_move_to, 
    get_feedback_full, 
    # set_magnet, 
    go_to_init,
    Z_SAFE,
    Z_GRIP,
    STEP_SIZE
)

def capture_marker(marker_id):
    input(f"\n[STEP] Jog arm to ArUco marker {marker_id}. Press Enter...")
    # Using YOUR feedback function
    data = get_feedback_full()
    if data[0] is not None:
        x, y, z = data[0], data[1], data[2]
        print(f">>> DATA FOR ID {marker_id}: x={x:.2f}, y={y:.2f}, z={z:.2f}")
        return x, y
    print("!!! FAILED TO GET FEEDBACK !!!")
    return None
 
def test_linear_consistency():
    print("\n[TEST] Testing your linear_move_to logic...")
    # Move from a safe start to a safe end point
    # Adjust these to coordinates near the center of your board
    print("Moving to Start (300, 0, 120)...")
    linear_move_to(300, 0, 120)
    
    print("Executing Linear Slide to (350, 50, 120)...")
    linear_move_to(350, 50, 120)
    print("Check: Was the move straight? Did the magnet stay level?")

if __name__ == "__main__":
    print("--- ROARM HARDWARE TEST SLOT ---")
    
    while True:
        print("\n1. Capture 4 Corners (Calibration)")
        print("2. Test Magnet (ON/OFF)")
        print("3. Test YOUR linear_move_to")
        print("4. Go to Init")
        print("5. Exit")
        
        choice = input("Select: ")
        
        if choice == '1':
            results = {}
            for cid in [21, 22, 23, 24]:
                pos = capture_marker(cid)
                if pos: results[cid] = pos
            print("\nCOPY THESE TO main_2.py ROBOT_REALITY:")
            print(results)
            
        elif choice == '2':
            set_magnet(True)
            time.sleep(2)
            set_magnet(False)
            print("Magnet Cycle Complete.")
            
        elif choice == '3':
            test_linear_consistency()
            
        elif choice == '4':
            go_to_init()
            
        elif choice == '5':
            break