from bauhaus import Encoding, proposition, constraint
from bauhaus.utils import count_solutions
from nnf import dsharp, config
import argparse
import sys

from level import level_layout
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


@proposition(F)
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


# Get dimensions of level
n_row = len(level_layout)
n_col = len(level_layout[0])

# Propositions
straight = [[Tile(r, c, 'S') for c in range(n_col)] for r in range(n_row)]
curved = [[Tile(r, c, 'C') for c in range(n_col)] for r in range(n_row)]
bridge = [[Tile(r, c, 'B') for c in range(n_col)] for r in range(n_row)]
moat    = [[Tile(r, c, 'M') for c in range(n_col)] for r in range(n_row)]
ocean   = [[Tile(r, c, 'O') for c in range(n_col)] for r in range(n_row)]

# Create propositions for linking horizontally and vertically
# Prevents repeated propositions for linking up & down, left & right
link_horizontal = [[Link(r, c, 'H') for c in range(n_col - 1)] for r in range(n_row)]
link_vertical = [[Link(r, c, 'V') for c in range(n_col)] for r in range(n_row - 1)]

link_up    = [None] + link_vertical
link_down  = link_vertical + [None]
link_left  = [[None] + r for r in link_horizontal]
link_right = [r + [None] for r in link_horizontal]

# Maximum number of bits needed to store the length of a solution path
# in a level with dimensions n_row by n_col
n_length = (n_row * n_col).bit_length()

# Create water and length propositions used when finding the length of a solution path
water = [[Water(r, c) for c in range(n_col)] for r in range(n_row)]
length = [[[Length(r, c, 2 ** i) for i in range(n_length)] for c in range(n_col)] for r in range(n_row)]

# Constraints

def get_solution(detect_loop=False, remove=None, self_loops=[]):
    """
    Find a solution path from an ocean tile to a moat tile
    detect_loop - detect self-loops that may be present in the solver's output
    remove - 'moat', 'ocean', or None. Specify which tile to treat as blank
    self_loops - List of lists specifying which tiles can form self-loops

    Returns an encoding with the constraints needed to find a solution
    to the level.
    """

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
                E.add_constraint(straight[r][c])
                # Corners
                if r == 0 and c == 0:  # Top left corner
                    constraint.add_none_of(E, link_down[r][c], link_right[r][c])
                elif r == 0 and c == n_col - 1:  # Top right corner
                    constraint.add_none_of(E, link_down[r][c], link_left[r][c])
                elif r == n_row - 1 and c == 0:  # Bottom left corner
                    constraint.add_none_of(E, link_up[r][c], link_right[r][c])
                elif r == n_row - 1 and c == n_col - 1:  # Bottom right corner
                    constraint.add_none_of(E, link_up[r][c], link_left[r][c])

                elif c == 0:   # Left wall
                    E.add_constraint(
                          ~link_up[r][c] & ~link_down[r][c] & ~link_right[r][c]  # Not linked
                        |  link_up[r][c] &  link_down[r][c] & ~link_right[r][c]  # Up & down
                    )
                elif c == n_col - 1:  # Right wall
                    E.add_constraint(
                          ~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c]  # Not linked
                        |  link_up[r][c] &  link_down[r][c] & ~link_left[r][c]  # Up & down
                    )
                elif r == 0:  # Top wall
                    E.add_constraint(
                          ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Not linked
                        | ~link_down[r][c] &  link_left[r][c] &  link_right[r][c]  # Left & right
                    )
                elif r == n_row - 1 or r == 0:  # Bottom wall
                    E.add_constraint(
                          ~link_up[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Not linked
                        | ~link_up[r][c] &  link_left[r][c] &  link_right[r][c]  # Left & right
                    )
                else:
                    E.add_constraint(
                          ~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Not linked
                        |  link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Up & down
                        | ~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] &  link_right[r][c]  # Left & right
                    )
            # Curved tile
            # Bends the path of the water by 90 degrees in any direction
            elif tile == 'L':
                blank = False
                E.add_constraint(curved[r][c])
                # Corners
                if r == 0 and c == 0:  # Top left corner
                    E.add_constraint(
                          ~link_down[r][c] & ~link_right[r][c]  # Not linked
                        |  link_down[r][c] &  link_right[r][c]  # Down & right
                    )
                elif r == 0 and c == n_col - 1:  # Top right corner
                    E.add_constraint(
                          ~link_down[r][c] & ~link_left[r][c]  # Not linked
                        |  link_down[r][c] &  link_left[r][c]  # Down & left
                    )
                elif r == n_row - 1 and c == 0:  # Bottom left corner
                    E.add_constraint(
                          ~link_up[r][c] & ~link_right[r][c]  # Not linked
                        |  link_up[r][c] &  link_right[r][c]  # Up & right
                    )
                elif r == n_row - 1 and c == n_col - 1:  # Bottom right corner
                    E.add_constraint(
                          ~link_up[r][c] & ~link_left[r][c]  # Not linked
                        |  link_up[r][c] &  link_left[r][c]  # Up & left
                    )

                # Sides (w/o corners)
                elif r == 0:  # Top wall
                    E.add_constraint(
                          ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Not linked
                        |  link_down[r][c] & ~link_left[r][c] &  link_right[r][c]  # Down & right
                        |  link_down[r][c] &  link_left[r][c] & ~link_right[r][c]  # Down & left
                    )
                elif r == n_row - 1:  # Bottom wall
                    E.add_constraint(
                          ~link_up[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Not linked
                        |  link_up[r][c] & ~link_left[r][c] &  link_right[r][c]  # Up & right
                        |  link_up[r][c] &  link_left[r][c] & ~link_right[r][c]  # Up & left
                    )
                elif c == 0:  # Left wall
                    E.add_constraint(
                          ~link_up[r][c] & ~link_down[r][c] & ~link_right[r][c]  # Not linked
                        | ~link_up[r][c] &  link_down[r][c] &  link_right[r][c]  # Down & right
                        |  link_up[r][c] & ~link_down[r][c] &  link_right[r][c]  # Up & right
                    )
                elif c == n_col - 1:  # Right wall
                    E.add_constraint(
                          ~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c]  # Not linked
                        | ~link_up[r][c] &  link_down[r][c] &  link_left[r][c]  # Down & left
                        |  link_up[r][c] & ~link_down[r][c] &  link_left[r][c]  # Up & left
                    )
                else:
                    E.add_constraint(
                          ~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Not linked
                        |  link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c]  # Up & left
                        |  link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c]  # Up & right
                        | ~link_up[r][c] &  link_down[r][c] &  link_left[r][c] & ~link_right[r][c]  # Down & left
                        | ~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] &  link_right[r][c]  # Down & right
                    )
            # Bridge tile
            # Allows water to flow straight in either or both directions
            elif tile == '+':
                blank = False
                E.add_constraint(bridge[r][c])
                # Corners
                if r == 0 and c == 0:  # Top left corner
                    constraint.add_none_of(E, link_down[r][c], link_right[r][c])
                elif r == 0 and c == n_col - 1:  # Top right corner
                    constraint.add_none_of(E, link_down[r][c], link_left[r][c])
                elif r == n_row - 1 and c == 0:  # Bottom left corner
                    constraint.add_none_of(E, link_up[r][c], link_right[r][c])
                elif r == n_row - 1 and c == n_col - 1:  # Bottom right corner
                    constraint.add_none_of(E, link_up[r][c], link_left[r][c])

                elif r == 0:  # Top wall
                    E.add_constraint(
                          ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Not linked
                        | ~link_down[r][c] &  link_left[r][c] &  link_right[r][c]  # Left & right
                    )
                elif r == n_row - 1:  # Bottom wall
                    E.add_constraint(
                          ~link_up[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Not linked
                        | ~link_up[r][c] &  link_left[r][c] &  link_right[r][c]  # Left & right
                    )
                elif c == 0:  # Left wall
                    E.add_constraint(
                          ~link_up[r][c] & ~link_down[r][c] & ~link_right[r][c]  # Not linked
                        |  link_up[r][c] &  link_down[r][c] & ~link_right[r][c]  # Down & up
                    )
                elif c == n_col - 1:  # Right wall
                    E.add_constraint(
                          ~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c]  # Not linked
                        |  link_up[r][c] &  link_down[r][c] & ~link_left[r][c]  # Down & up
                    )
                else:
                    E.add_constraint(
                          ~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Not linked
                        |  link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c]  # Up & down
                        | ~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] &  link_right[r][c]  # Left & right
                        |  link_up[r][c] &  link_down[r][c] &  link_left[r][c] &  link_right[r][c]  # All 4 directions
                    )
            # Moat tile
            # The goal of the level
            # To avoid duplicate solutions, links only in one direction
            elif tile == '#' and not remove == 'moat':
                blank = False
                E.add_constraint(moat[r][c])
                # Corners
                if r == 0 and c == 0:  # Top left corner
                    constraint.add_at_most_one(E, link_down[r][c], link_right[r][c])
                elif r == 0 and c == n_col - 1:  # Top right corner
                    constraint.add_at_most_one(E, link_down[r][c], link_left[r][c])
                elif r == n_row - 1 and c == 0:  # Bottom left corner
                    constraint.add_at_most_one(E, link_up[r][c], link_right[r][c])
                elif r == n_row - 1 and c == n_col - 1:  # Bottom right corner
                    constraint.add_at_most_one(E, link_up[r][c], link_left[r][c])

                # Sides (w/o corners)
                elif r == 0:  # Top wall
                    constraint.add_at_most_one(E, link_down[r][c], link_left[r][c], link_right[r][c])
                elif r == n_row - 1:  # Bottom wall
                    constraint.add_at_most_one(E, link_up[r][c], link_left[r][c], link_right[r][c])
                elif c == 0:  # Left wall
                    constraint.add_at_most_one(E, link_up[r][c], link_down[r][c], link_right[r][c])
                elif c == n_col - 1:  # Right wall
                    constraint.add_at_most_one(E, link_up[r][c], link_down[r][c], link_left[r][c])
                else:
                    constraint.add_at_most_one(E, link_up[r][c], link_down[r][c], link_left[r][c], link_right[r][c])

            # Ocean tile
            # The start of the water
            # Links only in one direction 
            elif tile == 'U' and not remove == 'ocean':
                blank = False
                E.add_constraint(ocean[r][c])
                if not remove == 'moat':
                    # Corners
                    if r == 0 and c == 0:  # Top left corner
                        constraint.add_exactly_one(E, link_down[r][c], link_right[r][c])
                    elif r == 0 and c == n_col - 1:  # Top right corner
                        constraint.add_exactly_one(E, link_down[r][c], link_left[r][c])
                    elif r == n_row - 1 and c == 0:  # Bottom left corner
                        constraint.add_exactly_one(E, link_up[r][c], link_right[r][c])
                    elif r == n_row - 1 and c == n_col - 1:  # Bottom right corner
                        constraint.add_exactly_one(E, link_up[r][c], link_left[r][c])

                    # Sides (w/o corners)
                    elif r == 0:  # Top wall
                        constraint.add_exactly_one(E, link_down[r][c], link_left[r][c], link_right[r][c])
                    elif r == n_row - 1:  # Bottom wall
                        constraint.add_exactly_one(E, link_up[r][c], link_left[r][c], link_right[r][c])
                    elif c == 0:  # Left wall
                        constraint.add_exactly_one(E, link_up[r][c], link_down[r][c], link_right[r][c])
                    elif c == n_col - 1:  # Right wall
                        constraint.add_exactly_one(E, link_up[r][c], link_down[r][c], link_left[r][c])
                    else:
                        constraint.add_exactly_one(E, link_up[r][c], link_down[r][c], link_left[r][c], link_right[r][c])

                # Corners
                if r == 0 and c == 0:  # Top left corner
                    constraint.add_at_most_one(E, link_down[r][c], link_right[r][c])
                elif r == 0 and c == n_col - 1:  # Top right corner
                    constraint.add_at_most_one(E, link_down[r][c], link_left[r][c])
                elif r == n_row - 1 and c == 0:  # Bottom left corner
                    constraint.add_at_most_one(E, link_up[r][c], link_right[r][c])
                elif r == n_row - 1 and c == n_col - 1:  # Bottom right corner
                    constraint.add_at_most_one(E, link_up[r][c], link_left[r][c])

                # Sides (w/o corners)
                elif r == 0:  # Top wall
                    constraint.add_at_most_one(E, link_down[r][c], link_left[r][c], link_right[r][c])
                elif r == n_row - 1:  # Bottom wall
                    constraint.add_at_most_one(E, link_up[r][c], link_left[r][c], link_right[r][c])
                elif c == 0:  # Left wall
                    constraint.add_at_most_one(E, link_up[r][c], link_down[r][c], link_right[r][c])
                elif c == n_col - 1:  # Right wall
                    constraint.add_at_most_one(E, link_up[r][c], link_down[r][c], link_left[r][c])
                else:
                    constraint.add_at_most_one(E, link_up[r][c], link_down[r][c], link_left[r][c], link_right[r][c])

            # Blank tile
            if blank:
                constraint.add_none_of(E, straight[r][c], curved[r][c], bridge[r][c], moat[r][c], ocean[r][c])
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
            constraint.add_at_most_one(E, straight[r][c], curved[r][c], bridge[r][c], moat[r][c], ocean[r][c])

    
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
        temp = moat[0][0] & (link_down[0][0] | link_right[0][0])
        for r in range(n_row):
            for c in range(n_col):
                if r == 0 and c == 0:  # Top left corner case already handled
                    continue
                elif r == 0 and c == n_col - 1:  # Top right corner
                    temp = temp | moat[r][c] & (link_down[r][c] | link_left[r][c])
                elif r == n_row - 1 and c == 0:  # Bottom left corner
                    temp = temp | moat[r][c] & (link_up[r][c] | link_right[r][c])
                elif r == n_row - 1 and c == n_col - 1: # Bottom right corner
                    temp = temp | moat[r][c] & (link_up[r][c] | link_left[r][c])
                
                # Sides (w/o corners)
                elif r == 0:  # Top wall
                    temp = temp | moat[r][c] & (link_down[r][c] | link_left[r][c] | link_right[r][c])
                elif r == n_row - 1:  # Bottom wall
                    temp = temp | moat[r][c] & (link_up[r][c] | link_left[r][c] | link_right[r][c])
                elif c == 0:  # Left wall
                    temp = temp | moat[r][c] & (link_up[r][c] | link_down[r][c] | link_right[r][c])
                elif c == n_col - 1:  # Right wall
                    temp = temp | moat[r][c] & (link_up[r][c] | link_down[r][c] | link_left[r][c])
                else:
                    temp = temp | moat[r][c] & (link_up[r][c] | link_down[r][c] | link_left[r][c] | link_right[r][c])
        E.add_constraint(temp)  # Find a solution

    return E


def get_length(solution):
    """
    Given an output from the SAT solver containing a solution to the level, 
    finds the length of the solution path.
    solution - The output from the SAT solver

    Returns an encoding with the constraints to get the length.
    Once a solution has been found, the length of the solution path
    is the length propositions at the bottom right tile stored as
    (2^0)(N(0)) + (2^1)(N(2)) + (2^2)(N(2)) + ...
    """

    # Clear constraints so that we can run this function more than once
    F._custom_constraints = set()

    # Get configuration of water
    for r in range(n_row):
        for c in range(n_col):
            if (r > 0 and solution[link_up[r][c]] 
                    or r < n_row - 1 and solution[link_down[r][c]] 
                    or c > 0 and solution[link_left[r][c]] 
                    or c < n_col - 1 and solution[link_right[r][c]]):
                F.add_constraint(water[r][c])
            else:
                F.add_constraint(~water[r][c])

    # Set length for top left tile
    # The length is 1 if there is water, 0 otherwise
    F.add_constraint((water[0][0] & length[0][0][0]) 
                  | (~water[0][0] & ~length[0][0][0]))
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
            propagate_carry = length[prev_row][prev_col][0]

            # If a tile contains water, we "add one" to the previous count
            F.add_constraint(water[r][c] >> (~length[prev_row][prev_col][0] &  length[r][c][0] 
                                             | length[prev_row][prev_col][0] & ~length[r][c][0]))
            for i in range(1, n_length):
                F.add_constraint(water[r][c] >> ((~propagate_carry & ~length[prev_row][prev_col][i]) >> ~length[r][c][i]))
                F.add_constraint(water[r][c] >> ((~propagate_carry &  length[prev_row][prev_col][i]) >>  length[r][c][i]))
                F.add_constraint(water[r][c] >> (( propagate_carry & ~length[prev_row][prev_col][i]) >>  length[r][c][i]))
                F.add_constraint(water[r][c] >> (( propagate_carry &  length[prev_row][prev_col][i]) >> ~length[r][c][i]))
                propagate_carry = propagate_carry & length[prev_row][prev_col][i]

            # Otherwise, keep the count the same
            for i in range(n_length):
                F.add_constraint(~water[r][c] >> (~length[prev_row][prev_col][i] & ~length[r][c][i] 
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
            print(f"Removed {len(self_loops) - 2} self-loops.")


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

        # Visualize longest solution path
        longest_solution = viz.convert_solution(longest_solution_dict, level_layout)
        viz.viz_level(longest_solution)
