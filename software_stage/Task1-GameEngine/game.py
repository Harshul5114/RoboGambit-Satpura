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
def minimax(alpha, beta, depth, playing_white, white_captured, black_captured, bb):

    terminal_state = is_terminal(None, playing_white, white_captured, black_captured, bb)

    if terminal_state == 1:
        # checkmate
        return -100000 - depth if playing_white else 100000 + depth

    if terminal_state == 2:
        return 0
    
    if depth == 0:
        return evaluate(bb)
    
    if 

    moves = get_all_moves(playing_white, white_captured, black_captured, bb)

    # move ordering
    moves.sort(key=lambda move: score_move(bb, move), reverse=True)

    if playing_white:

        max_eval = float('-inf')

        for move in moves:

            captured = make_temp_move(bb, *move)

            val = minimax(alpha, beta, depth-1,
                          False, white_captured, black_captured, bb)

            undo_temp_move(bb, *move, captured)

            if val > max_eval:
                max_eval = val

            if val > alpha:
                alpha = val

            if beta <= alpha:
                break

        return max_eval

    else:

        min_eval = float('inf')

        for move in moves:

            captured = make_temp_move(bb, *move)

            val = minimax(alpha, beta, depth-1,
                          True, white_captured, black_captured, bb)

            undo_temp_move(bb, *move, captured)

            if val < min_eval:
                min_eval = val

            if val < beta:
                beta = val

            if beta <= alpha:
                break

        return min_eval


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

    if white_captured is None:
        white_captured = []

    if black_captured is None:
        black_captured = []

    bb = Bitboards.from_board_array(board)

    if(playing_white):
        best_value = float('-inf')
    else:
        best_value = float('inf')
    best_move = None
    
    alpha = float('-inf')
    beta = float('inf')


    all_moves = get_all_moves(playing_white, white_captured, black_captured, bb)
    all_moves.sort(key=lambda move: score_move(bb, move), reverse=True)  # Sort moves by heuristic score
    for move in all_moves:
        
        captured = make_temp_move(bb, *move)
        
        value = minimax(alpha, beta, 6, not playing_white, white_captured, black_captured, bb)

        undo_temp_move(bb, *move, captured)
        
        if (playing_white and value > best_value) or (not playing_white and value < best_value):
            best_value = value
            best_move = move
            
        if(playing_white):
            alpha = max(alpha, value)
        else:
            beta = min(beta, value)
    
    return None if not best_move else format_move(*best_move) 





# ---------------------------------------------------------------------------
# Quick smoke-test  
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example: standard-ish starting position on a 6x6 board
    # White pieces on rows 4-5, Black pieces on rows 0-1
    initial_board = np.array([
        [ 2,  3,  4,  5,  3,  2],   # Row 1 (A1–F1) — White back rank
        [ 1,  1,  1,  1,  1,  1],   # Row 2         — White pawns
        [ 0,  0,  0,  0,  0,  0],   # Row 3
        [ 0,  0,  0,  0,  0,  0],   # Row 4
        [ 6,  6,  6,  6,  6,  6],   # Row 5         — Black pawns
        [ 7,  8,  9, 10,  8,  7],   # Row 6 (A6–F6) — Black back rank
    ], dtype=int)

    initial_board_2 = np.array([
        [0, 0, 0, 3, 5, 0],
        [1, 3, 4, 0, 0, 1],
        [0, 7, 1, 8, 0, 6],
        [0, 0, 2, 3, 0, 0],
        [0, 0, 0, 9, 0, 0],
        [0, 0, 10, 7, 0, 0]
    ])

    print("Board:\n", initial_board_2)
    move = _get_best_move(initial_board_2, playing_white=False)
    print("Best move for Black:", move)