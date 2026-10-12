import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from photon import PhotonState
from optics.beam_splitter import beam_splitter
from optics.mode_network import embed_two_mode_component


# Create a photon in mode 0 of a 4-mode system
photon = PhotonState(
    modes=4,
    input_mode=0
)

print("Initial photon state:")
print(photon)

print("\nInitial probabilities:")
print(photon.probabilities())


# Create a 50:50 beam splitter
bs = beam_splitter(0.5)


# Apply the beam splitter between mode 0 and mode 2
four_mode_bs = embed_two_mode_component(
    bs,
    modes=4,
    mode_a=0,
    mode_b=2
)


# Apply the optical network
photon.apply_unitary(four_mode_bs)


print("\nOutput photon state:")
print(photon)

print("\nOutput probabilities:")
print(photon.probabilities())

print("\nTotal probability:")
print(photon.probabilities().sum())