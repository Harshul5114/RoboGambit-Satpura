import pygame
from game import get_all_moves, get_best_move, cell_to_idx, is_terminal
import time
import numpy as np
from bitboard import *
from utils import *
BOARD_SIZE = 6
CELL = 100

WIDTH = BOARD_SIZE * CELL + 80
HEIGHT = BOARD_SIZE * CELL + 80

LIGHT = (240,217,181)
DARK = (181,136,99)

SELECT = (50,50,200)
MOVE = (50,200,50)

TEXT = (20,20,20)

PIECE_UNICODE = {
    1:"♙",2:"♘",3:"♗",4:"♕",5:"♔",
    6:"♟",7:"♞",8:"♝",9:"♛",10:"♚"
}

DEBUG = True # to print engine moves in console and other stuff maybe in future


white_captured = []
black_captured = []

def print_board(board : np.ndarray):
    piece_map = {
            1: 'P', 2: 'N', 3: 'B', 4: 'Q', 5: 'K',
            6: 'p', 7: 'n', 8: 'b', 9: 'q', 10: 'k'
        }
    for r in range(BOARD_SIZE-1, -1, -1):
        row = ""
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            row += (piece_map[piece] + " ") if piece != 0 else ". "
        print(row)

def mouse_to_square(pos):

    x,y = pos

    col = (x-40)//CELL
    row = BOARD_SIZE-1 - ((y-40)//CELL)

    return row,col

def bb_to_board(bb: Bitboards):
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)

    for pid in range(1, 11):
        bb_piece = bb.get_bb(pid)

        while bb_piece:
            sq = Bitboards.lsb(bb_piece)
            r, c = Bitboards.index_to_rc(sq)
            board[r][c] = pid
            bb_piece &= bb_piece - 1

    return board

def draw_board(screen,board,selected,legal,thinking, playing_white=True):

    dboard = np.copy(board)

    # if not playing_white:
    #     dboard = np.flip(dboard)

    screen.fill((30,30,30))

    piece_font = pygame.font.SysFont("Segoe UI Symbol", 60)
    coord_font = pygame.font.SysFont("Arial",18)
    msg_font = pygame.font.SysFont("Arial",28)

    # squares
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):

            color = LIGHT if (r+c)%2==0 else DARK

            rect = pygame.Rect(
                40 + c*CELL,
                40 + (BOARD_SIZE-1-r)*CELL,
                CELL,
                CELL
            )

            pygame.draw.rect(screen,color,rect)

            if selected == (r,c):
                pygame.draw.rect(screen,SELECT,rect,4)

            for m in legal:
                if (m[3],m[4])==(r,c):

                    cx = 40 + c*CELL + CELL//2
                    cy = 40 + (BOARD_SIZE-1-r)*CELL + CELL//2

                    pygame.draw.circle(screen,MOVE,(cx,cy),10)

            piece = dboard[r][c]

            if piece!=0:

                symbol = PIECE_UNICODE[piece]

                text = piece_font.render(symbol,True,(0,0,0))

                cx = 40 + c*CELL + CELL//2
                cy = 40 + (BOARD_SIZE-1-r)*CELL + CELL//2

                screen.blit(text,text.get_rect(center=(cx,cy)))

    # column letters
    for c in range(BOARD_SIZE):

        letter = chr(ord('A')+c)

        text = coord_font.render(letter,True,(255,255,255))

        x = 40 + c*CELL + CELL//2
        screen.blit(text,text.get_rect(center=(x,20)))

    # row numbers
    for r in range(BOARD_SIZE):

        num = str(r+1)

        text = coord_font.render(num,True,(255,255,255))

        y = 40 + (BOARD_SIZE-1-r)*CELL + CELL//2
        screen.blit(text,text.get_rect(center=(20,y)))

    if thinking:

        msg = msg_font.render("Bot thinking...",True,(200,50,50))

        screen.blit(msg,(WIDTH//2-100,HEIGHT-35))


def apply_engine_move(move, bb: Bitboards):
    """
    Apply engine move using ONLY bitboards.
    Returns captured piece.
    """

    if move is None:
        return None

    part = move.split(":")[1]

    src = part.split("->")[0]
    dst = part.split("->")[1]

    sr, sc = cell_to_idx(src)

    if "=" in dst:
        dst_cell, promo = dst.split("=")
        dr, dc = cell_to_idx(dst_cell)
        new_piece = int(promo)
    else:
        dr, dc = cell_to_idx(dst)
        new_piece = None

    # determine piece from bitboards
    src_bit = Bitboards.bit_of(sr, sc)

    piece = None
    for pid in range(1, 11):
        if bb.get_bb(pid) & src_bit:
            piece = pid
            break

    if piece is None:
        raise RuntimeError("No piece found at source square")

    if new_piece is None:
        new_piece = piece

    move_tuple = (piece, sr, sc, dr, dc, new_piece)

    # apply move and return captured piece
    captured = bb.make_move(move_tuple)

    return captured
    



def choose_promotion(screen, playing_white, white_captured=None, black_captured=None):

    font = pygame.font.SysFont(None, 20)

    while True:

        for event in pygame.event.get():

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_1:
                    if playing_white and 2 in white_captured:
                        return 2   # knight
                    elif not playing_white and 7 in black_captured:
                        return 7   # knight
                        

                elif event.key == pygame.K_2:
                    if playing_white and 3 in white_captured:
                        return 3   # bishop
                    elif not playing_white and 8 in black_captured:
                        return 8   # bishop 
                elif event.key == pygame.K_3:
                    if playing_white and 4 in white_captured:
                        return 4   # queen
                    elif not playing_white and 9 in black_captured:
                        return 9   # queen

        screen.fill((30,30,30))

        text = font.render(
            "Pawn Promotion: 1=Knight 2=Bishop 3=Queen",
            True,
            (255,255,255)
        )

        screen.blit(text,(80,300))

        pygame.display.flip()




def run_ui(board, playing_white=True):

    bb = Bitboards.from_board_array(board)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption("Chess Engine UI")

    selected = None
    legal = []
    thinking = False
    running = True

    if DEBUG:
        times = []

    while running:

        board = bb_to_board(bb)   # ALWAYS rebuild board from bitboards

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and not thinking:

                row,col = mouse_to_square(pygame.mouse.get_pos())

                if not (0<=row<6 and 0<=col<6):
                    continue

                if selected is None:

                    piece = board[row][col]

                    if 1 <= piece <= 5:

                        selected = (row,col)

                        moves = get_all_moves(True, white_captured, black_captured, bb)

                        legal = []
                        seen_targets = set()

                        for m in moves:
                            if m[1]==row and m[2]==col:

                                target=(m[3],m[4])

                                if target not in seen_targets:
                                    legal.append(m)
                                    seen_targets.add(target)

                else:

                    moved = False

                    for m in legal:

                        if (m[3],m[4])==(row,col):

                            piece,sr,sc,dr,dc,new_piece = m

                            if new_piece != piece:
                                chosen = None
                                while chosen is None:
                                    chosen = choose_promotion(screen, playing_white, white_captured, black_captured)
                                new_piece = chosen

                                m = (piece,sr,sc,dr,dc,new_piece)

                            captured = bb.make_move(m)

                            if captured:
                                if captured in [6,7,8,9,10]:
                                    black_captured.append(captured)
                                else:
                                    white_captured.append(captured)

                            moved = True
                            selected = None
                            legal = []
                            break

                    if moved:
                        playing_white = False
                        thinking = True
                    else:
                        selected = None
                        legal = []

        board = bb_to_board(bb)

        draw_board(screen, board, selected, legal, thinking, playing_white)
        pygame.display.flip()

        if thinking:

            pygame.display.flip()

            board = bb_to_board(bb)

            st = time.time()

            move = get_best_move(
                board,
                playing_white,
            )

            et = time.time()

            if DEBUG:
                print("Engine move:", move)
                print("Time taken: {:.2f} seconds".format(et-st))
                times.append(et-st)

            captured = apply_engine_move(move, bb)

            if captured:
                if captured in [1,2,3,4,5]:
                    white_captured.append(captured)
                else:
                    black_captured.append(captured)

            thinking = False
            playing_white = True

            # print(white_captured, black_captured)

            # board = bb_to_board(bb)

            # print_board(board)
            # print("--------------------------------")
            # bb.print_board()

    if DEBUG:
        print("Game over!")
        print("Total moves played:",len(times))
        print("Average engine move time: {:.2f}".format(sum(times)/len(times) if times else 0))

    pygame.quit()

def run_auto_play(board, delay=0.5):
    """Makes the bot play against itself."""
    bb = Bitboards.from_board_array(board)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess Bot Auto-Play")

    playing_white = True
    running = True
    
    # Track captures for the promotion rule
    white_captured = []
    black_captured = []

    times = []

    while running:
        # 1. Update Board for UI
        current_board_array = bb_to_board(bb)
        
        # 2. Check for Terminal State
        # We generate moves to see if the game is over
        # 3. Draw the current state
        draw_board(screen, current_board_array, None, [], True, playing_white)
        pygame.display.flip()

        print("Current player:", "White" if playing_white else "Black")
        moves = get_all_moves(playing_white, white_captured, black_captured, bb)
        if not moves:
            print("Game Over!")
            if in_check(bb, playing_white):
                print(f"{'Black' if playing_white else 'White'} wins by Checkmate!")
            else:
                print("Draw by Stalemate!")
            
            time.sleep(7)
            break


        # 4. Handle Pygame Events (to allow closing the window)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                return

        # 5. Engine Turn
        # NOTE: Make sure get_best_move can accept bb, white_captured, and black_captured
        s = time.time()
        move_str = get_best_move(
            current_board_array, 
            playing_white,
        )
        e = time.time()
        times.append(e - s)

        if move_str:
            # Apply the move and update capture lists
            print(f"White move: {move_str}" if playing_white else f"Black move: {move_str}")
            captured = apply_engine_move(move_str, bb)
            if captured:
                if 1 <= captured <= 5: # White piece captured
                    white_captured.append(captured)
                else: # Black piece captured
                    black_captured.append(captured)
            
            playing_white = not playing_white
            time.sleep(delay) # Pause so humans can follow
        else:
            print("No moves returned by engine.")
            
            break
    
    print("final board:")
    print_board(current_board_array)
    print("last player:", "White" if playing_white else "Black")
    print("Total moves played:", len(times))
    print("Average engine move time: {:.2f} seconds".format(sum(times)/len(times) if times else 0))
    pygame.quit()