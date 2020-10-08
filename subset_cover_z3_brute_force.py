from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from itertools import product
from subset_cover import SolveStatus
from subset_cover import SubsetCover
from subset_cover import SubsetCoverParameters
from subset_cover import SubsetCoverSolution
from time import time
from typing import Any
from typing import List
from z3 import *


@dataclass(frozen=True)
class ChoiceSet:
    '''The set you're allowed to choose.

    I.e., the rings you put on your fingers.
    '''
    set_size: int
    elements: List[int]
    variable: Any


@dataclass(frozen=True)
class HitSet:
    '''The sets you're trying to hit by picking choice sets.

    I.e., the subsets of rings that interact with magical effects.
    '''
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
            ChoiceSet(
                set_size=choice_set_size,
                elements=elts,
                variable=Bool(f"Choice_{elts}")
            )
            for elts in combinations(elements, choice_set_size)
        ]

        hit_sets = dict(
            (
                tuple(sorted(elts)),
                HitSet(
                    set_size=hit_set_size,
                    elements=elts,
                    variable=Bool(f"Hit_{elts}")
                )
            )
            for elts in combinations(elements, hit_set_size)
        )

        implications = []

        '''
        For a choice set like (1,2,3), we construct the implication,
        for each subset of size hit_set_size (e.g. = 2),

            ChoiceSet_(1,2,3) => Hit_(1,2)
            ChoiceSet_(1,2,3) => Hit_(2,3)
            ChoiceSet_(1,2,3) => Hit_(1,3)

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
              ChoiceSet(1,2,3) OR
              ChoiceSet(1,2,4) OR
              ...
        '''
        for hit_set in hit_sets.values():
            relevant_choice_set_vars = [
                choice_set.variable
                for choice_set in hit_set_to_choice_set_lookup[hit_set]
            ]
            implications.append(
                Implies(
                    hit_set.variable,
                    Or(*relevant_choice_set_vars)))

        # needed for minimization of number of chosen sets
        choice_counters = []
        for i, choice_set in enumerate(choice_sets):
            count_var = Int('count_' + str(i))
            implications.append(choice_set.variable == count_var)
            choice_counters.append(count_var)

        solver = Solver()
        for hit_set in hit_sets.values():
            solver.add(hit_set.variable)  # all must be hit

        for impl in implications:
            solver.add(impl)

        solver.add(sum(choice_counters) == parameters.num_choice_sets)

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
            c.elements for c in choice_sets
            if model.evaluate(c.variable)
        ]
        actual_hit_sets = [
            h.elements for h in hit_sets.values()
            if model.evaluate(h.variable)
        ]
        n = len(elements)
        max_hits = int(n * (n-1) / 2)

        return SubsetCoverSolution(status=SolveStatus.SOLVED,
                                   solve_time_seconds=end - start)

if __name__ == "__main__":
    result = SubsetCoverZ3BruteForce().solve(
        SubsetCoverParameters(num_elements=7,
                              hit_set_size=3,
                              choice_set_size=2,
                              num_choice_sets=4))

    print(result)
