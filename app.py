from helper import *
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

def draw_square(square, highlighted, spacing=3):
    if isinstance(square, BlackSquare):
        sys.stdout.write('\u2588' * spacing)
    else:
        if highlighted:
            sys.stdout.write('\x1b[1;31m')

        if square.letter is None:
            sys.stdout.write('   ')
        else:
            sys.stdout.write(' %s ' % square.letter)

        if highlighted:
            sys.stdout.write('\x1b[0m')

def draw_top(squares, pos, d, spacing=3):
    sys.stdout.write(TL)
    sys.stdout.write(HL * spacing)

    for c in range(W - 1):
        sys.stdout.write(TM)
        sys.stdout.write(HL * spacing)

    sys.stdout.write(TR + '\n')

def draw_row(r, squares, curr_word, pos, d, spacing=3):
    left = ML
    middle = MM
    right = MR + '\n'

    if r == H - 1:
        left = BL
        middle = BM
        right = BR

    for c in range(W):
        sys.stdout.write(VL)
        draw_square(squares[r][c], [r, c] in curr_word, spacing)

    sys.stdout.write(VL + '\n')

    sys.stdout.write(left)
    sys.stdout.write(HL * spacing)

    for c in range(W - 1):
        sys.stdout.write(middle)
        sys.stdout.write(HL * spacing)

    sys.stdout.write(right)

def curr_word_indices(squares, pos, d):
    idxs = []
    p = pos[:]

    while p[d] >= 0 and not isinstance(squares[p[0]][p[1]], BlackSquare):
        idxs.insert(0, p[:])
        p[d] -= 1

    p = pos[:]
    p[d] += 1

    while p[d] < DIMENSIONS[d] and not isinstance(squares[p[0]][p[1]], BlackSquare):
        idxs.append(p[:])
        p[d] += 1

    return idxs

def draw(squares, pos, d):
    spacing = 3
    curr_word = curr_word_indices(squares, pos, d)

    draw_top(squares, pos, d, spacing)

    for r in range(H):
        draw_row(r, squares, curr_word, pos, d, spacing)

    sys.stdout.write('\x1b[0J')


def display_recommendations(recs):
    sys.stdout.write('\x1b[H')
    sys.stdout.write('\x1b[%dB' % 1)
    sys.stdout.write('\x1b[%dC' % (W * 4 + 3))

    for rec in recs:
        sys.stdout.write(rec)
        sys.stdout.write('\x1b[%dD' % len(rec))
        sys.stdout.write('\x1b[1B')


def position_cursor(pos):
    sys.stdout.write('\x1b[H')
    sys.stdout.write('\x1b[%dB' % ((pos[0] * 2) + 1))
    sys.stdout.write('\x1b[%dC' % ((pos[1] * 4) + 2))


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
recs = []

sys.stdout.write('\x1b[2J')
sys.stdout.flush()

while True:
    sys.stdout.write('\x1b[H')
    sys.stdout.flush()

    draw(squares, cursor, direction)
    display_recommendations(recs)
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
            curr_word = curr_word_indices(squares, cursor, direction)
            constraints = []

            for i, ix in enumerate(curr_word):
                sq = squares[ix[0]][ix[1]]

                if sq.letter is not None:
                    constraints.append((i, sq.letter))

            recs = get_matches(constraints, len(curr_word))
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
