from bauhaus import Encoding, proposition, constraint
from bauhaus.utils import count_solutions, likelihood

E = Encoding()


@proposition(E)
class Win:
    def __repr__(self):
        return "Win"


@proposition(E)
class Tile:
    def __init__(self, row, col, tile_type):
        self.row = row
        self.col = col
        self.type = tile_type

    def __repr__(self) -> str:
        return f"{self.type}({self.row}, {self.col})"


@proposition(E)
class Water:
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __repr__(self) -> str:
        return f"W({self.row}, {self.col})"


@proposition(E)
class Link:
    def __init__(self, row, col, direction):
        self.row = row
        self.col = col
        self.direction = direction

    def __repr__(self) -> str:
        return f"L{self.direction}({self.row}, {self.col})"
