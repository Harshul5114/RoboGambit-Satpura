import numpy as np
from utils import *
from constants import *
from bitboard import *

def get_pawn_moves(board, row: int, col: int, piece: int,
                   white_captured: list, black_captured: list, bb: Bitboards|None = None):
   
    moves = []

    # helper lambdas
    idx = bb.rc_to_index(row, col)
    src_bit = 1 << idx

    if is_white(piece):
        # single push target index
        dst_idx = idx + BOARD_FILES
        if 0 <= dst_idx < BOARD_SQ:
            dst_bit = 1 << dst_idx
            if not (bb.all_occ() & dst_bit):
                # update board array temporarily to test in_check exactly as original
                # need to update the check function to take bitbooards instead of board
                board[row][col] = 0
                dr, dc = bb.index_to_rc(dst_idx)
                captured_at_dst = board[dr][dc]
                board[dr][dc] = piece
                if not in_check(board, True):
                    # promotion?
                    if row == len(board) - 2 and len(white_captured) != 0:
                        for new_piece in set(white_captured):
                            if new_piece != piece:
                                moves.append((piece, row, col, dr, dc, new_piece))
                    elif row != len(board) - 2:
                        moves.append((piece, row, col, dr, dc, piece))
                # restore
                board[row][col] = piece
                board[dr][dc] = captured_at_dst

        # capture right (r+1, c+1)
        if (col + 1) < BOARD_FILES:
            dr, dc = row + 1, col + 1
            dst_idx = bb.rc_to_index(dr, dc)
            dst_bit = 1 << dst_idx
            if 0 <= dr < BOARD_RANKS and (bb.black_occ() & dst_bit):
                captured = board[dr][dc]
                board[row][col] = 0
                board[dr][dc] = piece
                if not in_check(board, True):
                    if row == len(board) - 2 and len(white_captured) != 0:
                        for new_piece in set(white_captured):
                            if new_piece != piece:
                                moves.append((piece, row, col, dr, dc, new_piece))
                    elif row != len(board) - 2:
                        moves.append((piece, row, col, dr, dc, piece))
                board[row][col] = piece
                board[dr][dc] = captured

        # capture left (r+1, c-1)
        if (col - 1) >= 0:
            dr, dc = row + 1, col - 1
            dst_idx = bb.rc_to_index(dr, dc)
            dst_bit = 1 << dst_idx
            if 0 <= dr < BOARD_RANKS and (bb.black_occ() & dst_bit):
                captured = board[dr][dc]
                board[row][col] = 0
                board[dr][dc] = piece
                if not in_check(board, True):
                    if row == len(board) - 2 and len(white_captured) != 0:
                        for new_piece in set(white_captured):
                            if new_piece != piece:
                                moves.append((piece, row, col, dr, dc, new_piece))
                    elif row != len(board) - 2:
                        moves.append((piece, row, col, dr, dc, piece))
                board[row][col] = piece
                board[dr][dc] = captured

    else:
        # black pawn
        dst_idx = idx - BOARD_FILES
        if 0 <= dst_idx < BOARD_SQ:
            dst_bit = 1 << dst_idx
            if not (bb.all_occ() & dst_bit):
                board[row][col] = 0
                dr, dc = bb.index_to_rc(dst_idx)
                captured_at_dst = board[dr][dc]
                board[dr][dc] = piece
                if not in_check(board, False):
                    if row == 1 and len(black_captured) != 0:
                        for new_piece in set(black_captured):
                            if new_piece != piece:
                                moves.append((piece, row, col, dr, dc, new_piece))
                    elif row != 1:
                        moves.append((piece, row, col, dr, dc, piece))
                board[row][col] = piece
                board[dr][dc] = captured_at_dst

        # capture right (r-1, c+1)
        if (col + 1) < BOARD_FILES:
            dr, dc = row - 1, col + 1
            dst_idx = bb.rc_to_index(dr, dc)
            dst_bit = 1 << dst_idx
            if 0 <= dr < BOARD_RANKS and (bb.white_occ() & dst_bit):
                captured = board[dr][dc]
                board[row][col] = 0
                board[dr][dc] = piece
                if not in_check(board, False):
                    if row == 1 and len(black_captured) != 0:
                        for new_piece in set(black_captured):
                            if new_piece != piece:
                                moves.append((piece, row, col, dr, dc, new_piece))
                    elif row != 1:
                        moves.append((piece, row, col, dr, dc, piece))
                board[row][col] = piece
                board[dr][dc] = captured

        # capture left (r-1, c-1)
        if (col - 1) >= 0:
            dr, dc = row - 1, col - 1
            dst_idx = bb.rc_to_index(dr, dc)
            dst_bit = 1 << dst_idx
            if 0 <= dr < BOARD_RANKS and (bb.white_occ() & dst_bit):
                captured = board[dr][dc]
                board[row][col] = 0
                board[dr][dc] = piece
                if not in_check(board, False):
                    if row == 1 and len(black_captured) != 0:
                        for new_piece in set(black_captured):
                            if new_piece != piece:
                                moves.append((piece, row, col, dr, dc, new_piece))
                    elif row != 1:
                        moves.append((piece, row, col, dr, dc, piece))
                board[row][col] = piece
                board[dr][dc] = captured

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