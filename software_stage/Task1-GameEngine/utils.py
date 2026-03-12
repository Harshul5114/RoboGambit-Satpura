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

def in_check(bb, role_white):

    # king bitboard
    king_bb = bb.WK if role_white else bb.BK

    if king_bb == 0:
        return True

    king_sq = king_bb.bit_length() - 1
    kr = king_sq // BOARD_FILES
    kc = king_sq % BOARD_FILES

    # -----------------
    # pawn attacks
    # -----------------

    if role_white:

        pawns = bb.BP

        if kc > 0:
            if pawns & (1 << (king_sq + 5)):
                return True

        if kc < BOARD_FILES - 1:
            if pawns & (1 << (king_sq + 7)):
                return True

    else:

        pawns = bb.WP

        if kc > 0:
            if pawns & (1 << (king_sq - 7)):
                return True

        if kc < BOARD_FILES - 1:
            if pawns & (1 << (king_sq - 5)):
                return True

    # -----------------
    # knight attacks
    # -----------------

    enemy_knights = bb.BN if role_white else bb.WN

    for dr, dc in KNIGHT_MOVES:

        r = kr + dr
        c = kc + dc

        if 0 <= r < BOARD_RANKS and 0 <= c < BOARD_FILES:

            sq = r * BOARD_FILES + c

            if enemy_knights & (1 << sq):
                return True

    # -----------------
    # king attacks
    # -----------------

    enemy_king = bb.BK if role_white else bb.WK

    for dr in (-1,0,1):
        for dc in (-1,0,1):

            if dr == 0 and dc == 0:
                continue

            r = kr + dr
            c = kc + dc

            if 0 <= r < BOARD_RANKS and 0 <= c < BOARD_FILES:

                sq = r * BOARD_FILES + c

                if enemy_king & (1 << sq):
                    return True

    # occupancy
    occ = bb.all_occ()

    # -----------------
    # orthogonal rays
    # -----------------

    enemy_queen = bb.BQ if role_white else bb.WQ

    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:

        r = kr + dr
        c = kc + dc

        while 0 <= r < BOARD_RANKS and 0 <= c < BOARD_FILES:

            sq = r * BOARD_FILES + c
            bit = 1 << sq

            if occ & bit:

                if enemy_queen & bit:
                    return True

                break

            r += dr
            c += dc

    # -----------------
    # diagonal rays
    # -----------------

    enemy_bishop = bb.BB if role_white else bb.WB
    enemy_queen = bb.BQ if role_white else bb.WQ

    for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:

        r = kr + dr
        c = kc + dc

        while 0 <= r < BOARD_RANKS and 0 <= c < BOARD_FILES:

            sq = r * BOARD_FILES + c
            bit = 1 << sq

            if occ & bit:

                if (enemy_bishop | enemy_queen) & bit:
                    return True

                break

            r += dr
            c += dc

    return False

