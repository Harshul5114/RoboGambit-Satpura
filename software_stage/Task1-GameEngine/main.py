import numpy as np
from ui import run_ui
# Board: 6x6 NumPy array
#   - 0  : Empty cell
#   - 1  : White Pawn
#   - 2  : White Knight
#   - 3  : White Bishop
#   - 4  : White Queen
#   - 5  : White King
#   - 6  : Black Pawn
#   - 7  : Black Knight
#   - 8  : Black Bishop
#   - 9  : Black Queen
#   - 10 : Black King
board = np.array([
    [0, 0, 0, 0, 0, 5],
    [0, 0, 0, 0, 4, 0],
    [0, 0, 1, 0, 0, 0],
    [0, 0, 0, 7, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [10, 0, 0, 0, 0, 0]
])

start_board = np.array(
    [
        [2, 3, 5, 4, 3, 2],
        [1, 1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [6, 6, 6, 6, 6, 6],
        [7, 8, 10, 9, 8, 7]
    ]
)




run_ui(start_board, playing_white= True)