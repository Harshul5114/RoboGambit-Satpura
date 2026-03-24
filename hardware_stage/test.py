from main_2 import *

test_board = np.zeros((6, 6), dtype=int)
test_board[0][0] = 1  # White piece at A1
execute_turn("1:A1->B2", test_board)