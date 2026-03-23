"""
RoboGambit 2025-26 — Task 1: Autonomous Game Engine
Organised by Aries and Robotics Club, IIT Delhi

Board: 6x6 NumPy array
  - 0  : Empty cell
  - 1  : White Pawn
  - 2  : White Knight
  - 3  : White Bishop
  - 4  : White Queen
  - 5  : White King
  - 6  : Black Pawn
  - 7  : Black Knight
  - 8  : Black Bishop
  - 9  : Black Queen
  - 10 : Black King

Board coordinates:
  - Bpttom-left  = A1  (index [0][0])
  - Columns   = A-F (left to right)
  - Rows      = 6-1 (top to bottom)(from white's perspective)

Move output format:  "<piece_id>:<source_cell>-><target_cell>"
  e.g.  "1:B3->B4"   (White Pawn moves from B3 to B4)
"""

import numpy as np
from typing import Optional
from bitboard import *
import sys 
from utils import *
from constants import *
from moves import *

sys.setrecursionlimit(10**5)

import cProfile
import pstats



# TT Flags
EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2

# The Transposition Table
TT_MAX_SIZE = 200000
TT = {} 

# Zobrist Keys (Initialize these once at the start of your program)
import random
random.seed(42) # Consistent hashing
ZOBRIST_TABLE = {pid: [random.getrandbits(64) for _ in range(36)] for pid in range(1, 11)}
ZOBRIST_SIDE = random.getrandbits(64)

def get_hash(bb: Bitboards, playing_white: bool):
    """Calculates the full hash from scratch. Only used once at the root."""
    h = 0
    for piece_id in range(1, 11):
        pieces = bb.get_bb(piece_id)
        while pieces:
            sq = Bitboards.lsb(pieces)
            h ^= ZOBRIST_TABLE[piece_id][sq]
            pieces &= pieces - 1
    
    if not playing_white:
        h ^= ZOBRIST_SIDE
    return h

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def get_all_moves(playing_white: bool,
                  white_captured: list, black_captured: list,
                  bb: Bitboards):

    moves = []

    if playing_white:
        piece_map = [
            (1, bb.WP, get_pawn_moves),
            (2, bb.WN, get_knight_moves),
            (3, bb.WB, get_bishop_moves),
            (4, bb.WQ, get_queen_moves),
            (5, bb.WK, get_king_moves),
        ]
    else:
        piece_map = [
            (6, bb.BP, get_pawn_moves),
            (7, bb.BN, get_knight_moves),
            (8, bb.BB, get_bishop_moves),
            (9, bb.BQ, get_queen_moves),
            (10, bb.BK, get_king_moves),
        ]

    for piece_id, bitboard, move_func in piece_map:

        pieces = bitboard

        while pieces:
            sq = Bitboards.lsb(pieces)
            r, c = Bitboards.index_to_rc(sq)

            if piece_id in (1, 6):
                moves += move_func(r, c, piece_id,
                                   white_captured, black_captured, bb)
            else:
                moves += move_func(r, c, piece_id, bb)

            pieces &= pieces - 1

    return moves

def score_move(bb, move):

    piece, sr, sc, dr, dc, new_piece = move

    dst_bit = Bitboards.bit_of(dr, dc)

    captured = None
    

    captured = bb.get_piece_at(dr, dc)

    score = 0

    if captured:
        score += 10 * abs(PIECE_VALUES[captured]) - abs(PIECE_VALUES[piece])

    if new_piece != piece:
        score += 200

    return score
# ---------------------------------------------------------------------------
# Board evaluation heuristic  (TODO: tune weights / add positional tables)
# ---------------------------------------------------------------------------

def is_terminal(playing_white, white_captured, black_captured, bb, all_moves):
    if(len(all_moves) == 0 and in_check(bb, playing_white)):
        return 1 #checkmate 
    elif(len(all_moves) == 0 and not in_check(bb, playing_white)):
        return 2 #stalemate 
    else:
        return 0
        
def pst_bonus(piece, row, col):
    """
    Returns the positional bonus for a piece. 
    Positive for White, negative for Black.
    """
    is_w = is_white(piece)
    sign = 1 if is_w else -1
    
    # Get the multiplier weight for this specific piece type
    weight = PST_WEIGHTS[piece]
    
    # Use 5 - row for Black to ensure symmetry (White pushes up, Black pushes down)
    r_idx = row if is_w else (5 - row)
    
    # Select the base table based on piece type
    if piece in (WHITE_PAWN, BLACK_PAWN):
        base_val = PAWN_BASE[r_idx, col]
        
    elif piece in (WHITE_KNIGHT, BLACK_KNIGHT):
        base_val = KNIGHT_BASE[r_idx, col]
        
    elif piece in (WHITE_BISHOP, BLACK_BISHOP):
        base_val = BISHOP_BASE[r_idx, col]
        
    elif piece in (WHITE_QUEEN, BLACK_QUEEN):
        base_val = QUEEN_BASE[r_idx, col]
        
    elif piece in (WHITE_KING, BLACK_KING):
        base_val = KING_BASE[r_idx, col]

            
    else:
        return 0.0

    # Calculate final bonus: (Table Value * Piece Weight)
    # Result is an integer (standard for chess engines)
    return sign * int(base_val * weight)

def evaluate(bb: Bitboards) -> int:
    """
    Evaluates the board state for 6x6 Chess.
    Positive = White advantage, Negative = Black advantage.
    """
    score = 0
    
    # 1. Map piece types to their respective bitboards and PST tables
    # Note: We use the base tables from constants.py
    piece_map = {
        WHITE_PAWN: bb.WP,
        WHITE_KNIGHT: bb.WN,
        WHITE_BISHOP: bb.WB,
        WHITE_QUEEN: bb.WQ,
        WHITE_KING: bb.WK,
        BLACK_PAWN: bb.BP,
        BLACK_KNIGHT: bb.BN,
        BLACK_BISHOP: bb.BB,
        BLACK_QUEEN: bb.BQ,
        BLACK_KING: bb.BK,
    }

    # 2. Determine Game Phase
    # In 6x6, the board is cramped. Endgame starts when few pieces remain.
    # We count bits in the 'all occupancy' bitboard.
    total_pieces = Bitboards.popcount(bb.all_occ())
    is_endgame = total_pieces <= 8  # Threshold for 6x6 board

    # 3. Main Evaluation Loop
    for piece_id, bitboard in piece_map.items():
        if bitboard == 0:
            continue
            
        is_w = is_white(piece_id)
        material_val = PIECE_VALUES[piece_id]
        
        # Iterate over every piece of this type using bitwise operations
        temp_bb = bitboard
        while temp_bb:
            sq = Bitboards.lsb(temp_bb)
            r, c = Bitboards.index_to_rc(sq)
            
            # Add Material Value
            score += material_val
            
            pst_b = pst_bonus(piece_id, r, c)
            
            # Special King Logic: In endgame, King should be central/active.
            # We invert the penalty of the standard KING_BASE.
            if (piece_id == WHITE_KING or piece_id == BLACK_KING) and is_endgame:
                pst_b = -pst_b
            
            score += pst_b
            
            # Clear the Least Significant Bit to move to the next piece
            temp_bb &= temp_bb - 1



    # 4. Global Bonuses
    # Bishop pair is very strong on a 6x6 board because they cover both colors.
    if bin(bb.WB).count('1') >= 2: score += 30
    if bin(bb.BB).count('1') >= 2: score -= 30

    return score
# ---------------------------------------------------------------------------
# Format move string
# ---------------------------------------------------------------------------

def format_move(piece: int, src_row: int, src_col: int,
                dst_row: int, dst_col: int, new_piece: int) -> str:
    """Return move in required format: '<piece_id>:<source_cell>-><target_cell>=<new_piece>'."""
    src_cell = idx_to_cell(src_row, src_col)
    dst_cell = idx_to_cell(dst_row, dst_col)
    return f"{piece}:{src_cell}->{dst_cell}" if piece == new_piece else f"{piece}:{src_cell}->{dst_cell}={new_piece}" 

def store_tt(current_hash, depth, val, alpha_orig, beta_orig):
    """Helper to keep Minimax clean."""
    flag = EXACT
    if val <= alpha_orig:
        flag = UPPERBOUND
    elif val >= beta_orig:
        flag = LOWERBOUND

    if len(TT) >= TT_MAX_SIZE:
        TT.clear()
        
    TT[current_hash] = {'depth': depth, 'value': val, 'flag': flag}
# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def minimax(
             alpha: int,
             beta: int,
             depth: int, 
             playing_white: bool, 
             white_captured: list, 
             black_captured: list, 
             bb: Bitboards, 
             current_hash: int,
             ):
    
    alpha_orig = alpha
    beta_orig = beta

    # -----------------------------------------
    # 1. Transposition Table Lookup
    # -----------------------------------------
    if current_hash in TT:
        entry = TT[current_hash]
        if entry['depth'] >= depth:

            if entry['flag'] == EXACT: return entry['value']
            if entry['flag'] == LOWERBOUND: alpha = max(alpha, entry['value'])
            if entry['flag'] == UPPERBOUND: beta = min(beta, entry['value'])
            if alpha >= beta: return entry['value']

    # -----------------------------------------
    # 2. Leaf Node Evaluaton
    # -----------------------------------------
    if depth == 0:
        return evaluate(bb)

    # -----------------------------------------
    # 3. Generate & Order Moves
    # -----------------------------------------
    moves = get_all_moves(playing_white, white_captured, black_captured, bb)
    moves.sort(key=lambda move: score_move(bb, move), reverse=True)

    # -----------------------------------------
    # 4. Terminal State (Checkmate/Stalemate)
    # -----------------------------------------
    terminal_state = is_terminal(playing_white, white_captured, black_captured, bb, moves)
    if terminal_state == 1:
        return -100000 - depth if playing_white else 100000 + depth
    if terminal_state == 2:
        return 0

    # -----------------------------------------
    # 6. SINGLE SEARCH LOOP (Combined White/Black)
    # -----------------------------------------
    best_eval = float('-inf') if playing_white else float('inf')
    # Point to the correct capture list to use based on whose turn it is
    my_captures = black_captured if playing_white else white_captured

    for move in moves:
        piece, sr, sc, dr, dc, new_piece = move
        src_idx = sr * 6 + sc
        dst_idx = dr * 6 + dc

        # 1. Execute Move first (gets the captured piece ID)
        captured = make_temp_move(bb, *move)

        # 2. Calculate Hash using the 'captured' variable
        # XOR out source, XOR in destination, XOR toggle side
        next_hash = current_hash ^ ZOBRIST_TABLE[piece][src_idx] ^ ZOBRIST_TABLE[new_piece][dst_idx] ^ ZOBRIST_SIDE
        
        # If something was captured, XOR it out of the hash
        if captured:
            next_hash ^= ZOBRIST_TABLE[captured][dst_idx]
            my_captures.append(captured)
        
        # 3. Recurse
        val = minimax(alpha, beta, depth - 1, not playing_white, 
                      white_captured, black_captured, bb, next_hash)
        
        # 4. Undo Move
        if captured: my_captures.pop()
        undo_temp_move(bb, *move, captured)

        # Alpha-Beta Updates
        if playing_white:
            best_eval = max(best_eval, val)
            alpha = max(alpha, val)
        else:
            best_eval = min(best_eval, val)
            beta = min(beta, val)
            
        if beta <= alpha:
            break

    # -----------------------------------------
    # 7. TT Store
    # -----------------------------------------
    store_tt(current_hash, depth, best_eval, alpha_orig, beta_orig)
    return best_eval

# we need a mechanism to take into account stalemate conditions
# right now the only mechanism is checkmate so we need to disallow any moves that result in a check for the player
# doing this would make the possible moves for a state of the board to be empty in the case of a checkmate or stalemate
# then we check if the king is in check and remove it and evaluate the board and if it is not then we evaluate the board as it is

def get_best_move(board: np.ndarray, playing_white: bool = True) -> Optional[str]:
    """
    Given the current board state, return the best move string.

    Parameters
    ----------
    board        : 6×6 NumPy array representing the current game state.
    playing_white: True if the engine is playing as White, False for Black.
   

    Returns
    -------
    Move string in the format '<piece_id>:<src_cell>-><dst_cell>', or
    None if no legal moves are available.
    """
    white_captured = [2, 2, 3, 3, 4, 5]
    black_captured = [7, 7, 8, 8, 9, 10]

    #scan board to find captured pieces
    for r in range(6):
        for c in range(6):
            piece = board[r][c]
            if piece in white_captured:
                white_captured.remove(piece)
            elif piece in black_captured:
                black_captured.remove(piece)

    return _get_best_move(board, playing_white, white_captured, black_captured)


def _get_best_move(board: np.ndarray, playing_white: bool = True, white_captured: list = None, black_captured: list = None) -> Optional[str]:
    
    if white_captured is None:
        white_captured = []

    if black_captured is None:
        black_captured = []


    bb = Bitboards.from_board_array(board)

    # print("Initial Board Evaluation:", evaluate(bb)) #!remove

    # 1. Initialize the hash for the starting position
    current_hash = get_hash(bb, playing_white)

    if playing_white:
        best_value = float('-inf')
    else:
        best_value = float('inf')
        
    best_move = None
    alpha = float('-inf')
    beta = float('inf')

    all_moves = get_all_moves(playing_white, white_captured, black_captured, bb)
    all_moves.sort(key=lambda move: score_move(bb, move), reverse=True)

    is_endgame = Bitboards.popcount(bb.all_occ()) <= 8
    search_depth = 9 if is_endgame else 7   # * idk
    
    for move in all_moves:
        piece, sr, sc, dr, dc, new_piece = move
        
        # 1. Get captured piece BEFORE moving to calculate hash
        captured = bb.get_piece_at(dr, dc)

        # 2. Incremental hash
        src_idx = sr * 6 + sc
        dst_idx = dr * 6 + dc
        next_hash = current_hash ^ ZOBRIST_SIDE ^ ZOBRIST_TABLE[piece][src_idx] ^ ZOBRIST_TABLE[new_piece][dst_idx]
        if captured:
            next_hash ^= ZOBRIST_TABLE[captured][dst_idx]
        
        # 3. Apply move AND update capture lists
        make_temp_move(bb, *move)
        if captured:
            if playing_white: black_captured.append(captured)
            else: white_captured.append(captured)

        # 4. Recurse (Note: Pass depth - 1 because root is ply 1)
        value = minimax(alpha, beta, search_depth, not playing_white, white_captured, black_captured, bb, next_hash)

        # 5. Undo everything in reverse order
        if captured:
            if playing_white: black_captured.pop()
            else: white_captured.pop()
        undo_temp_move(bb, *move, captured)
        
        if (playing_white and value > best_value) or (not playing_white and value < best_value):
            best_value = value
            best_move = move
            
        if playing_white:
            alpha = max(alpha, value)
        else:
            beta = min(beta, value)


    # print("Best Move Evaluation:", best_value) #!remove
    return None if not best_move else format_move(*best_move)

# ---------------------------------------------------------------------------
# Quick smoke-test  
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test Case: White to move
    # Setup: White has a Queen and King, Black has a lone King.
    # White should look for a move that pressures the Black King.
    # pr = cProfile.Profile()
    winning_white_board = np.array(
    [
        [2, 3, 5, 4, 3, 0],
        [1, 1, 0, 1, 1, 1],
        [0, 0, 1, 0, 2, 0],
        [0, 0, 6, 0, 0, 0],
        [6, 6, 0, 6, 6, 6],
        [7, 8, 10, 9, 8, 7]
    ]
)

    print("--- Test Case: Bot Playing White ---")
    print("Board State:")
    print(winning_white_board)
    
    # We pass playing_white=True
    # The engine will now maximize the evaluation score
    # pr.enable()
    move = get_best_move(winning_white_board, playing_white=True)
    # pr.disable()
    # ps = pstats.Stats(pr).sort_stats('cumulative')
    
    print("\nBest move for White:", move)

    # ps.print_stats(30)
