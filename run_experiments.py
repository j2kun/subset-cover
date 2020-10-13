from collections import defaultdict
from experiments import experiments
from subset_cover_ilp import SubsetCoverILP
from subset_cover_z3 import SubsetCoverZ3
from subset_cover_z3_brute_force import SubsetCoverZ3BruteForce
from subset_cover_z3_cardinality import SubsetCoverZ3Cardinality
import json

methods = [
    SubsetCoverILP,
    SubsetCoverZ3,
    SubsetCoverZ3BruteForce,
    SubsetCoverZ3Cardinality,
]

if __name__ == "__main__":
    data = defaultdict(lambda: defaultdict(list))
    for experiment in experiments:
        print(experiment)
        for method in methods:
            result = method().solve(experiment.parameters)
            print(f"{method.__name__}: {result.solve_time_seconds} ({result.status})")
            data[experiment.family][method.__name__].insert(
                    experiment.order, result.solve_time_seconds)

    with open('experiment_results.json', 'w') as outfile:
        outfile.write(json.dumps(data))
