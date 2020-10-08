from experiments import experiments
from subset_cover_ilp import SubsetCoverILP
from subset_cover_z3 import SubsetCoverZ3
from subset_cover_z3_brute_force import SubsetCoverZ3BruteForce

methods = [
    SubsetCoverILP,
    SubsetCoverZ3,
    SubsetCoverZ3BruteForce,
]

if __name__ == "__main__":
    for experiment in experiments:
        print(experiment)
        for method in methods:
            result = method().solve(experiment.parameters)
            print(f"{method.__name__}: {result.solve_time_seconds} ({result.status})")
