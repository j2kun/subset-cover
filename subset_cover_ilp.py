from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from itertools import product
from typing import Any
from typing import List
from typing import Tuple
from z3 import *

from ortools.linear_solver import pywraplp


@dataclass(frozen=True)
class ChoiceSetMember:
    '''Whether an element is chosen to be in a choice set.'''
    element: int
    choice_set_index: int
    variable: Any


@dataclass(frozen=True)
class IsHit:
    '''Whether a hit set is hit by a given choice set.'''
    hit_set: Tuple[int]
    choice_set_index: int
    variable: Any


class ChoiceSetMembers:
    '''A class that constructs ChoiceSetMember instances and the associated lookups.'''
    def __init__(self, solver, elements, choice_set_indices):
        self.memberships = [
            ChoiceSetMember(element=element,
                            choice_set_index=choice_set_index,
                            variable=solver.IntVar(
                                0, 1,
                                f"Member_({choice_set_index},{element})"))
            for (element,
                 choice_set_index) in product(elements, choice_set_indices)
        ]

        self.memberships_lookup = dict(
            ((mem.choice_set_index, mem.element), mem)
            for mem in self.memberships)

        self.memberships_by_choice_set = defaultdict(set)
        for membership in self.memberships:
            self.memberships_by_choice_set[membership.choice_set_index].add(
                membership)

    def for_choice_set_index_and_element(self, choice_set_index, element):
        return self.memberships_lookup[(choice_set_index, element)]

    def for_choice_set_index(self, choice_set_index):
        return self.memberships_by_choice_set[choice_set_index]


def make_hit_sets(elements, hit_set_size):
    return [
        tuple(sorted(elts)) for elts in combinations(elements, hit_set_size)
    ]


class IsHits:
    '''A class that defines IsHit variables for each
    hit set and choice set pair.
    '''
    def __init__(self, solver, hit_sets, choice_set_indices):
        self.is_hit_variables = [
            IsHit(hit_set=hit_set,
                  choice_set_index=choice_set_index,
                  variable=solver.IntVar(
                      0, 1, f"IsHit_({hit_set},{choice_set_index})")) for
            hit_set, choice_set_index in product(hit_sets, choice_set_indices)
        ]

        self.lookup = {(x.hit_set, x.choice_set_index): x
                       for x in self.is_hit_variables}

        self.by_hit_set = defaultdict(set)
        for is_hit in self.is_hit_variables:
            self.by_hit_set[is_hit.hit_set].add(is_hit)

    def all(self):
        return self.is_hit_variables

    def for_hit_set(self, hit_set):
        return self.by_hit_set[hit_set]


def construct_problem(num_elements, choice_set_size, hit_set_size,
                      num_choice_sets):
    solver = pywraplp.Solver.CreateSolver('subset_cover', 'SCIP')

    elements = list(range(num_elements))
    choice_set_indices = list(range(num_choice_sets))
    hit_sets = make_hit_sets(elements, hit_set_size)

    choice_set_members = ChoiceSetMembers(solver, elements, choice_set_indices)
    is_hits = IsHits(solver, hit_sets, choice_set_indices)

    # Each choice set must have size choice_set_size.
    for choice_set_index in choice_set_indices:
        members = choice_set_members.for_choice_set_index(choice_set_index)
        member_vars = [x.variable for x in members]
        solver.Add(sum(member_vars) == choice_set_size)

    # Each hit set must be hit by at least one choice set
    for hit_set in hit_sets:
        is_hits_for_hit_set = is_hits.for_hit_set(hit_set)
        is_hit_vars = [x.variable for x in is_hits_for_hit_set]
        solver.Add(sum(is_hit_vars) >= 1)

    # For each choice set and IsHit, the IsHit value is 1 forces
    # the corresponding hit set to have all its elements in the choice set.
    for is_hit in is_hits.all():
        choice_set_index = is_hit.choice_set_index
        hit_set = is_hit.hit_set

        lhs = sum(
            choice_set_members.for_choice_set_index_and_element(
                choice_set_index, element).variable for element in hit_set)
        rhs = hit_set_size * is_hit.variable

        # if IsHit == 1, then the LHS must be at least hit_set_size, but
        # because there are only hit_set_size many terms in LHS, that is also
        # the max value, so all the variables in LHS must equal 1, i.e., all
        # the hit set elements are in the choice set.
        solver.Add(lhs >= rhs)

    # The objective does not matter because we are looking for a feasible solution
    solver.Maximize(1)
    time_limit_seconds = 120
    solver.SetTimeLimit(time_limit_seconds * 1000)

    print(
        f"Starting solve, checking if {num_choice_sets} choice sets is enough."
    )
    print(f"Model has {solver.NumVariables()} variables "
          f"and {solver.NumConstraints()} constraints.")

    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        sets = []
        for choice_set_index in choice_set_indices:
            members = choice_set_members.for_choice_set_index(choice_set_index)
            nonzero_members = tuple(
                sorted([
                    x.element for x in members
                    if x.variable.solution_value() == 1
                ]))
            sets.append(nonzero_members)
        return sorted(sets)
    else:
        # give up and assume infeasible
        return None


if __name__ == "__main__":
    num_elements = 7
    choice_set_size = 3
    hit_set_size = 2
    # print(construct_problem(10, 5, 3, 50))


    num_sets = 6
    best_so_far = None
    while True:
        result = construct_problem(num_elements, choice_set_size, hit_set_size,
                                   num_sets)
        if result is not None:
            best_so_far = result
            break
        num_sets += 1

    print(best_so_far)
