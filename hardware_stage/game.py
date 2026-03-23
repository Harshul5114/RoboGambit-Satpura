# ==== CONSTANTS ====
import numpy as np

EMPTY = 0

# Piece IDs
WHITE_PAWN   = 1
WHITE_KNIGHT = 2
WHITE_BISHOP = 3
WHITE_QUEEN  = 4
WHITE_KING   = 5
BLACK_PAWN   = 6
BLACK_KNIGHT = 7
BLACK_BISHOP = 8
BLACK_QUEEN  = 9
BLACK_KING   = 10

KNIGHT_MOVES = [(-2,-1),(-2,1),(2,-1),(2,1),(-1,-2),(-1,2),(1,-2),(1,2)]
KING_MOVES = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

WHITE_PIECES = {WHITE_PAWN, WHITE_KNIGHT, WHITE_BISHOP, WHITE_QUEEN, WHITE_KING}
BLACK_PIECES = {BLACK_PAWN, BLACK_KNIGHT, BLACK_BISHOP, BLACK_QUEEN, BLACK_KING}

BOARD_SIZE = 6

PIECE_VALUES = {
    WHITE_PAWN:   100,
    WHITE_KNIGHT: 340,  # Increased: Very strong in small spaces
    WHITE_BISHOP: 315,  # Slightly lower than Knight for 6x6
    WHITE_QUEEN:  950, # Massive: Only piece with orthogonal + diagonal mobility
    WHITE_KING:   20000,
    BLACK_PAWN:   -100,
    BLACK_KNIGHT: -340,
    BLACK_BISHOP: -315,
    BLACK_QUEEN:  -950,
    BLACK_KING:   -20000
}
# Column index → letter
COL_TO_FILE = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F'}
FILE_TO_COL = {v: k for k, v in COL_TO_FILE.items()}

BOARD_RANKS = 6
BOARD_FILES = 6

# PIECE SQUARE TABLES
# (Optional heuristic: add bonuses/penalties for piece positions)

# Base tables in range approx [-1, +1]; white's perspective.
PAWN_BASE = np.array([
    [0.0,  0.0,  0.0,  0.0,  0.0,  0.0 ],
    [0.15, 0.25, 0.35, 0.35, 0.25, 0.15],
    [0.3,  0.45, 0.6,  0.6,  0.45, 0.3 ],
    [0.45, 0.6,  0.8,  0.8,  0.6,  0.45],
    [0.6,  0.8,  1.0,  1.0,  0.8,  0.6 ],
    [0.0,  0.0,  0.0,  0.0,  0.0,  0.0 ]
])

KNIGHT_BASE = np.array([
    [-0.5, -0.4, -0.3, -0.3, -0.4, -0.5],
    [-0.4,  0.2,  0.5,  0.5,  0.2, -0.4],
    [-0.3,  0.5,  1.0,  1.0,  0.5, -0.3],
    [-0.3,  0.5,  1.0,  1.0,  0.5, -0.3],
    [-0.4,  0.2,  0.5,  0.5,  0.2, -0.4],
    [-0.5, -0.4, -0.3, -0.3, -0.4, -0.5]
])

BISHOP_BASE = np.array([
    [-0.3, -0.1,  0.0,  0.0, -0.1, -0.3],
    [-0.1,  0.1,  0.2,  0.2,  0.1, -0.1],
    [ 0.0,  0.2,  0.4,  0.4,  0.2,  0.0],
    [ 0.0,  0.2,  0.4,  0.4,  0.2,  0.0],
    [-0.1,  0.1,  0.2,  0.2,  0.1, -0.1],
    [-0.3, -0.1,  0.0,  0.0, -0.1, -0.3]
])

QUEEN_BASE = np.array([
    [-0.2, -0.1,  0.0,  0.0, -0.1, -0.2],
    [-0.1,  0.1,  0.2,  0.2,  0.1, -0.1],
    [ 0.0,  0.2,  0.3,  0.3,  0.2,  0.0],
    [ 0.0,  0.2,  0.3,  0.3,  0.2,  0.0],
    [-0.1,  0.1,  0.2,  0.2,  0.1, -0.1],
    [-0.2, -0.1,  0.0,  0.0, -0.1, -0.2]
])

# King: opening/middlegame prefer castled/safe (edges), in endgame want central king (we keep simple small bias)


KING_BASE = np.array([
    [ 0.0,  0.5,  0.2,  0.2,  0.5,  0.0],  # Back rank: Safe (Corners/Sides preferred)
    [-0.5, -1.0, -1.0, -1.0, -1.0, -0.5],  # 2nd rank: Exposed
    [-1.0, -2.0, -2.0, -2.0, -2.0, -1.0],  # 3rd rank: Danger zone
    [-1.5, -2.5, -3.0, -3.0, -2.5, -1.5],  # Center: Death trap
    [-2.0, -3.0, -4.0, -4.0, -3.0, -2.0],  # Front: Suicide
    [-3.0, -4.0, -5.0, -5.0, -4.0, -3.0]   # Enemy territory
])


# Multipliers for Piece-Square Tables
# Higher = Piece is more "picky" about which square it stands on.
PST_WEIGHTS = {
    WHITE_PAWN:   10,
    WHITE_KNIGHT: 8,
    WHITE_BISHOP: 5,
    WHITE_QUEEN:  3,
    WHITE_KING:   4,

    BLACK_PAWN:   10,
    BLACK_KNIGHT: 8,
    BLACK_BISHOP: 5,
    BLACK_QUEEN:  3,
    BLACK_KING:   4
}


# ==== BITBOARD ====
# bitboard.py
# Reworked bitboard helpers for 6x6 board (works with existing code's square_index mapping).
# Replace your existing bitboard.py with the contents below.

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

# ==== UTILS ====
import numpy as np

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

# ==== MOVE GENERATION ====


def make_temp_move(bb, piece, sr, sc, dr, dc, new_piece):
    src_idx = bb.rc_to_index(sr, sc)
    dst_idx = bb.rc_to_index(dr, dc)
    src_bit = 1 << src_idx
    dst_bit = 1 << dst_idx

    # 1. Remove moving piece from source
    bb.set_bb(piece, bb.get_bb(piece) & ~src_bit)

    # 2. Identify if there is a capture
    captured_piece = bb.get_piece_at(dr, dc)


    # If there's a piece at the destination, you MUST clear its bit!
    if captured_piece != 0:
        bb.set_bb(captured_piece, bb.get_bb(captured_piece) & ~dst_bit)


    # 3. Add piece at destination (handles regular moves and promotions)
    bb.set_bb(new_piece, bb.get_bb(new_piece) | dst_bit)

    return captured_piece

def undo_temp_move(bb, piece, sr, sc, dr, dc, new_piece, captured_piece):
    src_idx = bb.rc_to_index(sr, sc)
    dst_idx = bb.rc_to_index(dr, dc)
    src_bit = 1 << src_idx
    dst_bit = 1 << dst_idx

    # 1. Remove the piece from where it moved to
    bb.set_bb(new_piece, bb.get_bb(new_piece) & ~dst_bit)
    
    # 2. Put the original piece back at the source
    bb.set_bb(piece, bb.get_bb(piece) | src_bit)

    # 3. If a piece was captured, put it back on the destination square
    if captured_piece != 0:
        bb.set_bb(captured_piece, bb.get_bb(captured_piece) | dst_bit)



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

# ==== ENGINE ====

"""
RoboGambit 2025-26 — Task 1: Autonomous Game Engine
Organised by Aries and Robotics Club, IIT Delhi

Board: 6x6 NumPy array
  - 0  : Empty cell
  - 1  : White Pawn
  - 2  : White Knight
  - 3  : White Bishop
  - 4  : White Queen
  - 5  : White King
  - 6  : Black Pawn
  - 7  : Black Knight
  - 8  : Black Bishop
  - 9  : Black Queen
  - 10 : Black King

Board coordinates:
  - Bpttom-left  = A1  (index [0][0])
  - Columns   = A-F (left to right)
  - Rows      = 6-1 (top to bottom)(from white's perspective)

Move output format:  "<piece_id>:<source_cell>-><target_cell>"
  e.g.  "1:B3->B4"   (White Pawn moves from B3 to B4)
"""

from typing import Optional
import sys 


sys.setrecursionlimit(10**5)

import cProfile
import pstats



# TT Flags
EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2

# The Transposition Table
TT_MAX_SIZE = 200000
TT = {} 

# Zobrist Keys (Initialize these once at the start of your program)
import random
random.seed(42) # Consistent hashing
ZOBRIST_TABLE = {pid: [random.getrandbits(64) for _ in range(36)] for pid in range(1, 11)}
ZOBRIST_SIDE = random.getrandbits(64)

def get_hash(bb: Bitboards, playing_white: bool):
    """Calculates the full hash from scratch. Only used once at the root."""
    h = 0
    for piece_id in range(1, 11):
        pieces = bb.get_bb(piece_id)
        while pieces:
            sq = Bitboards.lsb(pieces)
            h ^= ZOBRIST_TABLE[piece_id][sq]
            pieces &= pieces - 1
    
    if not playing_white:
        h ^= ZOBRIST_SIDE
    return h

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def get_all_moves(playing_white: bool,
                  white_captured: list, black_captured: list,
                  bb: Bitboards):

    moves = []

    if playing_white:
        piece_map = [
            (1, bb.WP, get_pawn_moves),
            (2, bb.WN, get_knight_moves),
            (3, bb.WB, get_bishop_moves),
            (4, bb.WQ, get_queen_moves),
            (5, bb.WK, get_king_moves),
        ]
    else:
        piece_map = [
            (6, bb.BP, get_pawn_moves),
            (7, bb.BN, get_knight_moves),
            (8, bb.BB, get_bishop_moves),
            (9, bb.BQ, get_queen_moves),
            (10, bb.BK, get_king_moves),
        ]

    for piece_id, bitboard, move_func in piece_map:

        pieces = bitboard

        while pieces:
            sq = Bitboards.lsb(pieces)
            r, c = Bitboards.index_to_rc(sq)

            if piece_id in (1, 6):
                moves += move_func(r, c, piece_id,
                                   white_captured, black_captured, bb)
            else:
                moves += move_func(r, c, piece_id, bb)

            pieces &= pieces - 1

    return moves

def score_move(bb, move):

    piece, sr, sc, dr, dc, new_piece = move

    dst_bit = Bitboards.bit_of(dr, dc)

    captured = None
    

    captured = bb.get_piece_at(dr, dc)

    score = 0

    if captured:
        score += 10 * abs(PIECE_VALUES[captured]) - abs(PIECE_VALUES[piece])

    if new_piece != piece:
        score += 200

    return score
# ---------------------------------------------------------------------------
# Board evaluation heuristic  (TODO: tune weights / add positional tables)
# ---------------------------------------------------------------------------

def is_terminal(playing_white, white_captured, black_captured, bb, all_moves):
    if(len(all_moves) == 0 and in_check(bb, playing_white)):
        return 1 #checkmate 
    elif(len(all_moves) == 0 and not in_check(bb, playing_white)):
        return 2 #stalemate 
    else:
        return 0
        
def pst_bonus(piece, row, col):
    """
    Returns the positional bonus for a piece. 
    Positive for White, negative for Black.
    """
    is_w = is_white(piece)
    sign = 1 if is_w else -1
    
    # Get the multiplier weight for this specific piece type
    weight = PST_WEIGHTS[piece]
    
    # Use 5 - row for Black to ensure symmetry (White pushes up, Black pushes down)
    r_idx = row if is_w else (5 - row)
    
    # Select the base table based on piece type
    if piece in (WHITE_PAWN, BLACK_PAWN):
        base_val = PAWN_BASE[r_idx, col]
        
    elif piece in (WHITE_KNIGHT, BLACK_KNIGHT):
        base_val = KNIGHT_BASE[r_idx, col]
        
    elif piece in (WHITE_BISHOP, BLACK_BISHOP):
        base_val = BISHOP_BASE[r_idx, col]
        
    elif piece in (WHITE_QUEEN, BLACK_QUEEN):
        base_val = QUEEN_BASE[r_idx, col]
        
    elif piece in (WHITE_KING, BLACK_KING):
        base_val = KING_BASE[r_idx, col]

            
    else:
        return 0.0

    # Calculate final bonus: (Table Value * Piece Weight)
    # Result is an integer (standard for chess engines)
    return sign * int(base_val * weight)

def evaluate(bb: Bitboards) -> int:
    """
    Evaluates the board state for 6x6 Chess.
    Positive = White advantage, Negative = Black advantage.
    """
    score = 0
    
    # 1. Map piece types to their respective bitboards and PST tables
    # Note: We use the base tables from constants.py
    piece_map = {
        WHITE_PAWN: bb.WP,
        WHITE_KNIGHT: bb.WN,
        WHITE_BISHOP: bb.WB,
        WHITE_QUEEN: bb.WQ,
        WHITE_KING: bb.WK,
        BLACK_PAWN: bb.BP,
        BLACK_KNIGHT: bb.BN,
        BLACK_BISHOP: bb.BB,
        BLACK_QUEEN: bb.BQ,
        BLACK_KING: bb.BK,
    }

    # 2. Determine Game Phase
    # In 6x6, the board is cramped. Endgame starts when few pieces remain.
    # We count bits in the 'all occupancy' bitboard.
    total_pieces = Bitboards.popcount(bb.all_occ())
    is_endgame = total_pieces <= 8  # Threshold for 6x6 board

    # 3. Main Evaluation Loop
    for piece_id, bitboard in piece_map.items():
        if bitboard == 0:
            continue
            
        is_w = is_white(piece_id)
        material_val = PIECE_VALUES[piece_id]
        
        # Iterate over every piece of this type using bitwise operations
        temp_bb = bitboard
        while temp_bb:
            sq = Bitboards.lsb(temp_bb)
            r, c = Bitboards.index_to_rc(sq)
            
            # Add Material Value
            score += material_val
            
            pst_b = pst_bonus(piece_id, r, c)
            
            # Special King Logic: In endgame, King should be central/active.
            # We invert the penalty of the standard KING_BASE.
            if (piece_id == WHITE_KING or piece_id == BLACK_KING) and is_endgame:
                pst_b = -pst_b
            
            score += pst_b
            
            # Clear the Least Significant Bit to move to the next piece
            temp_bb &= temp_bb - 1



    # 4. Global Bonuses
    # Bishop pair is very strong on a 6x6 board because they cover both colors.
    if bin(bb.WB).count('1') >= 2: score += 30
    if bin(bb.BB).count('1') >= 2: score -= 30

    return score
# ---------------------------------------------------------------------------
# Format move string
# ---------------------------------------------------------------------------

def format_move(piece: int, src_row: int, src_col: int,
                dst_row: int, dst_col: int, new_piece: int) -> str:
    """Return move in required format: '<piece_id>:<source_cell>-><target_cell>=<new_piece>'."""
    src_cell = idx_to_cell(src_row, src_col)
    dst_cell = idx_to_cell(dst_row, dst_col)
    return f"{piece}:{src_cell}->{dst_cell}" if piece == new_piece else f"{piece}:{src_cell}->{dst_cell}={new_piece}" 

def store_tt(current_hash, depth, val, alpha_orig, beta_orig):
    """Helper to keep Minimax clean."""
    flag = EXACT
    if val <= alpha_orig:
        flag = UPPERBOUND
    elif val >= beta_orig:
        flag = LOWERBOUND

    if len(TT) >= TT_MAX_SIZE:
        TT.clear()
        
    TT[current_hash] = {'depth': depth, 'value': val, 'flag': flag}
# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def minimax(
             alpha: int,
             beta: int,
             depth: int, 
             playing_white: bool, 
             white_captured: list, 
             black_captured: list, 
             bb: Bitboards, 
             current_hash: int,
             ):
    
    alpha_orig = alpha
    beta_orig = beta

    # -----------------------------------------
    # 1. Transposition Table Lookup
    # -----------------------------------------
    if current_hash in TT:
        entry = TT[current_hash]
        if entry['depth'] >= depth:

            if entry['flag'] == EXACT: return entry['value']
            if entry['flag'] == LOWERBOUND: alpha = max(alpha, entry['value'])
            if entry['flag'] == UPPERBOUND: beta = min(beta, entry['value'])
            if alpha >= beta: return entry['value']

    # -----------------------------------------
    # 2. Leaf Node Evaluaton
    # -----------------------------------------
    if depth == 0:
        return evaluate(bb)

    # -----------------------------------------
    # 3. Generate & Order Moves
    # -----------------------------------------
    moves = get_all_moves(playing_white, white_captured, black_captured, bb)
    moves.sort(key=lambda move: score_move(bb, move), reverse=True)

    # -----------------------------------------
    # 4. Terminal State (Checkmate/Stalemate)
    # -----------------------------------------
    terminal_state = is_terminal(playing_white, white_captured, black_captured, bb, moves)
    if terminal_state == 1:
        return -100000 - depth if playing_white else 100000 + depth
    if terminal_state == 2:
        return 0

    # -----------------------------------------
    # 6. SINGLE SEARCH LOOP (Combined White/Black)
    # -----------------------------------------
    best_eval = float('-inf') if playing_white else float('inf')
    # Point to the correct capture list to use based on whose turn it is
    my_captures = black_captured if playing_white else white_captured

    for move in moves:
        piece, sr, sc, dr, dc, new_piece = move
        src_idx = sr * 6 + sc
        dst_idx = dr * 6 + dc

        # 1. Execute Move first (gets the captured piece ID)
        captured = make_temp_move(bb, *move)

        # 2. Calculate Hash using the 'captured' variable
        # XOR out source, XOR in destination, XOR toggle side
        next_hash = current_hash ^ ZOBRIST_TABLE[piece][src_idx] ^ ZOBRIST_TABLE[new_piece][dst_idx] ^ ZOBRIST_SIDE
        
        # If something was captured, XOR it out of the hash
        if captured:
            next_hash ^= ZOBRIST_TABLE[captured][dst_idx]
            my_captures.append(captured)
        
        # 3. Recurse
        val = minimax(alpha, beta, depth - 1, not playing_white, 
                      white_captured, black_captured, bb, next_hash)
        
        # 4. Undo Move
        if captured: my_captures.pop()
        undo_temp_move(bb, *move, captured)

        # Alpha-Beta Updates
        if playing_white:
            best_eval = max(best_eval, val)
            alpha = max(alpha, val)
        else:
            best_eval = min(best_eval, val)
            beta = min(beta, val)
            
        if beta <= alpha:
            break

    # -----------------------------------------
    # 7. TT Store
    # -----------------------------------------
    store_tt(current_hash, depth, best_eval, alpha_orig, beta_orig)
    return best_eval

# we need a mechanism to take into account stalemate conditions
# right now the only mechanism is checkmate so we need to disallow any moves that result in a check for the player
# doing this would make the possible moves for a state of the board to be empty in the case of a checkmate or stalemate
# then we check if the king is in check and remove it and evaluate the board and if it is not then we evaluate the board as it is

def get_best_move(board: np.ndarray, playing_white: bool = True) -> Optional[str]:
    """
    Given the current board state, return the best move string.

    Parameters
    ----------
    board        : 6×6 NumPy array representing the current game state.
    playing_white: True if the engine is playing as White, False for Black.
   

    Returns
    -------
    Move string in the format '<piece_id>:<src_cell>-><dst_cell>', or
    None if no legal moves are available.
    """
    white_captured = [2, 2, 3, 3, 4, 5]
    black_captured = [7, 7, 8, 8, 9, 10]

    #scan board to find captured pieces
    for r in range(6):
        for c in range(6):
            piece = board[r][c]
            if piece in white_captured:
                white_captured.remove(piece)
            elif piece in black_captured:
                black_captured.remove(piece)

    return _get_best_move(board, playing_white, white_captured, black_captured)


def _get_best_move(board: np.ndarray, playing_white: bool = True, white_captured: list = None, black_captured: list = None) -> Optional[str]:
    
    if white_captured is None:
        white_captured = []

    if black_captured is None:
        black_captured = []


    bb = Bitboards.from_board_array(board)

    # print("Initial Board Evaluation:", evaluate(bb)) #!remove

    # 1. Initialize the hash for the starting position
    current_hash = get_hash(bb, playing_white)

    if playing_white:
        best_value = float('-inf')
    else:
        best_value = float('inf')
        
    best_move = None
    alpha = float('-inf')
    beta = float('inf')

    all_moves = get_all_moves(playing_white, white_captured, black_captured, bb)
    all_moves.sort(key=lambda move: score_move(bb, move), reverse=True)

    is_endgame = Bitboards.popcount(bb.all_occ()) <= 8
    search_depth = 8 if is_endgame else 6   # * idk
    
    for move in all_moves:
        piece, sr, sc, dr, dc, new_piece = move
        
        # 1. Get captured piece BEFORE moving to calculate hash
        captured = bb.get_piece_at(dr, dc)

        # 2. Incremental hash
        src_idx = sr * 6 + sc
        dst_idx = dr * 6 + dc
        next_hash = current_hash ^ ZOBRIST_SIDE ^ ZOBRIST_TABLE[piece][src_idx] ^ ZOBRIST_TABLE[new_piece][dst_idx]
        if captured:
            next_hash ^= ZOBRIST_TABLE[captured][dst_idx]
        
        # 3. Apply move AND update capture lists
        make_temp_move(bb, *move)
        if captured:
            if playing_white: black_captured.append(captured)
            else: white_captured.append(captured)

        # 4. Recurse (Note: Pass depth - 1 because root is ply 1)
        value = minimax(alpha, beta, search_depth, not playing_white, white_captured, black_captured, bb, next_hash)

        # 5. Undo everything in reverse order
        if captured:
            if playing_white: black_captured.pop()
            else: white_captured.pop()
        undo_temp_move(bb, *move, captured)
        
        if (playing_white and value > best_value) or (not playing_white and value < best_value):
            best_value = value
            best_move = move
            
        if playing_white:
            alpha = max(alpha, value)
        else:
            beta = min(beta, value)


    # print("Best Move Evaluation:", best_value) #!remove
    return None if not best_move else format_move(*best_move)

# ---------------------------------------------------------------------------
# Quick smoke-test  
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test Case: White to move
    # Setup: White has a Queen and King, Black has a lone King.
    # White should look for a move that pressures the Black King.
    # pr = cProfile.Profile()
    winning_white_board = np.array(
    [
        [2, 3, 5, 4, 3, 0],
        [1, 1, 0, 1, 1, 1],
        [0, 0, 1, 0, 2, 0],
        [0, 0, 6, 0, 0, 0],
        [6, 6, 0, 6, 6, 6],
        [7, 8, 10, 9, 8, 7]
    ]
)

    print("--- Test Case: Bot Playing Black ---")
    print("Board State:")
    print(winning_white_board)
    
    # We pass playing_white=False
    # The engine will now maximize the evaluation score
    # pr.enable()
    move = get_best_move(winning_white_board, playing_white=False)
    # pr.disable()
    # ps = pstats.Stats(pr).sort_stats('cumulative')
    
    print("\nBest move for Black:", move)

    # ps.print_stats(30)


