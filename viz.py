from sty import fg, bg, rs
import random


class Path:
    """
    Class representing a path in a level.
    self.type - The type of tile. Can be one of S, C, B, M, O, blank
    self.link - Whether the tile links up, down, left, right
    self.water - Whether or not the tile contains water.
    self.row - The row that the tile is in.
    self.col - The column that the tile is in.
    """
    def __init__(self, row, col) -> None:
        self.type = "blank"
        self.link = [False, False, False, False]  # [U, D, L, R]
        self.water = False
        self.row = row
        self.col = col


def convert_solution(sol, level_layout):
    """
    Convert the dictionary output from the SAT solver
    into an easier-to-use list.
    sol - A solution to the level.
    level_layout - The layout of the level.
    """
    n_row = len(level_layout)
    n_col = len(level_layout[0][0])
    link_map = {'U': 0, 'D': 1, 'L': 2, 'R': 3}

    level = [[Path(r, c) for c in range(n_col)] for r in range(n_row)]
    for k, v in sol.items():
        prop = getattr(k, 'prop', None)
        if v and prop == 'tile':
            level[k.row][k.col].type = k.tile_type
        elif prop == 'water':
            level[k.row][k.col].water = v
        elif prop == 'link':
            level[k.row][k.col].link[link_map[k.direction]] = v

    return level

def viz_level(level):
    n_row = len(level)
    n_col = len(level[0])

    # Get character to be printed
    for r in range(n_row):
        for c in range(n_col):
            path = level[r][c]
            char = ' '

            # Straight tile
            if path.type == 'S':
                if path.link == [False, False, True, True]:
                    char = '━'
                elif path.link == [True, True, False, False]:
                    char = '┃'
                else:
                    char = random.choice("━┃")

            # Curved tile
            elif path.type == 'C':  
                if path.link == [False, True, False, True]:
                    char = '┏'
                elif path.link == [False, True, True, False]:
                    char = '┓'
                elif path.link == [True, False, False, True]:
                    char = '┗'
                elif path.link == [True, False, True, False]:
                    char = '┛'
                else:
                    char = random.choice("┏┓┗┛")

            # Bridge tile
            elif path.type == 'B':
                char = '╋'

            # Moat tile
            elif path.type == 'M':
                char = '#'

            # Ocean tile
            elif path.type == 'O':
                if path.link == [True, False, False, False]:
                    char = 'U'
                elif path.link == [False, True, False, False]:
                    char = '∩'
                elif path.link == [False, False, True, False]:
                    char = '⊂'
                elif path.link == [False, False, False, True]:
                    char = '⊃'
                else:
                    char = random.choice("U∩⊂⊃")

            # Color the tiles that contain water
            if path.water:
                print(bg.blue + fg.white + char + rs.bg + rs.fg, end='')
            else:
                print(fg.white + char + rs.fg, end='')
        print()
