import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from hom import hom_dip
from visualization.plots import plot_hom_dip


distinguishabilities, coincidences = hom_dip(
    points=100
)

plot_hom_dip(
    distinguishabilities,
    coincidences
)