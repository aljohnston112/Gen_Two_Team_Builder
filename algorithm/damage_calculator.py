from algorithm.defense_multipliers import get_defense_multipliers_for_types
from data_class.Attack import Attack
from data_class.Category import Category
from data_class.Pokemon import Pokemon


def get_low_kick_power(pounds):
    if pounds < 21.9:
        power = 20
    elif pounds < 55.1:
        power = 40
    elif pounds < 110.2:
        power = 60
    elif pounds < 220.4:
        power = 80
    elif pounds < 440.9:
        power = 100
    else:
        power = 120
    return power


def get_reversal_power(attackers_current_hp, max_hp):
    attackers_current_hp = attackers_current_hp / max_hp
    if attackers_current_hp >= 68.75:
        power = 20
    elif attackers_current_hp >= 35.42:
        power = 40
    elif attackers_current_hp >= 20.83:
        power = 80
    elif attackers_current_hp >= 10.42:
        power = 100
    elif attackers_current_hp >= 4.17:
        power = 150
    else:
        power = 200
    return power


def get_all_moves(attacker):
    all_moves = []
    if attacker.special_attacks is not None:
        all_moves += attacker.special_attacks
    if attacker.genII_level_to_attacks is not None:
        for moves in (attacker.genII_level_to_attacks.values()):
            all_moves += moves
    if attacker.genI_attacks is not None:
        all_moves += attacker.genI_attacks
    if attacker.egg_moves is not None:
        all_moves += attacker.egg_moves
    if attacker.move_tutor_attacks is not None:
        all_moves += attacker.move_tutor_attacks
    if attacker.pre_evolution_attacks is not None:
        all_moves += attacker.pre_evolution_attacks
    if attacker.tm_or_hm_to_attack is not None:
        all_moves += attacker.tm_or_hm_to_attack.values()
    return all_moves


def get_max_damage_opponent_pokemon_can_do_to_player(
        attacker: Pokemon,
        defender: Pokemon,
        attackers_current_hp,
        level: int = 50,
) -> (float, Attack):
    defender_types = defender.pokemon_information.pokemon_types
    defender_defense_multipliers = get_defense_multipliers_for_types(frozenset(defender_types))
    max_damage = 0
    all_moves = get_all_moves(attacker)
    best_pokemon_move = None

    for pokemon_move in all_moves:
        is_special = pokemon_move.category is Category.SPECIAL
        if not is_special:
            attack_stat = attacker.all_stats.level_50_max_stats.attack
            defense_stat = defender.all_stats.level_50_min_stats.defense
        else:
            attack_stat = attacker.all_stats.level_50_max_stats.attack
            defense_stat = defender.all_stats.level_50_min_stats.special_defense

        zero = True
        move_power = pokemon_move.power
        if pokemon_move.name == "Low Kick":
            move_power = get_low_kick_power(defender.pokemon_information.pounds)
            zero = False
        elif pokemon_move.name == "Present":
            move_power = 120
            zero = False
        elif pokemon_move.name == "Reversal":
            move_power = 0
        elif pokemon_move.name == "Magnitude":
            move_power = 150
            zero = False
        elif pokemon_move.name == "Hidden Power":
            move_power = 70
            zero = False
        elif pokemon_move.name in ['Explosion', "Selfdestruct"]:
            move_power = 0
        elif pokemon_move.name == "Sky AttackCrystal Only":
            move_power = 70
        elif pokemon_move.name == "Sky Attack":
            move_power = 70
        elif pokemon_move.name == "Hyper Beam":
            move_power = 75

        damage = (
                     (
                             (
                                     (
                                             (((2.0 * level) / 5.0) + 2.0) *
                                             move_power *
                                             (attack_stat / defense_stat)
                                     ) / 50.0
                             ) * 2 + 2
                     )
                 ) * defender_defense_multipliers[pokemon_move.pokemon_type]

        if (pokemon_move.pokemon_type in attacker.pokemon_information.pokemon_types or
                pokemon_move.name == "Hidden Power"):
            damage = damage * 1.5

        if pokemon_move.name in ["Night Shade", "Seismic Toss"]:
            damage = level * defender_defense_multipliers[pokemon_move.pokemon_type]
            zero = False

        if zero and move_power == 0:
            damage = 0

        if damage > max_damage:
            best_pokemon_move = pokemon_move
        max_damage = max(damage, max_damage)

    return max_damage, best_pokemon_move


def get_max_damage_attacker_pokemon_can_do_to_defender(
        attacker: Pokemon,
        defender: Pokemon,
        attackers_current_hp,
        level: int
) -> tuple[float, Attack]:
    defender_types = defender.pokemon_information.pokemon_types
    defender_defense_multipliers = get_defense_multipliers_for_types(frozenset(defender_types))
    max_damage = 0
    all_moves = get_all_moves(attacker)

    best_move = None
    for pokemon_move in all_moves:
        if pokemon_move.accuracy == 100:
            is_special = pokemon_move.category is Category.SPECIAL
            if not is_special:
                attack_stat = attacker.all_stats.level_50_min_stats.attack
                defense_stat = defender.all_stats.level_50_max_stats.defense
            else:
                attack_stat = attacker.all_stats.level_50_min_stats.attack
                defense_stat = defender.all_stats.level_50_max_stats.special_defense

            zero = True
            move_power = pokemon_move.power
            if pokemon_move.name == "Low Kick":
                move_power = get_low_kick_power(defender.pokemon_information.pounds)
                zero = False
            elif pokemon_move.name == "Reversal":
                move_power = 0
            elif pokemon_move.name == "Magnitude":
                move_power = 10
                zero = False
            elif pokemon_move.name == "Hidden Power":
                move_power = 31
                zero = False
            elif pokemon_move.name in ['Explosion', "Selfdestruct"]:
                move_power = 0
            elif pokemon_move.name == "Sky AttackCrystal Only":
                move_power = 70

            damage = (
                         (
                                 (
                                         (
                                                 (((2.0 * level) / 5.0) + 2.0) *
                                                 move_power *
                                                 (attack_stat / defense_stat)
                                         ) / 50.0
                                 ) * 2 + 2
                         )
                     ) * defender_defense_multipliers[pokemon_move.pokemon_type]

            if (pokemon_move.pokemon_type in attacker.pokemon_information.pokemon_types and
                    pokemon_move.name != "Hidden Power"):
                damage = damage * 1.5
            if pokemon_move.name == "Hidden Power":
                damage = damage * min(defender_defense_multipliers.values())

            if pokemon_move.name in ["Night Shade", "Seismic Toss"]:
                damage = level * defender_defense_multipliers[pokemon_move.pokemon_type]
                zero = False

            if pokemon_move.name == "Present":
                damage = - (defender.all_stats.level_50_max_stats.health / 4)
                zero = False

            if zero and move_power == 0:
                damage = 0

            if damage > max_damage:
                best_move = pokemon_move
            max_damage = max(damage, max_damage)

    return max_damage, best_move
