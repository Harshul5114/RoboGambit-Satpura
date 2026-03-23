import time
from main import *

def test_gripper_limits():
    """
    Use this to find your GRIP_OPEN and GRIP_CLOSE constants.
    It will cycle between two values so you can see if they are right.
    """
    print("--- Gripper Test ---")
    while True:
        val = input("Enter Radian value to test (or 'q' to quit): ")
        if val.lower() == 'q': break
        try:
            set_gripper(float(val))
        except:
            print("Invalid input.")

def test_origin_and_grid():
    """
    Moves the arm to the four corners of your 6x6 board.
    Use this to set BASE_X, BASE_Y, and SQUARE_SIZE.
    """
    print("--- Grid Calibration Test ---")
    # Corners in (row, col) format
    corners = [(0, 0), (0, 5), (5, 5), (5, 0)]
    
    go_to_init()
    
    for r, c in corners:
        x, y = square_to_coords(r, c)
        print(f"Testing Corner: Row {r}, Col {c} -> X: {x}, Y: {y}")
        
        # Hover at Z_SAFE first for safety
        go_to(x, y, Z_SAFE)
        # Lower slightly to see if it's centered
        go_to(x, y, Z_HOVER) 
        
        input("Press Enter to move to next corner...")
        go_to(x, y, Z_SAFE)

def test_pick_place_cycle():
    """
    Tests the full movement logic: Pick from A1, Place at B2.
    Run this without a piece first, then with a piece.
    """
    print("--- Pick and Place Sequence Test ---")
    # A1 is (0,0), B2 is (1,1)
    sr, sc = 0, 0
    dr, dc = 1, 1
    
    input("Place a piece on A1 and press Enter...")
    
    # 1. Pick up from A1
    print("Action: Picking up from A1")
    pick_up(sr, sc)
    
    # 2. Place down at B2
    print("Action: Placing down at B2")
    place_down(dr, dc)
    
    # 3. Reset
    go_to_init()
    print("Test Complete.")