import game
import numpy as np
import requests
import argparse
import serial
import time
import json
import math

# from hardware_stage.test import cell_to_coords
# from perception import board
from typing import Tuple

DEBUG = True
TESTING = True  # Set to False when running on the actual robot

# ser = serial.Serial('COM3', 115200) 
BOARD = np.zeros((6, 6), dtype=int)

#* needs tuning 
# --- Physical Calibration ---
# Adjust these based on where your board sits relative to the arm
BASE_X = 250     
BASE_Y = -150    
SQUARE_SIZE = 60 # mm

# --- Z-Heights ---
Z_SAFE  = 120    # Height to move across the board without hitting pieces
Z_HOVER = 50     # Just above a piece before grabbing
Z_GRIP  = 18     # Height where the gripper is around the piece center

# --- Gripper States (Radians) --- #! measure these (imp)
GRIP_OPEN  = 1.2
GRIP_CLOSE = 3.0

# Define graveyard slots in a line or 2xN grid
# Coordinates are relative to your robot's base
GRAVEYARD_SLOTS = [
    (100, -150), (100, -210), (100, -270), # Row 1
    (160, -150), (160, -210), (160, -270)  # Row 2
]

# Track which slots are occupied: {slot_index: piece_id}
graveyard_state = {i: None for i in range(len(GRAVEYARD_SLOTS))}

def get_board_state() -> np.ndarray:
    """Use the perception module to get the current board state."""
    # add code to update BOARD using perception.board
    global BOARD
    BOARD = board.copy()
    return BOARD

def move() -> str:
    """Determine the best move using the game module."""
    board_state = get_board_state()
    return game.get_best_move(board_state) #? is the bot always playing white?

def movetocmd(move:str) -> str:
    """convert the move string to a command string for the robot."""
    pass

def pick():
    """Send the command to pick up a piece."""
    ser.write(b'1')

def place():
    """Send the command to place a piece."""
    ser.write(b'0')

def send_cmd(command: str):
    """Send the move string to the robot's actuators."""
    print("TESTING" if TESTING else "SENDING", end=': ')
    print(command)

    if TESTING: return

    #* not needed ig
    # parser = argparse.ArgumentParser(description='Http JSON Communication')
    # args = parser.parse_args()

    ip_addr = "192.168.4.1"

    url = f"http://{ip_addr}/js?json={command}"
    try:
        response = requests.get(url, timeout=5)
        return response.text
    except Exception as e:
        print(f"Connection failed: {e}")
        return None


# == helper functions ================================================== (added by me, not in the original code)

def debug_print(message: str):
    """Utility function for consistent debug output."""
    if DEBUG:
        print(f"[DEBUG] {message}")



def parse_move(move: str) -> Tuple[int, int, int, int, int, int]:
    """Parse the move string into source and destination coordinates."""
    # format: "<piece_id>:<source_cell>-><destination_cell>=<promote_piece_id>"

    left, right = move.split("->")
    piece_id, source_cell = left.split(":")
    if "=" in right:
        destination_cell, promote_piece_id = right.split("=")
    else:
        destination_cell = right
        promote_piece_id = piece_id

    sr, sc = game.cell_to_idx(source_cell)
    dr, dc = game.cell_to_idx(destination_cell)

    return int(piece_id), sr, sc, dr, dc, int(promote_piece_id)

def square_to_coords(row: int, col: int) -> Tuple[int, int]:
    """Convert board coordinates (row, col) to physical coordinates (x, y)."""
    x = BASE_X + col * SQUARE_SIZE
    y = BASE_Y + row * SQUARE_SIZE
    return x, y

def go_to(x, y, z, speed=0.5):
    """Moves arm to a coordinate. T:104 is blocking."""
    debug_print(f"Moving to (x={x}, y={y}, z={z}) at speed {speed}")
    cmd = f'{{"T":104,"x":{x},"y":{y},"z":{z},"t":0,"spd":{speed}}}'
    send_cmd(cmd)
    wait_until_reached(x, y, z)

def set_gripper(state):
    """1.2 for Open, 3.0 for Close."""
    debug_print(f"Setting gripper state to: {'OPEN' if state == GRIP_OPEN else 'CLOSE'}")
    cmd = f'{{"T":106,"cmd":{state},"spd":0,"acc":0}}'
    send_cmd(cmd)
    time.sleep(0.5) # Physical delay for the servo to finish



def get_current_pos():
    """Returns the current (x, y, z) from the arm's sensors."""
    response = send_cmd('{"T":105}')
    if response:
        try:
            # The feedback comes back as T:1051
            data = json.loads(response)
            return data.get('x'), data.get('y'), data.get('z')
        except:
            return None, None, None
    return None, None, None

def wait_until_reached(target_x, target_y, target_z, tolerance=2.0, timeout=10):
    """
    Polls the arm's position until it is within 'tolerance' mm of the target.
    """
    debug_print(f"Waiting for arm to reach {target_x}, {target_y}, {target_z}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        curr_x, curr_y, curr_z = get_current_pos()
        
        if curr_x is None:
            continue
            
        # Calculate Euclidean distance to target
        distance = math.sqrt(
            (target_x - curr_x)**2 + 
            (target_y - curr_y)**2 + 
            (target_z - curr_z)**2
        )
        
        if distance <= tolerance:
            debug_print(f"Target reached! (Distance: {distance:.2f}mm)")
            return True
        
        time.sleep(0.1) # Poll every 100ms
        
    debug_print("Timeout: Arm didn't reach target in time.")
    return False

# ==== movement primitives ================================================== 

def go_to_init():
    """
    Resets the arm to the starting position. 
    Required by Rule 9 to clear the camera's field of view.
    """
    debug_print("Returning to Initial Position...")
    # T:100 is the specific code for CMD_MOVE_INIT
    send_cmd('{"T":100}')
    
    # The documentation says this command 'blocks', meaning the arm 
    # handles the timing, but a small sleep ensures your Python 
    # script doesn't try to read the camera too early.
    # time.sleep(2.0) #* might do this in the main loop instead after calling go_to_init()




def pick_up_from_coords(x, y):
    set_gripper(GRIP_OPEN)
    go_to(x, y, Z_SAFE)  # Move above piece
    go_to(x, y, Z_GRIP)  # Lower to piece
    set_gripper(GRIP_CLOSE)
    go_to(x, y, Z_SAFE)  # Lift piece

def place_down_from_coords(x, y):
    go_to(x, y, Z_SAFE)  # Move above target
    go_to(x, y, Z_GRIP)  # Lower to surface
    set_gripper(GRIP_OPEN)
    go_to(x, y, Z_SAFE)  # Lift away

def pick_up(row, col):
    x, y = square_to_coords(row, col)
    pick_up_from_coords(x, y)

def place_down(row, col):
    x, y = square_to_coords(row, col)
    place_down_from_coords(x, y)  # Use the revised function


def dispose_piece(piece_id): #? might need rework later after asking from gamemakers
    """Finds an empty slot and places the captured piece there."""
    target_slot = None
    for i, occupant in graveyard_state.items():
        if occupant is None:
            target_slot = i
            break
            
    if target_slot is None:
        debug_print("Error: Graveyard is full!") # Concern for organizers if this happens
        return

    slot_x, slot_y = GRAVEYARD_SLOTS[target_slot]
    
    # Sequence: Move to slot -> Lower -> Release -> Lift
    go_to(slot_x, slot_y, Z_SAFE)
    go_to(slot_x, slot_y, Z_GRIP)
    set_gripper(GRIP_OPEN)
    go_to(slot_x, slot_y, Z_SAFE)
    
    # Update local state
    graveyard_state[target_slot] = piece_id

def promote_piece(row, col, new_piece_id): #? might need rework later after asking from gamemakers
    pass


def execute_turn(move_str, current_board):
    """
    Handles a full turn: Clear camera -> Move piece -> Reset arm.
    """
    
    # Parse the engine's move (e.g., "1:A1->B2")
    p_id, sr, sc, dr, dc, new_p_id = parse_move(move_str)
    
    # Handle Capture Sequence
    if current_board[dr][dc] != 0:
        debug_print(f"Capture detected! Removing piece ID {current_board[dr][dc]}")
        pick_up(dr, dc)
        dispose_piece(current_board[dr][dc]) # Moves piece to graveyard

    # Handle Promotion Sequence
    if new_p_id != p_id:
        debug_print(f"Promoting piece at {game.idx_to_cell(dr,dc)} to ID {new_p_id}")
        promote_piece(sr, sc, new_p_id) 
        
    # Handle Normal Move Sequence
    debug_print(f"Moving piece {p_id} from {game.idx_to_cell(sr,sc)} to {game.idx_to_cell(dr,dc)}")
    pick_up(sr, sc)
    place_down(dr, dc)
    
    # Final Reset
    go_to_init()
    debug_print("Turn Complete.")

if __name__ == "__main__":
    # write code to run the main loop of the program, calling move() and send_cmd() as needed

    pass

