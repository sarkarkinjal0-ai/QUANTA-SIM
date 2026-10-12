from hom import hom_dip


distinguishabilities, coincidences = hom_dip(
    points=6
)


print("Distinguishability:")
print(distinguishabilities)

print("\nCoincidence Probability:")
print(coincidences)