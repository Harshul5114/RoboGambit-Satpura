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

WHITE_PIECES = {WHITE_PAWN, WHITE_KNIGHT, WHITE_BISHOP, WHITE_QUEEN, WHITE_KING}
BLACK_PIECES = {BLACK_PAWN, BLACK_KNIGHT, BLACK_BISHOP, BLACK_QUEEN, BLACK_KING}

BOARD_SIZE = 6

PIECE_VALUES = {
    WHITE_PAWN:   100,
    WHITE_KNIGHT: 300,
    WHITE_BISHOP: 320,
    WHITE_QUEEN:  900,
    WHITE_KING:  20000,
    BLACK_PAWN:  -100,
    BLACK_KNIGHT:-300,
    BLACK_BISHOP:-320,
    BLACK_QUEEN: -900,
    BLACK_KING: -20000,
}
# Column index → letter
COL_TO_FILE = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F'}
FILE_TO_COL = {v: k for k, v in COL_TO_FILE.items()}



# PIECE SQUARE TABLES
# (Optional heuristic: add bonuses/penalties for piece positions)

# Base tables in range approx [-1, +1]; white's perspective.
PAWN_BASE = np.array([
    [ 0.0,  0.0,  0.0,  0.0,  0.0,  0.0],  # rank 1 (home)
    [ 0.1,  0.1,  0.1,  0.1,  0.1,  0.1],
    [ 0.2,  0.2,  0.25, 0.25, 0.2,  0.2],
    [ 0.3,  0.3,  0.35, 0.35, 0.3,  0.3],
    [ 0.4,  0.4,  0.4,  0.4,  0.4,  0.4],
    [ 0.0,  0.0,  0.0,  0.0,  0.0,  0.0]   # last rank (promotion rank) — special handled by move logic
])

KNIGHT_BASE = np.array([
    [-0.6, -0.4, -0.2, -0.2, -0.4, -0.6],
    [-0.4,  0.2,  0.4,  0.4,  0.2, -0.4],
    [-0.2,  0.4,  0.6,  0.6,  0.4, -0.2],
    [-0.2,  0.4,  0.6,  0.6,  0.4, -0.2],
    [-0.4,  0.2,  0.4,  0.4,  0.2, -0.4],
    [-0.6, -0.4, -0.2, -0.2, -0.4, -0.6]
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
    [-0.4, -0.2,  0.0,  0.0, -0.2, -0.4],
    [-0.2, -0.1,  0.1,  0.1, -0.1, -0.2],
    [ 0.0,  0.1,  0.2,  0.2,  0.1,  0.0],
    [ 0.0,  0.1,  0.2,  0.2,  0.1,  0.0],
    [-0.2, -0.1,  0.1,  0.1, -0.1, -0.2],
    [-0.4, -0.2,  0.0,  0.0, -0.2, -0.4]
])

FACTORS = {
    'pawn':  0.10,   # pawn bonus ≈ piece_value * 0.10 * base_value  -> up to ~10 pts
    'knight':0.08,   # knight ≈ 300 * 0.08 * base -> up to ~24 pts
    'bishop':0.08,   # bishop ≈ 320 * 0.08 -> up to ~25 pts
    'queen': 0.05,   # queen ≈ 900 * 0.05 -> up to ~45 pts (but base is small so actual smaller)
    'king':  0.03    # king safety tiny
}
# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Move generation  
# ---------------------------------------------------------------------------