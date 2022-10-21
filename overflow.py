from bauhaus import Encoding, proposition, constraint, print_theory
from bauhaus.utils import count_solutions, likelihood
from nnf import dsharp

E = Encoding()
F = Encoding()
G = Encoding()


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


@proposition(F)
class Length:
    """
    Proposition representing the length of a path.
    self.number: The number that the proposition represents
    """

    def __init__(self, number):
        self.number = number

    def __repr__(self) -> str:
        return f"len {self.number}"


# - = straight
# + = bridge
# L = curved
# M = moat
# O = ocean
level_layout = [
    [" L-MMML-L"],
    ["-LLLLL-LL"],
    ["LL-L++++L"],
    ["L+L--L+L-"],
    ["LL-LLLL-L"],
    ["     O   "]
]

n_row = len(level_layout)
n_col = len(level_layout[0][0])

# Propositions
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

length = [None] + [Length(i + 1) for i in range(n_row * n_col)]

# Constraints


def theory():
    # Each level has a certain layout of tiles
    # Each tile can only link in a certain way
    for r, row in enumerate(level_layout):
        for c, tile in enumerate(row[0]):
            # Straight tile
            if tile == '-':
                E.add_constraint(straight[r][c])
                if (r == 0 and c == 0) or (r == n_row - 1 and c == 0) or (r == 0 and c == n_col - 1) or (r == n_row - 1 and c == n_col - 1):  # Corners
                    E.add_constraint(~water[r][c])
                elif c == 0 or c == n_col - 1:   # Left & right side
                    E.add_constraint(water[r][c] >> (
                        ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])
                    ))
                elif r == n_row - 1 or r == 0:  # Top and bottom
                    E.add_constraint(water[r][c] >> (
                        ( ~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & link_right[r][c] & water[r][c-1] & water[r][c+1])
                    ))
                else:
                    E.add_constraint(water[r][c] >> (
                        ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])  # Up & down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] &  link_right[r][c] & water[r][c-1] & water[r][c+1])  # Left & right
                    ))
            # Curved tile
            elif tile == 'L':
                E.add_constraint(curved[r][c])
                if (r == 0 or r == n_row - 1 or c == 0 or c == n_col - 1):  # Edges

                    # Corners
                    if (r == 0 and c == 0):  # Top left corner
                        E.add_constraint(water[r][c] >> (
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r+1][c] & water[r][c+1])  # Down & right
                        ))
                    elif (r == 0 and c == n_col - 1):  # Top right corner
                        E.add_constraint(water[r][c] >> (
                            ( ~link_up[r][c] & link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r+1][c] & water[r][c-1])  # Down & left
                        ))
                    elif (r == n_row - 1 and c == 0):  # Bottom left corner
                        E.add_constraint(water[r][c] >> (
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r-1][c] & water[r][c+1])  # Up & right
                        ))
                    elif (r == n_row - 1 and c == n_col - 1):  # Bottom right corner
                        E.add_constraint(water[r][c] >> (
                            ( link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r][c-1])  # Up & left
                        ))

                    # Sides (w/o corners)
                    elif (r == 0):  # Top wall
                        E.add_constraint(water[r][c] >> (
                            ( ~link_up[r][c] & link_down[r][c] &  ~link_left[r][c] & link_right[r][c] & water[r+1][c] & water[r][c+1])  # Down & right
                            | ( ~link_up[r][c] & link_down[r][c] & link_left[r][c] &  ~link_right[r][c] & water[r+1][c] & water[r][c-1])  # Down & left
                        ))
                    elif (r == n_row - 1):  # Bottom wall
                        E.add_constraint(water[r][c] >> (
                            ( link_up[r][c] & ~link_down[r][c] &  ~link_left[r][c] & link_right[r][c] & water[r-1][c] & water[r][c+1])  # Up & right
                            | ( link_up[r][c] & ~link_down[r][c] & link_left[r][c] &  ~link_right[r][c] & water[r-1][c] & water[r][c-1])  # Up & left
                        ))
                    elif (c == 0):  # Left wall
                        E.add_constraint(water[r][c] >> (
                            ( ~link_up[r][c] & link_down[r][c] &  ~link_left[r][c] & link_right[r][c] & water[r+1][c] & water[r][c+1])  # Down & right
                            | ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r-1][c] & water[r][c+1])  # Up & right
                        ))
                    elif (c == n_col - 1):  # Right wall
                        E.add_constraint(water[r][c] >> (
                            ( ~link_up[r][c] & link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r+1][c] & water[r][c-1])  # Down & left
                            | ( link_up[r][c] & ~link_down[r][c] & link_left[r][c] &  ~link_right[r][c] & water[r-1][c] & water[r][c-1])  # Up & left
                        ))
                else:
                    E.add_constraint(water[r][c] >> (
                        ( link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r][c-1])  # Up & left
                        | ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r-1][c] & water[r][c+1])  # Up & right
                        | (~link_up[r][c] &  link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r+1][c] & water[r][c-1])  # Down & left
                        | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r+1][c] & water[r][c+1])  # Down & right
                    ))
            # Bridge tile
            elif tile == '+':
                E.add_constraint(bridge[r][c])
                if (r == 0 and c == 0) or (r == n_row - 1 and c == 0) or (r == 0 and c == n_col - 1) or (r == n_row - 1 and c == n_col - 1):  # Corners
                    E.add_constraint(~water[r][c])
                elif (r == 0 or r == n_row - 1):
                    E.add_constraint(water[r][c] >> (
                        ( ~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & link_right[r][c] & water[r][c-1] & water[r][c+1])  # Left & right
                    ))
                elif (c == 0 or c == n_col - 1):
                    E.add_constraint(water[r][c] >> (
                        ( link_up[r][c] & link_down[r][c] &  ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])  # Down & up
                    ))                
                else:
                    E.add_constraint(water[r][c] >> (
                        ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])  # Up & down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] &  link_right[r][c] & water[r][c-1] & water[r][c+1])  # Left & right
                        | ( link_up[r][c] &  link_down[r][c] &  link_left[r][c] &  link_right[r][c] & water[r-1][c] & water[r+1][c] & water[r][c-1] & water[r][c+1])  # All 4 directions
                    ))
            # Moat tile
            elif tile == 'M':
                E.add_constraint(moat[r][c])
                if (r == 0 or r == n_row - 1 or c == 0 or c == n_col - 1):  # Edges

                    # Corners
                    if (r == 0 and c == 0):  # Top left corner
                        E.add_constraint(water[r][c] >> (
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r][c+1])  # Right
                        ))
                    elif (r == 0 and c == n_col - 1):  # Top right corner
                        E.add_constraint(water[r][c] >> (
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        ))
                    elif (r == n_row - 1 and c == 0):  # Bottom left corner
                        E.add_constraint(water[r][c] >> (
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r][c+1])  # Right
                        ))
                    elif (r == n_row - 1 and c == n_col - 1):  # Bottom right corner
                        E.add_constraint(water[r][c] >> (
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        ))

                    # Sides (w/o corners)
                    elif (r == 0):  # Top wall
                        E.add_constraint(water[r][c] >> (
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r][c+1])  # Right
                            | (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        ))
                    elif (r == n_row - 1):  # Bottom wall
                        E.add_constraint(water[r][c] >> (
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r][c+1])  # Right
                            | (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        ))
                    elif (c == 0):  # Left wall
                        E.add_constraint(water[r][c] >> (
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r][c+1])  # Right
                        ))
                    elif (c == n_col - 1):  # Right wall
                        E.add_constraint(water[r][c] >> (
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        ))
                    
                else:
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & ~moat[r-1][c])  # Up
                        | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c] & ~moat[r+1][c])  # Down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1] & ~moat[r][c-1])  # Left
                        | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1] & ~moat[r][c+1])  # Right
                    ))
            # Ocean tile
            elif tile == 'O':
                E.add_constraint(ocean[r][c])
                if (r == 0 or r == n_row - 1 or c == 0 or c == n_col - 1):  # Edges

                    # Corners
                    if (r == 0 and c == 0):  # Top left corner
                        E.add_constraint(
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r][c+1])  # Right
                        )
                    elif (r == 0 and c == n_col - 1):  # Top right corner
                        E.add_constraint(
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        )
                    elif (r == n_row - 1 and c == 0):  # Bottom left corner
                        E.add_constraint(
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r][c+1])  # Right
                        )
                    elif (r == n_row - 1 and c == n_col - 1):  # Bottom right corner
                        E.add_constraint(
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        )

                    # Sides (w/o corners)
                    elif (r == 0):  # Top wall
                        E.add_constraint(
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r][c+1])  # Right
                            | (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        )
                    elif (r == n_row - 1):  # Bottom wall
                        E.add_constraint(
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r][c+1])  # Right
                            | (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        )
                    elif (c == 0):  # Left wall
                        E.add_constraint(
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r][c+1])  # Right
                        )
                    elif (c == n_col - 1):  # Right wall
                        E.add_constraint(
                            ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        )
                else:
                    E.add_constraint(
                          ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                        | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                    )
            # Blank tile
            else:
                constraint.add_none_of(E, straight[r][c], curved[r][c], bridge[r][c], moat[r][c], ocean[r][c])

            # A tile can be at most one of straight, curved, bridge, moat, ocean
            # If none, it is a blank tile
            constraint.add_at_most_one(E, straight[r][c], curved[r][c], bridge[r][c], moat[r][c], ocean[r][c])

    # Water
    # If there is water on a tile, it must either be an ocean tile 
    # or is connected to another tile containing water
    for r in range(1, n_row - 1):
        for c in range(1, n_col - 1):
            E.add_constraint(water[r][c] >> (ocean[r][c]
                    | water[r-1][c] & link_up[r][c]
                    | water[r][c-1] & link_left[r][c]
                    | water[r][c+1] & link_right[r][c]
                    | water[r+1][c] & link_down[r][c])
            )
    for c in range(1, n_col - 1):
        E.add_constraint(water[0][c] >>
                (ocean[0][c] | water[1][c] & link_down[0][c]
                | water[0][c-1] & link_left[0][c]
                | water[0][c+1] & link_right[0][c])
        )
        E.add_constraint(water[n_row-1][c] >>
                (ocean[n_row-1][c] | water[n_row-2][c] & link_up[n_row-1][c]
                | water[n_row-1][c-1] & link_left[n_row-1][c]
                | water[n_row-1][c+1] & link_right[n_row-1][c])
        )
    for r in range(1, n_row - 1):
        E.add_constraint(water[r][0] >>
                (ocean[r][0] | water[r-1][0] & link_up[r][0]
                | water[r+1][0] & link_down[r][0]
                | water[r][1] & link_right[r][0])
        )
        E.add_constraint(water[r][n_col-1] >>
                (ocean[r][n_col-1] | water[r-1][n_col-1] & link_up[r][n_col-1]
                | water[r+1][n_col-1] & link_down[r][n_col-1]
                | water[r][n_col-2] & link_left[r][n_col-1])
        )
    E.add_constraint(water[0][0] >>
            (ocean[0][0] | water[1][0] & link_down[0][0]
            | water[0][1] & link_right[0][0])
    )
    E.add_constraint(water[0][n_col-1] >>
            (ocean[0][n_col-1] | water[1][n_col-1] & link_down[0][n_col-1]
            | water[0][n_col-2] & link_left[0][n_col-1])
    )
    E.add_constraint(water[n_row-1][0] >>
            (ocean[n_row-1][0] | water[n_row-2][0] & link_up[n_row-1][0]
            | water[n_row-1][1] & link_right[n_row-1][0])
    )
    E.add_constraint(water[n_row-1][n_col-1] >>
            (ocean[n_row-1][n_col-1] | water[n_row-2][n_col-1] & link_up[n_row-1][n_col-1]
            | water[n_row-1][n_col-2] & link_left[n_row-1][n_col-1])
    )

    # Linking
    # If a tile links up, the tile above must link down
    for r in range(1, n_row):
        for c in range(n_col):
            E.add_constraint(link_up[r][c] >> link_down[r-1][c])
    # If a tile links down, the tile below must link up 
    for r in range(n_row - 1):
        for c in range(n_col):
            E.add_constraint(link_down[r][c] >> link_up[r+1][c])
    # If a tile links left, the tile on the left must link right
    for r in range(n_row):
        for c in range(1, n_col):
            E.add_constraint(link_left[r][c] >> link_right[r][c-1])
    # If a tile links right, the tile on the right must link left
    for r in range(n_row):
        for c in range(n_col - 1):
            E.add_constraint(link_right[r][c] >> link_left[r][c+1])
    
    # Tiles cannot link out of bounds
    for r in range(n_row):
        E.add_constraint(~link_left[r][0])
        E.add_constraint(~link_right[r][n_col - 1])
    for c in range(n_col):
        E.add_constraint(~link_up[0][c])
        E.add_constraint(~link_down[n_row - 1][c])

    # Win
    # The level has a solution if there is a moat tile filled with water
    temp = moat[0][0] & water[0][0]
    for r in range(n_row):
        for c in range(n_col):
            temp = temp | moat[r][c] & water[r][c]
    E.add_constraint(win >> temp)
    E.add_constraint(win)

    return E


def get_length(solution):
    # Given an output from the SAT solver, returns the length of the path.
    # Get configuration of water
    for r in range(n_row):
        for c in range(n_col):
            if solution[water[r][c]]:
                F.add_constraint(water[r][c])
            else:
                F.add_constraint(~water[r][c])

    # Iterate over every possible subset of the tiles.
    # If a bit is on, there is water in tile j. Else, it does not contain water.
    for i in range(2 ** (n_row * n_col)):
        n_ones = 0
        if i & 1 == 1:
            temp = water[0][0]
        else:
            temp = ~water[0][0]

        for j in range(n_row * n_col):
            if i & (1 << j) > 0:
                n_ones += 1
                # Tile must contain water
                temp = temp & water[j // n_row][j % n_row]
            else:
                # Tile must not contain water
                temp = temp & ~water[j // n_row][j % n_row]
        # If a solution has this layout, the path is length equal to the number of 1 bits in i
        F.add_constraint(temp >> length[n_ones])
        constraint.at_most_one(F, *length)

    return F


def get_longest(length_values):
    # Given the lengths of each solution path, return the largest length number.
    # Get solution lengths
    for i, e in enumerate(length_values):
        if e:
            G.add_constraint(length[i+1])
        else:
            G.add_constraint(~length[i+1])

    # If i is the largest length, there is no longer length
    temp = length[n_row * n_col]
    for i in range(n_row * n_col - 1, 1, -1):
        G.add_constraint(length[i] >> ~temp)
        temp = temp | length[i]
    constraint.at_most_one(G, *length)  # Might not be needed

    return G


if __name__ == "__main__":
    T = theory()
    T = T.compile()

    print("\nSatisfiable: %s" % T.satisfiable())
    # print_theory(T.solve(), 'objects')
    all_solutions = dsharp.compile(T.to_CNF(), smooth=True).model_count()

    lengths = []
    for solution in all_solutions:
        U = get_length(solution)
        U = U.compile()
        lengths.append(U.solve())
    
    length_values = [False for _ in range(n_row * n_col + 1)]
    for i in lengths:
        for j in range(1, n_row * n_col + 1):
            if lengths[length[j]]:
                length_values[j] = True

    V = get_longest(length_values)
    V = V.compile()
    longest_length = V.solve()

    for i, e in enumerate(lengths):
        if e[length[longest_length]]:
            print(all_solutions[i])
            break

