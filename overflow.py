from bauhaus import Encoding, proposition, constraint
from bauhaus.utils import count_solutions
from nnf import dsharp, config
import argparse
import sys

import viz

# Increase maximum recursion depth for larger levels
sys.setrecursionlimit(10 ** 6)

# Use faster SAT solver
config.sat_backend = "kissat"


# Parse arguments
parser = argparse.ArgumentParser(
        prog = 'Overflow',
        description = 'Solver for the Overflow game.'
)

parser.add_argument('-v', '--verbose',
        action='store_true',
        default=False,
        help='Print detailed processing information onto the screen (default=False)'
)

args = parser.parse_args()
verbose = vars(args)['verbose']  # Set verbosity


# Create Propositions
E = Encoding()
F = Encoding()


@proposition(E)
class Tile:
    """
    Proposition representing a type of tile.
    self.row - The row that the tile is in.
    self.col - The column that the tile is in.
    self.tile_type - The type of tile. Can be one of R, M, O
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

    def __init__(self, row, col, number):
        self.row = row
        self.col = col
        self.number = number

    def __repr__(self) -> str:
        return f"len {self.number}({self.row}, {self.col})"


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

# level_layout = [  # From project proposal
#     " L-MMML-L",
#     "-LLLLL-LL",
#     "LL-L++++L",
#     "L+L--L+L-",
#     "LL-LLLL-L",
#     "     O   "
# ]

# level_layout = [  # Two paths with different lengths
#     "-LL",
#     "O+M",
#     "LL-"
# ]

# level_layout = [  # Two paths with the same length
#     "O ",
#     "LM"
# ]

# level_layout = [
#     " MM+O+MM",
#     " -     -",
#     " -     -",
#     " O-O--OL",
#     "        "
# ]

level_layout = [  # Multiple oceans
    "L---LO-L",
    "-L-OL-O-",
    "M-O---L-",
    "LLL-OL+L",
    "-L+-L-MM",
    "--LLOLM-",
    "L+LL---L",
    "MLL----M"
]


n_row = len(level_layout)
n_col = len(level_layout[0])

# Propositions
regular = [[Tile(r, c, 'R') for c in range(n_col)] for r in range(n_row)]
moat    = [[Tile(r, c, 'M') for c in range(n_col)] for r in range(n_row)]
ocean   = [[Tile(r, c, 'O') for c in range(n_col)] for r in range(n_row)]

water = [[Water(r, c) for c in range(n_col)] for r in range(n_row)]

# Create propositions for linking horizontally and vertically
# Prevents repeated propositions for linking up & down, left & right
link_horizontal = [[Link(r, c, 'H') for c in range(n_col - 1)] for r in range(n_row)]
link_vertical = [[Link(r, c, 'V') for c in range(n_col)] for r in range(n_row - 1)]

link_up    = [None] + link_vertical
link_down  = link_vertical + [None]
link_left  = [[None] + r for r in link_horizontal]
link_right = [r + [None] for r in link_horizontal]

n_length = (n_row * n_col).bit_length()
waterf = [[WaterF(r, c) for c in range(n_col)] for r in range(n_row)]
length = [[[Length(r, c, 2 ** i) for i in range(n_length)] for c in range(n_col)] for r in range(n_row)]

# Constraints

def get_solution(detect_loop=False, remove=None, self_loops=[]):
    # Find a solution path from an ocean tile to a moat tile

    # Clear constraints so that we can run this function more than once
    E._custom_constraints = set()
    E.clear_constraints()

    # Specify how tiles link to one another when transporting water
    for r, row in enumerate(level_layout):
        for c, tile in enumerate(row):
            blank = True
            # Straight tile
            # A straight path that goes up and down or left and right
            if tile == '-':
                blank = False
                E.add_constraint(regular[r][c])
                if r == 0 and c == 0 or r == n_row - 1 and c == 0 or r == 0 and c == n_col - 1 or r == n_row - 1 and c == n_col - 1:  # Corners
                    E.add_constraint(~water[r][c])
                elif c == 0:   # Left wall
                    E.add_constraint(water[r][c] >> (
                        link_up[r][c] & link_down[r][c] & ~link_right[r][c]
                    ))
                elif c == n_col - 1:  # Right wall
                    E.add_constraint(water[r][c] >> (
                        link_up[r][c] & link_down[r][c] & ~link_left[r][c]
                    ))
                elif r == 0:  # Top wall
                    E.add_constraint(water[r][c] >> (
                        ~link_down[r][c] & link_left[r][c] & link_right[r][c]
                    ))
                elif r == n_row - 1 or r == 0:  # Bottom wall
                    E.add_constraint(water[r][c] >> (
                        ~link_up[r][c] & link_left[r][c] & link_right[r][c]
                    ))
                else:
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c])  # Up & down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] &  link_right[r][c])  # Left & right
                    ))
            # Curved tile
            # Bends the path of the water by 90 degrees in any direction
            elif tile == 'L':
                blank = False
                E.add_constraint(regular[r][c])
                # Corners
                if r == 0 and c == 0:  # Top left corner
                    E.add_constraint(water[r][c] >> (
                        link_down[r][c] & link_right[r][c]  # Down & right
                    ))
                elif r == 0 and c == n_col - 1:  # Top right corner
                    E.add_constraint(water[r][c] >> (
                        link_down[r][c] & link_left[r][c]  # Down & left
                    ))
                elif r == n_row - 1 and c == 0:  # Bottom left corner
                    E.add_constraint(water[r][c] >> (
                        link_up[r][c] & link_right[r][c]  # Up & right
                    ))
                elif r == n_row - 1 and c == n_col - 1:  # Bottom right corner
                    E.add_constraint(water[r][c] >> (
                        link_up[r][c] & link_left[r][c]  # Up & left
                    ))

                # Sides (w/o corners)
                elif r == 0:  # Top wall
                    E.add_constraint(water[r][c] >> (
                          (link_down[r][c] & ~link_left[r][c] &  link_right[r][c])  # Down & right
                        | (link_down[r][c] &  link_left[r][c] & ~link_right[r][c])  # Down & left
                    ))
                elif r == n_row - 1:  # Bottom wall
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_left[r][c] &  link_right[r][c])  # Up & right
                        | ( link_up[r][c] &  link_left[r][c] & ~link_right[r][c])  # Up & left
                    ))
                elif c == 0:  # Left wall
                    E.add_constraint(water[r][c] >> (
                          (~link_up[r][c] &  link_down[r][c] & link_right[r][c])  # Down & right
                        | ( link_up[r][c] & ~link_down[r][c] & link_right[r][c])  # Up & right
                    ))
                elif c == n_col - 1:  # Right wall
                    E.add_constraint(water[r][c] >> (
                          (~link_up[r][c] &  link_down[r][c] & link_left[r][c])  # Down & left
                        | ( link_up[r][c] & ~link_down[r][c] & link_left[r][c])  # Up & left
                    ))
                else:
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c])  # Up & left
                        | ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c])  # Up & right
                        | (~link_up[r][c] &  link_down[r][c] &  link_left[r][c] & ~link_right[r][c])  # Down & left
                        | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] &  link_right[r][c])  # Down & right
                    ))
            # Bridge tile
            # Allows water to flow straight in either or both directions
            elif tile == '+':
                blank = False
                E.add_constraint(regular[r][c])
                if r == 0 and c == 0 or r == n_row - 1 and c == 0 or r == 0 and c == n_col - 1 or r == n_row - 1 and c == n_col - 1:  # Corners
                    E.add_constraint(~water[r][c])
                elif r == 0:  # Top wall
                    E.add_constraint(water[r][c] >> (
                        ~link_down[r][c] & link_left[r][c] & link_right[r][c]  # Left & right
                    ))
                elif r == n_row - 1:  # Bottom wall
                    E.add_constraint(water[r][c] >> (
                        ~link_up[r][c] & link_left[r][c] & link_right[r][c]  # Left & right
                    ))
                elif c == 0:  # Left wall
                    E.add_constraint(water[r][c] >> (
                        link_up[r][c] & link_down[r][c] & ~link_right[r][c]  # Down & up
                    ))
                elif c == n_col - 1:  # Right wall
                    E.add_constraint(water[r][c] >> (
                        link_up[r][c] & link_down[r][c] & ~link_left[r][c]  # Down & up
                    ))
                else:
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c])  # Up & down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] &  link_right[r][c])  # Left & right
                        | ( link_up[r][c] &  link_down[r][c] &  link_left[r][c] &  link_right[r][c])  # All 4 directions
                    ))
            # Moat tile
            # The goal of the level
            # To avoid duplicate solutions, links only in one direction
            elif tile == 'M' and not remove == 'moat':
                blank = False
                E.add_constraint(moat[r][c])
                # Corners
                if r == 0 and c == 0:  # Top left corner
                    E.add_constraint(water[r][c] >> (
                          ( link_down[r][c] & ~link_right[r][c])  # Down
                        | (~link_down[r][c] &  link_right[r][c])  # Right
                    ))
                elif r == 0 and c == n_col - 1:  # Top right corner
                    E.add_constraint(water[r][c] >> (
                          ( link_down[r][c] & ~link_left[r][c])  # Down
                        | (~link_down[r][c] &  link_left[r][c])  # Left
                    ))
                elif r == n_row - 1 and c == 0:  # Bottom left corner
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_right[r][c])  # Up
                        | (~link_up[r][c] &  link_right[r][c])  # Right
                    ))
                elif r == n_row - 1 and c == n_col - 1:  # Bottom right corner
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_left[r][c])  # Up
                        | (~link_up[r][c] &  link_left[r][c])  # Left
                    ))

                # Sides (w/o corners)
                elif r == 0:  # Top wall
                    E.add_constraint(water[r][c] >> (
                          ( link_down[r][c] & ~link_left[r][c] & ~link_right[r][c])  # Down
                        | (~link_down[r][c] & ~link_left[r][c] &  link_right[r][c])  # Right
                        | (~link_down[r][c] &  link_left[r][c] & ~link_right[r][c])  # Left
                    ))
                elif r == n_row - 1:  # Bottom wall
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_left[r][c] & ~link_right[r][c])  # Up
                        | (~link_up[r][c] & ~link_left[r][c] &  link_right[r][c])  # Right
                        | (~link_up[r][c] &  link_left[r][c] & ~link_right[r][c])  # Left
                    ))
                elif c == 0:  # Left wall
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_down[r][c] & ~link_right[r][c])  # Up
                        | (~link_up[r][c] &  link_down[r][c] & ~link_right[r][c])  # Down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_right[r][c])  # Right
                    ))
                elif c == n_col - 1:  # Right wall
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c])  # Up
                        | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c])  # Down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c])  # Left
                    ))
                    
                else:
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c])  # Up
                        | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c])  # Down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c])  # Left
                        | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c])  # Right
                    ))
            # Ocean tile
            # The start of the water
            # Links only in one direction 
            elif tile == 'O' and not remove == 'ocean':
                blank = False
                E.add_constraint(ocean[r][c])
                if not remove == 'moat':
                    E.add_constraint(water[r][c])
                # Corners
                if r == 0 and c == 0:  # Top left corner
                    E.add_constraint(water[r][c] >> (
                          ( link_down[r][c] & ~link_right[r][c])  # Down
                        | (~link_down[r][c] &  link_right[r][c])  # Right
                    ))
                elif r == 0 and c == n_col - 1:  # Top right corner
                    E.add_constraint(water[r][c] >> (
                          ( link_down[r][c] & ~link_left[r][c])  # Down
                        | (~link_down[r][c] &  link_left[r][c])  # Left
                    ))
                elif r == n_row - 1 and c == 0:  # Bottom left corner
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_right[r][c])  # Up
                        | (~link_up[r][c] &  link_right[r][c])  # Right
                    ))
                elif r == n_row - 1 and c == n_col - 1:  # Bottom right corner
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_left[r][c])  # Up
                        | (~link_up[r][c] &  link_left[r][c])  # Left
                    ))

                # Sides (w/o corners)
                elif r == 0:  # Top wall
                    E.add_constraint(water[r][c] >> (
                          ( link_down[r][c] & ~link_left[r][c] & ~link_right[r][c])  # Down
                        | (~link_down[r][c] & ~link_left[r][c] &  link_right[r][c])  # Right
                        | (~link_down[r][c] &  link_left[r][c] & ~link_right[r][c])  # Left
                    ))
                elif r == n_row - 1:  # Bottom wall
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_left[r][c] & ~link_right[r][c])  # Up
                        | (~link_up[r][c] & ~link_left[r][c] &  link_right[r][c])  # Right
                        | (~link_up[r][c] &  link_left[r][c] & ~link_right[r][c])  # Left
                    ))
                elif c == 0:  # Left wall
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_down[r][c] & ~link_right[r][c])  # Up
                        | (~link_up[r][c] &  link_down[r][c] & ~link_right[r][c])  # Down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_right[r][c])  # Right
                    ))
                elif c == n_col - 1:  # Right wall
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c])  # Up
                        | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c])  # Down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c])  # Left
                    ))
                else:
                    E.add_constraint(water[r][c] >> (
                          ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c])  # Up
                        | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c])  # Down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c])  # Left
                        | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c])  # Right
                    ))
            # Blank tile
            if blank:
                constraint.add_none_of(E, regular[r][c], moat[r][c], ocean[r][c])
                # Corners
                if r == 0 and c == 0:  # Top left corner
                    constraint.add_none_of(E, link_down[r][c], link_right[r][c])
                elif r == 0 and c == n_col - 1:  # Top right corner
                    constraint.add_none_of(E, link_down[r][c], link_left[r][c])
                elif r == n_row - 1 and c == 0:  # Bottom left corner
                    constraint.add_none_of(E, link_up[r][c], link_right[r][c])
                elif r == n_row - 1 and c == n_row - 1: # Bottom right corner
                    constraint.add_none_of(E, link_up[r][c], link_left[r][c])
                
                # Sides (w/o corners)
                elif r == 0:  # Top wall
                    constraint.add_none_of(E, link_down[r][c], link_left[r][c], link_right[r][c])
                elif r == n_row - 1:  # Bottom wall
                    constraint.add_none_of(E, link_up[r][c], link_left[r][c], link_right[r][c])
                elif c == 0:  # Left wall
                    constraint.add_none_of(E, link_up[r][c], link_down[r][c], link_right[r][c])
                elif c == n_col - 1:  # Right wall
                    constraint.add_none_of(E, link_up[r][c], link_down[r][c], link_left[r][c])
                else:
                    constraint.add_none_of(E, link_up[r][c], link_down[r][c], link_left[r][c], link_right[r][c])

            # A tile can be at most one of straight, curved, bridge, moat, ocean
            # If none, it is a blank tile
            constraint.add_at_most_one(E, regular[r][c], moat[r][c], ocean[r][c])

            # Restrict linking to remove duplicate solutions
            # Corners
            if r == 0 and c == 0:  # Top left corner
                E.add_constraint(~water[r][c] >> (~link_down[r][c] & ~link_right[r][c]))
            elif r == 0 and c == n_col - 1:  # Top right corner
                E.add_constraint(~water[r][c] >> (~link_down[r][c] & ~link_left[r][c]))
            elif r == n_row - 1 and c == 0:  # Bottom left corner
                E.add_constraint(~water[r][c] >> (~link_up[r][c] & ~link_right[r][c]))
            elif r == n_row - 1 and c == n_col - 1:  # Bottom right corner
                E.add_constraint(~water[r][c] >> (~link_up[r][c] & ~link_left[r][c]))

            # Sides (w/o corners)
            elif r == 0:  # Top wall
                E.add_constraint(~water[r][c] >> (~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]))
            elif r == n_row - 1:  # Bottom wall
                E.add_constraint(~water[r][c] >> (~link_up[r][c] & ~link_left[r][c] & ~link_right[r][c]))
            elif c == 0:  # Left wall
                E.add_constraint(~water[r][c] >> (~link_up[r][c] & ~link_down[r][c] & ~link_right[r][c]))
            elif c == n_col - 1:  # Right wall
                E.add_constraint(~water[r][c] >> (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c]))
            else:
                E.add_constraint(~water[r][c] >> (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]))

    # Water
    # If there is water on a tile, it must either be an ocean tile 
    # or is connected to another tile containing water
    
    # Corners
    E.add_constraint(water[0][0] >> (ocean[0][0]  # Top left corner
            | water[1][0] & link_down[0][0]
            | water[0][1] & link_right[0][0]
    ))
    E.add_constraint(water[0][n_col-1] >> (ocean[0][n_col-1]  # Top right corner
            | water[1][n_col-1] & link_down[0][n_col-1]
            | water[0][n_col-2] & link_left[0][n_col-1]
    ))
    E.add_constraint(water[n_row-1][0] >> (ocean[n_row-1][0]  # Bottom left corner
            | water[n_row-2][0] & link_up[n_row-1][0]
            | water[n_row-1][1] & link_right[n_row-1][0]
    ))
    E.add_constraint(water[n_row-1][n_col-1] >> (ocean[n_row-1][n_col-1]  # Bottom right corner
            | water[n_row-2][n_col-1] & link_up[n_row-1][n_col-1]
            | water[n_row-1][n_col-2] & link_left[n_row-1][n_col-1]
    ))

    # Sides (w/o corners)
    for c in range(1, n_col - 1):
        E.add_constraint(water[0][c] >> (ocean[0][c]  # Top wall
                | water[1][c]   & link_down[0][c]
                | water[0][c-1] & link_left[0][c]
                | water[0][c+1] & link_right[0][c]
        ))
        E.add_constraint(water[n_row-1][c] >> (ocean[n_row-1][c]  # Bottom wall
                | water[n_row-2][c]   & link_up[n_row-1][c]
                | water[n_row-1][c-1] & link_left[n_row-1][c]
                | water[n_row-1][c+1] & link_right[n_row-1][c]
        ))
    for r in range(1, n_row - 1):
        E.add_constraint(water[r][0] >> (ocean[r][0]  # Left wall
                | water[r-1][0] & link_up[r][0]
                | water[r+1][0] & link_down[r][0]
                | water[r][1]   & link_right[r][0]
        ))
        E.add_constraint(water[r][n_col-1] >> (ocean[r][n_col-1]  # Right wall
                | water[r-1][n_col-1] & link_up[r][n_col-1]
                | water[r+1][n_col-1] & link_down[r][n_col-1]
                | water[r][n_col-2]   & link_left[r][n_col-1]
        ))
    
    # Elsewhere
    for r in range(1, n_row - 1):
        for c in range(1, n_col - 1):
            E.add_constraint(water[r][c] >> (ocean[r][c]
                    | water[r-1][c] & link_up[r][c]
                    | water[r][c-1] & link_left[r][c]
                    | water[r][c+1] & link_right[r][c]
                    | water[r+1][c] & link_down[r][c]
            ))

    
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
        E.add_constraint(temp)  # Find a solution

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

    # Set length for top left tile
    # The length is 1 if there is water, 0 otherwise
    F.add_constraint((waterf[0][0] & length[0][0][0]) 
                  | (~waterf[0][0] & ~length[0][0][0]))
    for i in range(1, n_length):
        F.add_constraint(~length[0][0][i])

    # Count number of water tiles in binary
    # Note that the length propositions are ordered 1, 2, 4, 8, ...
    for r in range(n_row):
        for c in range(n_col):
            # Top left case already handled
            if r == 0 and c == 0:
                continue

            prev_row = r if c > 0 else r - 1
            prev_col = c - 1 if c > 0 else n_col - 1
            # If the previous bit positions are all 1's
            temp = length[prev_row][prev_col][0]

            # If a tile contains water, we "add one" to the previous count
            F.add_constraint(waterf[r][c] >> (~length[prev_row][prev_col][0] &  length[r][c][0] 
                                             | length[prev_row][prev_col][0] & ~length[r][c][0]))
            for i in range(1, n_length):
                F.add_constraint(waterf[r][c] >> ((~temp & ~length[prev_row][prev_col][i]) >> ~length[r][c][i]))
                F.add_constraint(waterf[r][c] >> ((~temp &  length[prev_row][prev_col][i]) >>  length[r][c][i]))
                F.add_constraint(waterf[r][c] >> (( temp & ~length[prev_row][prev_col][i]) >>  length[r][c][i]))
                F.add_constraint(waterf[r][c] >> (( temp &  length[prev_row][prev_col][i]) >> ~length[r][c][i]))
                temp = temp & length[prev_row][prev_col][i]

            # Otherwise, keep the count the same
            for i in range(n_length):
                F.add_constraint(~waterf[r][c] >> (~length[prev_row][prev_col][i] & ~length[r][c][i] 
                                                  | length[prev_row][prev_col][i] &  length[r][c][i]))

    return F


if __name__ == "__main__":
    # Self-loop detection
    # Remove all ocean tiles and solve for all paths.
    # Any tiles containing water are self-loops.
    T = get_solution(detect_loop=True, remove='ocean')
    T = T.compile()
    moat_loops = dsharp.compile(T.to_CNF(), smooth=True).models()
    moat_loops = [i for i in moat_loops]

    # Remove all moat tiles and solve for all paths.
    # Also removes the requirement that oceans must contain water
    # in order to find all subsets of ocean self-loops.
    T = get_solution(detect_loop=True, remove='moat')
    T = T.compile()
    ocean_loops = dsharp.compile(T.to_CNF(), smooth=True).models()
    ocean_loops = [i for i in ocean_loops]

    all_loops = moat_loops + ocean_loops
    
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
    if verbose:
            print(f"Removed {len(self_loops) - 1} self-loops.")


    # Find all paths
    T = get_solution(self_loops=self_loops)
    T = T.compile()

    is_satisfiable = T.satisfiable()
    print(f"\nSatisfiable: {is_satisfiable}")
    if is_satisfiable:
        print(f"Number of solutions: {count_solutions(T)}")
        all_solutions = dsharp.compile(T.to_CNF(), smooth=True).models()
        all_solutions = [i for i in all_solutions]

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
        longest_length_index = 0
        for i, l in enumerate(lengths):
            total_length = 0
            for j in range(n_length):
                if l[length[n_row - 1][n_col - 1][j]]:
                    total_length += length[n_row - 1][n_col - 1][j].number
            if total_length > longest_length:
                longest_length = total_length
                longest_length_index = i
            
            # Return the path with the longest length
            longest_solution_dict = all_solutions[longest_length_index]

        print("Longest solution has length", longest_length)

        longest_solution = viz.convert_solution(longest_solution_dict, level_layout)
        viz.viz_level(longest_solution)
