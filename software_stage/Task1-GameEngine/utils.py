import numpy as np
from constants import *
from bitboard import *

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
    king_bb = bb.WK if role_white else bb.BK
    if not king_bb: return True
    king_sq = Bitboards.lsb(king_bb)
    occ = bb.all_occ()
    
    # 1. Check Knights and Pawns (Instant)
    enemy_knights = bb.BN if role_white else bb.WN
    if KNIGHT_ATTACKS[king_sq] & enemy_knights: return True

    enemy_pawns = bb.BP if role_white else bb.WP
    pawn_attacks = WHITE_PAWN_ATTACKS[king_sq] if role_white else BLACK_PAWN_ATTACKS[king_sq]
    if pawn_attacks & enemy_pawns: return True
    
    # 2. Check Queen/Bishop diagonals (Instant)
    # Check diagonals (Bishop + Queen)
    enemy_diagonals = (bb.BB | bb.BQ) if role_white else (bb.WB | bb.WQ)
    diag_attacks = 0
    for i in range(4, 8): diag_attacks |= get_ray_attacks(king_sq, occ, i)
    if diag_attacks & enemy_diagonals: return True
    
    # Check orthogonals (Queen)
    enemy_queens = bb.BQ if role_white else bb.WQ
    ortho_attacks = 0
    for i in range(0, 4): ortho_attacks |= get_ray_attacks(king_sq, occ, i)
    if ortho_attacks & enemy_queens: return True

    # 3. Check King (Instant)
    enemy_king = bb.BK if role_white else bb.WK
    if KING_ATTACKS[king_sq] & enemy_king: return True

    return False

