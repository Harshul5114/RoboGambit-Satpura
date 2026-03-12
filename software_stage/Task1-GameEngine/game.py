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


# TT Flags
EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2

# The Transposition Table
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

    for pid in range(1,11):
        if bb.get_bb(pid) & dst_bit:
            captured = pid
            break

    score = 0

    if captured:
        score += 10 * abs(PIECE_VALUES[captured]) - abs(PIECE_VALUES[piece])

    if new_piece != piece:
        score += 200

    return score
# ---------------------------------------------------------------------------
# Board evaluation heuristic  (TODO: tune weights / add positional tables)
# ---------------------------------------------------------------------------

def is_terminal(board: np.ndarray, playing_white, white_captured, black_captured, bb):
    all_moves = get_all_moves(playing_white, white_captured, black_captured, bb)
    if(len(all_moves) == 0 and in_check(bb, playing_white)):
        return 1 #checkmate 
    elif(len(all_moves) == 0 and not in_check(bb, playing_white)):
        return 2 #stalemate 
    else:
        return 0
        
def pst_bonus(piece, row, col):
    """Return signed positional bonus (positive for White, negative for Black)."""
    # choose absolute piece value for sign handling
    is_white_piece = is_white(piece)

    sign = 1 if is_white_piece else -1

    if piece in (WHITE_PAWN, BLACK_PAWN):
        base = PAWN_BASE[row, col] if is_white_piece else PAWN_BASE[::-1, :][row, col]
        return sign * PIECE_VALUES[WHITE_PAWN] * FACTORS['pawn'] * base

    if piece in (WHITE_KNIGHT, BLACK_KNIGHT):
        base = KNIGHT_BASE[row, col] if is_white_piece else KNIGHT_BASE[::-1, :][row, col]
        return sign * PIECE_VALUES[WHITE_KNIGHT] * FACTORS['knight'] * base

    if piece in (WHITE_BISHOP, BLACK_BISHOP):
        base = BISHOP_BASE[row, col] if is_white_piece else BISHOP_BASE[::-1, :][row, col]
        return sign * PIECE_VALUES[WHITE_BISHOP] * FACTORS['bishop'] * base

    if piece in (WHITE_QUEEN, BLACK_QUEEN):
        base = QUEEN_BASE[row, col] if is_white_piece else QUEEN_BASE[::-1, :][row, col]
        return sign * PIECE_VALUES[WHITE_QUEEN] * FACTORS['queen'] * base

    if piece in (WHITE_KING, BLACK_KING):
        base = KING_BASE[row, col] if is_white_piece else KING_BASE[::-1, :][row, col]
        return sign * 200 * FACTORS['king'] * base

    return 0.0        

def evaluate(bb: Bitboards):

    score = 0

    piece_map = [
        (WHITE_PAWN, bb.WP),
        (WHITE_KNIGHT, bb.WN),
        (WHITE_BISHOP, bb.WB),
        (WHITE_QUEEN, bb.WQ),
        (WHITE_KING, bb.WK),
        (BLACK_PAWN, bb.BP),
        (BLACK_KNIGHT, bb.BN),
        (BLACK_BISHOP, bb.BB),
        (BLACK_QUEEN, bb.BQ),
        (BLACK_KING, bb.BK),
    ]

    for piece, bitboard in piece_map:

        pieces = bitboard

        while pieces:

            sq = Bitboards.lsb(pieces)
            r, c = Bitboards.index_to_rc(sq)

            score += PIECE_VALUES[piece]
            score += pst_bonus(piece, r, c)

            pieces &= pieces - 1

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

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def minimax(alpha, beta, depth, playing_white, white_captured, black_captured, bb, current_hash):
    """
    Complete Minimax with Alpha-Beta Pruning and Transposition Table.
    """
    alpha_orig = alpha

    # 1. Transposition Table Lookup
    if current_hash in TT:
        entry = TT[current_hash]
        if entry['depth'] >= depth:
            if entry['flag'] == EXACT:
                return entry['value']
            elif entry['flag'] == LOWERBOUND:
                alpha = max(alpha, entry['value'])
            elif entry['flag'] == UPPERBOUND:
                beta = min(beta, entry['value'])
            
            if alpha >= beta:
                return entry['value']

    # 2. Terminal State Handling
    terminal_state = is_terminal(None, playing_white, white_captured, black_captured, bb)
    
    if terminal_state == 1:
        # Checkmate: If it's your turn and you're mated, you lose. 
        # We add/subtract depth to prefer the shortest path to mate.
        return -100000 - depth if playing_white else 100000 + depth

    if terminal_state == 2:
        # Stalemate is a draw (0), not the material score.
        return 0
    
    if depth == 0:
        # At leaf nodes, return the static evaluation
        return evaluate(bb)

    # 3. Move Generation and Ordering
    moves = get_all_moves(playing_white, white_captured, black_captured, bb)
    moves.sort(key=lambda move: score_move(bb, move), reverse=True)

    if playing_white:
        max_eval = float('-inf')
        for move in moves:
            piece, sr, sc, dr, dc, new_piece = move
            src_idx = sr * 6 + sc
            dst_idx = dr * 6 + dc

            # Calculate Incremental Hash
            # 1. Remove piece from source, 2. Place piece at dest, 3. Toggle turn
            next_hash = current_hash ^ ZOBRIST_TABLE[piece][src_idx] ^ ZOBRIST_TABLE[piece][dst_idx] ^ ZOBRIST_SIDE
            
            # 4. If capture, XOR out the captured piece
            captured_pid = bb.get_piece_at(dr, dc) # Helper needed to identify piece at dest
            if captured_pid:
                next_hash ^= ZOBRIST_TABLE[captured_pid][dst_idx]

            # Execute move
            captured = make_temp_move(bb, *move)
            val = minimax(alpha, beta, depth - 1, False, white_captured, black_captured, bb, next_hash)
            undo_temp_move(bb, *move, captured)

            max_eval = max(max_eval, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break # Alpha-Beta Pruning
        res_val = max_eval

    else:
        min_eval = float('inf')
        for move in moves:
            piece, sr, sc, dr, dc, new_piece = move
            src_idx = sr * 6 + sc
            dst_idx = dr * 6 + dc

            next_hash = current_hash ^ ZOBRIST_TABLE[piece][src_idx] ^ ZOBRIST_TABLE[piece][dst_idx] ^ ZOBRIST_SIDE
            
            captured_pid = bb.get_piece_at(dr, dc)
            if captured_pid:
                next_hash ^= ZOBRIST_TABLE[captured_pid][dst_idx]

            captured = make_temp_move(bb, *move)
            val = minimax(alpha, beta, depth - 1, True, white_captured, black_captured, bb, next_hash)
            undo_temp_move(bb, *move, captured)

            min_eval = min(min_eval, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        res_val = min_eval

    # 4. Store Result in Transposition Table
    new_entry = {'depth': depth, 'value': res_val}
    if res_val <= alpha_orig:
        new_entry['flag'] = UPPERBOUND
    elif res_val >= beta:
        new_entry['flag'] = LOWERBOUND
    else:
        new_entry['flag'] = EXACT
        
    TT[current_hash] = new_entry
    return res_val


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
    return _get_best_move(board, playing_white, [], [])


def _get_best_move(board: np.ndarray, playing_white: bool = True, white_captured: list = None, black_captured: list = None) -> Optional[str]:
    
    if white_captured is None:
        white_captured = []

    if black_captured is None:
        black_captured = []

    bb = Bitboards.from_board_array(board)

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
    
    for move in all_moves:
        piece, sr, sc, dr, dc, new_piece = move
        
        captured = make_temp_move(bb, *move)
        
        # Calculate incremental hash for root moves
        src_idx = sr * 6 + sc
        dst_idx = dr * 6 + dc
        next_hash = current_hash ^ ZOBRIST_SIDE ^ ZOBRIST_TABLE[piece][src_idx] ^ ZOBRIST_TABLE[new_piece][dst_idx]
        if captured != 0:
            next_hash ^= ZOBRIST_TABLE[captured][dst_idx]
        
        # Notice we pass next_hash into minimax
        value = minimax(alpha, beta, 6, not playing_white, white_captured, black_captured, bb, next_hash)

        undo_temp_move(bb, *move, captured)
        
        if (playing_white and value > best_value) or (not playing_white and value < best_value):
            best_value = value
            best_move = move
            
        if playing_white:
            alpha = max(alpha, value)
        else:
            beta = min(beta, value)
    
    return None if not best_move else format_move(*best_move)

# ---------------------------------------------------------------------------
# Quick smoke-test  
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test Case: White to move
    # Setup: White has a Queen and King, Black has a lone King.
    # White should look for a move that pressures the Black King.
    winning_white_board = np.array([
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 4, 0, 0, 0], # White Queen at C3
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0,0, 0], # Black King at D5
        [10, 0, 0, 5, 0, 0]  # White King at D6
    ], dtype=int)

    print("--- Test Case: Bot Playing White ---")
    print("Board State:")
    print(winning_white_board)
    
    # We pass playing_white=True
    # The engine will now maximize the evaluation score
    move = get_best_move(winning_white_board, playing_white=True)
    
    print("\nBest move for White:", move)