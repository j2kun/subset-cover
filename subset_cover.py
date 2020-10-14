from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum


class SolveStatus(Enum):
    '''
    A generalization over the solve statuses of each solver.
    '''
    # unknown includes timeout or the solver giving up
    UNKNOWN = 0
    SOLVED = 1
    INFEASIBLE = 2


@dataclass(frozen=True)
class SubsetCoverParameters:
    '''The number of elements in the universe set.'''
    num_elements: int

    '''The size of the sets that must be hit by choice sets.'''
    hit_set_size: int

    '''The size of the sets used to cover hit sets.'''
    choice_set_size: int

    '''If set, the number of allowed choice sets.'''
    num_choice_sets: int


@dataclass(frozen=True)
class SubsetCoverSolution:
    '''Whether the solve succeeded or not.'''
    status: SolveStatus
    solve_time_seconds: int
    # I could add the actual solution here, but not really
    # necessary for timing.


class SubsetCover(ABC):
    '''An interface for a subset cover implementation.'''
    @abstractmethod
    def solve(self, parameters: SubsetCoverParameters) -> SubsetCoverSolution:
        pass
