import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from photon import PhotonState
from optics.beam_splitter import beam_splitter


photon = PhotonState(modes=2, input_mode=0)

print("Initial photon state:")
print(photon)

print("\nInitial probabilities:")
print(photon.probabilities())


bs = beam_splitter(0.5)

photon.apply_unitary(bs)

print("\nAfter 50:50 beam splitter:")
print(photon)

print("\nOutput probabilities:")
print(photon.probabilities())