import pygame
from game import get_all_moves, get_best_move, cell_to_idx, is_terminal
import time

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


def mouse_to_square(pos):

    x,y = pos

    col = (x-40)//CELL
    row = BOARD_SIZE-1 - ((y-40)//CELL)

    return row,col


def draw_board(screen,board,selected,legal,thinking):

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

            piece = board[r][c]

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


def apply_engine_move(board,move):

    if move is None:
        return

    part = move.split(":")[1]

    src = part.split("->")[0]
    dst = part.split("->")[1]

    if "=" in dst:
        dst = dst.split("=")[0]

    sr,sc = cell_to_idx(src)
    dr,dc = cell_to_idx(dst)

    piece = board[sr][sc]

    board[sr][sc] = 0
    board[dr][dc] = piece


def run_ui(board):

    pygame.init()

    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption("Chess Engine UI")

    selected = None
    legal = []

    playing_white = True
    thinking = False

    running = True

    if DEBUG:
        times = []

    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running=False

            # if is_terminal(board,True):
            #     running=False

            if event.type == pygame.MOUSEBUTTONDOWN and not thinking:

                row,col = mouse_to_square(pygame.mouse.get_pos())

                if not (0<=row<6 and 0<=col<6):
                    continue

                if selected is None:

                    piece = board[row][col]

                    if 1<=piece<=5:  # white pieces

                        selected=(row,col)

                        moves = get_all_moves(board,True,[],[])

                        legal=[m for m in moves if m[1]==row and m[2]==col]

                else:
                        
                    moved=False

                    for m in legal:

                        if (m[3],m[4])==(row,col):

                            piece,sr,sc,dr,dc,new_piece=m

                            board[sr][sc]=0
                            board[dr][dc]=new_piece

                            moved=True
                            selected=None
                            legal=[]

                            break

                    if moved:
                        playing_white=False
                        thinking=True
                    else:
                        selected=None
                        legal=[]

        draw_board(screen,board,selected,legal,thinking)
        pygame.display.flip()

        # BOT MOVE
        if thinking:

            pygame.display.flip()

            st = time.time()
            move = get_best_move(board,playing_white=False)
            et = time.time()

            if DEBUG:
                print("Engine move:",move)
                print("Time taken: {:.2f} seconds".format(et-st))
                times.append(et-st)

                        

            apply_engine_move(board,move)

            thinking=False
            playing_white=True

        #if terminal, print message and wait a bit before closing
        #print who won also based on value returned by is_terminal() (1:checkmate, 2:stalemate, else 0)
        #print who won based on playing_white variable (if True, player is white, else black)
        # if is_terminal(board,True):
        #     result = is_terminal(board,True)

        #     if result == 1:
        #         if playing_white:
        #             msg = "Checkmate! Black wins."
        #         else:
        #             msg = "Checkmate! White wins."
        #     elif result == 2:
        #         msg = "Stalemate! It's a draw."
        #     else:
        #         msg = "Game over!"

        #     print(msg)

        #     pygame.time.wait(3000)

    if DEBUG:
        print("Game over!")
        print("Total moves played:",len(times))
        print("Average engine move time: {:.2f} seconds".format(sum(times)/len(times) if times else 0))

    pygame.quit()