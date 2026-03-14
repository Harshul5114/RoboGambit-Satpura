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
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.15, 0.25, 0.35, 0.35, 0.25, 0.15],
    [0.3, 0.45, 0.6, 0.6, 0.45, 0.3],
    [0.45, 0.6, 0.8, 0.8, 0.6, 0.45],
    [0.6, 0.8, 1.0, 1.0, 0.8, 0.6],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
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
    WHITE_PAWN:   5,  # Highest: Promotion is the #1 goal in 6x6
    WHITE_KNIGHT: 15,  # High: Knights must be central to be effective
    WHITE_BISHOP: 5,   # Medium: Range is slightly wasted on small boards
    WHITE_QUEEN:  5,   # Low: Queen is lethal from anywhere
    WHITE_KING:   5,  # Very High: Position is crucial for safety/checkmate
    
    # Mirror for Black
    BLACK_PAWN:   5,
    BLACK_KNIGHT: 15,
    BLACK_BISHOP: 5,
    BLACK_QUEEN:  5,
    BLACK_KING:   5
}
# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Move generation  
# ---------------------------------------------------------------------------