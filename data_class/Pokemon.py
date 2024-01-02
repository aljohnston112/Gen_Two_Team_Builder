from typing import Dict, List, Optional

import attr
from attr import frozen

from data_class.AllStats import AllStats
from data_class.Attack import Attack
from data_class.PokemonInformation import PokemonInformation


@frozen
class Pokemon:
    pokemon_information: PokemonInformation
    all_stats: AllStats
    genII_level_to_attacks: Dict[int, List[Attack]]

    genI_attacks: Optional[List[Attack]] = attr.field(default=None)
    tm_or_hm_to_attack: Optional[Dict[str, Attack]] = attr.field(default=None)
    move_tutor_attacks: Optional[List[Attack]] = attr.field(default=None)
    egg_moves: Optional[List[Attack]] = attr.field(default=None)
    pre_evolution_attacks: Optional[List[Attack]] = attr.field(default=None)
    special_attacks: Optional[List[Attack]] = attr.field(default=None)
