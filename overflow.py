from bauhaus import Encoding, proposition, constraint, print_theory
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

# Constraints
def theory():
    # Each level has a certain layout of tiles
    # Each tile can only link in a certain way
    for r, row in enumerate(level_layout):
        for c, tile in enumerate(row[0]):
            print(c)
            # Straight tile
            if tile == '-':
                E.add_constraint(straight[r][c])
                if r == 0 and c == 0 or r == n_row - 1 and c == 0 or ...:  # TODO: Same for two other corners
                    E.add_constraint(~water[r][c])
                elif c == 0 or c == n_col - 1:  # Left & right side
                    E.add_constraint(water[r][c] >> (
                        ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])
                    ))
                # TODO: Will also need to cover up and down
                else:
                    E.add_constraint(water[r][c] >> (
                        ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])  # Up & down
                        | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] &  link_right[r][c] & water[r][c-1] & water[r][c+1])  # Left & right
                    ))
            # Curved tile
            elif tile == 'L':
                E.add_constraint(curved[r][c])
                E.add_constraint(water[r][c] >> (
                      ( link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r][c-1])  # Up & left
                    | ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r-1][c] & water[r][c+1])  # Up & right
                    | (~link_up[r][c] &  link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r+1][c] & water[r][c-1])  # Down & left
                    | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r+1][c] & water[r][c+1])  # Down & right
                ))
            # Bridge tile
            elif tile == '+':
                E.add_constraint(bridge[r][c])
                E.add_constraint(water[r][c] >> (
                      ( link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & water[r+1][c])  # Up & down
                    | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] &  link_right[r][c] & water[r][c-1] & water[r][c+1])  # Left & right
                    | ( link_up[r][c] &  link_down[r][c] &  link_left[r][c] &  link_right[r][c] & water[r-1][c] & water[r+1][c] & water[r][c-1] & water[r][c+1])  # All 4 directions
                ))
            # Moat tile
            elif tile == 'M':
                E.add_constraint(moat[r][c])
                E.add_constraint(water[r][c] >> (
                      ( link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r-1][c] & ~moat[r-1][c])  # Up
                    | (~link_up[r][c] &  link_down[r][c] & ~link_left[r][c] & ~link_right[r][c] & water[r+1][c] & ~moat[r+1][c])  # Down
                    | (~link_up[r][c] & ~link_down[r][c] &  link_left[r][c] & ~link_right[r][c] & water[r][c-1] & ~moat[r][c-1])  # Left
                    | (~link_up[r][c] & ~link_down[r][c] & ~link_left[r][c] &  link_right[r][c] & water[r][c+1] & ~moat[r][c+1])  # Right
                ))
            # Ocean tile
            elif tile == 'O':
                E.add_constraint(ocean[r][c])
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
                    | water[r][c+1] & link_right[r][c])
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
    temp  = moat[0][0] & water[0][0]
    for r in range(n_row):
        for c in range(n_col):
            temp = temp | moat[r][c] & water[r][c]
    E.add_constraint(win >> temp)
    E.add_constraint(win)

    return E

if __name__ == "__main__":
    T = theory()
    T = T.compile()

    print("\nSatisfiable: %s" % T.satisfiable())
    print_theory(T.solve(), 'objects')