'''A set of helper types and classes common to all subset cover models.'''
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from itertools import product
from typing import Any
from typing import List
from typing import Tuple
from typing import Callable

# To allow z3 and ILP models to share these helpers
VariableConstructor = Callable[[str], Any]


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


@dataclass(frozen=True)
class HitSet:
    '''The sets you're trying to hit by picking choice sets.'''
    set_size: int
    elements: List[int]
    variable: Any



class ChoiceSetMembers:
    '''A class that constructs ChoiceSetMember instances and the associated lookups.'''
    def __init__(self, elements, choice_set_indices,
                 variable_constructor: VariableConstructor):
        self.memberships = [
            ChoiceSetMember(element=element,
                            choice_set_index=choice_set_index,
                            variable=variable_constructor(
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

    def grouped_by_choice_set(self):
        return self.memberships_by_choice_set.values()

    def all_variables(self):
        return [mem.variable for mem in self.memberships]


def make_hit_sets(elements, hit_set_size):
    return [
        tuple(sorted(elts)) for elts in combinations(elements, hit_set_size)
    ]


class IsHits:
    '''A class that defines IsHit variables for each
    hit set and choice set pair.
    '''
    def __init__(self, hit_sets, choice_set_indices,
                 variable_constructor: VariableConstructor):
        self.is_hit_variables = [
            IsHit(hit_set=hit_set,
                  choice_set_index=choice_set_index,
                  variable=variable_constructor(
                      f"IsHit_({hit_set},{choice_set_index})")) for hit_set,
            choice_set_index in product(hit_sets, choice_set_indices)
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
