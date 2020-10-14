from ilp_model import ChoiceSetMember
from ilp_model import ChoiceSetMembers
from ilp_model import IsHit
from ilp_model import IsHits
from ilp_model import make_hit_sets
from subset_cover import SolveStatus
from subset_cover import SubsetCover
from subset_cover import SubsetCoverParameters
from subset_cover import SubsetCoverSolution
from time import time

from ortools.linear_solver import pywraplp


class SubsetCoverILP(SubsetCover):
    '''
    An implementation of the subset cover problem formulated as
    an integer linear program.
    '''
    def solve(self, parameters: SubsetCoverParameters) -> SubsetCoverSolution:
        solver = pywraplp.Solver.CreateSolver('subset_cover', 'SCIP')

        elements = list(range(parameters.num_elements))
        choice_set_indices = list(range(parameters.num_choice_sets))
        hit_sets = make_hit_sets(elements, parameters.hit_set_size)

        choice_set_members = ChoiceSetMembers(solver, elements,
                                              choice_set_indices)
        is_hits = IsHits(solver, hit_sets, choice_set_indices)

        # Each choice set must have size choice_set_size.
        for choice_set_index in choice_set_indices:
            members = choice_set_members.for_choice_set_index(choice_set_index)
            member_vars = [x.variable for x in members]
            solver.Add(sum(member_vars) == parameters.choice_set_size)

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
            rhs = parameters.hit_set_size * is_hit.variable

            # if IsHit == 1, then the LHS must be at least hit_set_size, but
            # because there are only hit_set_size many terms in LHS, that is also
            # the max value, so all the variables in LHS must equal 1, i.e., all
            # the hit set elements are in the choice set.
            solver.Add(lhs >= rhs)

        # The objective does not matter because we are looking for a feasible solution
        solver.Maximize(1)
        time_limit_seconds = 60 * 5
        solver.SetTimeLimit(time_limit_seconds * 1000)

        start = time()
        status = solver.Solve()
        end = time()
        elapsed = end - start

        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            sets = []
            for choice_set_index in choice_set_indices:
                members = choice_set_members.for_choice_set_index(
                    choice_set_index)
                nonzero_members = tuple(
                    sorted([
                        x.element for x in members
                        if x.variable.solution_value() == 1
                    ]))
                sets.append(nonzero_members)
            # return sorted(sets)
            return SubsetCoverSolution(status=SolveStatus.SOLVED,
                                       solve_time_seconds=elapsed)
        elif status == pywraplp.Solver.INFEASIBLE:
            return SubsetCoverSolution(status=SolveStatus.INFEASIBLE,
                                       solve_time_seconds=elapsed)
        else:
            return SubsetCoverSolution(status=SolveStatus.UNKNOWN,
                                       solve_time_seconds=elapsed)


if __name__ == "__main__":
    result = SubsetCoverILP().solve(
        SubsetCoverParameters(num_elements=7,
                              choice_set_size=3,
                              hit_set_size=2,
                              num_choice_sets=4))

    print(result)
