from collections import defaultdict
from dataclasses import dataclass
from subset_cover import SubsetCoverParameters


@dataclass(frozen=True)
class Experiment:
    family: str
    parameters: SubsetCoverParameters
    order: int  # order within a family, for plotting


experiments = []

experiments.append(
    Experiment(
        family='small sat',
        order=0,
        parameters=SubsetCoverParameters(
            num_elements=6,
            choice_set_size=3,
            hit_set_size=2,
            num_choice_sets=7,
        ),
    ))


experiments.append(
    Experiment(
        family='small unsat',
        order=0,
        parameters=SubsetCoverParameters(
            num_elements=6,
            choice_set_size=3,
            hit_set_size=2,
            num_choice_sets=3,
        ),
    ))


experiments.append(
    Experiment(
        family='large sat',
        order=0,
        parameters=SubsetCoverParameters(
            num_elements=9,
            choice_set_size=5,
            hit_set_size=3,
            num_choice_sets=50,
        ),
    ))


experiments.append(
    Experiment(
        family='large unsat',
        order=0,
        parameters=SubsetCoverParameters(
            num_elements=9,
            choice_set_size=5,
            hit_set_size=3,
            num_choice_sets=3,
        ),
    ))


experiments.extend([
    Experiment(
        family='sat search n=7',
        order=i,
        parameters=SubsetCoverParameters(
            num_elements=7,
            choice_set_size=3,
            hit_set_size=2,
            num_choice_sets=i,
        ),
    )
    for i in range(1, 20)
])


experiments.extend([
    Experiment(
        family='search n=8',
        order=i,
        parameters=SubsetCoverParameters(
            num_elements=8,
            choice_set_size=3,
            hit_set_size=2,
            num_choice_sets=i,
        ),
    )
    for i in range(1, 20)
])
