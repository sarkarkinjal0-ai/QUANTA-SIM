from fock import FockState


state1 = FockState([1, 0])

state2 = FockState([1, 1])

state3 = FockState([2, 0])


print("State 1:")
print(state1)

print("Total photons:")
print(state1.photon_number())


print("\nState 2:")
print(state2)

print("Total photons:")
print(state2.photon_number())


print("\nState 3:")
print(state3)

print("Total photons:")
print(state3.photon_number())