from collections import defaultdict
from common_model import HitSet
from dataclasses import dataclass
from itertools import combinations
from itertools import product
from subset_cover import SolveStatus
from subset_cover import SubsetCover
from subset_cover import SubsetCoverParameters
from subset_cover import SubsetCoverSolution
from subset_cover import print_table
from time import time
from typing import Any
from typing import List
from z3 import And
from z3 import AtLeast
from z3 import AtMost
from z3 import Bool
from z3 import Implies
from z3 import Or
from z3 import Solver
from z3 import sat
from z3 import unknown
from z3 import unsat


@dataclass(frozen=True)
class ChoiceSet:
    set_size: int
    elements: List[int]
    variable: Any


class SubsetCoverZ3BruteForce(SubsetCover):
    '''
    An implementation of the subset cover problem that uses Z3, and encodes the
    problem in such a way that enumerates all possible choice sets.
    '''
    def solve(self, parameters: SubsetCoverParameters) -> SubsetCoverSolution:
        choice_set_size = parameters.choice_set_size
        hit_set_size = parameters.hit_set_size
        elements = list(range(parameters.num_elements))
        choice_sets = [
            ChoiceSet(set_size=choice_set_size,
                      elements=elts,
                      variable=Bool(f"Choice_{elts}"))
            for elts in combinations(elements, choice_set_size)
        ]

        hit_sets = dict((tuple(sorted(elts)),
                         HitSet(set_size=hit_set_size,
                                elements=elts,
                                variable=Bool(f"Hit_{elts}")))
                        for elts in combinations(elements, hit_set_size))

        implications = []
        '''
        For a choice set like (1,2,3), we construct the implication,
        for each subset of size hit_set_size (e.g. = 2),

            Choice_(1,2,3) => Hit_(1,2)
            Choice_(1,2,3) => Hit_(2,3)
            Choice_(1,2,3) => Hit_(1,3)

        '''
        # also builds up this index
        hit_set_to_choice_set_lookup = defaultdict(set)
        for choice_set in choice_sets:
            for hit_set_key in combinations(choice_set.elements, hit_set_size):
                hit_set = hit_sets[tuple(sorted(hit_set_key))]
                hit_set_to_choice_set_lookup[hit_set].add(choice_set)
                implications.append(
                    Implies(choice_set.variable, hit_set.variable))
        '''
        For a hit set like (1,2), we construct the implication:

            Hit_(1,2) =>
              Choice(1,2,3) OR
              Choice(1,2,4) OR
              ...
        '''
        for hit_set in hit_sets.values():
            relevant_choice_set_vars = [
                choice_set.variable
                for choice_set in hit_set_to_choice_set_lookup[hit_set]
            ]
            implications.append(
                Implies(hit_set.variable, Or(*relevant_choice_set_vars)))

        args = [cs.variable
                for cs in choice_sets] + [parameters.num_choice_sets]
        choice_sets_at_most = AtMost(*args)
        choice_sets_at_least = AtLeast(*args)

        solver = Solver()
        solver.set("timeout", 1000 * 60 * 15)
        for hit_set in hit_sets.values():
            solver.add(hit_set.variable)  # all must be hit

        for impl in implications:
            solver.add(impl)

        solver.add(choice_sets_at_most)
        solver.add(choice_sets_at_least)

        # print(solver.to_smt2())

        start = time()
        result = solver.check()
        end = time()
        elapsed = end - start

        if result == unsat:
            return SubsetCoverSolution(status=SolveStatus.INFEASIBLE,
                                       solve_time_seconds=end - start)
        if result == unknown:
            return SubsetCoverSolution(status=SolveStatus.UNKNOWN,
                                       solve_time_seconds=end - start)

        model = solver.model()
        chosen_sets = [
            c.elements for c in choice_sets if model.evaluate(c.variable)
        ]
        actual_hit_sets = [
            h.elements for h in hit_sets.values() if model.evaluate(h.variable)
        ]
        n = len(elements)
        max_hits = int(n * (n - 1) / 2)
        # print(chosen_sets)

        return SubsetCoverSolution(status=SolveStatus.SOLVED,
                                   solve_time_seconds=end - start)


if __name__ == "__main__":
    from math import comb

    for n in range(8, 16):
        k = int(n / 2)
        l = 3
        max_num_sets = int(2 * comb(n, l) / comb(k, l))
        params = SubsetCoverParameters(num_elements=n,
                                       choice_set_size=k,
                                       hit_set_size=l,
                                       num_choice_sets=max_num_sets)
        print_table(params, SubsetCoverZ3BruteForce().solve(params), header=(n == 8))
