# bitboard.py
# Reworked bitboard helpers for 6x6 board (works with existing code's square_index mapping).
# Replace your existing bitboard.py with the contents below.
import numpy as np
from typing import Tuple

BOARD_RANKS = 6
BOARD_FILES = 6
BOARD_SQ = BOARD_RANKS * BOARD_FILES  # 36

# Precomputed file masks for 6x6 board
FILE_MASKS = []
for f in range(BOARD_FILES):
    mask = 0
    for r in range(BOARD_RANKS):
        mask |= (1 << (r * BOARD_FILES + f))
    FILE_MASKS.append(mask)

FILE_A = FILE_MASKS[0]
FILE_F = FILE_MASKS[-1]

RANK_MASKS = []
for r in range(BOARD_RANKS):
    mask = 0
    for f in range(BOARD_FILES):
        mask |= (1 << (r * BOARD_FILES + f))
    RANK_MASKS.append(mask)

ALL_ONES = (1 << BOARD_SQ) - 1


class Bitboards:
    def __init__(self):
        """Initialize empty bitboards for all pieces (6x6 board, 36 bits used)."""
        # White pieces
        self.WP = 0
        self.WN = 0
        self.WB = 0
        self.WQ = 0
        self.WK = 0
        # Black pieces
        self.BP = 0
        self.BN = 0
        self.BB = 0
        self.BQ = 0
        self.BK = 0

    # ---- piece accessors -------------------------------------------------
    def get_bb(self, piece_id: int) -> int:
        """Return the bitboard corresponding to piece id (1..10)."""
        if piece_id == 1: return self.WP
        if piece_id == 2: return self.WN
        if piece_id == 3: return self.WB
        if piece_id == 4: return self.WQ
        if piece_id == 5: return self.WK
        if piece_id == 6: return self.BP
        if piece_id == 7: return self.BN
        if piece_id == 8: return self.BB
        if piece_id == 9: return self.BQ
        if piece_id == 10: return self.BK
        return 0

    def set_bb(self, piece_id: int, value: int):
        """Set the bitboard for the given piece id."""
        if piece_id == 1: self.WP = value; return
        if piece_id == 2: self.WN = value; return
        if piece_id == 3: self.WB = value; return
        if piece_id == 4: self.WQ = value; return
        if piece_id == 5: self.WK = value; return
        if piece_id == 6: self.BP = value; return
        if piece_id == 7: self.BN = value; return
        if piece_id == 8: self.BB = value; return
        if piece_id == 9: self.BQ = value; return
        if piece_id == 10: self.BK = value; return

    # ---- occupancy helpers -----------------------------------------------
    def white_occ(self) -> int:
        return self.WP | self.WN | self.WB | self.WQ | self.WK

    def black_occ(self) -> int:
        return self.BP | self.BN | self.BB | self.BQ | self.BK

    def all_occ(self) -> int:
        return self.white_occ() | self.black_occ()

    # ---- bit utilities --------------------------------------------------
    @staticmethod
    def popcount(x: int) -> int:
        return x.bit_count()

    @staticmethod
    def lsb(x: int) -> int:
        """Return index (0..35) of least-significant 1 bit. Assumes x != 0."""
        return (x & -x).bit_length() - 1

    @staticmethod
    def msb(x: int) -> int:
        return x.bit_length() - 1

    @staticmethod
    def index_to_rc(index: int) -> Tuple[int, int]:
        return (index // BOARD_FILES, index % BOARD_FILES)

    @staticmethod
    def rc_to_index(r: int, c: int) -> int:
        return r * BOARD_FILES + c

    @staticmethod
    def bit_of(r: int, c: int) -> int:
        return 1 << (r * BOARD_FILES + c)

    # ---- printing / debug ------------------------------------------------
    def print_bb(self, bb: int):
        """Print bitboard as 6x6 human readable grid (rank 6 -> 1 top to bottom)."""
        for r in range(BOARD_RANKS - 1, -1, -1):
            row = ""
            for c in range(BOARD_FILES):
                sq = r * BOARD_FILES + c
                row += ("1 " if (bb >> sq) & 1 else ". ")
            print(row)
        print()

    def print_board(self):
        """Print the entire board with pieces."""
        piece_map = {
            1: 'P', 2: 'N', 3: 'B', 4: 'Q', 5: 'K',
            6: 'p', 7: 'n', 8: 'b', 9: 'q', 10: 'k'
        }
        for r in range(BOARD_RANKS - 1, -1, -1):
            row = ""
            for c in range(BOARD_FILES):
                sq = r * BOARD_FILES + c
                piece_char = '.'
                for pid in range(1, 11):
                    if (self.get_bb(pid) >> sq) & 1:
                        piece_char = piece_map[pid]
                        break
                row += piece_char + " "
            print(row)
        print()

    # ---- conversion from board array ------------------------------------
    @classmethod
    def from_board_array(cls, board_array: np.ndarray) -> "Bitboards":
        bb = cls()
        for r in range(BOARD_RANKS):
            for c in range(BOARD_FILES):
                piece = int(board_array[r][c])
                if piece != 0:
                    prev = bb.get_bb(piece)
                    bb.set_bb(piece, prev | cls.bit_of(r, c))
        return bb

    def make_move(self, move: tuple, white_captured: list = None, black_captured: list = None):
        """Apply a move tuple (piece, sr, sc, dr, dc, new_piece) to the bitboards."""
        piece, sr, sc, dr, dc, new_piece = move
        src_bit = self.bit_of(sr, sc)
        dst_bit = self.bit_of(dr, dc)

        # remove any piece occupying destination (capture)
        # find which piece occupied destination and clear it
        captured = 0
        for pid in range(1, 11):
            pb = self.get_bb(pid)
            if pb & dst_bit:
                self.set_bb(pid, pb & ~dst_bit)
                captured = pid
                # if(1 <= pid <= 5):
                #     white_captured.append(pid)
                # elif(6 <= pid <= 10):
                #     black_captured.append(pid)

        # remove source piece from its old bb (note piece id at source)
        pb_src = self.get_bb(piece)
        self.set_bb(piece, pb_src & ~src_bit)

        # place the moved piece (new_piece accounts for promotion)
        pb_new = self.get_bb(new_piece)
        self.set_bb(new_piece, pb_new | dst_bit)

        return captured
    
    def get_piece_at(self, r: int, c: int) -> int:
        """Return piece id at given square (0 if empty)."""
        sq = self.rc_to_index(r, c)
        for pid in range(1, 11):
            if (self.get_bb(pid) >> sq) & 1:
                return pid
        return 0



