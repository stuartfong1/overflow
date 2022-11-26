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