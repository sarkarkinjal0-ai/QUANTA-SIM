from hom import hom_interference


for distinguishability in [0.0, 0.5, 1.0]:

    probabilities = hom_interference(
        distinguishability
    )

    print(
        f"\nDistinguishability = {distinguishability}"
    )

    print("P(|2,0>) =", probabilities[0])
    print("P(|1,1>) =", probabilities[1])
    print("P(|0,2>) =", probabilities[2])

    print("Total Probability =", probabilities.sum())