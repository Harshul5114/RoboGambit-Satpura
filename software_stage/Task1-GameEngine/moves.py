import numpy as np
from utils import *
from constants import *
from bitboard import *

def make_temp_move(bb, piece, sr, sc, dr, dc, new_piece):
    src_idx = bb.rc_to_index(sr, sc)
    dst_idx = bb.rc_to_index(dr, dc)
    src_bit = 1 << src_idx
    dst_bit = 1 << dst_idx

    # remove piece from source
    bb.set_bb(piece, bb.get_bb(piece) & ~src_bit)

    # capture if needed
    captured_piece = 0
    for pid in range(1, 11):
        pb = bb.get_bb(pid)
        if pb & dst_bit:
            bb.set_bb(pid, pb & ~dst_bit)
            captured_piece = pid


    # add piece at destination
    bb.set_bb(new_piece, bb.get_bb(new_piece) | dst_bit)

    return captured_piece



def undo_temp_move(bb, piece, sr, sc, dr, dc, new_piece, captured_piece):
    src_idx = bb.rc_to_index(sr, sc)
    dst_idx = bb.rc_to_index(dr, dc)
    src_bit = 1 << src_idx
    dst_bit = 1 << dst_idx

    bb.set_bb(new_piece, bb.get_bb(new_piece) & ~dst_bit)
    bb.set_bb(piece, bb.get_bb(piece) | src_bit)

    if captured_piece != 0:
        bb.set_bb(captured_piece, bb.get_bb(captured_piece) | dst_bit)


# moves.py

def get_sliding_bitboard_attacks(sq, occupancy, piece_type):
    """
    Generates a full attack bitboard for a sliding piece.
    piece_type: 3 (Bishop), 4 (Queen)
    """
    attacks = 0
    # Bishop: Directions 4, 5, 6, 7 (Diagonals)
    # Queen: Directions 0-7 (All)
    
    if piece_type in [WHITE_BISHOP, BLACK_BISHOP, WHITE_QUEEN, BLACK_QUEEN]:
        # Diagonal rays
        for i in range(4, 8):
            attacks |= get_ray_attacks(sq, occupancy, i)
            
    if piece_type in [WHITE_QUEEN, BLACK_QUEEN]:
        # Orthogonal rays (Queen acting as Rook since you have no rooks)
        for i in range(0, 4):
            attacks |= get_ray_attacks(sq, occupancy, i)
            
    return attacks

def get_sliding_moves(row, col, piece, bb):
    moves = []
    sq = Bitboards.rc_to_index(row, col)
    occ = bb.all_occ()
    own_occ = bb.white_occ() if is_white(piece) else bb.black_occ()
    
    # One call to get all potential attack squares
    attacks = get_sliding_bitboard_attacks(sq, occ, piece)
    
    # Filter out our own pieces
    legal_destinations = attacks & ~own_occ
    
    while legal_destinations:
        dst_sq = Bitboards.lsb(legal_destinations)
        dr, dc = Bitboards.index_to_rc(dst_sq)
        
        # We still need the safety check, but the number of calls is 
        # minimized because we only check valid destination squares.
        captured = make_temp_move(bb, piece, row, col, dr, dc, piece)
        if not in_check(bb, is_white(piece)):
            moves.append((piece, row, col, dr, dc, piece))
        undo_temp_move(bb, piece, row, col, dr, dc, piece, captured)
        
        legal_destinations &= legal_destinations - 1
    return moves




def get_pawn_moves(row, col, piece, white_captured, black_captured, bb):
    """
    Calculates legal Pawn moves using precomputed attack bitboards for captures
    and bitwise occupancy checks for pushes.
    """
    moves = []
    sq = Bitboards.rc_to_index(row, col)
    is_w = is_white(piece)
    
    # 1. Forward Push (Quiet Move)
    # White moves up (index increases), Black moves down (index decreases)
    fwd_inc = BOARD_FILES if is_w else -BOARD_FILES
    dst_sq = sq + fwd_inc
    
    if 0 <= dst_sq < BOARD_SQ:
        dst_bit = 1 << dst_sq
        # Check if the square in front is empty
        if not (bb.all_occ() & dst_bit):
            dr, dc = Bitboards.index_to_rc(dst_sq)
            # Promotion occurs when moving to the last rank
            is_promo = (row == BOARD_RANKS - 2 if is_w else row == 1)
            
            if is_promo:
                promo_list = white_captured if is_w else black_captured
                # Get unique options from captured pieces, excluding pawns
                for promo in set(p for p in promo_list if p not in (WHITE_PAWN, BLACK_PAWN)):
                    captured_p = make_temp_move(bb, piece, row, col, dr, dc, promo)
                    if not in_check(bb, is_w):
                        moves.append((piece, row, col, dr, dc, promo))
                    undo_temp_move(bb, piece, row, col, dr, dc, promo, captured_p)
            else:
                captured_p = make_temp_move(bb, piece, row, col, dr, dc, piece)
                if not in_check(bb, is_w):
                    moves.append((piece, row, col, dr, dc, piece))
                undo_temp_move(bb, piece, row, col, dr, dc, piece, captured_p)

    # 2. Captures using Precomputed Attack Bitboards
    # Fetch precomputed attack mask for the current square
    attack_mask = WHITE_PAWN_ATTACKS[sq] if is_w else BLACK_PAWN_ATTACKS[sq]
    enemy_occ = bb.black_occ() if is_w else bb.white_occ()
    
    # A capture is legal if the destination is hit by the pawn AND occupied by an enemy
    legal_captures = attack_mask & enemy_occ
    
    while legal_captures:
        dst_sq = Bitboards.lsb(legal_captures)
        dr, dc = Bitboards.index_to_rc(dst_sq)
        
        is_promo = (row == BOARD_RANKS - 2 if is_w else row == 1)
        if is_promo:
            promo_list = white_captured if is_w else black_captured
            for promo in set(p for p in promo_list if p not in (WHITE_PAWN, BLACK_PAWN)):
                captured_p = make_temp_move(bb, piece, row, col, dr, dc, promo)
                if not in_check(bb, is_w):
                    moves.append((piece, row, col, dr, dc, promo))
                undo_temp_move(bb, piece, row, col, dr, dc, promo, captured_p)
        else:
            captured_p = make_temp_move(bb, piece, row, col, dr, dc, piece)
            if not in_check(bb, is_w):
                moves.append((piece, row, col, dr, dc, piece))
            undo_temp_move(bb, piece, row, col, dr, dc, piece, captured_p)
            
        legal_captures &= legal_captures - 1 # Clear LSB to move to next capture
        
    return moves

# moves.py

def get_knight_moves(row, col, piece, bb):
    moves = []
    sq = bb.rc_to_index(row, col)
    
    # Fetch precomputed attacks
    attack_mask = KNIGHT_ATTACKS[sq]
    
    # You cannot move to a square occupied by your own side
    own_occ = bb.white_occ() if is_white(piece) else bb.black_occ()
    legal_destinations = attack_mask & ~own_occ
    
    while legal_destinations:
        dst_sq = Bitboards.lsb(legal_destinations)
        dr, dc = Bitboards.index_to_rc(dst_sq)
        
        # Verify king safety (Standard check)
        captured = make_temp_move(bb, piece, row, col, dr, dc, piece)
        if not in_check(bb, is_white(piece)):
            moves.append((piece, row, col, dr, dc, piece))
        undo_temp_move(bb, piece, row, col, dr, dc, piece, captured)
        
        legal_destinations &= legal_destinations - 1 # Clear LSB
    return moves


def get_bishop_moves(row, col, piece, bb):
    """Uses bitboard-optimized sliding generation."""
    return get_sliding_moves(row, col, piece, bb)

def get_queen_moves(row, col, piece, bb):
    """Uses bitboard-optimized sliding generation."""
    return get_sliding_moves(row, col, piece, bb)

def get_king_moves(row, col, piece, bb):

    moves = []
    sq = Bitboards.rc_to_index(row, col)
    
    attack_mask = KING_ATTACKS[sq]
    
    own_occ = bb.white_occ() if is_white(piece) else bb.black_occ()
    legal_destinations = attack_mask & ~own_occ
    
    while legal_destinations:
        dst_sq = Bitboards.lsb(legal_destinations)
        dr, dc = Bitboards.index_to_rc(dst_sq)
        
        captured = make_temp_move(bb, piece, row, col, dr, dc, piece)
        
        if not in_check(bb, is_white(piece)):
            moves.append((piece, row, col, dr, dc, piece))
            
        undo_temp_move(bb, piece, row, col, dr, dc, piece, captured)
        
        legal_destinations &= legal_destinations - 1
        
    return moves