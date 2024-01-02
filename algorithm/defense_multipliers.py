from collections import defaultdict

from data_class.PokemonType import PokemonType
from parser.TypeChartRepository import type_chart_defend


class DefenseMultipliers:
    def __init__(self):
        self.current_defense_multipliers = defaultdict(lambda: 1.0)

    def __getitem__(self, key):
        return self.current_defense_multipliers.get(key)


def get_defense_multipliers_for_type(
        pokemon_type: PokemonType,
        current_defense_multipliers: DefenseMultipliers
):

    # [no_eff, not_eff, normal_eff, super_eff]
    no_effect_types = type_chart_defend[0].get(pokemon_type, [])
    not_effective_types = type_chart_defend[1].get(pokemon_type, [])
    normal_effective_types = type_chart_defend[2].get(pokemon_type, [])
    super_effective_types = type_chart_defend[3].get(pokemon_type, [])
    for no_effect_type in no_effect_types:
        current_defense_multipliers[no_effect_type] *= 0.0
    for not_effective_type in not_effective_types:
        current_defense_multipliers[not_effective_type] *= 0.5
    for normal_effective_type in normal_effective_types:
        current_defense_multipliers[normal_effective_type] *= 1.0
    for super_effective_type in super_effective_types:
        current_defense_multipliers[super_effective_type] *= 2.0
    return current_defense_multipliers


def get_defense_multipliers_for_types(defender_types: frozenset[PokemonType]):
    defense_multipliers = defaultdict(lambda: 1.0)
    for defender_type in defender_types:
        defense_multipliers = get_defense_multipliers_for_type(defender_type, defense_multipliers)
    return defense_multipliers
