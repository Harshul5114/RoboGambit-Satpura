import numpy as np


class Bitboards:
    def __init__(self):
        """Initialize empty bitboards for all pieces."""

        #white pieces 
        self.WP = 0
        self.WN = 0
        self.WB = 0
        self.WQ = 0
        self.WK = 0
        #black pieces

        self.BP = 0
        self.BN = 0
        self.BB = 0
        self.BQ = 0
        self.BK = 0

        self.piece_map = {
            1: self.WP,
            2: self.WN,
            3: self.WB,
            4: self.WQ,
            5: self.WK,
            6: self.BP,
            7: self.BN,
            8: self.BB,
            9: self.BQ,
            10: self.BK
        }

    def print_bb(self, bb):
        """Print a bitboard as a 6x6 grid."""

        for r in range(5,-1,-1):
            row = ""
            for c in range(6):
                sq = r*6 + c
                if bb & (1<<sq):
                    row += "1 "
                else:
                    row += ". "
            print(row)


def board_to_bitboards(board: np.ndarray) -> Bitboards:
    """Convert a board array into piece bitboards."""

    bb = Bitboards()

    for r in range(6):
        for c in range(6):

            sq = square_index(r, c)
            bit = 1 << sq

            piece = board[r][c]

            if piece != 0:
                bb.piece_map[int(piece)] |= bit

    return bb


def white_occ(bb: Bitboards):
    """Return all occupied squares by white."""
    return bb.WP | bb.WN | bb.WB | bb.WQ | bb.WK

def black_occ(bb: Bitboards):
    """Return all occupied squares by black."""
    return bb.BP | bb.BN | bb.BB | bb.BQ | bb.BK

def all_occ(bb: Bitboards):
    """Return all occupied squares."""
    return white_occ(bb) | black_occ(bb)

def square_index(row: int, col: int) -> int:
    """Map (row, col) to a linear square index."""
    return row * 6 + col

def update_bitboards(bb: Bitboards, move: tuple):
    """Apply a move update to the bitboards."""

    piece, sr, sc, dr, dc, new_piece = move

    src = 1 << square_index(sr, sc)
    dst = 1 << square_index(dr, dc)

    # remove piece from source
    bb.piece_map[piece] &= ~src

    # add piece to destination
    bb.piece_map[new_piece] |= dst
