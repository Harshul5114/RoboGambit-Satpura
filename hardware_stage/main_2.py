import game
import numpy as np
import requests
import serial
import time
import json
import math
from collections import deque
import cv2

import perception
from typing import Tuple, Optional

# ===========================================================================
#  CONFIG
# ===========================================================================

DEBUG   = True
TESTING = True   # Set False when running on real hardware

# --- Communication ---
ser    = serial.Serial('COM3', 115200)   # Serial: electromagnet only
IP     = "192.168.4.1"                   # HTTP: all arm movement

# --- Board state ---
BOARD = np.zeros((6, 6), dtype=int)
_board_history = deque(maxlen=7)  # tune this window size


# --- Wrist angle ---
# CRITICAL: always keep t = π so the electromagnet stays level with the board.
# Sending t=0 tilts the end-effector and makes pick-up impossible.
EOAT_LEVEL = math.pi  # 3.14159...

# ===========================================================================
#  CALIBRATION
# ===========================================================================
# Record the arm's T:1051 (x, y) sensor readings for each of the 4 board
# corners *at Z_GRIP height* and fill them in below.
#
# Corner layout (looking down from above):
#
#       col 0          col 5
#  row 0  TL --------- TR
#         |             |
#  row 5  BL --------- BR
#
# Leave a corner as None until you have its reading — square_to_coords()
# will fall back to the simple linear formula for any board where corners
# are incomplete.

CORNER_TL: Optional[Tuple[float, float]] = None  # (x, y) at row=0, col=0
CORNER_TR: Optional[Tuple[float, float]] = None  # (x, y) at row=0, col=5
CORNER_BL: Optional[Tuple[float, float]] = None  # (x, y) at row=5, col=0
CORNER_BR: Optional[Tuple[float, float]] = None  # (x, y) at row=5, col=5

# Simple fallback parameters (used when corners are incomplete)
BASE_X     = 250
BASE_Y     = -150


# --- Z-Heights ---
Z_SAFE  = 120   # Cruise height — clears all pieces
Z_HOVER = 50    # Just above a piece (optional pre-grip pause)
Z_GRIP  = 18    # Gripper centred on piece

# --- Graveyard ---
GRAVEYARD = (400, -150)  # (x, y) for captured pieces

# --- Tuning parameters ---
STEP_SIZE  = 5.0    # mm between ideal waypoints
STEP_DELAY = 0.05   # seconds to wait for arm to move before reading feedback
                    # this is the single biggest tuning knob — too short and
                    # feedback lags behind the command; too long and motion is jerky
KP         = 0.8    # proportional gain on position error (0.0 = open loop, 1.0 = full correction)
                    # start at 0.5 and increase until tracking is tight without oscillating
STEP_TOL   = 8.0    # mm — if actual error > this after a step, log a warning
                    # (doesn't stop motion — just flags mechanical slip or lag)




# ===========================================================================
#  COORDINATE MAPPING
# ===========================================================================

def transform_to_robot(board_x, board_y):
    """Converts Board (mm) to Robot (mm) using the H-Matrix."""
    # Format the point for cv2.perspectiveTransform
    point = np.array([[[board_x, board_y]]], dtype=np.float32)
    transformed = cv2.perspectiveTransform(point, perception.H_WORLD_TO_ROBOT)
    
    rx, ry = transformed[0][0]
    return rx, ry

def square_to_coords(row, col):
    """Logic for the center of any square (0-5)"""
    # 0,0 is at top-left. Our Board Space has 0,0 at center.
    # A 6x6 board with 60mm squares:
    bw_x = (2.5 - row) * perception.SQUARE_SIZE
    bw_y = (2.5 - col) * perception.SQUARE_SIZE

    return transform_to_robot(bw_x, bw_y)

def find_nearest_piece(target_id, start_row, start_col, all_poses):
    """Finds the (x, y) of the piece closest to the expected square."""
    # Get where we THINK the piece should be
    expected_x = (2.5 - start_row) * perception.SQUARE_SIZE
    expected_y = (2.5 - start_col) * perception.SQUARE_SIZE
    
    if target_id not in all_poses:
        debug_print(f"Piece {target_id} not seen by camera!")
        return expected_x, expected_y # Fallback to grid
        
    # Find the detected coordinate with the smallest distance to expected center
    best_pose = min(all_poses[target_id], 
                    key=lambda p: math.hypot(p[0]-expected_x, p[1]-expected_y))
    
    return best_pose
# ===========================================================================
#  COMMUNICATION
# ===========================================================================

def send_cmd(command: str) -> Optional[str]:
    """
    Send a JSON command to the arm over HTTP.
    Returns the response body, or None on failure / in TESTING mode.
    """
    if DEBUG:
        print(f"{'[TEST]' if TESTING else '[SEND]'} {command}")
    if TESTING:
        return None

    url = f"http://{IP}/js?json={command}"
    try:
        response = requests.get(url, timeout=5)
        return response.text
    except Exception as e:
        print(f"[ERR] HTTP request failed: {e}")
        return None





def get_feedback_full():
    """
    Request T:1051 and return (x, y, z, s, e).
    s and e are shoulder and elbow angles (rad) used for wrist levelling.
    Returns (None, None, None, 0.0, 0.0) on failure or in TESTING mode.
    """
    response = send_cmd('{"T":105}')
    if response:
        try:
            data = json.loads(response)
            return (
                data.get('x'),
                data.get('y'),
                data.get('z'),
                data.get('s', 0.0),
                data.get('e', 0.0),
            )
        except (json.JSONDecodeError, AttributeError):
            pass
    return None, None, None, 0.0, 0.0


def electromagnet_on():
    """Energise the electromagnet to grip a piece."""
    if TESTING:
        debug_print("Electromagnet ON (TESTING mode)")
        return
    ser.write(b'1')
    debug_print("Electromagnet ON")


def electromagnet_off():
    """De-energise the electromagnet to release a piece."""
    if TESTING:
        debug_print("Electromagnet OFF (TESTING mode)")
        return
    ser.write(b'0')
    debug_print("Electromagnet OFF")


# ===========================================================================
#  LOW-LEVEL MOTION PRIMITIVES
# ===========================================================================


def linear_move_to(tx: float, ty: float, tz: float,
                   step_size: float = STEP_SIZE,
                   step_delay: float = STEP_DELAY,
                   kp: float = KP):
    """
    True closed-loop linear interpolation.

    Every step:
      1. Compute the ideal waypoint along the straight line.
      2. Read T:1051 to get the arm's actual position AND joint angles.
      3. Blend: cmd = ideal + Kp * (ideal - actual)
         This proportionally corrects for any drift accumulated so far,
         pulling the arm back toward the ideal trajectory.
      4. Compute wrist angle from live s/e to keep magnet level.
      5. Send T:1041 with the corrected position and level wrist.
      6. Sleep STEP_DELAY, then repeat.

    The arm's actual start position is read from T:1051 before the loop
    begins, so the path is always relative to where the arm *actually* is,
    not where we think it is.
    """
    # --- Read actual start position ---
    sx, sy, sz, s0, e0 = get_feedback_full()

    if sx is None:
        # TESTING mode — no feedback available, simulate a perfect move
        debug_print("[LIN] TESTING: no feedback, simulating straight move.")
        sx, sy, sz = tx, ty, tz

    dx = tx - sx
    dy = ty - sy
    dz = tz - sz
    dist = math.sqrt(dx*dx + dy*dy + dz*dz)

    if dist < 0.5:
        debug_print("[LIN] Already at target.")
        return True

    n_steps = max(1, math.ceil(dist / step_size))
    debug_print(f"[LIN] ({sx:.1f},{sy:.1f},{sz:.1f}) → ({tx:.1f},{ty:.1f},{tz:.1f}) | {dist:.1f}mm / {n_steps} steps")

    for i in range(1, n_steps + 1):
        alpha = i / n_steps

        # --- Ideal waypoint on the straight line ---
        ix = sx + alpha * dx
        iy = sy + alpha * dy
        iz = sz + alpha * dz

        # --- Read actual position + joint angles ---
        ax, ay, az, s, e = get_feedback_full()

        if ax is None:
            # Feedback lost mid-move — send ideal point and hope for the best
            debug_print(f"[LIN] step {i}/{n_steps}: feedback lost, sending ideal waypoint")
            ax, ay, az, s, e = ix, iy, iz, s0, e0

        # --- Proportional correction ---
        # If the arm is behind/off ideal, this pushes the command ahead to compensate
        cx = ix + kp * (ix - ax)
        cy = iy + kp * (iy - ay)
        cz = iz + kp * (iz - az)

        # --- Wrist levelling from live joint angles ---
        t_level = math.pi - (s + e)

        # --- Log tracking error ---
        err = math.sqrt((ix-ax)**2 + (iy-ay)**2 + (iz-az)**2)
        if err > STEP_TOL:
            debug_print(f"[LIN] step {i}/{n_steps}: WARNING large tracking error {err:.1f}mm")
        else:
            debug_print(f"[LIN] step {i}/{n_steps}: ideal=({ix:.1f},{iy:.1f},{iz:.1f}) actual=({ax:.1f},{ay:.1f},{az:.1f}) err={err:.1f}mm t={t_level:.3f}")

        # --- Send corrected command ---
        cmd = f'{{"T":1041,"x":{cx:.3f},"y":{cy:.3f},"z":{cz:.3f},"t":{t_level:.5f}}}'
        send_cmd(cmd)

        time.sleep(step_delay)

    debug_print("[LIN] Move complete.")
    return True



# ===========================================================================
#  HIGH-LEVEL MOTION PRIMITIVES
# ===========================================================================

def go_to_init():
    """
    Reset arm then fold into a tucked pose to clear the camera's field
    of view for the opponent's turn.

    T:100 moves to the default extended pose (base=0, s=0, e=90, h=180).
    The second command folds the arm back and up using T:122 so the arm
    is compact and out of the camera's line of sight.

    Tune FOLD_S and FOLD_E on the real hardware — these are starting guesses.
    """
    FOLD_S = -60   # degrees: pull shoulder backward (away from board)
    FOLD_E = 30    # degrees: fold elbow upward (forearm points up)
    FOLD_H = 180   # degrees: keep wrist level / neutral
    FOLD_SPD = 50  # deg/s — slow enough to be safe
    FOLD_ACC = 10  # smooth start/stop

    debug_print("Returning to home position...")
    send_cmd('{"T":100}')

    debug_print("Folding arm to clear camera view...")
    fold_cmd = (
        f'{{"T":122,"b":0,"s":{FOLD_S},"e":{FOLD_E},'
        f'"h":{FOLD_H},"spd":{FOLD_SPD},"acc":{FOLD_ACC}}}'
    )
    send_cmd(fold_cmd)




# ===========================================================================
#  PIECE OPERATIONS
# ===========================================================================

def pick_up_from_coords(x: float, y: float):
    """Full pick-up sequence at physical coordinates (x, y)."""
    electromagnet_off()          # ensure magnet is off before approach
    linear_move_to(x, y, Z_SAFE)  # move above piece
    linear_move_to(x, y, Z_GRIP) # optional hover step for better grip
    electromagnet_on()
    time.sleep(0.1)              # brief settle so magnet grips before lifting
    linear_move_to(x, y, Z_SAFE)  # lift straight up with piece


def place_down_from_coords(x: float, y: float):
    """Full place-down sequence at physical coordinates (x, y)."""
    linear_move_to(x, y, Z_SAFE)  # move above placement site
    linear_move_to(x, y, Z_GRIP) # lower to placement height
    electromagnet_off()
    time.sleep(0.1)
    linear_move_to(x, y, Z_SAFE)  # lift away cleanly


def pick_up(row: int, col: int):
    x, y = square_to_coords(row, col)
    pick_up_from_coords(x, y)


def place_down(row: int, col: int):
    x, y = square_to_coords(row, col)
    place_down_from_coords(x, y)


def dispose_piece():
    """Move a held piece to the graveyard and release."""
    gx, gy = GRAVEYARD
    linear_move_to(gx, gy, Z_SAFE)
    linear_move_to(gx, gy, Z_GRIP)
    electromagnet_off()
    linear_move_to(gx, gy, Z_SAFE)



    

# ===========================================================================
#  GAME LOGIC
# ===========================================================================
def get_stable_board(n_samples: int = 7, delay_ms: int = 30) -> np.ndarray: #* idk might work nicely
    """Sample the board multiple times and return majority-vote result."""
    import time
    _board_history.clear()
    
    for _ in range(n_samples):
        _board_history.append(board.copy())  # type: ignore
        time.sleep(delay_ms / 1000.0)  # wait between samples
    
    stacked = np.stack(_board_history, axis=0)  # (n_samples, 6, 6)
    stable = np.apply_along_axis(
        lambda x: np.bincount(x, minlength=11).argmax(),
        axis=0,
        arr=stacked
    )
    return stable.astype(int)


def get_board_state() -> np.ndarray:
    """Use the perception module to get the current board state."""
    global BOARD
    BOARD = get_stable_board(n_samples=7, delay_ms=30)  # ~210ms total
    return BOARD

def decide_move() -> str:
    """Ask the engine for the best move given the current board state."""
    board_state = get_board_state()
    return game.get_best_move(board_state)


def parse_move(move_str: str) -> Tuple[int, int, int, int, int, int]:
    """
    Parse the engine's move string into indices.

    Format: "<piece_id>:<source_cell>-><dest_cell>[=<promote_id>]"
    Example: "1:A1->B2"  or  "1:A6->A1=3"

    Returns: (piece_id, src_row, src_col, dst_row, dst_col, promote_id)
    """
    left, right = move_str.split("->")
    piece_id, source_cell = left.split(":")
    if "=" in right:
        destination_cell, promote_piece_id = right.split("=")
    else:
        destination_cell = right
        promote_piece_id = piece_id

    sr, sc = game.cell_to_idx(source_cell)
    dr, dc = game.cell_to_idx(destination_cell)

    return int(piece_id), sr, sc, dr, dc, int(promote_piece_id)


def execute_turn(move_str: str, current_board: np.ndarray):
    """
    Execute one full turn:
        1. Parse the engine's move.
        2. If capture: remove opponent piece to graveyard first.
        3. If promotion: move pawn to dest, dispose it, human replaces piece.
        4. If normal move: pick up and place down.
        5. Return arm to home/folded position.

    Promotion note: we physically move the pawn to the destination square
    first (so the board reflects the right square), dispose it, then pause
    for a human to place the promoted piece. The engine has already decided
    the promoted piece ID — we just need the square to be correct.
    """
    p_id, sr, sc, dr, dc, new_p_id = parse_move(move_str)

    all_poses = perception.get_current_poses() 
    actual_x, actual_y = find_nearest_piece(p_id, sr, sc, all_poses)

    is_capture   = (current_board[dr][dc] != 0)
    is_promotion = (new_p_id != p_id)

    # --- Step 1: Clear the destination square if capture ---
    if is_capture:
        debug_print(f"[TURN] Capture: removing piece {current_board[dr][dc]} at ({game.idx_to_cell(dr, dc)})")
        pick_up_from_coords(actual_x, actual_y)  # pick up the piece that's actually there
        dispose_piece()

    # --- Step 2: Move or promote ---
    if is_promotion:
        debug_print(f"[TURN] Promotion: moving pawn from {game.idx_to_cell(sr, sc)} → {game.idx_to_cell(dr, dc)}, then disposing")
        pick_up_from_coords(actual_x, actual_y)  # pick up the piece that's actually there
        dispose_piece()

        # input("  Place the promoted piece on the board, then press Enter to continue...")

    else:
        # --- Normal move ---
        debug_print(f"[TURN] Moving piece {p_id} from {game.idx_to_cell(sr, sc)} to {game.idx_to_cell(dr, dc)}")
        pick_up_from_coords(actual_x, actual_y)
        place_down(dr, dc)

    # --- Step 3: Always reset arm at end of turn ---
    go_to_init()
    debug_print("[TURN] Complete.")


# ===========================================================================
#  UTILITIES
# ===========================================================================

def debug_print(message: str):
    if DEBUG:
        print(f"[DEBUG] {message}")


def calibration_helper():
    """
    Interactive helper to record corner calibration coordinates.

    Move the arm to each corner square manually (using the web UI),
    then call this function — it reads T:1051 and prints the values to
    paste into the CORNER_* constants above.
    """
    corners = [
        ("TL", 0, 0),
        ("TR", 0, 5),
        ("BL", 5, 0),
        ("BR", 5, 5),
    ]
    print("\n=== CALIBRATION HELPER ===")
    print("Move arm to each corner square at Z_GRIP height, then press Enter.\n")
    for name, row, col in corners:
        input(f"  Position arm at corner {name} (row={row}, col={col}), then press Enter...")
        x, y, z, _, _ = get_feedback_full()
        if x is not None:
            print(f"  CORNER_{name} = ({x:.2f}, {y:.2f})   [z={z:.2f}]")
        else:
            print(f"  [!] Could not read feedback — is TESTING=False and arm connected?")
    print("\nPaste the values above into the CORNER_* constants at the top of this file.")


# ===========================================================================
#  MAIN LOOP
# ===========================================================================

if __name__ == "__main__":

    # Uncomment once all corners are measured:
    # calibration_helper()

    go_to_init()

    while True:
        # 1. Get board state from perception
        current_board = get_board_state()

        # 2. Ask engine for best move
        move_str = decide_move()
        if move_str is None:
            debug_print("No move returned — game may be over.")
            break

        debug_print(f"Engine move: {move_str}")

        # 3. Execute the physical move
        execute_turn(move_str, current_board)

        # Optional: wait for opponent / camera to settle before next perception read
        # time.sleep(1.0)