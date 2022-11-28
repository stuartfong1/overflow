"""
Create level layout to be solved.
Each string in the list represents a row in the level.
All rows in the level must have the same length.

##################
#                #
#  Tiles:        #
#  - = straight  #
#  + = bridge    #
#  L = curved    #
#  # = moat      #
#  U = ocean     #
#                #
##################
"""


# level_layout = [  # Longest solution contains self-loop
#     "L-L###L-L",
#     "-LLL--LL-",
#     "--L---LL-",
#     "L+LLLL+-L",
#     "LLLLLL---",
#     "      U  "
# ]

level_layout = [  # Level seen in project proposal
    " L-###L-L",
    "-LLLLL-LL",
    "LL-L++++L",
    "L+L--L+L-",
    "LL-LLLL-L",
    "     U   "
]

# level_layout = [  # Two possible solution paths with different lengths
#     "-LL",
#     "U+#",
#     "LL-"
# ]

# level_layout = [  # Two possible solution paths with the same length
#     "UL",
#     "L#"
# ]

# level_layout = [  # Multiple oceans
#     "L---LU-L",
#     "-L-UL-U-",
#     "#-U---L-",
#     "LLL-UL+L",
#     "-L+-L-##",
#     "--LLUL#-",
#     "L+LL---L",
#     "#LL----#"
# ]


############################################################

# Get maximum row length
if len(level_layout) > 0:
    max_col = max([len(i) for i in level_layout])

# If the level layout has a non-rectangular shape,
# pad shorter rows with blank tiles
for i, e in enumerate(level_layout):
    if len(e) < max_col:
        level_layout += ' ' * (max_col - len(i))

# Pad dimensions to at least 2 by 2
if len(level_layout) == 0 or len(level_layout[0]) == 0:
    level_layout = ["  ", "  "]
if len(level_layout) == 1:
    level_layout = level_layout + [' ' * len(level_layout[0])]
if len(level_layout[0]) == 1:
    level_layout = [i + ' ' for i in level_layout]
