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


def get_pawn_moves(row, col, piece, white_captured, black_captured, bb):

    moves = []
    src_idx = bb.rc_to_index(row, col)

    if is_white(piece):

        # -----------------
        # forward move
        # -----------------
        dst_idx = src_idx + BOARD_FILES

        if dst_idx < BOARD_SQ:

            dst_bit = 1 << dst_idx

            if not (bb.all_occ() & dst_bit):

                dr, dc = bb.index_to_rc(dst_idx)
                captured_piece = 0

                # promotion row
                if row == BOARD_RANKS - 2:

                    promo_options = [
                        p for p in set(white_captured)
                        if p not in (WHITE_PAWN, BLACK_PAWN)
                    ]

                    for promo in promo_options:

                        make_temp_move(bb, piece, row, col, dr, dc, promo)

                        if not in_check(bb, True):
                            moves.append((piece, row, col, dr, dc, promo))

                        undo_temp_move(bb, piece, row, col, dr, dc, promo, captured_piece)

                else:

                    make_temp_move(bb, piece, row, col, dr, dc, piece)

                    if not in_check(bb, True):
                        moves.append((piece, row, col, dr, dc, piece))

                    undo_temp_move(bb, piece, row, col, dr, dc, piece, captured_piece)

        # -----------------
        # captures
        # -----------------
        for dc_shift in [-1, 1]:

            dc = col + dc_shift
            dr = row + 1

            if not (0 <= dc < BOARD_FILES and 0 <= dr < BOARD_RANKS):
                continue

            dst_idx = bb.rc_to_index(dr, dc)
            dst_bit = 1 << dst_idx

            if bb.black_occ() & dst_bit:


                if row == BOARD_RANKS - 2:

                    promo_options = [
                        p for p in set(white_captured)
                        if p not in (WHITE_PAWN, BLACK_PAWN)
                    ]

                    for promo in promo_options:

                        captured_piece = make_temp_move(bb, piece, row, col, dr, dc, promo)

                        if not in_check(bb, True):
                            moves.append((piece, row, col, dr, dc, promo))

                        undo_temp_move(bb, piece, row, col, dr, dc, promo, captured_piece)

                else:

                    captured_piece = make_temp_move(bb, piece, row, col, dr, dc, piece)

                    if not in_check(bb, True):
                        moves.append((piece, row, col, dr, dc, piece))

                    undo_temp_move(bb, piece, row, col, dr, dc, piece, captured_piece)

    else:

        # -----------------
        # forward move
        # -----------------
        dst_idx = src_idx - BOARD_FILES

        if dst_idx >= 0:

            dst_bit = 1 << dst_idx

            if not (bb.all_occ() & dst_bit):

                dr, dc = bb.index_to_rc(dst_idx)
                captured_piece = 0

                # promotion row
                if row == 1:

                    promo_options = [
                        p for p in set(black_captured)
                        if p not in (WHITE_PAWN, BLACK_PAWN)
                    ]

                    for promo in promo_options:

                        captured_piece = make_temp_move(bb, piece, row, col, dr, dc, promo)

                        if not in_check(bb, False):
                            moves.append((piece, row, col, dr, dc, promo))

                        undo_temp_move(bb, piece, row, col, dr, dc, promo, captured_piece)

                else:

                    captured_piece = make_temp_move(bb, piece, row, col, dr, dc, piece)

                    if not in_check(bb, False):
                        moves.append((piece, row, col, dr, dc, piece))

                    undo_temp_move(bb, piece, row, col, dr, dc, piece, captured_piece)

        # -----------------
        # captures
        # -----------------
        for dc_shift in [-1, 1]:

            dc = col + dc_shift
            dr = row - 1

            if not (0 <= dc < BOARD_FILES and 0 <= dr < BOARD_RANKS):
                continue

            dst_idx = bb.rc_to_index(dr, dc)
            dst_bit = 1 << dst_idx

            if bb.white_occ() & dst_bit:


                if row == 1:

                    promo_options = [
                        p for p in set(black_captured)
                        if p not in (WHITE_PAWN, BLACK_PAWN)
                    ]

                    for promo in promo_options:

                        captured_piece = make_temp_move(bb, piece, row, col, dr, dc, promo)

                        if not in_check(bb, False):
                            moves.append((piece, row, col, dr, dc, promo))

                        undo_temp_move(bb, piece, row, col, dr, dc, promo, captured_piece)

                else:

                    captured_piece = make_temp_move(bb, piece, row, col, dr, dc, piece)

                    if not in_check(bb, False):
                        moves.append((piece, row, col, dr, dc, piece))

                    undo_temp_move(bb, piece, row, col, dr, dc, piece, captured_piece)

    return moves

def get_knight_moves(row, col, piece, bb):

    moves = []

    white_occ = bb.white_occ()
    black_occ = bb.black_occ()

    for dr, dc in KNIGHT_MOVES:

        r = row + dr
        c = col + dc

        if not (0 <= r < BOARD_RANKS and 0 <= c < BOARD_FILES):
            continue

        bit = Bitboards.bit_of(r, c)

        if is_white(piece):
            if white_occ & bit:
                continue
        else:
            if black_occ & bit:
                continue

        captured = make_temp_move(bb, piece, row, col, r, c, piece)

        if not in_check(bb, is_white(piece)):
            moves.append((piece, row, col, r, c, piece))

        undo_temp_move(bb, piece, row, col, r, c, piece, captured)

    return moves

def get_sliding_moves(row, col, piece, directions, bb):

    moves = []

    white_occ = bb.white_occ()
    black_occ = bb.black_occ()

    for dr, dc in directions:

        r = row + dr
        c = col + dc

        while 0 <= r < BOARD_RANKS and 0 <= c < BOARD_FILES:

            bit = Bitboards.bit_of(r, c)

            if is_white(piece):
                if white_occ & bit:
                    break
            else:
                if black_occ & bit:
                    break

            captured = make_temp_move(bb, piece, row, col, r, c, piece)

            if not in_check(bb, is_white(piece)):
                moves.append((piece, row, col, r, c, piece))

            undo_temp_move(bb, piece, row, col, r, c, piece, captured)

            if captured != 0:
                break

            r += dr
            c += dc

    return moves

def get_bishop_moves(row, col, piece, bb):
    diagonals = [(-1,-1),(-1,1),(1,-1),(1,1)]
    return get_sliding_moves(row, col, piece, diagonals, bb)

def get_queen_moves(row, col, piece, bb):
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    return get_sliding_moves(row, col, piece, dirs, bb)

def get_king_moves(row, col, piece, bb):

    moves = []

    white_occ = bb.white_occ()
    black_occ = bb.black_occ()

    for dr, dc in KING_MOVES:

        r = row + dr
        c = col + dc

        if not (0 <= r < BOARD_RANKS and 0 <= c < BOARD_FILES):
            continue

        bit = Bitboards.bit_of(r, c)

        if is_white(piece):
            if white_occ & bit:
                continue
        else:
            if black_occ & bit:
                continue

        captured = make_temp_move(bb, piece, row, col, r, c, piece)

        if not in_check(bb, is_white(piece)):
            moves.append((piece, row, col, r, c, piece))

        undo_temp_move(bb, piece, row, col, r, c, piece, captured)

    return moves