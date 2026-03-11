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
sys.setrecursionlimit(10**5)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMPTY = 0

# Piece IDs
WHITE_PAWN   = 1
WHITE_KNIGHT = 2
WHITE_BISHOP = 3
WHITE_QUEEN  = 4
WHITE_KING   = 5
BLACK_PAWN   = 6
BLACK_KNIGHT = 7
BLACK_BISHOP = 8
BLACK_QUEEN  = 9
BLACK_KING   = 10

KNIGHT_MOVES = [(-2,-1),(-2,1),(2,-1),(2,1),(-1,-2),(-1,2),(1,-2),(1,2)]

WHITE_PIECES = {WHITE_PAWN, WHITE_KNIGHT, WHITE_BISHOP, WHITE_QUEEN, WHITE_KING}
BLACK_PIECES = {BLACK_PAWN, BLACK_KNIGHT, BLACK_BISHOP, BLACK_QUEEN, BLACK_KING}

BOARD_SIZE = 6

PIECE_VALUES = {
    WHITE_PAWN:   100,
    WHITE_KNIGHT: 300,
    WHITE_BISHOP: 320,
    WHITE_QUEEN:  900,
    WHITE_KING:  20000,
    BLACK_PAWN:  -100,
    BLACK_KNIGHT:-300,
    BLACK_BISHOP:-320,
    BLACK_QUEEN: -900,
    BLACK_KING: -20000,
}
# Column index → letter
COL_TO_FILE = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F'}
FILE_TO_COL = {v: k for k, v in COL_TO_FILE.items()}



# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def idx_to_cell(row: int, col: int) -> str:
    """Convert (row, col) zero-indexed to board notation e.g. (0,0) -> 'A1'."""
    return f"{COL_TO_FILE[col]}{row + 1}"

def cell_to_idx(cell: str):
    """Convert board notation e.g. 'A1' -> (row=0, col=0)."""
    col = FILE_TO_COL[cell[0].upper()]
    row = int(cell[1]) - 1
    return row, col

def in_bounds(board: np.ndarray, row: int, col: int) -> bool:
    return 0 <= row < len(board) and 0 <= col < len(board[0])

def is_white(piece: int) -> bool:
    return piece in WHITE_PIECES

def is_black(piece: int) -> bool:
    return piece in BLACK_PIECES

def same_side(p1: int, p2: int) -> bool:
    return (is_white(p1) and is_white(p2)) or (is_black(p1) and is_black(p2))

# ---------------------------------------------------------------------------
# Move generation  
# ---------------------------------------------------------------------------

def in_check(board: np.ndarray, role_white : bool):
    target_king = 5 if role_white else 10
    king_pos = None
    for r in range(len(board)):
        for c in range(len(board[r])):
            if board[r][c] == target_king:
                king_pos = (r, c)
                break
        if king_pos is not None:
            break

    if king_pos is None:
        # no king found (shouldn't happen in normal play) — treat as in check
        return True

    kr, kc = king_pos

    #Pawn attack
    if role_white:
        for dr, dc in [(1, -1), (1, 1)]:
            rr, cc = kr + dr, kc + dc
            if in_bounds(board, rr, cc) and board[rr][cc] == 6:
                return True
    else:
        for dr, dc in [(-1, -1), (-1, 1)]:
            rr, cc = kr + dr, kc + dc
            if in_bounds(board, rr, cc) and board[rr][cc] == 1:
                return True
    #Knight attack
    for dr, dc in KNIGHT_MOVES:
        rr, cc = kr + dr, kc + dc
        if in_bounds(board, rr, cc):
            if role_white and board[rr][cc] == 7:
                return True
            if not role_white and board[rr][cc] == 2:
                return True
    #King attack
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = kr + dr, kc + dc
            if in_bounds(board, rr, cc):
                if role_white and board[rr][cc] == 10:
                    return True
                if not role_white and board[rr][cc] == 5:
                    return True
    # orthogonal rays
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        rr, cc = kr + dr, kc + dc
        while in_bounds(board, rr, cc):
            piece = board[rr][cc]
            if piece != 0:
                if role_white:
                    if piece == 9:  # black queen (orthogonal or diagonal)
                        return True
                else:
                    if piece == 4:  # white queen
                        return True
                break
            rr += dr
            cc += dc
    
    #diagnol rays
    for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        rr, cc = kr + dr, kc + dc
        while in_bounds(board, rr, cc):
            piece = board[rr][cc]
            if piece != 0:
                if role_white:
                    if piece == 8 or piece == 9:  # black bishop or queen
                        return True
                else:
                    if piece == 3 or piece == 4:  # white bishop or queen
                        return True
                break
            rr += dr
            cc += dc
    return False
                    

def get_pawn_moves(board: np.ndarray, row: int, col: int, piece: int,
                   white_captured: list, black_captured: list):

    moves = []

    if is_white(piece):

        # forward move
        r = row + 1
        c = col

        if in_bounds(board, r, c) and board[r][c] == 0:

            board[row][col] = 0
            board[r][c] = piece

            if not in_check(board, True):

                if row == len(board) - 2 and len(white_captured) != 0:
                    for new_piece in set(white_captured):
                        moves.append((piece, row, col, r, c, new_piece))
                else:
                    moves.append((piece, row, col, r, c, piece))

            board[row][col] = piece
            board[r][c] = 0


        # capture right
        r = row + 1
        c = col + 1

        if in_bounds(board, r, c) and is_black(board[r][c]):

            captured = board[r][c]

            board[row][col] = 0
            board[r][c] = piece

            if not in_check(board, True):

                if row == len(board) - 2 and len(white_captured) != 0:
                    for new_piece in set(white_captured):
                        moves.append((piece, row, col, r, c, new_piece))
                else:
                    moves.append((piece, row, col, r, c, piece))

            board[row][col] = piece
            board[r][c] = captured


        # capture left
        r = row + 1
        c = col - 1

        if in_bounds(board, r, c) and is_black(board[r][c]):

            captured = board[r][c]

            board[row][col] = 0
            board[r][c] = piece

            if not in_check(board, True):

                if row == len(board) - 2 and len(white_captured) != 0:
                    for new_piece in set(white_captured):
                        moves.append((piece, row, col, r, c, new_piece))
                else:
                    moves.append((piece, row, col, r, c, piece))

            board[row][col] = piece
            board[r][c] = captured


    else:  # black pawn

        # forward move
        r = row - 1
        c = col

        if in_bounds(board, r, c) and board[r][c] == 0:

            board[row][col] = 0
            board[r][c] = piece

            if not in_check(board, False):

                if row == 1 and len(black_captured) != 0:
                    for new_piece in set(black_captured):
                        moves.append((piece, row, col, r, c, new_piece))
                else:
                    moves.append((piece, row, col, r, c, piece))

            board[row][col] = piece
            board[r][c] = 0


        # capture right
        r = row - 1
        c = col + 1

        if in_bounds(board, r, c) and is_white(board[r][c]):

            captured = board[r][c]

            board[row][col] = 0
            board[r][c] = piece

            if not in_check(board, False):

                if row == 1 and len(black_captured) != 0:
                    for new_piece in set(black_captured):
                        moves.append((piece, row, col, r, c, new_piece))
                else:
                    moves.append((piece, row, col, r, c, piece))

            board[row][col] = piece
            board[r][c] = captured


        # capture left
        r = row - 1
        c = col - 1

        if in_bounds(board, r, c) and is_white(board[r][c]):

            captured = board[r][c]

            board[row][col] = 0
            board[r][c] = piece

            if not in_check(board, False):

                if row == 1 and len(black_captured) != 0:
                    for new_piece in set(black_captured):
                        moves.append((piece, row, col, r, c, new_piece))
                else:
                    moves.append((piece, row, col, r, c, piece))

            board[row][col] = piece
            board[r][c] = captured


    return moves

def get_knight_moves(board: np.ndarray, row: int, col: int, piece: int):
    moves = []

    for dst in KNIGHT_MOVES:
        new_board = board.copy()
        if(in_bounds(board, row + dst[0], col + dst[1])):
            new_board[row + dst[0]][col + dst[1]] = piece 
        new_board[row][col] = 0
        if(in_bounds(board, row + dst[0], col + dst[1]) and not same_side(piece, board[row + dst[0]][col + dst[1]]) and not in_check(new_board, is_white(piece))):
            moves.append((piece, row, col, row + dst[0], col + dst[1], piece))
    return moves

def get_sliding_moves(board, row, col, piece, directions):
    moves = []
    for dr, dc in directions:
        r = row + dr
        c = col + dc

        while in_bounds(board, r, c):
            target = board[r][c]
            if same_side(piece, target):
                break
            new_board = board.copy()
            new_board[row][col] = 0
            new_board[r][c] = piece

            if not in_check(new_board, is_white(piece)):
                moves.append((piece, row, col, r, c, piece))
            if target != 0:
                break
            r += dr
            c += dc

    return moves

def get_bishop_moves(board: np.ndarray, row: int, col: int, piece: int):
    diagonals = [(-1,-1),(-1,1),(1,-1),(1,1)]
    return get_sliding_moves(board, row, col, piece, diagonals)

def get_queen_moves(board: np.ndarray, row: int, col: int, piece: int):
    all_dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    return get_sliding_moves(board, row, col, piece, all_dirs)

def get_king_moves(board: np.ndarray, row: int, col: int, piece: int):
    moves = []
    dirs = [(0,1), (1,0), (1,1), (0,-1), (-1,0), (-1,1), (-1,-1), (1,-1)]
    for d in dirs:
        new_board = board.copy()
        if(in_bounds(board, row + d[0], col + d[1])):
            new_board[row + d[0]][col + d[1]] = piece 
        new_board[row][col] = 0
        if(in_bounds(board, row + d[0], col + d[1]) and not same_side(piece, board[row + d[0]][col + d[1]]) and not in_check(new_board, is_white(piece))):
            moves.append((piece, row, col, row + d[0], col + d[1], piece))
    return moves


MOVE_GENERATORS = {
    WHITE_PAWN:   get_pawn_moves,
    WHITE_KNIGHT: get_knight_moves,
    WHITE_BISHOP: get_bishop_moves,
    WHITE_QUEEN:  get_queen_moves,
    WHITE_KING:   get_king_moves,
    BLACK_PAWN:   get_pawn_moves,
    BLACK_KNIGHT: get_knight_moves,
    BLACK_BISHOP: get_bishop_moves,
    BLACK_QUEEN:  get_queen_moves,
    BLACK_KING:   get_king_moves,
}


def get_all_moves(board: np.ndarray, playing_white: bool, white_captured: list, black_captured: list):
    """Return list of (piece_id, src_row, src_col, dst_row, dst_col) for all legal moves."""
    moves = []
    for row in range(len(board)):
        for col in range(len(board[row])):
            piece = board[row][col]
            if((playing_white and piece == 1) or (not playing_white and piece == 6)):
                moves += get_pawn_moves(board, row, col, piece, white_captured, black_captured)
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

def is_terminal(board: np.ndarray, playing_white, white_captured, black_captured):
    if(len(get_all_moves(board, playing_white, white_captured, black_captured)) == 0 and in_check(board, playing_white)):
        return 1 #checkmate 
    elif(len(get_all_moves(board, playing_white, white_captured, black_captured)) == 0 and not in_check(board, playing_white)):
        return 2 #stalemate 
    else:
        return 0
        
        

def evaluate(board: np.ndarray) -> float:
    """
    Static board evaluation from White's perspective.
    Positive  → advantage for White
    Negative  → advantage for Black
    TODO: Add mobility, piece-square tables, king safety, etc.
    """
    score = 0.0
    for row in range(len(board)):
        for col in range(len(board[row])):
            piece = board[row][col]
            if piece != EMPTY:
                score += PIECE_VALUES.get(piece, 0)
    return score

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------


def make_move(board, move, white_captured, black_captured):

    piece, sr, sc, dr, dc, new_piece = move

    captured = board[dr][dc]

    board[sr][sc] = 0
    board[dr][dc] = new_piece

    if 1 <= captured <= 5:
        white_captured.append(captured)
    elif 6 <= captured <= 10:
        black_captured.append(captured)

    return captured

def unmake_move(board, move, captured, white_captured, black_captured):

    piece, sr, sc, dr, dc, new_piece = move

    board[sr][sc] = piece
    board[dr][dc] = captured

    if 1 <= captured <= 5:
        white_captured.pop()
    elif 6 <= captured <= 10:
        black_captured.pop()

# ---------------------------------------------------------------------------
# Format move string
# ---------------------------------------------------------------------------

def format_move(piece: int, src_row: int, src_col: int,
                dst_row: int, dst_col: int, new_piece: int) -> str:
    """Return move in required format: '<piece_id>:<source_cell>-><target_cell>'."""
    src_cell = idx_to_cell(src_row, src_col)
    dst_cell = idx_to_cell(dst_row, dst_col)
    return f"{piece}:{src_cell}->{dst_cell}" if piece == new_piece else f"{piece}:{src_cell}->{dst_cell}={new_piece}" 

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def minimax(board, alpha, beta, depth, playing_white, white_captured, black_captured):
    if is_terminal(board, playing_white, white_captured, black_captured) == 1:
        king_row = -1
        king_col = -1
        for row in range(len(board)):
            for col in range(len(board[row])):
                piece = board[row][col]
                if((playing_white and piece == 5) or (not playing_white and piece == 10)):
                    king_row = row 
                    king_col = col 
        new_board = board.copy()
        new_board[king_row][king_col] = 0
        return evaluate(new_board)*depth
    
    elif(depth == 0 or is_terminal(board, playing_white, white_captured, black_captured) == 2):
        return evaluate(board)   
    
    if playing_white:
        max_eval = float('-inf')

        moves = get_all_moves(board, playing_white, white_captured, black_captured)
        moves.sort(key=lambda move: score_move(board, move), reverse=True)
        
        for move in moves:
            captured = make_move(board, move, white_captured, black_captured)
            eval = minimax(board, alpha, beta, depth - 1, not playing_white, white_captured, black_captured)
            unmake_move(board, move, captured, white_captured, black_captured)
            
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            
            # alpha-beta pruning
            if beta <= alpha:
                break
        
        return max_eval
    
    
    else:
        min_eval = float('inf')

        moves = get_all_moves(board, playing_white, white_captured, black_captured)
        moves.sort(key=lambda move: score_move(board, move), reverse=True)
        
        for move in moves:
            captured = make_move(board, move, white_captured, black_captured)
            eval = minimax(board, alpha, beta, depth - 1, not playing_white, white_captured, black_captured)
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

    # bb = board_to_bitboards(board)

    if(playing_white):
        best_value = float('-inf')
    else:
        best_value = float('inf')
    best_move = None
    
    alpha = float('-inf')
    beta = float('inf')

    temp_white_captured = []
    temp_black_captured = []
    all_moves = get_all_moves(board, playing_white, temp_white_captured, temp_black_captured)
    all_moves.sort(key=lambda move: score_move(board, move), reverse=playing_white)  # Sort moves by heuristic score
    for move in all_moves:
        
        captured = make_move(board, move, temp_white_captured, temp_black_captured)
        
        value = minimax(board, alpha, beta, 4, not playing_white, temp_white_captured, temp_black_captured)

        unmake_move(board, move, captured, temp_white_captured, temp_black_captured)
        
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
    move = get_best_move(initial_board_2, playing_white=False)
    print("Best move for White:", move)