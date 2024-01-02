
def get_all_attacks_for_pokemon(pokemon):
    all_moves = []
    if pokemon.special_attacks is not None:
        all_moves += pokemon.special_attacks
    if pokemon.genII_level_to_attacks is not None:
        for moves in (pokemon.genII_level_to_attacks.values()):
            all_moves += moves
    if pokemon.genI_attacks is not None:
        all_moves += pokemon.genI_attacks
    if pokemon.egg_moves is not None:
        all_moves += pokemon.egg_moves
    if pokemon.move_tutor_attacks is not None:
        all_moves += pokemon.move_tutor_attacks
    if pokemon.pre_evolution_attacks is not None:
        all_moves += pokemon.pre_evolution_attacks
    if pokemon.tm_or_hm_to_attack is not None:
        all_moves += pokemon.tm_or_hm_to_attack.values()
    return all_moves


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
