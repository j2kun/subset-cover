from collections import defaultdict
from common_model import ChoiceSetMember
from common_model import ChoiceSetMembers
from common_model import HitSet
from dataclasses import dataclass
from itertools import combinations
from itertools import product
from math import comb
from subset_cover import SolveStatus
from subset_cover import SubsetCover
from subset_cover import SubsetCoverParameters
from subset_cover import SubsetCoverSolution
from time import time
from typing import Any
from typing import List
from z3 import And
from z3 import Implies
from z3 import Int
from z3 import Or
from z3 import Solver
from z3 import sat
from z3 import unknown
from z3 import unsat


class MinSubsetCoverZ3Integer(SubsetCover):
    '''
    An implementation of the subset cover problem that uses Z3,
    and encodes the problem in such a way that does not require
    an enumeration of all possible choice sets.
    '''
    def solve(self, parameters: SubsetCoverParameters) -> SubsetCoverSolution:
        num_choice_sets = int(
            2 * comb(parameters.num_elements, parameters.hit_set_size) /
            comb(parameters.choice_set_size, parameters.hit_set_size))
        elements = list(range(parameters.num_elements))
        choice_sets = list(range(num_choice_sets))
        hit_set_size = parameters.hit_set_size

        choice_set_members = ChoiceSetMembers(elements, choice_sets, Int)

        '''
        TODO: finish this

        Need to make this more like the ILP model with a binary
        switch for whether the set is chosen,
        then minimize the sum of switches.
        '''
        # each choice set must have a specific size
        choice_set_size_constraints = [
            sum(mem.variable
                for mem in memberships) == parameters.choice_set_size
            for memberships in choice_set_members.grouped_by_choice_set()
        ]

        hit_sets = dict((tuple(sorted(elts)),
                         HitSet(set_size=hit_set_size,
                                elements=elts,
                                variable=Int(f"Hit_{elts}")))
                        for elts in combinations(elements, hit_set_size))

        implications = []
        '''
        For a hit set like (1,2), we construct the implication,
        for each choice set i,

            Member_(i,1) == 1 and Member_(i,2) == 1 => Hit_(1,2) == 1

        '''
        for choice_set_index in choice_sets:
            mems = choice_set_members.for_choice_set_index(choice_set_index)
            for membership_subset in combinations(mems, hit_set_size):
                hit_set = hit_sets[tuple(
                    sorted([mem.element for mem in membership_subset]))]
                implications.append(
                    Implies(
                        And(*[mem.variable == 1 for mem in membership_subset]),
                        hit_set.variable == 1))
        '''
        For a hit set like (1,2), we construct the implication:

            Hit_(1,2) == 1 =>
              Member(1, 1) == 1 AND Member(1, 2) == 1
              OR
              Member(2, 1) == 1 AND Member(2, 2) == 1
              OR
              ...
        '''
        for hit_set in hit_sets.values():
            clauses = []

            for choice_set in choice_sets:
                mems = [
                    choice_set_members.for_choice_set_index_and_element(
                        choice_set, elt) for elt in hit_set.elements
                ]
                clauses.append(And(*[mem.variable == 1 for mem in mems]))

            implications.append(Implies(hit_set.variable == 1, Or(*clauses)))

        solver = Solver()
        solver.set("timeout", 60 * 5 * 1000)
        for size_constraint in choice_set_size_constraints:
            solver.add(size_constraint)

        for var in choice_set_members.all_variables():
            solver.add(var >= 0)
            solver.add(var <= 1)

        for hit_set in hit_sets.values():
            solver.add(hit_set.variable == 1)

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
                    if model.evaluate(mem.variable).as_long() > 0
                ]))
            realized_choice_sets.append(choice_set)

        print(
            f"Chose {len(realized_choice_sets)} sets: {realized_choice_sets}")
        return SubsetCoverSolution(status=SolveStatus.SOLVED,
                                   solve_time_seconds=end - start)


if __name__ == "__main__":
    n = 10
    k = int(n / 2)
    l = 3
    max_num_sets = int(2 * comb(n, l) / comb(k, l))
    params = SubsetCoverParameters(num_elements=n,
                                   choice_set_size=k,
                                   hit_set_size=l,
                                   num_choice_sets=max_num_sets)
    print(params)
    print(MinSubsetCoverZ3Integer().solve(params))
