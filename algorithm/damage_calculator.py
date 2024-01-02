from algorithm.PokemonState import PokemonState
from algorithm.defense_multipliers import get_defense_multipliers_for_types
from data_class.Attack import Attack
from data_class.Category import Category
from algorithm.attack_util import get_all_attacks_for_pokemon, get_reversal_power, get_low_kick_power


def get_attack_power(attack, attacker_state: PokemonState, defender):
    buff = attacker_state.buffed
    move_power = attack.power
    if move_power == -1:
        move_power = 0

    if attack.name == "Low Kick":
        move_power = get_low_kick_power(defender.pokemon_information.pounds)
    elif attack.name == "Present":
        if buff:
            move_power = 120
        else:
            move_power = 0
    elif attack.name == "Reversal":
        move_power = get_reversal_power(attacker_state.current_hp, attacker_state.get_max_hp())
    elif attack.name == "Magnitude":
        if buff:
            move_power = 150
        else:
            move_power = 10
    elif attack.name == "Hidden Power":
        if buff:
            move_power = 70
        else:
            move_power = 31
    elif attack.name in ['Explosion', "Selfdestruct"]:
        move_power = 0
    elif attack.name == "Sky AttackCrystal Only":
        move_power = 70
    elif attack.name == "Sky Attack":
        move_power = 70
    elif attack.name == "Hyper Beam":
        move_power = 75
    return move_power


def get_max_damage_attacker_can_do_to_defender(
        attacker_state: PokemonState,
        defender_state: PokemonState,
        level: int = 50,
) -> (float, Attack):
    attacker = attacker_state.get_pokemon()
    defender = defender_state.get_pokemon()

    defender_types = defender.pokemon_information.pokemon_types
    defender_defense_multipliers = get_defense_multipliers_for_types(frozenset(defender_types))
    max_damage = 0
    all_attacks = get_all_attacks_for_pokemon(attacker)
    best_pokemon_move = None

    for attack in all_attacks:
        is_special = attack.category is Category.SPECIAL
        if not is_special:
            attack_stat = attacker_state.attack_stat * attacker_state.stat_modifiers.attack_modifier
            defense_stat = defender_state.defense_stat * defender_state.stat_modifiers.defense_modifier
        else:
            attack_stat = attacker_state.special_attack * attacker_state.stat_modifiers.special_attack_modifier
            defense_stat = defender_state.special_defense * defender_state.stat_modifiers.special_defense_modifier

        attack_power = get_attack_power(attack, attacker_state, defender)
        damage = (
                     (
                             (
                                     (
                                             (((2.0 * level) / 5.0) + 2.0) *
                                             attack_power *
                                             (attack_stat / defense_stat)
                                     ) / 50.0
                             ) * 2 + 2
                     )
                 ) * defender_defense_multipliers[attack.pokemon_type]

        zero = True
        if attack.name in ["Night Shade", "Seismic Toss"]:
            damage = level
            zero = False

        if (attack.pokemon_type in attacker.pokemon_information.pokemon_types or
                (attack.name == "Hidden Power") and attacker_state.buffed):
            damage = damage * 1.5

        if attack.name == "Hidden Power" and not attacker_state.buffed:
            damage = damage * min(defender_defense_multipliers.values())

        if attack.name == "Present" and not attacker_state.buffed:
            damage = - (defender_state.get_max_hp() / 4)

        if zero and attack_power == 0:
            damage = 0

        if damage > max_damage:
            best_pokemon_move = attack
        max_damage = max(damage, max_damage)

    return max_damage, best_pokemon_move
