from common_model import ChoiceSetMember
from common_model import ChoiceSetMembers
from common_model import IsHit
from common_model import IsHits
from common_model import make_hit_sets
from subset_cover import SolveStatus
from subset_cover import SubsetCover
from subset_cover import SubsetCoverParameters
from subset_cover import SubsetCoverSolution
from subset_cover import print_table
from time import time

from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model


class SubsetCoverCP(SubsetCover):
    '''
    An implementation of the subset cover problem formulated as
    a constraint satisfaction problem.

    This is identical to SubsetCoverILP,
    but there is no optimization objective.
    '''
    def solve(self, parameters: SubsetCoverParameters) -> SubsetCoverSolution:
        model = cp_model.CpModel()

        def make_binary_var(name: str):
            return model.NewIntVar(0, 1, name)

        elements = list(range(parameters.num_elements))
        choice_set_indices = list(range(parameters.num_choice_sets))
        hit_sets = make_hit_sets(elements, parameters.hit_set_size)

        choice_set_members = ChoiceSetMembers(elements, choice_set_indices,
                                              make_binary_var)
        is_hits = IsHits(hit_sets, choice_set_indices, make_binary_var)

        # Each choice set must have size choice_set_size.
        for choice_set_index in choice_set_indices:
            members = choice_set_members.for_choice_set_index(choice_set_index)
            member_vars = [x.variable for x in members]
            model.Add(sum(member_vars) == parameters.choice_set_size)

        # Each hit set must be hit by at least one choice set
        for hit_set in hit_sets:
            is_hits_for_hit_set = is_hits.for_hit_set(hit_set)
            is_hit_vars = [x.variable for x in is_hits_for_hit_set]
            model.Add(sum(is_hit_vars) >= 1)

        # For each choice set and IsHit, the IsHit value is 1 forces
        # the corresponding hit set to have all its elements in the choice set.
        for is_hit in is_hits.all():
            choice_set_index = is_hit.choice_set_index
            hit_set = is_hit.hit_set

            lhs = sum(
                choice_set_members.for_choice_set_index_and_element(
                    choice_set_index, element).variable for element in hit_set)
            rhs = parameters.hit_set_size * is_hit.variable

            # if IsHit == 1, then the LHS must be at least hit_set_size, but
            # because there are only hit_set_size many terms in LHS, that is also
            # the max value, so all the variables in LHS must equal 1, i.e., all
            # the hit set elements are in the choice set.
            model.Add(lhs >= rhs)

        time_limit_seconds = 60 * 15
        # model.SetTimeLimit(time_limit_seconds * 1000)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds

        start = time()
        status = solver.Solve(model)
        end = time()
        elapsed = end - start

        if status == cp_model.OPTIMAL:
            sets = []
            for choice_set_index in choice_set_indices:
                members = choice_set_members.for_choice_set_index(
                    choice_set_index)
                nonzero_members = tuple(
                    sorted([
                        x.element for x in members
                        if solver.Value(x.variable) == 1
                    ]))
                sets.append(nonzero_members)
            # return sorted(sets)
            return SubsetCoverSolution(status=SolveStatus.SOLVED,
                                       solve_time_seconds=elapsed)
        elif status == cp_model.INFEASIBLE:
            return SubsetCoverSolution(status=SolveStatus.INFEASIBLE,
                                       solve_time_seconds=elapsed)
        else:
            return SubsetCoverSolution(status=SolveStatus.UNKNOWN,
                                       solve_time_seconds=elapsed)


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
        print_table(params, SubsetCoverCP().solve(params), header=(n == 8))
