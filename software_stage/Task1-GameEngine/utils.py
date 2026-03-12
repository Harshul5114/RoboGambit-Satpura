import numpy as np
from constants import *

def idx_to_cell(row: int, col: int) -> str:
    """Convert (row, col) zero-indexed to board notation e.g. (0,0) -> 'A1'."""
    return f"{COL_TO_FILE[col]}{row + 1}"

def cell_to_idx(cell: str):
    """Convert board notation e.g. 'A1' -> (row=0, col=0)."""
    col = FILE_TO_COL[cell[0].upper()]
    row = int(cell[1]) - 1
    return row, col

def in_bounds(board: np.ndarray, row: int, col: int) -> bool:
    return 0 <= row < 6 and 0 <= col < 6

def is_white(piece: int) -> bool:
    return piece in WHITE_PIECES

def is_black(piece: int) -> bool:
    return piece in BLACK_PIECES

def same_side(p1: int, p2: int) -> bool:
    return (is_white(p1) and is_white(p2)) or (is_black(p1) and is_black(p2))

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

