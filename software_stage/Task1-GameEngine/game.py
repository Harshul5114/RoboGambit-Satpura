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


def get_all_moves(board: np.ndarray, playing_white: bool, white_captured: list, black_captured: list, bb: Bitboards):
    """Return list of (piece_id, src_row, src_col, dst_row, dst_col) for all legal moves."""
    moves = []
    for row in range(len(board)):
        for col in range(len(board[row])):
            piece = board[row][col]
            if((playing_white and piece == 1) or (not playing_white and piece == 6)):
                moves += get_pawn_moves(board, row, col, piece, white_captured, black_captured, bb)
            elif((playing_white and piece == 2) or (not playing_white and piece == 7)):
                moves += get_knight_moves(board, row, col, piece)
            elif((playing_white and piece == 3) or (not playing_white and piece == 8)):
                moves += get_bishop_moves(board, row, col, piece)
            elif((playing_white and piece == 4) or (not playing_white and piece == 9)):
                moves += get_queen_moves(board, row, col, piece)
            elif((playing_white and piece == 5) or (not playing_white and piece == 10)):
                moves += get_king_moves(board, row, col, piece)

    
    return moves

def score_move(board, move):

    piece, sr, sc, dr, dc, new_piece = move

    target = board[dr][dc]

    score = 0

    # capture priority
    if target != 0:
        score += 10 * abs(PIECE_VALUES.get(target, 0)) - abs(PIECE_VALUES.get(piece, 0))

    # promotion bonus
    if new_piece != piece:
        score += 800

    return score
# ---------------------------------------------------------------------------
# Board evaluation heuristic  (TODO: tune weights / add positional tables)
# ---------------------------------------------------------------------------

def is_terminal(board: np.ndarray, playing_white, white_captured, black_captured, bb):
    all_moves = get_all_moves(board, playing_white, white_captured, black_captured, bb)
    if(len(all_moves) == 0 and in_check(board, playing_white)):
        return 1 #checkmate 
    elif(len(all_moves) == 0 and not in_check(board, playing_white)):
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
        return sign * 300 * FACTORS['knight'] * base

    if piece in (WHITE_BISHOP, BLACK_BISHOP):
        base = BISHOP_BASE[row, col] if is_white_piece else BISHOP_BASE[::-1, :][row, col]
        return sign * 320 * FACTORS['bishop'] * base

    if piece in (WHITE_QUEEN, BLACK_QUEEN):
        base = QUEEN_BASE[row, col] if is_white_piece else QUEEN_BASE[::-1, :][row, col]
        return sign * 900 * FACTORS['queen'] * base

    if piece in (WHITE_KING, BLACK_KING):
        base = KING_BASE[row, col] if is_white_piece else KING_BASE[::-1, :][row, col]
        return sign * 20000 * FACTORS['king'] * base

    return 0.0        

def evaluate(board: np.ndarray) -> float:
    score = 0.0
    for r in range(6):
        for c in range(6):
            piece = board[r][c]
            if piece == EMPTY:
                continue
            # material (use piece value table, white positive, black negative)
            score += PIECE_VALUES.get(piece, 0)
            # positional PST bonus
            score += pst_bonus(piece, r, c)
    # small mobility bonus (optional)
    # mobility_weight = 2.0
    # score += mobility_weight * (len(get_all_moves(board, True, [], [])) - len(get_all_moves(board, False, [], [])))
    return score

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------


# def make_move(board, move, white_captured, black_captured):

#     piece, sr, sc, dr, dc, new_piece = move

#     captured = board[dr][dc]

#     board[sr][sc] = 0
#     board[dr][dc] = new_piece

#     if 1 <= captured <= 5:
#         white_captured.append(captured)
#     elif 6 <= captured <= 10:
#         black_captured.append(captured)

#     return captured

# def unmake_move(board, move, captured, white_captured, black_captured):

#     piece, sr, sc, dr, dc, new_piece = move

#     board[sr][sc] = piece
#     board[dr][dc] = captured

#     if 1 <= captured <= 5:
#         white_captured.pop()
#     elif 6 <= captured <= 10:
#         black_captured.pop()

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
def minimax(board, alpha, beta, depth, playing_white, white_captured, black_captured, bb):
    terminal_state = is_terminal(board, playing_white, white_captured, black_captured, bb)
    if terminal_state == 1:
        # Find the king position to remove for evaluation
        king_row = -1
        king_col = -1
        target_king = 5 if playing_white else 10
        for row in range(len(board)):
            for col in range(len(board[row])):
                if board[row][col] == target_king:
                    king_row = row 
                    king_col = col 
                    break
            if king_row != -1:
                break
        
        # Safety check: only modify board if king was found
        if king_row != -1 and king_col != -1:
            board[king_row][king_col] = 0
            eval = evaluate(board)*depth
            board[king_row][king_col] = target_king
            return eval
        else:
            # If king somehow not found, return board evaluation as-is
            return evaluate(board)
    
    elif(depth == 0 or terminal_state == 2):
        return evaluate(board)   
    
    if playing_white:
        max_eval = float('-inf')

        moves = get_all_moves(board, playing_white, white_captured, black_captured, bb)
        moves.sort(key=lambda move: score_move(board, move), reverse=True)
        
        for move in moves:
            captured = make_move(board, move, white_captured, black_captured)
            eval = minimax(board, alpha, beta, depth - 1, not playing_white, white_captured, black_captured, bb)
            unmake_move(board, move, captured, white_captured, black_captured)
            
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            
            # alpha-beta pruning
            if beta <= alpha:
                break
        
        return max_eval

    
    else:
        min_eval = float('inf')

        moves = get_all_moves(board, playing_white, white_captured, black_captured, bb)
        moves.sort(key=lambda move: score_move(board, move), reverse=True)
        
        for move in moves:
            captured = make_move(board, move, white_captured, black_captured)
            eval = minimax(board, alpha, beta, depth - 1, not playing_white, white_captured, black_captured, bb)
            unmake_move(board, move, captured, white_captured, black_captured)

            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            
            # alpha-beta pruning
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

    bb = Bitboards.from_board_array(board)

    if(playing_white):
        best_value = float('-inf')
    else:
        best_value = float('inf')
    best_move = None
    
    alpha = float('-inf')
    beta = float('inf')


    all_moves = get_all_moves(board, playing_white, white_captured, black_captured, bb)
    all_moves.sort(key=lambda move: score_move(board, move), reverse=playing_white)  # Sort moves by heuristic score
    for move in all_moves:
        
        captured = make_move(board, move, white_captured, black_captured)
        
        value = minimax(board, alpha, beta, 4, not playing_white, white_captured, black_captured, bb)

        unmake_move(board, move, captured, white_captured, black_captured)
        
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
    print("Best move for White:", move)