import argparse
import termios
import atexit
import string
import sys

HL = '\u2500'
VL = '\u2502'

TL = '\u250c'
TM = '\u252c'
TR = '\u2510'

ML = '\u251c'
MM = '\u253c'
MR = '\u2524'

BL = '\u2514'
BM = '\u2534'
BR = '\u2518'

# (TL, TM, TR, ML, MR, BL, BM, BR, self)

SIDE_TL = 0
SIDE_TH = 0.1
SIDE_LV = 0.2
SIDE_TM = 1
SIDE_TR = 2
SIDE_ML = 3
SIDE_MH = 3.1
SIDE_MV = 3.2
SIDE_MM = 4
SIDE_MR = 5
SIDE_BL = 6
SIDE_BH = 6.1
SIDE_RV = 6.2
SIDE_BM = 7
SIDE_BR = 8

TO_BOLD = {
    SIDE_TH: (HL, '\u2501'),
    SIDE_MH: (HL, '\u2501', '\u2501', '\u2501'),
    SIDE_BH: (HL, '\u2501'),
    SIDE_LV: (VL, '\u2503'),
    SIDE_MV: (VL, '\u2503', '\u2503', '\u2503'),
    SIDE_RV: (VL, '\u2503'),
    SIDE_TL: (TL, '\u250f'),
    SIDE_TM: (TM, '\u2531', '\u2522', '\u2533'),
    SIDE_TR: (TR, '\u2513'),
    SIDE_ML: (ML, '\u2521', '\u2522', '\u2520'),
    SIDE_MM: (MM, '\u2543', '\u2534', '\u2544', '\u2545', '\u2542', None, None, '\u2546', None, '\u2542'),
    SIDE_MR: (MR, '\u2529', '\u252a', '\u2528'),
    SIDE_BL: (BL, '\u2517'),
    SIDE_BM: (BM, '\u2539', '\u253a', '\u2537'),
    SIDE_BR: (BR, '\u251b')
}

H = 21
W = 21
DIMENSIONS = [H, W]

old_term_attrs = termios.tcgetattr(sys.stdin.fileno())
tcsetattr_flags = termios.TCSAFLUSH

if hasattr(termios, 'TCSASOFT'):
    tcsetattr_flags |= termios.TCSASOFT

def restore_term_attrs():
    global old_term_attrs, tcsetattr_flags
    termios.tcsetattr(sys.stdin.fileno(), tcsetattr_flags, old_term_attrs)
    sys.stdout.flush()

new_term_attrs = old_term_attrs[:]
new_term_attrs[3] &= ~termios.ICANON
new_term_attrs[3] &= ~termios.ECHO

atexit.register(restore_term_attrs)
termios.tcsetattr(sys.stdin.fileno(), tcsetattr_flags, new_term_attrs)

log_file = open('log.txt', 'w')

def close_log_file():
    global log_file
    log_file.close()

atexit.register(close_log_file)

def log(*args):
    print(*args, file=log_file)
    log_file.flush()

def is_part_of_word(squares, r, c, pos, d):
    p = [min(pos[0], r), min(pos[1], c)]
    sq_pos = [r, c]

    while p[d] < DIMENSIONS[d] and p[d] < sq_pos[d]:
        if isinstance(squares[p[0]][p[1]], BlackSquare):
            return False

        p[d] += 1

    log(r, c, pos, d, p[d] == sq_pos[d])
    return p[d] == sq_pos[d]

def side_for(squares, r, c, pos, d, side):
    idx = num = 0
    cr, cc = int(side) // 3, int(side) % 3

    for i in range(max(cr - 1, 0), min(cr + 1, 2)):
        for j in range(max(cc - 1, 0), min(cc + 1, 2)):
            idx |= is_part_of_word(squares, r + i - cr, c + j - cc, pos, d) << num
            num += 1

    log(r, c, side, idx)
    log('')
    return TO_BOLD[side][idx]

def draw_square(square, spacing=3):
    if isinstance(square, BlackSquare):
        sys.stdout.write('\u2588' * spacing)
    elif square.letter is None:
        sys.stdout.write('   ')
    else:
        sys.stdout.write(' %s ' % square.letter)

def draw_top(squares, pos, d, spacing=3):
    sys.stdout.write(side_for(squares, 0, 0, pos, d, SIDE_TL))
    sys.stdout.write(side_for(squares, 0, 0, pos, d, SIDE_TH) * spacing)

    for c in range(1, W):
        sys.stdout.write(side_for(squares, 0, c, pos, d, SIDE_TM))
        sys.stdout.write(side_for(squares, 0, c, pos, d, SIDE_TH) * spacing)

    sys.stdout.write(side_for(squares, 0, W, pos, d, SIDE_TR) + '\n')

def draw_row(r, squares, pos, d, spacing=3):
    left = SIDE_ML
    middle = SIDE_MM
    right = SIDE_MR
    line = SIDE_MH
    addend = '\n'

    if r == H - 1:
        left = SIDE_BL
        middle = SIDE_BM
        right = SIDE_BR
        line = SIDE_BH
        addend = ''

    sys.stdout.write(side_for(squares, r, 0, pos, d, SIDE_LV))
    draw_square(squares[r][0], spacing)

    for c in range(1, W):
        sys.stdout.write(side_for(squares, r, c, pos, d, SIDE_MV))
        draw_square(squares[r][c], spacing)

    sys.stdout.write(side_for(squares, r, W, pos, d, SIDE_RV) + '\n')

    sys.stdout.write(side_for(squares, r + 1, 0, pos, d, left))
    sys.stdout.write(side_for(squares, r + 1, 0, pos, d, line) * spacing)

    for c in range(1, W):
        sys.stdout.write(side_for(squares, r + 1, c, pos, d, middle))
        sys.stdout.write(side_for(squares, r + 1, c, pos, d, line) * spacing)

    sys.stdout.write(side_for(squares, r + 1, W, pos, d, right))
    sys.stdout.write(addend)

def draw(squares, pos, d):
    spacing = 3

    draw_top(squares, pos, d, spacing)

    for r in range(H):
        draw_row(r, squares, pos, d, spacing)

    sys.stdout.write('\x1b[0J')

    sys.stdout.write('\x1b[%dA' % (H * 2))
    sys.stdout.write('\x1b[%dD' % (W * 4))


def position_cursor(pos):
    sys.stdout.write('\x1b[%dB' % ((pos[0] * 2) + 1))
    sys.stdout.write('\x1b[%dC' % ((pos[1] * 4) + 1))


def increment_cursor(pos, d):
    pos[d] += 1

    if pos[d] >= DIMENSIONS[d]:
        pos[1 - d] += 1
        pos[d] = 0

        if pos[1 - d] >= DIMENSIONS[1 - d]:
            pos[1 - d] = 0
            d = 1 - d

    return pos, d


def decrement_cursor(pos, d):
    pos[d] -= 1

    if pos[d] < 0:
        pos[1 - d] -= 1
        pos[d] = DIMENSIONS[d] - 1

        if pos[1 - d] < 0:
            pos[1 - d] = DIMENSIONS[1 - d] - 1
            d = 1 - d

    return pos, d


class Square(object):
    pass

class BlackSquare(Square):
    pass

class LetterSquare(Square):
    def __init__(self, letter=None):
        self.letter = letter


def save_board(squares, default_fname='board.txt'):
    sys.stdout.write('\x1b[H')
    sys.stdout.write('\x1b[%dB' % (H * 2 + 1))
    sys.stdout.write('Enter saved filename (default %s): ' % default_fname)
    sys.stdout.flush()

    fname = ''
    ch = sys.stdin.read(1)

    while ch != '\n' and ch in string.printable:
        sys.stdout.write(ch)
        sys.stdout.flush()

        fname += ch
        ch = sys.stdin.read(1)

    if len(fname) == 0:
        fname = default_fname

    with open(fname, 'w') as f:
        for r in range(H):
            for c in range(W):
                sq = squares[r][c]

                if isinstance(sq, BlackSquare):
                    f.write('b,%d,%d,\n' % (r, c))

                elif sq.letter is None:
                    f.write('l,%d,%d,\n' % (r, c))

                else:
                    f.write('l,%d,%d,%s\n' % (r, c, sq.letter))

    sys.stdout.write('\x1b[1K')
    sys.stdout.write('\x1b[0G')
    sys.stdout.write('Successfully saved board to %s' % fname)
    sys.stdout.flush()


def load_board(fname, squares):
    with open(fname, 'r') as f:
        for line in f:
            comps = line.strip('\n').split(',')

            if len(comps) == 4:
                r = int(comps[1])
                c = int(comps[2])

                if comps[0] == 'b':
                    squares[r][c] = BlackSquare()

                elif comps[0] == 'l':
                    letter = None

                    if len(comps[3]) > 0:
                        letter = comps[3]

                    squares[r][c] = LetterSquare(letter)


parser = argparse.ArgumentParser('CrossMaker')
parser.add_argument('-l', dest='saved_file', type=str, help='Saved file to load from')
args = parser.parse_args()

squares = [[LetterSquare() for _ in range(W)] for _ in range(H)]

if args.saved_file is not None:
    load_board(args.saved_file, squares)

cursor = [0, 0]
direction = 1

sys.stdout.write('\x1b[2J')
sys.stdout.flush()

while True:
    sys.stdout.write('\x1b[H')
    sys.stdout.flush()

    draw(squares, cursor, direction)
    position_cursor(cursor)

    sys.stdout.flush()

    while True:
        ch = sys.stdin.read(1)

        if ch == '\n':
            direction = 1 - direction
            break

        elif ch == 'S':
            save_board(squares)
            break

        elif ch == 'R':
            n = calc_word_len(squares, cursor, direction)
            break

        elif ch == 'X':
            r, c = cursor

            if isinstance(squares[r][c], BlackSquare):
                squares[r][c] = LetterSquare()
                squares[H - 1 - r][W - 1 - c] = LetterSquare()
            else:
                squares[r][c] = BlackSquare()
                squares[H - 1 - r][W - 1 - c] = BlackSquare()

            cursor, direction = increment_cursor(cursor, direction)
            break

        elif ch in string.printable:
            r, c = cursor

            if not isinstance(squares[r][c], LetterSquare):
                squares[r][c] = LetterSquare()

            squares[r][c].letter = ch.upper()
            cursor, direction = increment_cursor(cursor, direction)
            break

        elif ch == '\x7f':
            cursor, direction = decrement_cursor(cursor, direction)
            r, c = cursor

            if isinstance(squares[r][c], BlackSquare):
                squares[H - 1 - r][W - 1 - c] = LetterSquare()

            squares[r][c] = LetterSquare()
            break

        elif ch == '\x1b':
            if sys.stdin.read(1) == '[':
                ch = sys.stdin.read(1)

                if ch == 'A':
                    cursor[0] = max(0, cursor[0] - 1)
                    break

                elif ch == 'B':
                    cursor[0] = min(H - 1, cursor[0] + 1)
                    break

                elif ch == 'C':
                    cursor[1] = min(W - 1, cursor[1] + 1)
                    break

                elif ch == 'D':
                    cursor[1] = max(0, cursor[1] - 1)
                    break

        else:
            print(ch.encode('ascii'))
