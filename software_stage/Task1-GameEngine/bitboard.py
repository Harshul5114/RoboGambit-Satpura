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
        match piece_id:
            case 1: return self.WP
            case 2: return self.WN
            case 3: return self.WB
            case 4: return self.WQ
            case 5: return self.WK
            case 6: return self.BP
            case 7: return self.BN
            case 8: return self.BB
            case 9: return self.BQ
            case 10: return self.BK
            case _: return 0

    def set_bb(self, piece_id: int, value: int):
        """Set the bitboard for the given piece id."""
        match piece_id:
            case 1: self.WP = value
            case 2: self.WN = value
            case 3: self.WB = value
            case 4: self.WQ = value
            case 5: self.WK = value
            case 6: self.BP = value
            case 7: self.BN = value
            case 8: self.BB = value
            case 9: self.BQ = value
            case 10: self.BK = value
            case _: pass

        

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
    
    



# ----- attack bitboards (precomputed for 6x6) ---------------------------------

KNIGHT_ATTACKS = [0] * BOARD_SQ
KING_ATTACKS = [0] * BOARD_SQ
WHITE_PAWN_ATTACKS = [0]*BOARD_SQ
BLACK_PAWN_ATTACKS = [0]*BOARD_SQ
RAY_MASKS = [[0] * 8 for _ in range(36)]

# Precompute knight and king attack bitboards for each square on 6x6 board
for sq in range(BOARD_SQ):

    r, c = Bitboards.index_to_rc(sq)

    # knight
    attacks = 0
    for dr, dc in [(-2,-1),(-2,1),(2,-1),(2,1),(-1,-2),(-1,2),(1,-2),(1,2)]:
        rr, cc = r+dr, c+dc
        if 0 <= rr < BOARD_RANKS and 0 <= cc < BOARD_FILES:
            attacks |= 1 << Bitboards.rc_to_index(rr,cc)
    KNIGHT_ATTACKS[sq] = attacks

    # king
    attacks = 0
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r+dr, c+dc
            if 0 <= rr < BOARD_RANKS and 0 <= cc < BOARD_FILES:
                attacks |= 1 << Bitboards.rc_to_index(rr,cc)
    KING_ATTACKS[sq] = attacks


# precompute pawn attacks for white and black
for sq in range(BOARD_SQ):

    r,c = Bitboards.index_to_rc(sq)

    # white
    attacks = 0
    for dc in (-1,1):
        rr,cc = r+1, c+dc
        if 0<=rr<BOARD_RANKS and 0<=cc<BOARD_FILES:
            attacks |= 1 << Bitboards.rc_to_index(rr,cc)
    WHITE_PAWN_ATTACKS[sq] = attacks

    # black
    attacks = 0
    for dc in (-1,1):
        rr,cc = r-1, c+dc
        if 0<=rr<BOARD_RANKS and 0<=cc<BOARD_FILES:
            attacks |= 1 << Bitboards.rc_to_index(rr,cc)
    BLACK_PAWN_ATTACKS[sq] = attacks


# precompute ray masks for sliding pieces (bishop, queen)
directions = [
        (1, 0), (-1, 0), (0, 1), (0, -1),   # Orthogonal
        (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal
    ]
for sq in range(36):
    r, c = Bitboards.index_to_rc(sq)
    for i, (dr, dc) in enumerate(directions):
        mask = 0
        curr_r, curr_c = r + dr, c + dc
        while 0 <= curr_r < 6 and 0 <= curr_c < 6:
            mask |= (1 << Bitboards.rc_to_index(curr_r, curr_c))
            curr_r += dr
            curr_c += dc
        RAY_MASKS[sq][i] = mask



def get_ray_attacks(sq, occupancy, direction_idx):
    """
    Returns attacks for a single ray using the 'Shadow' bitmasking trick.
    This replaces 'while' loops with bitwise math.
    """
    ray = RAY_MASKS[sq][direction_idx]
    blockers = ray & occupancy
    if not blockers:
        return ray
    
    # Find the first blocker
    # If direction is positive (N, E, NE, NW), the blocker is the LSB
    # If direction is negative (S, W, SE, SW), the blocker is the MSB
    if direction_idx in [0, 2, 4, 5]: # Positive directions
        first_blocker_sq = Bitboards.lsb(blockers)
    else: # Negative directions
        first_blocker_sq = Bitboards.msb(blockers)
        
    # The shadow is everything behind the first blocker in that ray
    shadow = RAY_MASKS[first_blocker_sq][direction_idx]
    return ray & ~shadow
    