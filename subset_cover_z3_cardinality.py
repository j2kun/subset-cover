from collections import defaultdict
from common_model import ChoiceSetMember
from common_model import ChoiceSetMembers
from common_model import HitSet
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
from z3 import And
from z3 import Implies
from z3 import AtLeast
from z3 import AtMost
from z3 import Bool
from z3 import Or
from z3 import Solver
from z3 import sat
from z3 import unknown
from z3 import unsat


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

        choice_set_members = ChoiceSetMembers(elements, choice_sets, Bool)

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
                    choice_set_members.for_choice_set_index_and_element(choice_set_index, elt)
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
        for choice_set_index in choice_sets:
            mems = choice_set_members.for_choice_set_index(choice_set_index)
            choice_set = list(
                sorted([
                    mem.element for mem in mems
                    if model.evaluate(mem.variable)
                ]))
            realized_choice_sets.append(choice_set)

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
