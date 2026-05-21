import pygame as pg
import random

# ---------- SETTINGS ----------
COLS = 10          # how many columns (left-right)
ROWS = 20          # how many rows (top-down)
CELL = 35         # size of each cell in pixels
W = COLS * CELL    # window width  (pixels)
H = ROWS * CELL    # window height (pixels)
FPS = 240

# ---------- SHAPES (4x4 grids) ----------
# 1 = block exists, 0 = empty
SHAPES = {
    "I": [[0,0,0,0],
          [1,1,1,1],
          [0,0,0,0],
          [0,0,0,0]],

    "O": [[0,0,0,0],
          [0,1,1,0],
          [0,1,1,0],
          [0,0,0,0]],

    "T": [[0,0,0,0],
          [1,1,1,0],
          [0,1,0,0],
          [0,0,0,0]],

    "S": [[0,0,0,0],
          [0,1,1,0],
          [1,1,0,0],
          [0,0,0,0]],

    "Z": [[0,0,0,0],
          [1,1,0,0],
          [0,1,1,0],
          [0,0,0,0]],

    "J": [[0,0,0,0],
          [1,1,1,0],
          [0,0,1,0],
          [0,0,0,0]],

    "L": [[0,0,0,0],
          [1,1,1,0],
          [1,0,0,0],
          [0,0,0,0]],
}

# ---------- ROTATE (clockwise) ----------
def rotate(mat):
    # Example idea:
    # 1) flip the rows upside down: mat[::-1]
    # 2) zip(*...) reads columns -> makes a rotated shape
    flipped = mat[::-1]
    columns = zip(*flipped)             # creates tuples
    return [list(row) for row in columns]  # convert tuples -> lists


# ---------- NEW PIECE ----------
def new_piece():
    kind = random.choice(list(SHAPES.keys()))
    mat = [row[:] for row in SHAPES[kind]]  # copy the 4x4 grid
    return {
        "kind": kind,
        "mat": mat,
        "x": COLS // 2 - 2,   # start near the middle
        "y": 0
    }


# ---------- NEW GAME ----------
def new_game():
    game = {}

    # board is ROWS x COLS full of 0 (empty)
    game["board"] = [[0 for _ in range(COLS)] for _ in range(ROWS)]

    game["cur"] = new_piece()
    game["score"] = 0
    game["game_over"] = False

    game["drop_time"] = 0
    game["drop_speed"] = 500  # milliseconds between automatic drops

    return game


# ---------- CHECK IF PIECE FITS ----------
def fits(board, mat, x, y):
    # Go through every cell in the 4x4 mat
    for r in range(4):
        for c in range(4):
            if mat[r][c] == 0:
                continue  # skip empty parts of the piece

            new_x = x + c
            new_y = y + r

            # check walls / floor / ceiling
            if new_x < 0 or new_x >= COLS or new_y < 0 or new_y >= ROWS:
                return False

            # check if board already has a block there
            if board[new_y][new_x] == 1:
                return False

    return True


# ---------- CLEAR FULL LINES ----------
def clear_lines(game):
    board = game["board"]
    new_board = []
    cleared = 0

    for row in board:
        if all(cell == 1 for cell in row):
            cleared += 1
        else:
            new_board.append(row)

    # add empty rows at the top to keep board size same
    while len(new_board) < ROWS:
        new_board.insert(0, [0] * COLS)

    game["board"] = new_board

    # simple scoring
    if cleared > 0:
        game["score"] += cleared * 100


# ---------- LOCK PIECE INTO BOARD ----------
def lock_piece(game):
    board = game["board"]
    piece = game["cur"]

    for r in range(4):
        for c in range(4):
            if piece["mat"][r][c] == 1:
                board[piece["y"] + r][piece["x"] + c] = 1

    clear_lines(game)

    # spawn new piece
    game["cur"] = new_piece()

    # if new piece does not fit, game over
    p = game["cur"]
    if not fits(game["board"], p["mat"], p["x"], p["y"]):
        game["game_over"] = True


# ---------- MOVE LEFT / RIGHT ----------
def move(game, dx):
    piece = game["cur"]
    if fits(game["board"], piece["mat"], piece["x"] + dx, piece["y"]):
        piece["x"] += dx


# ---------- ROTATE CURRENT PIECE ----------
def rotate_cur(game):
    piece = game["cur"]
    new_mat = rotate(piece["mat"])

    # try rotate in same place
    if fits(game["board"], new_mat, piece["x"], piece["y"]):
        piece["mat"] = new_mat
        return

    # tiny wall-kick: try shift left/right if rotation hits wall
    for kick in (-1, 1, -2, 2):
        if fits(game["board"], new_mat, piece["x"] + kick, piece["y"]):
            piece["x"] += kick
            piece["mat"] = new_mat
            return


# ---------- SOFT DROP (down 1) ----------
def soft_drop(game):
    piece = game["cur"]
    if fits(game["board"], piece["mat"], piece["x"], piece["y"] + 1):
        piece["y"] += 1
    else:
        lock_piece(game)


# ---------- HARD DROP (down until it can't) ----------
def hard_drop(game):
    piece = game["cur"]
    while fits(game["board"], piece["mat"], piece["x"], piece["y"] + 1):
        piece["y"] += 1
    lock_piece(game)


# ---------- DRAW ONE CELL ----------
def draw_cell(screen, x, y, filled):
    rect = pg.Rect(x * CELL, y * CELL, CELL, CELL)
    pg.draw.rect(screen, (40, 40, 40), rect, 1)  # grid outline

    if filled:
        inner = rect.inflate(-2, -2)
        pg.draw.rect(screen, (200, 200, 200), inner)


# ---------- MAIN LOOP ----------
def main():   
    pg.init()
    screen = pg.display.set_mode((W, H))
    pg.display.set_caption("Beginner Tetris")
    clock = pg.time.Clock()
    font = pg.font.SysFont(None, 28)
    
    pg.joystick.init()
    
    if pg.joystick.get_count()> 0:
        joystick = pg.joystick.Joystick(0)
        joystick.init()
        print('Connected:', joystick.get_name())
    else:
        joystick = None

    print("Axes:", joystick.get_numaxes())
    print("Buttons:", joystick.get_numbuttons())
    print("Hats:", joystick.get_numhats())

    game = new_game()

    running = True
    zr_pressed = False

    while running:
        now = pg.time.get_ticks()

        # -------- EVENTS (keyboard) --------
        for event in pg.event.get():
            
            if joystick and event.type == pg.JOYHATMOTION:####################
                print("HAT:", event.value)

            if joystick and event.type == pg.JOYBUTTONDOWN:
                print("BUTTON:", event.button)

            if joystick and event.type == pg.JOYAXISMOTION:
                if abs(event.value) > 0.5:
                    print("AXIS:", event.axis, "VALUE:", round(event.value, 2))   ###################### 
            
            
            if event.type == pg.QUIT:
                running = False
            
            if event.type == pg.KEYDOWN and not game["game_over"]:
                if event.key == pg.K_a or event.key == pg.K_a:
                    move(game, -1)
                elif event.key == pg.K_d or event.key == pg.K_d:
                    move(game, 1)
                elif event.key == pg.K_w or event.key == pg.K_w:
                    rotate_cur(game)
                elif event.key == pg.K_s or event.key == pg.K_s:
                    soft_drop(game)
                elif event.key == pg.K_SPACE:
                    hard_drop(game)

            #----------sensibility of the d pad--------    
            if joystick and event.type == pg.JOYAXISMOTION and not game["game_over"]:
               if event.axis == 5:
                    if event.value > 0.8 and not zr_pressed:
                        hard_drop(game)
                        zr_pressed = True
                    elif event.value < 0.2:
                        zr_pressed = False

            # -------- CONTROLLER: D-PAD --------
            if joystick and event.type == pg.JOYBUTTONDOWN and not game["game_over"]:               
                if event.button == 13:
                    move(game, -1)
                elif event.button == 14:
                    move(game, 1)
                if event.button == 12:
                    soft_drop(game)

            # -------- CONTROLLER: BUTTON ROTATE --------

            if joystick and event.type == pg.JOYBUTTONDOWN and not game["game_over"]:
                if event.button == 1:
                    rotate_cur(game)

        # -------- AUTO DROP --------   
        if not game["game_over"]:
            if now - game["drop_time"] >= game["drop_speed"]:
                game["drop_time"] = now
                soft_drop(game)

        # -------- DRAW --------
        screen.fill((10, 10, 10))

        # draw board (locked blocks)
        for y in range(ROWS):
            for x in range(COLS):
                draw_cell(screen, x, y, game["board"][y][x] == 1)

        # draw current falling piece (not locked yet)
        if not game["game_over"]:
            piece = game["cur"]
            for r in range(4):
                for c in range(4):
                    if piece["mat"][r][c] == 1:
                        draw_cell(screen, piece["x"] + c, piece["y"] + r, True)

        # score text
        score_text = font.render(f"Score: {game['score']}", True, (220, 220, 220))
        screen.blit(score_text, (10, 10))

        # game over text
        if game["game_over"]:
            over_text = font.render("GAME OVER (close window)", True, (255, 80, 80))
            screen.blit(over_text, (10, 40))

        pg.display.flip()
        clock.tick(FPS)
    
    pg.quit()


# IMPORTANT: this starts the game when you run the file
if __name__ == "__main__":
    main()