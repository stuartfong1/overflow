from bauhaus import Encoding, proposition, constraint
from bauhaus.utils import count_solutions
from nnf import dsharp
import argparse
import sys

import viz

# Change maximum recursion depth for larger levels
sys.setrecursionlimit(10**6)

# Parse arguments
parser = argparse.ArgumentParser(
        prog = 'Overflow',
        description = 'Solver for the Overflow game.'
)

parser.add_argument('-n', '--no-logic', 
        action='store_true', 
        default=False,
        help='Use the Python implementation of calculating the path length (default=False)'
)

parser.add_argument('-v', '--verbose',
        action='store_true',
        default=False,
        help='Print detailed processing information onto the screen (default=False)'
)

args = parser.parse_args()

no_logic = vars(args)['no_logic']  # Use Python to calculate path length
verbose = vars(args)['verbose']  # Set verbosity


# Create Propositions
E = Encoding()
F = Encoding()


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
    self.prop - Identifies the tile as a regular tile.
    """

    def __init__(self, row, col, tile_type, prop='tile'):
        self.row = row
        self.col = col
        self.tile_type = tile_type
        self.prop = prop

    def __repr__(self) -> str:
        return f"{self.tile_type}({self.row}, {self.col})"


@proposition(E)
class Water:
    """
    Proposition representing a tile that contains water.
    self.row - The row that the tile is in.
    self.col - The column that the tile is in.
    self.prop - Identifies the tile as a water tile.
    """

    def __init__(self, row, col, prop='water'):
        self.row = row
        self.col = col
        self.prop = prop

    def __repr__(self) -> str:
        return f"W({self.row}, {self.col})"


@proposition(F)
class WaterF:
    """
    Proposition representing a tile that contains water.
    Identical to the Water class but for proposition F.
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
    self.prop - Identifies the tile as a link.
    """

    def __init__(self, row, col, direction, prop='link'):
        self.row = row
        self.col = col
        self.direction = direction
        self.prop = prop

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


# Create level layout

# - = straight
# + = bridge
# L = curved
# M = moat
# O = ocean

# level_layout = [  # Self-loops
#     "L-LMMML-L",
#     "-LLL--LL-",
#     "--L---LL-",
#     "L+LLLL+-L",
#     "LLLLLL---",
#     "      O  "
# ]

level_layout = [  # From project proposal
    " L-MMML-L",
    "-LLLLL-LL",
    "LL-L++++L",
    "L+L--L+L-",
    "LL-LLLL-L",
    "     O   "
]

# level_layout = [  # Two paths with different lengths
#     "-LL",
#     "O+M",
#     "LL-"
# ]

# level_layout = [  # Two paths with the same length
#     "OL",
#     "LM"
# ]

n_row = len(level_layout)
n_col = len(level_layout[0])

# Propositions
straight = [[Tile(r, c, 'S') for c in range(n_col)] for r in range(n_row)]
curved   = [[Tile(r, c, 'C') for c in range(n_col)] for r in range(n_row)]
bridge   = [[Tile(r, c, 'B') for c in range(n_col)] for r in range(n_row)]
moat     = [[Tile(r, c, 'M') for c in range(n_col)] for r in range(n_row)]
ocean    = [[Tile(r, c, 'O') for c in range(n_col)] for r in range(n_row)]

water = [[Water(r, c) for c in range(n_col)] for r in range(n_row)]

link_up    = [[Link(r, c, 'U') for c in range(n_col)] for r in range(n_row)]
link_down  = [[Link(r, c, 'D') for c in range(n_col)] for r in range(n_row)]
link_left  = [[Link(r, c, 'L') for c in range(n_col)] for r in range(n_row)]
link_right = [[Link(r, c, 'R') for c in range(n_col)] for r in range(n_row)]

win = Win()

waterf = [[WaterF(r, c) for c in range(n_col)] for r in range(n_row)]
length = [None] + [Length(i + 1) for i in range(n_row * n_col)]

# Constraints

def get_solution(detect_loop=False, self_loops=[]):
    # Find a solution path from an ocean tile to a moat tile

    # Clear constraints so that we can run this function more than once
    E._custom_constraints = set()
    E.clear_constraints()

    # Specify how tiles link to one another when transporting water
    for r, row in enumerate(level_layout):
        for c, tile in enumerate(row):
            # Straight tile
            # A straight path that goes up and down or left and right
            if tile == '-':
                E.add_constraint(straight[r][c])
                if (r == 0 and c == 0) or (r == n_row - 1 and c == 0) or (r == 0 and c == n_col - 1) or (r == n_row - 1 and c == n_col - 1):  # Corners
                    E.add_constraint(~water[r][c])
                elif c == 0 or c == n_col - 1:   # Left & right walls
                    E.add_constraint(water[r][c] >> (
                        ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])
                    ))
                elif r == n_row - 1 or r == 0:  # Top & bottom walls
                    E.add_constraint(water[r][c] >> (
                        ( ~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & link_right[r][c] & water[r][c-1] & water[r][c+1])
                    ))
                else:
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])  # Up & down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] &  link_right[r][c] & water[r][c-1] & water[r][c+1])  # Left & right
                    ))
            # Curved tile
            # Bends the path of the water by 90 degrees in any direction
            elif tile == 'L':
                E.add_constraint(curved[r][c])
                if (r == 0 or r == n_row - 1 or c == 0 or c == n_col - 1):  # Edges

                    # Corners
                    if (r == 0 and c == 0):  # Top left corner
                        E.add_constraint(water[r][c] >> (
                            (~link_up[r][c] & link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r+1][c] & water[r][c+1])  # Down & right
                        ))
                    elif (r == 0 and c == n_col - 1):  # Top right corner
                        E.add_constraint(water[r][c] >> (
                            (~link_up[r][c] & link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r+1][c] & water[r][c-1])  # Down & left
                        ))
                    elif (r == n_row - 1 and c == 0):  # Bottom left corner
                        E.add_constraint(water[r][c] >> (
                            (link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r-1][c] & water[r][c+1])  # Up & right
                        ))
                    elif (r == n_row - 1 and c == n_col - 1):  # Bottom right corner
                        E.add_constraint(water[r][c] >> (
                            (link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r][c-1])  # Up & left
                        ))

                    # Sides (w/o corners)
                    elif (r == 0):  # Top wall
                        E.add_constraint(water[r][c] >> (
                              ( ~link_up[r][c] & link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r+1][c] & water[r][c+1])  # Down & right
                            | ( ~link_up[r][c] & link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r+1][c] & water[r][c-1])  # Down & left
                        ))
                    elif (r == n_row - 1):  # Bottom wall
                        E.add_constraint(water[r][c] >> (
                              ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r-1][c] & water[r][c+1])  # Up & right
                            | ( link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r][c-1])  # Up & left
                        ))
                    elif (c == 0):  # Left wall
                        E.add_constraint(water[r][c] >> (
                              (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r+1][c] & water[r][c+1])  # Down & right
                            | ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & link_right[r][c] & water[r-1][c] & water[r][c+1])  # Up & right
                        ))
                    elif (c == n_col - 1):  # Right wall
                        E.add_constraint(water[r][c] >> (
                              (~link_up[r][c] &  link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r+1][c] & water[r][c-1])  # Down & left
                            | ( link_up[r][c] & ~link_down[r][c] & link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r][c-1])  # Up & left
                        ))
                else:
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r][c-1])  # Up & left
                        | ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r-1][c] & water[r][c+1])  # Up & right
                        | (~link_up[r][c] &  link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r+1][c] & water[r][c-1])  # Down & left
                        | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r+1][c] & water[r][c+1])  # Down & right
                    ))
            # Bridge tile
            # Allows water to flow straight in either or both directions
            elif tile == '+':
                E.add_constraint(bridge[r][c])
                if (r == 0 and c == 0) or (r == n_row - 1 and c == 0) or (r == 0 and c == n_col - 1) or (r == n_row - 1 and c == n_col - 1):  # Corners
                    E.add_constraint(~water[r][c])
                elif (r == 0 or r == n_row - 1):
                    E.add_constraint(water[r][c] >> (
                        (~link_up[r][c] & ~link_down[r][c] & link_left[r][c] & link_right[r][c] & water[r][c-1] & water[r][c+1])  # Left & right
                    ))
                elif (c == 0 or c == n_col - 1):
                    E.add_constraint(water[r][c] >> (
                        (link_up[r][c] & link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])  # Down & up
                    ))                
                else:
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])  # Up & down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] &  link_right[r][c] & water[r][c-1] & water[r][c+1])  # Left & right
                        | ( link_up[r][c] &  link_down[r][c] &  link_left[r][c] &  link_right[r][c] & water[r-1][c] & water[r+1][c] & water[r][c-1] & water[r][c+1])  # All 4 directions
                    ))
            # Moat tile
            # The goal of the level
            # To avoid duplicate solutions, links only in one direction
            elif tile == 'M':
                E.add_constraint(moat[r][c])
                if (r == 0 or r == n_row - 1 or c == 0 or c == n_col - 1):  # Edges

                    # Corners
                    if (r == 0 and c == 0):  # Top left corner
                        E.add_constraint(water[r][c] >> (
                              (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                        ))
                    elif (r == 0 and c == n_col - 1):  # Top right corner
                        E.add_constraint(water[r][c] >> (
                              (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        ))
                    elif (r == n_row - 1 and c == 0):  # Bottom left corner
                        E.add_constraint(water[r][c] >> (
                              ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                        ))
                    elif (r == n_row - 1 and c == n_col - 1):  # Bottom right corner
                        E.add_constraint(water[r][c] >> (
                              ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        ))

                    # Sides (w/o corners)
                    elif (r == 0):  # Top wall
                        E.add_constraint(water[r][c] >> (
                              (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                            | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        ))
                    elif (r == n_row - 1):  # Bottom wall
                        E.add_constraint(water[r][c] >> (
                              ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                            | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        ))
                    elif (c == 0):  # Left wall
                        E.add_constraint(water[r][c] >> (
                              ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                        ))
                    elif (c == n_col - 1):  # Right wall
                        E.add_constraint(water[r][c] >> (
                              ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                            | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                            | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        ))
                    
                else:
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                        | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                        | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                    ))
            # Ocean tile
            # The start of the water
            # Links only in one direction 
            elif tile == 'O':
                if detect_loop:
                    constraint.add_none_of(E, straight[r][c], curved[r][c], bridge[r][c], moat[r][c], ocean[r][c], link_up[r][c], link_down[r][c], link_left[r][c], link_right[r][c])
                    continue
                else:
                    E.add_constraint(ocean[r][c])
                    if (r == 0 or r == n_row - 1 or c == 0 or c == n_col - 1):  # Edges

                        # Corners
                        if (r == 0 and c == 0):  # Top left corner
                            E.add_constraint(
                                (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                                | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                            )
                        elif (r == 0 and c == n_col - 1):  # Top right corner
                            E.add_constraint(
                                (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                                | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                            )
                        elif (r == n_row - 1 and c == 0):  # Bottom left corner
                            E.add_constraint(
                                ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                                | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                            )
                        elif (r == n_row - 1 and c == n_col - 1):  # Bottom right corner
                            E.add_constraint(
                                ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                                | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                            )

                        # Sides (w/o corners)
                        elif (r == 0):  # Top wall
                            E.add_constraint(
                                (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                                | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                                | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                            )
                        elif (r == n_row - 1):  # Bottom wall
                            E.add_constraint(
                                ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                                | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                                | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
                            )
                        elif (c == 0):  # Left wall
                            E.add_constraint(
                                ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                                | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                                | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1])  # Right
                            )
                        elif (c == n_col - 1):  # Right wall
                            E.add_constraint(
                                ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c])  # Up
                                | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c])  # Down
                                | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1])  # Left
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
                constraint.add_none_of(E, straight[r][c], curved[r][c], bridge[r][c], moat[r][c], ocean[r][c], link_up[r][c], link_down[r][c], link_left[r][c], link_right[r][c])

            # A tile can be at most one of straight, curved, bridge, moat, ocean
            # If none, it is a blank tile
            constraint.add_at_most_one(E, straight[r][c], curved[r][c], bridge[r][c], moat[r][c], ocean[r][c])

            # Restrict linking to remove duplicate solutions
            E.add_constraint(~water[r][c] >> (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]))

    # Water
    # If there is water on a tile, it must either be an ocean tile 
    # or is connected to another tile containing water
    for r in range(1, n_row - 1):
        for c in range(1, n_col - 1):
            E.add_constraint(water[r][c] >> (ocean[r][c]
                    | water[r-1][c] & link_up[r][c]
                    | water[r][c-1] & link_left[r][c]
                    | water[r][c+1] & link_right[r][c]
                    | water[r+1][c] & link_down[r][c]
            ))
    for c in range(1, n_col - 1):
        E.add_constraint(water[0][c] >> (ocean[0][c]  # Top edge
                | water[1][c] & link_down[0][c]
                | water[0][c-1] & link_left[0][c]
                | water[0][c+1] & link_right[0][c]
        ))
        E.add_constraint(water[n_row-1][c] >> (ocean[n_row-1][c]  # Bottom edge
                | water[n_row-2][c] & link_up[n_row-1][c]
                | water[n_row-1][c-1] & link_left[n_row-1][c]
                | water[n_row-1][c+1] & link_right[n_row-1][c]
        ))
    for r in range(1, n_row - 1):
        E.add_constraint(water[r][0] >> (ocean[r][0]  # Left edge
                | water[r-1][0] & link_up[r][0]
                | water[r+1][0] & link_down[r][0]
                | water[r][1] & link_right[r][0]
        ))
        E.add_constraint(water[r][n_col-1] >> (ocean[r][n_col-1]  # Right edge
                | water[r-1][n_col-1] & link_up[r][n_col-1]
                | water[r+1][n_col-1] & link_down[r][n_col-1]
                | water[r][n_col-2] & link_left[r][n_col-1]
        ))
    E.add_constraint(water[0][0] >> (ocean[0][0]  # Top left corner
            | water[1][0] & link_down[0][0]
            | water[0][1] & link_right[0][0]
    ))
    E.add_constraint(water[0][n_col-1] >>  # Top right corner
            (ocean[0][n_col-1] | water[1][n_col-1] & link_down[0][n_col-1]
            | water[0][n_col-2] & link_left[0][n_col-1]
    ))
    E.add_constraint(water[n_row-1][0] >>  # Bottom left corner
            (ocean[n_row-1][0] | water[n_row-2][0] & link_up[n_row-1][0]
            | water[n_row-1][1] & link_right[n_row-1][0]
    ))
    E.add_constraint(water[n_row-1][n_col-1] >>  # Bottom right corner
            (ocean[n_row-1][n_col-1] | water[n_row-2][n_col-1] & link_up[n_row-1][n_col-1]
            | water[n_row-1][n_col-2] & link_left[n_row-1][n_col-1]
    ))

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

    
    if not detect_loop:
        # Prevent self-loops
        for self_loop in self_loops:
            if len(self_loop) > 0:
                temp = self_loop[0]
                for i in self_loop:
                    temp = temp & i
                E.add_constraint(~temp)

        # Win
        # The level has a solution if there is a moat tile filled with water
        temp = moat[0][0] & water[0][0]
        for r in range(n_row):
            for c in range(n_col):
                temp = temp | moat[r][c] & water[r][c]
        E.add_constraint(win >> temp)
        E.add_constraint(win)  # Find a solution

    return E


def get_length(solution):
    # Given an output from the SAT solver, returns the length of the path.

    # Clear constraints so that we can run this function more than once
    F._custom_constraints = set()

    # Get configuration of water
    for r in range(n_row):
        for c in range(n_col):
            if solution[water[r][c]]:
                F.add_constraint(waterf[r][c])
            else:
                F.add_constraint(~waterf[r][c])

    # Iterate over every possible subset of the tiles.
    # If a bit is on, there is water in tile j. Else, it does not contain water.
    for i in range(1, 2 ** (n_row * n_col)):
        # Give temp an initial value based on the top left tile
        if i & 1 == 1:
            temp = waterf[0][0]
            n_ones = 1
        else:
            temp = ~waterf[0][0]
            n_ones = 0

        for j in range(1, n_row * n_col):
            if i & (1 << j) > 0:
                # Tile must contain water
                temp = temp & waterf[j // n_col][j % n_col]
                n_ones += 1
            else:
                # Tile must not contain water
                temp = temp & ~waterf[j // n_col][j % n_col]
        # If a solution has this layout, the path is length equal to the number of 1 bits in i
        F.add_constraint(temp >> length[n_ones])

    return F


if __name__ == "__main__":
    # Self-loop detection
    # Remove all ocean tiles and solve for all paths.
    # Any tiles containing water are self-loops.
    T = get_solution(detect_loop=True)
    T = T.compile()
    all_loops = dsharp.compile(T.to_CNF(), smooth=True).models()
    all_loops = [i for i in all_loops]
    # Contains all combinations of self-loops
    self_loops = []
    for loop in all_loops:
        # Contains the linking that contributes to the self-loop
        self_loop = []
        for k, v in loop.items():
            prop = getattr(k, 'prop', None)
            if v and prop == 'link':
                self_loop.append(k)
        self_loops.append(self_loop)

    # Find all paths
    T = get_solution(self_loops=self_loops)
    T = T.compile()

    print("\nSatisfiable: %s" % T.satisfiable())
    print("Number of solutions: %d" % count_solutions(T))
    all_solutions = dsharp.compile(T.to_CNF(), smooth=True).models()
    all_solutions = [i for i in all_solutions]

    # Python implementation of finding longest solution
    if no_logic:
        # Get the lengths of each path
        lengths = []
        for i, solution in enumerate(all_solutions):
            if verbose:
                print(f"Getting length of solution {i + 1}...")
            len_path = 0
            for r in range(n_row):
                for c in range(n_col):
                    if solution[water[r][c]]:
                        len_path += 1
            lengths.append(len_path)

        # Get the maximum length
        longest_length = max(lengths)

        # Return the path with the longest length
        for i, l in enumerate(lengths):
            if l == longest_length:
                longest_solution_dict = all_solutions[i]
                break
        
    # Logic implementation of finding longest solution (slow)
    else:
        # Get the lengths of each path
        lengths = []
        for i, solution in enumerate(all_solutions):
            if verbose:
                print(f"Getting length of solution {i + 1}...")
            U = get_length(solution)
            U = U.compile()
            lengths.append(U.solve())
        
        # Get the maximum length
        longest_length = 0
        for l in lengths:
            for i in range(n_row * n_col, 0, -1):
                if l[length[i]] and i > longest_length:
                    longest_length = i
                    break
        
        # Return the path with the longest length
        for i, l in enumerate(lengths):
            if l[length[longest_length]]:
                longest_solution_dict = all_solutions[i]
                break

    print("Longest solution has length", longest_length)

    longest_solution = viz.convert_solution(longest_solution_dict, level_layout)
    viz.viz_level(longest_solution)
    

