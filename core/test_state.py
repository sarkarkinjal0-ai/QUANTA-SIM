from core.core.state import basis_state, probabilities

state = basis_state(0, 2)

print("State:", state)
print("Probabilities:", probabilities(state))