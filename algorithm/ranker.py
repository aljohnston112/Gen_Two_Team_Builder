import json
import math
import os.path
import string
import typing
from collections import defaultdict
from itertools import cycle, combinations

import cattr

import config
from algorithm.PokemonState import PokemonState
from algorithm.damage_calculator import get_max_damage_attacker_can_do_to_defender
from algorithm.rank_saver import save_defeats, save_move_ranks, save_ranks
from data_class.StatModifiers import StatModifiers
from data_source.PokemonDataSource import get_pokemon


def __rank_pokemon__(
        file_name,
        attacker_buffed,
        defender_buffed,
        attacker_is_min_stat,
        defender_is_min_stat,
        attacker_stat_modifiers,
        defender_stat_modifiers,
        level=50,
):
    pokemon = {k: v for k, v in get_pokemon().items()
               if v.pokemon_information.name not in [
                   "Articuno",
                   "Zapdos",
                   "Moltres",
                   "Raikou",
                   "Entei",
                   "Suicune",
                   "Mewtwo",
                   "Lugia",
                   "Ho-Oh",
                   "Mew",
                   "Celebi",
                   "Dragonite",
                   "Pupitar"
               ]}
    pokemon_to_times_defeated = defaultdict(lambda: 0)
    pokemon_to_pokemon_lost_to = defaultdict(set)
    attacker_to_move_to_pokemon_defeated = defaultdict(lambda: defaultdict(list))
    for attacking_pokemon in pokemon.values():
        attacking_pokemon = PokemonState(
            attacking_pokemon,
            attacker_stat_modifiers,
            attacker_buffed,
            attacker_is_min_stat
        )
        attacker_speed_stat = attacking_pokemon.speed

        for defender_pokemon in pokemon.values():
            defender_pokemon = PokemonState(
                defender_pokemon,
                defender_stat_modifiers,
                defender_buffed,
                defender_is_min_stat
            )
            defender_speed_stat = defender_pokemon.speed
            damage_to_defender, defender_attack = get_max_damage_attacker_can_do_to_defender(
                attacking_pokemon,
                defender_pokemon,
                attacker_buffed,
                level=level
            )
            damage_to_attacker, attacker_attack = get_max_damage_attacker_can_do_to_defender(
                defender_pokemon,
                attacking_pokemon,
                defender_buffed,
                level=level
            )

            attacker_first = attacker_speed_stat > defender_speed_stat
            if attacker_attack is not None and defender_attack is not None:
                if (attacker_attack.name == "Vital Throw" and
                        defender_attack.name != "Vital Throw"):
                    attacker_first = False
                if (defender_attack.name == "Vital Throw" and
                        attacker_attack.name != "Vital Throw"):
                    attacker_first = True

            if damage_to_attacker == 0 and damage_to_defender == 0:
                attacking_pokemon.add_damage(attacking_pokemon.get_max_hp())
            else:
                while attacking_pokemon.current_hp > 0 and defender_pokemon.current_hp > 0:
                    attacking_pokemon.add_damage(damage_to_attacker)
                    defender_pokemon.add_damage(damage_to_defender)

                    # TODO the moves should not be None
                    if attacker_attack is not None:
                        if (
                                attacker_attack.name == "Giga Drain" and
                                ((attacker_first and defender_pokemon.current_hp > 0) or
                                 not attacker_first)
                        ):
                            gained_health = math.ceil(damage_to_defender / 2)
                            if attacking_pokemon.current_hp < 0:
                                gained_health = damage_to_attacker + attacking_pokemon.current_hp
                            attacking_pokemon.add_health(gained_health)

                        if attacker_attack.name == "Double-Edge":
                            defender_pokemon.add_damage(math.ceil(damage_to_defender / 4))

                    if defender_attack is not None:
                        if (
                                defender_attack.name == "Giga Drain" and
                                (((not attacker_first and attacking_pokemon.current_hp > 0) or
                                  attacker_first))
                        ):
                            gained_health = math.ceil(damage_to_attacker / 2)
                            if defender_pokemon.current_hp < 0:
                                gained_health = damage_to_defender + defender_pokemon.current_hp
                            defender_pokemon.add_health(gained_health)

                            if defender_attack.name == "Double-Edge":
                                defender_pokemon.add_damage(math.ceil(damage_to_defender / 4))

                    damage_to_defender, defender_attack = get_max_damage_attacker_can_do_to_defender(
                        attacking_pokemon,
                        defender_pokemon,
                        attacker_buffed,
                        level=level
                    )

                    damage_to_attacker, attacker_attack = get_max_damage_attacker_can_do_to_defender(
                        defender_pokemon,
                        attacking_pokemon,
                        defender_buffed,
                        level=level
                    )

                if attacking_pokemon.current_hp > 0 or \
                        (
                                attacking_pokemon.current_hp <= 0 and
                                defender_pokemon.current_hp <= 0 and
                                attacker_first
                        ):
                    attacker_to_move_to_pokemon_defeated[
                        attacking_pokemon.pokemon.pokemon_information.name
                    ][
                        defender_attack.name
                    ].append(defender_pokemon.pokemon.pokemon_information.name)
                    pokemon_to_times_defeated[defender_pokemon.pokemon.pokemon_information.name] += 1
                else:
                    pokemon_to_pokemon_lost_to[attacking_pokemon.pokemon.pokemon_information.name].add(
                        defender_pokemon.pokemon.pokemon_information.name
                    )

            attacking_pokemon.restore()

    save_defeats(
        {
            k: list(v) for k, v in (pokemon_to_pokemon_lost_to.items())
        }
    )

    # TODO cache above
    # Do the ranking
    attacker_rank_to_pokemon = defaultdict(list)
    best_moves = defaultdict(lambda: 0)
    move_to_number_of_pokemon_that_used_it = defaultdict(lambda: 0)
    for attacker_name, move_to_pokemon_defeated in attacker_to_move_to_pokemon_defeated.items():
        best_attacker_moves = defaultdict(lambda: 0)

        number_of_pokemon_defeated_by_attacker = 0
        for move, pokemon_defeated in move_to_pokemon_defeated.items():
            best_attacker_moves[move] += len(pokemon_defeated)
            move_to_number_of_pokemon_that_used_it[move] += 1
            number_of_pokemon_defeated_by_attacker += len(pokemon_defeated)
        rank = number_of_pokemon_defeated_by_attacker / len(pokemon_to_pokemon_lost_to.keys())

        for move, pokemon_defeated in move_to_pokemon_defeated.items():
            for pokemon in pokemon_defeated:
                best_moves[move] += 1.0 / pokemon_to_times_defeated[pokemon]
            best_attacker_moves[move] /= number_of_pokemon_defeated_by_attacker

        attacker_rank_to_pokemon[rank].append((attacker_name, best_attacker_moves))

    for move, num in move_to_number_of_pokemon_that_used_it.items():
        best_moves[move] /= num
    save_move_ranks(config.MOVE_RANKS_FILE_PREFIX + "_" + file_name.split("/")[-1], best_moves)
    save_ranks(attacker_rank_to_pokemon, file_name)


def analyze_defeats(
        attacker_stat_modifier: float,
        attacker_accuracy_modifier: float
):
    with open(config.POKEMON_DEFEATED_FILE_JSON, "r") as fo:
        pokemon_to_pokemon_lost_to = cattr.structure(
            json.loads(fo.read()),
            typing.DefaultDict[str, list[str]]
        )
    min_overlaps = 999
    top_threats = set()
    for pokemon_combo in combinations(pokemon_to_pokemon_lost_to.keys(), 3):
        seen = set()
        overlaps = 0
        j = 0
        while j < len(pokemon_combo):
            pokemon = pokemon_combo[j]
            lost_to = pokemon_to_pokemon_lost_to[pokemon]
            i = 0
            while i < len(lost_to):
                p = lost_to[i]
                if p not in seen:
                    seen.add(p)
                else:
                    overlaps += 1
                i += 1
            j += 1
        if overlaps < min_overlaps:
            min_overlaps = overlaps

            # print(str(list(pokemon_combo)) + "\n")
            # print("with threats:\n")
            top_threats.clear()
            for threat in seen:
                top_threats.add(threat)
                print("    " + threat)

    pokemon_to_threat_count = defaultdict(lambda: 0)
    for defeated_pokemon, lost_to in pokemon_to_pokemon_lost_to.items():
        for threat in top_threats:
            if threat in lost_to:
                pokemon_to_threat_count[threat] += 1
    print("Top threat to the threat ranks:")
    print(sorted(pokemon_to_threat_count.items(), key=lambda e: e[1]))


def rank_pokemon():
    move_ranks_file_prefix = config.MOVE_RANKS_FILE_PREFIX
    player_ranks_file = config.PLAYER_RANKS

    # Modifiers
    # Stats: .25, .28, .33, .40, .50, .66, 1.00, 1.50, 2.00, 2.50, 3.00, 3.50, 4.00
    # Accuracy and evasion: .33, .36, .43, .50, .66, .75, 1.00, 1.33, 1.66, 2.00, 2.33, 2.66, 3.00
    for multiplier in [.25, .28, .33, .40, .50, .66, 1.00, 1.50, 2.00, 2.50, 3.00, 3.50, 4.00]:
        # TODO save the results to a file
        attacker_stat_modifier = 0.66
        attacker_accuracy_modifier = 1
        attacker_stat_modifiers = StatModifiers(
            attack_modifier=attacker_stat_modifier,
            special_attack_modifier=attacker_stat_modifier,
            defense_modifier=attacker_stat_modifier,
            special_defense_modifier=attacker_stat_modifier,
            speed_modifier=attacker_stat_modifier,
            accuracy_modifier=attacker_accuracy_modifier,
            evasion_modifier=attacker_accuracy_modifier
        )

        defender_stat_modifier = 1
        defender_accuracy_modifier = 1
        defender_stat_modifiers = StatModifiers(
            attack_modifier=defender_stat_modifier,
            special_attack_modifier=defender_stat_modifier,
            defense_modifier=defender_stat_modifier,
            special_defense_modifier=defender_stat_modifier,
            speed_modifier=defender_stat_modifier,
            accuracy_modifier=defender_accuracy_modifier,
            evasion_modifier=defender_accuracy_modifier
        )

        # if not os.path.isfile(player_ranks_file):
        #     __rank_pokemon__(
        #         player_ranks_file,
        #         attacker_is_min_stat=True,
        #         defender_is_min_stat=False,
        #         attacker_buffed=False,
        #         defender_buffed=True,
        #         attacker_stat_modifiers=min_stat_modifiers,
        #         defender_stat_modifiers=max_stat_modifiers
        #     )
        #
        # opponent_ranks_file = config.OPPONENT_RANKS
        # if not os.path.isfile(opponent_ranks_file):
        #     __rank_pokemon__(
        #         opponent_ranks_file,
        #         attacker_is_min_stat=False,
        #         defender_is_min_stat=False,
        #         attacker_buffed=True,
        #         defender_buffed=True,
        #         attacker_stat_modifiers=max_stat_modifiers,
        #         defender_stat_modifiers=max_stat_modifiers
        #     )

        real_ranks_file = config.REAL_RANKS
        if not os.path.isfile(real_ranks_file):
            __rank_pokemon__(
                real_ranks_file,
                attacker_is_min_stat=False,
                defender_is_min_stat=False,
                attacker_buffed=False,
                defender_buffed=True,
                attacker_stat_modifiers=attacker_stat_modifiers,
                defender_stat_modifiers=defender_stat_modifiers
            )

        # save_average_of_ranks()
        analyze_defeats(
            attacker_stat_modifier=0.66,
            attacker_accuracy_modifier = 1
        )
