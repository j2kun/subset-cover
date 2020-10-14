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


class ChoiceSetMembers:
    '''A class that constructs ChoiceSetMember instances and the associated lookups.'''
    def __init__(self, elements, choice_sets):
        self.memberships = [
            ChoiceSetMember(
                element=element,
                choice_set=choice_set_index,
                variable=Bool(f"Member_({choice_set_index},{element})"))
            for element, choice_set_index in product(elements, choice_sets)
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

    def grouped_by_choice_set(self):
        retur self.memberships_by_choice_set.values()
