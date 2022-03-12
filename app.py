import argparse
import termios
import atexit
import string
import sys

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

def draw_square(square, spacing=3):
    if isinstance(square, BlackSquare):
        sys.stdout.write('\u2588' * spacing)
    elif square.letter is None:
        sys.stdout.write('   ')
    else:
        sys.stdout.write(' %s ' % square.letter)

def draw(squares):
    spacing = 3

    sys.stdout.write('\u250C')
    sys.stdout.write('\u2500' * spacing)

    for c in range(W - 1):
        sys.stdout.write('\u252C')
        sys.stdout.write('\u2500' * spacing)

    sys.stdout.write('\u2510\n')

    for r in range(H - 1):
        for c in range(W):
            sys.stdout.write('\u2502')
            draw_square(squares[r][c], spacing=spacing)

        sys.stdout.write('\u2502\n')

        sys.stdout.write('\u251C')
        sys.stdout.write('\u2500' * spacing)

        for c in range(W - 1):
            sys.stdout.write('\u253C')
            sys.stdout.write('\u2500' * spacing)

        sys.stdout.write('\u2524\n')

    for c in range(W):
        sys.stdout.write('\u2502')
        draw_square(squares[H - 1][c], spacing=spacing)

    sys.stdout.write('\u2502\n')

    sys.stdout.write('\u2514')
    sys.stdout.write('\u2500' * spacing)

    for c in range(W - 1):
        sys.stdout.write('\u2534')
        sys.stdout.write('\u2500' * spacing)

    sys.stdout.write('\u2518')

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

    if pos[d] <= 0:
        pos[1 - d] -= 1
        pos[d] = DIMENSIONS[d] - 1

        if pos[1 - d] <= 0:
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

    draw(squares)
    position_cursor(cursor)

    sys.stdout.flush()

    while True:
        ch = sys.stdin.read(1)

        if ch == '\n':
            direction = 1 - direction

            sys.stdout.write('\x1b[H')
            sys.stdout.write('\x1b[%dB' % (H * 2 + 1))
            sys.stdout.write('Changed direction to %s' % ['DOWN', 'ACROSS'][direction])
            sys.stdout.flush()

            break

        elif ch == 'S':
            save_board(squares)

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
