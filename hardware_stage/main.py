import game
import numpy as np
import requests
import argparse
import serial
import time
import json
import math

# from perception import board
from typing import Tuple

DEBUG = True
TESTING = True  # * Set to False when running on the actual robot

ser = serial.Serial('COM3', 115200) 
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

GRAVEYARD = (400, -150)  # X and Y coordinates for captured pieces

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

def wait_until_reached(target_x, target_y, target_z,
                       tolerance=2.0,
                       max_step=5.0,
                       timeout=10):
    """
    Closed-loop controller:
    Iteratively nudges arm toward target using feedback.
    """

    debug_print(f"[CL] Target: ({target_x}, {target_y}, {target_z})")

    start_time = time.time()

    while time.time() - start_time < timeout:

        curr_x, curr_y, curr_z = get_current_pos()

        if curr_x is None:
            continue

        # --- compute error ---
        dx = target_x - curr_x
        dy = target_y - curr_y
        dz = target_z - curr_z

        dist = math.sqrt(dx*dx + dy*dy + dz*dz)

        debug_print(f"[CL] Curr: ({curr_x:.1f}, {curr_y:.1f}, {curr_z:.1f}) | Err: {dist:.2f}")

        # --- check if reached ---
        if dist <= tolerance:
            debug_print("[CL] Target reached.")
            return True

        # --- clamp step (avoid overshoot) ---
        step_dx = max(-max_step, min(max_step, dx))
        step_dy = max(-max_step, min(max_step, dy))
        step_dz = max(-max_step, min(max_step, dz))

        # --- next intermediate target ---
        next_x = curr_x + step_dx
        next_y = curr_y + step_dy
        next_z = curr_z + step_dz

        debug_print(f"[CL] Nudging → ({next_x:.1f}, {next_y:.1f}, {next_z:.1f})")

        # --- send correction ---
        cmd = f'{{"T":104,"x":{next_x},"y":{next_y},"z":{next_z},"t":0,"spd":0.2}}'
        send_cmd(cmd)

        # small wait before next feedback
        time.sleep(0.15)

    debug_print("[CL] Timeout: failed to reach target.")
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
    place()
    go_to(x, y, Z_SAFE)  # Move above piece
    go_to(x, y, Z_GRIP)  # Lower to piece
    pick()
    go_to(x, y, Z_SAFE)  # Lift piece

def place_down_from_coords(x, y):
    go_to(x, y, Z_SAFE)  # Move above target
    go_to(x, y, Z_GRIP)  # Lower to surface
    place()
    go_to(x, y, Z_SAFE)  # Lift away

def pick_up(row, col):
    x, y = square_to_coords(row, col)
    pick_up_from_coords(x, y)

def place_down(row, col):
    x, y = square_to_coords(row, col)
    place_down_from_coords(x, y)  # Use the revised function


def dispose_piece(): #? might need rework later after asking from gamemakers
    """Finds an empty slot and places the captured piece there."""
    gx, gy = GRAVEYARD
    go_to(gx, gy, Z_SAFE)  # Move above graveyard
    go_to(gx, gy, Z_GRIP)  # Lower to graveyard
    place()  # Release piece in graveyard
    go_to(gx, gy, Z_SAFE)  # Move away


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

