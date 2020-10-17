from subset_cover import SubsetCoverParameters
from subset_cover_ilp import SubsetCoverILP
from subset_cover_z3_brute_force import SubsetCoverZ3BruteForce
from subset_cover_z3_cardinality import SubsetCoverZ3Cardinality
from subset_cover_z3_integer import SubsetCoverZ3Integer


def print_table(parameters, solution, header=False, method=""):
    if header:
        print("method,status,solve_time_seconds,"
              "num_elements,choice_set_size,hit_set_size,"
              "num_choice_sets")

    print(f"{method},"
          f"{solution.status.name},"
          f"{solution.solve_time_seconds:.4f},"
          f"{parameters.num_elements},"
          f"{parameters.choice_set_size},"
          f"{parameters.hit_set_size},"
          f"{parameters.num_choice_sets}")


hard_feasible = SubsetCoverParameters(
    num_elements=7,
    choice_set_size=3,
    hit_set_size=2,
    num_choice_sets=7,
)

hard_infeasible = SubsetCoverParameters(
    num_elements=7,
    choice_set_size=3,
    hit_set_size=2,
    num_choice_sets=6,
)

methods = [
    SubsetCoverILP,
    SubsetCoverZ3Integer,
    SubsetCoverZ3BruteForce,
    SubsetCoverZ3Cardinality,
]


def run_experiment(params):
    header = True
    for method in methods:
        solution = method().solve(params)
        print_table(params, solution, header=header, method=method.__name__)
        header = False

if __name__ == "__main__":
    print("hard feasible")
    run_experiment(hard_feasible)

    print("hard infeasible")
    run_experiment(hard_infeasible)
