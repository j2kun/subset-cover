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
class ChoiceSetMember:
    '''Whether an element is chosen to be in a choice set.'''
    element: int
    choice_set: int
    variable: Any


@dataclass(frozen=True)
class HitSet:
    '''The sets you're trying to hit by picking choice sets.

    I.e., the subsets of rings that interact with magical effects.
    '''
    set_size: int
    elements: List[int]
    variable: Any


class SubsetCoverZ3Cardinality(SubsetCover):
    '''
    An implementation of the subset cover problem that uses Z3,
    and encodes the problem in such a way that does not require
    an enumeration of all possible choice sets.

    Uses cardinality constraints instead of integer inequalities.
    '''
    def solve(self, parameters: SubsetCoverParameters) -> SubsetCoverSolution:
        elements = list(range(parameters.num_elements))
        choice_sets = list(range(parameters.num_choice_sets))
        hit_set_size = parameters.hit_set_size

        choice_set_members = ChoiceSetMembers(elements, choice_sets)

        # each choice set must have a specific size
        choice_set_size_constraints = []
        for memberships in choice_set_members.grouped_by_choice_set():
            args = [mem.variable for mem in memberships] + [parameters.choice_set_size]
            choice_set_size_constraints.append(AtMost(args))
            choice_set_size_constraints.append(AtLeast(args))

        hit_sets = dict((tuple(sorted(elts)),
                         HitSet(set_size=hit_set_size,
                                elements=elts,
                                variable=Bool(f"Hit_{elts}")))
                        for elts in combinations(elements, hit_set_size))

        implications = []
        '''
        For a hit set like (1,2), we construct the implication,
        for each choice set i,

            Member_(i,1) and Member_(i,2) => Hit_(1,2)

        '''
        for choice_set_index in choice_sets:
            mems = choice_set_members.for_choice_set_index(choice_set_index)
            for membership_subset in combinations(mems, hit_set_size):
                hit_set = hit_sets[tuple(
                    sorted([mem.element for mem in membership_subset]))]
                implications.append(
                    Implies(
                        And(*[mem.variable for mem in membership_subset]),
                        hit_set.variable))
        '''
        For a hit set like (1,2), we construct the implication:

            Hit_(1,2) =>
              Member(1, 1) AND Member(1, 2)
              OR Member(2, 1) AND Member(2, 2)
              OR ...
        '''
        for hit_set in hit_sets.values():
            clauses = []

            for choice_set_index in choice_sets:
                mems = [
                    choice_set_members.for_choice_set_index_and_element(choice_set, elt)
                    for elt in hit_set.elements
                ]
                clauses.append(And(*[mem.variable for mem in mems]))

            implications.append(Implies(hit_set.variable, Or(*clauses)))

        solver = Solver()
        solver.set("timeout", 60*5)
        solver.set("sat.cardinality.solver", True)
        for size_constraint in choice_set_size_constraints:
            solver.add(size_constraint)

        for hit_set in hit_sets.values():
            solver.add(hit_set.variable)

        for impl in implications:
            solver.add(impl)
        '''
        with open(f'subset_cover_10_5_2_{num_choice_sets}.smt2', 'w') as outfile:
            outfile.write(solver.to_smt2())

        print(f"Solver has {len(solver.assertions())} assertions.")
        print(
            f"Starting solve, checking if {num_choice_sets} choice sets is enough."
        )
        '''
        start = time()
        result = solver.check()
        end = time()

        if result == unsat:
            return SubsetCoverSolution(status=SolveStatus.INFEASIBLE,
                                       solve_time_seconds=end - start)
        if result == unknown:
            return SubsetCoverSolution(status=SolveStatus.UNKNOWN,
                                       solve_time_seconds=end - start)

        model = solver.model()

        realized_choice_sets = []
        for choice_set, mems in memberships_by_choice_set.items():
            choice_set_members = list(
                sorted([
                    mem.element for mem in mems
                    if model.evaluate(mem.variable)
                ]))
            realized_choice_sets.append(choice_set_members)

        '''
        print(
            f"Chose {len(realized_choice_sets)} sets: {realized_choice_sets}")
        '''
        return SubsetCoverSolution(status=SolveStatus.SOLVED,
                                   solve_time_seconds=end - start)


if __name__ == "__main__":
    result = SubsetCoverZ3Cardinality().solve(
        SubsetCoverParameters(num_elements=7,
                              hit_set_size=2,
                              choice_set_size=3,
                              num_choice_sets=6))

    print(result)
