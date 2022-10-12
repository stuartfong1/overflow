from bauhaus import Encoding, proposition, constraint
from bauhaus.utils import count_solutions, likelihood

E = Encoding()


@proposition(E)
class Win:
    def __repr__(self):
        return "Win"


@proposition(E)
class Tile:
    """
    Proposition representing a type of tile.
    self.row - The row that the tile is in.
    self.col - The column that the tile is in.
    self.tile_type - The type of tile. Can be one of S, C, B, M, O
    """

    def __init__(self, row, col, tile_type):
        self.row = row
        self.col = col
        self.type = tile_type

    def __repr__(self) -> str:
        return f"{self.type}({self.row}, {self.col})"


@proposition(E)
class Water:
    """
    Proposition representing a tile that contains water.
    self.row - The row that the tile is in.
    self.col - The column that the tile is in.
    """

    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __repr__(self) -> str:
        return f"W({self.row}, {self.col})"


@proposition(E)
class Link:
    """
    Proposition representing a link between two tiles.
    self.row - The row that the tile is in.
    self.col - The column that the tile is in.
    self.direction - The direction of the link. Can be one of U, D, L, R
    """

    def __init__(self, row, col, direction):
        self.row = row
        self.col = col
        self.direction = direction

    def __repr__(self) -> str:
        return f"L{self.direction}({self.row}, {self.col})"


level_layout = [
    [" L-MMML-L"],
    ["-LLLLL-LL"],
    ["LL-L++++L"],
    ["L+L--L+L-"],
    ["LL-LLLL-L"],
]

n_row = len(level_layout)
n_col = len(level_layout[0][0])

straight = [[Tile(r, c, 'S') for c in range(n_col)] for r in range(n_row)]
curved = [[Tile(r, c, 'C') for c in range(n_col)] for r in range(n_row)]
bridge = [[Tile(r, c, 'B') for c in range(n_col)] for r in range(n_row)]
moat = [[Tile(r, c, 'M') for c in range(n_col)] for r in range(n_row)]
ocean = [[Tile(r, c, 'O') for c in range(n_col)] for r in range(n_row)]
water = [[Water(r, c) for c in range(n_col)] for r in range(n_row)]
link_up = [[Link(r, c, 'U') for c in range(n_col)] for r in range(n_row)]
link_down = [[Link(r, c, 'D') for c in range(n_col)] for r in range(n_row)]
link_left = [[Link(r, c, 'L') for c in range(n_col)] for r in range(n_row)]
link_right = [[Link(r, c, 'R') for c in range(n_col)] for r in range(n_row)]

win = Win()
