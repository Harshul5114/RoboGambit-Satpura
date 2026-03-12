import numpy as np
from utils import *
from constants import *
from bitboard import *

def make_temp_move(bb, piece, src_idx, dst_idx, new_piece):
    src_bit = 1 << src_idx
    dst_bit = 1 << dst_idx

    # remove piece from source
    bb.set_bb(piece, bb.get_bb(piece) & ~src_bit)

    # capture if needed
    for pid in range(1, 11):
        pb = bb.get_bb(pid)
        if pb & dst_bit:
            bb.set_bb(pid, pb & ~dst_bit)

    # add piece at destination
    bb.set_bb(new_piece, bb.get_bb(new_piece) | dst_bit)


def undo_temp_move(bb, piece, src_idx, dst_idx, captured_piece, new_piece):
    src_bit = 1 << src_idx
    dst_bit = 1 << dst_idx

    bb.set_bb(new_piece, bb.get_bb(new_piece) & ~dst_bit)
    bb.set_bb(piece, bb.get_bb(piece) | src_bit)

    if captured_piece != 0:
        bb.set_bb(captured_piece, bb.get_bb(captured_piece) | dst_bit)


def get_pawn_moves(board, row, col, piece, white_captured, black_captured, bb):

    moves = []
    src_idx = bb.rc_to_index(row, col)

    if is_white(piece):

        dst_idx = src_idx + BOARD_FILES

        if dst_idx < BOARD_SQ:

            dst_bit = 1 << dst_idx

            if not (bb.all_occ() & dst_bit):

                dr, dc = bb.index_to_rc(dst_idx)

                captured_piece = 0

                new_piece = piece

                if row == BOARD_RANKS - 2 and white_captured:

                    for promo in set(white_captured):

                        make_temp_move(bb, piece, src_idx, dst_idx, promo)

                        if not in_check(bb, True):

                            moves.append((piece, row, col, dr, dc, promo))

                        undo_temp_move(bb, piece, src_idx, dst_idx, captured_piece, promo)

                else:

                    make_temp_move(bb, piece, src_idx, dst_idx, piece)

                    if not in_check(bb, True):

                        moves.append((piece, row, col, dr, dc, piece))

                    undo_temp_move(bb, piece, src_idx, dst_idx, captured_piece, piece)

        for dc_shift in [-1, 1]:

            if 0 <= col + dc_shift < BOARD_FILES:

                dr = row + 1
                dc = col + dc_shift

                dst_idx = bb.rc_to_index(dr, dc)
                dst_bit = 1 << dst_idx

                if bb.black_occ() & dst_bit:

                    captured_piece = board[dr][dc]

                    make_temp_move(bb, piece, src_idx, dst_idx, piece)

                    if not in_check(bb, True):

                        moves.append((piece, row, col, dr, dc, piece))

                    undo_temp_move(bb, piece, src_idx, dst_idx, captured_piece, piece)

    else:

        dst_idx = src_idx - BOARD_FILES

        if dst_idx >= 0:

            dst_bit = 1 << dst_idx

            if not (bb.all_occ() & dst_bit):

                dr, dc = bb.index_to_rc(dst_idx)

                captured_piece = 0

                make_temp_move(bb, piece, src_idx, dst_idx, piece)

                if not in_check(bb, False):

                    moves.append((piece, row, col, dr, dc, piece))

                undo_temp_move(bb, piece, src_idx, dst_idx, captured_piece, piece)

        for dc_shift in [-1, 1]:

            if 0 <= col + dc_shift < BOARD_FILES:

                dr = row - 1
                dc = col + dc_shift

                dst_idx = bb.rc_to_index(dr, dc)
                dst_bit = 1 << dst_idx

                if bb.white_occ() & dst_bit:

                    captured_piece = board[dr][dc]

                    make_temp_move(bb, piece, src_idx, dst_idx, piece)

                    if not in_check(bb, False):

                        moves.append((piece, row, col, dr, dc, piece))

                    undo_temp_move(bb, piece, src_idx, dst_idx, captured_piece, piece)

    return moves

def get_knight_moves(board, row, col, piece, bb):

    moves = []

    src_idx = bb.rc_to_index(row, col)

    for dr, dc in KNIGHT_MOVES:

        r = row + dr
        c = col + dc

        if not in_bounds(board, r, c):
            continue

        dst_idx = bb.rc_to_index(r, c)
        dst_bit = 1 << dst_idx

        if same_side(piece, board[r][c]):
            continue

        captured = board[r][c]

        make_temp_move(bb, piece, src_idx, dst_idx, piece)

        if not in_check(bb, is_white(piece)):

            moves.append((piece, row, col, r, c, piece))

        undo_temp_move(bb, piece, src_idx, dst_idx, captured, piece)

    return moves

def get_sliding_moves(board, row, col, piece, directions, bb):

    moves = []

    src_idx = bb.rc_to_index(row, col)

    for dr, dc in directions:

        r = row + dr
        c = col + dc

        while in_bounds(board, r, c):

            if same_side(piece, board[r][c]):
                break

            dst_idx = bb.rc_to_index(r, c)

            captured = board[r][c]

            make_temp_move(bb, piece, src_idx, dst_idx, piece)

            if not in_check(bb, is_white(piece)):

                moves.append((piece, row, col, r, c, piece))

            undo_temp_move(bb, piece, src_idx, dst_idx, captured, piece)

            if captured != 0:
                break

            r += dr
            c += dc

    return moves

def get_bishop_moves(board: np.ndarray, row: int, col: int, piece: int):
    diagonals=[(-1,-1),(-1,1),(1,-1),(1,1)]
    return get_sliding_moves(board,row,col,piece,diagonals,bb)

def get_queen_moves(board: np.ndarray, row: int, col: int, piece: int):
    all_dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    return get_sliding_moves(board, row, col, piece, all_dirs, bb)

def get_king_moves(board, row, col, piece, bb):

    moves = []

    src_idx = bb.rc_to_index(row, col)

    for dr, dc in KING_MOVES:

        r = row + dr
        c = col + dc

        if not in_bounds(board, r, c):
            continue

        if same_side(piece, board[r][c]):
            continue

        dst_idx = bb.rc_to_index(r, c)

        captured = board[r][c]

        make_temp_move(bb, piece, src_idx, dst_idx, piece)

        if not in_check(bb, is_white(piece)):

            moves.append((piece, row, col, r, c, piece))

        undo_temp_move(bb, piece, src_idx, dst_idx, captured, piece)

    return moves