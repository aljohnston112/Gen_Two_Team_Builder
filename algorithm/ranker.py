import json
import math
import os.path
import string
import typing
from collections import defaultdict

import cattr

import config
from algorithm.PokemonState import PokemonState
from algorithm.damage_calculator import get_max_damage_attacker_can_do_to_defender
from data_class.StatModifiers import StatModifiers
from data_source.PokemonDataSource import get_pokemon


def save_ranks_json(rank_to_pokemon, file_name):
    file_name = "/".join(file_name.split("/")[:-1]) + "/json/" + file_name.split("/")[-1]
    with open(file_name + ".json", "w", encoding="utf-8") as fo:
        fo.write(json.dumps(cattr.unstructure(rank_to_pokemon)))


def save_ranks(rank_to_pokemon, file_name):
    save_ranks_json(rank_to_pokemon, file_name)
    with open(file_name, "w", encoding="utf-8") as fo:
        for k, v in sorted(rank_to_pokemon.items()):
            fo.write(f"Rank: {k}\n")
            for i, (pokemon, attacks) in zip(string.ascii_lowercase, v):
                fo.write(f"\n    Pokemon\n        {i}: " + str(pokemon) + "\n")
                fo.write("\n           attacks\n")
                for j, (attack, kill_count) in enumerate(attacks.items()):
                    fo.write(f"               {j}: " + str(attack) + "\n")
                    fo.write(f"               kill_count: " + str(kill_count) + "\n")
            fo.write("\n")


def save_move_ranks(
        file_name,
        best_player_moves: defaultdict
):
    save_ranks_json(best_player_moves, file_name)
    with open(file_name, "w", encoding="utf-8") as fo:
        for move, rank in sorted(best_player_moves.items(), key=lambda entry: entry[1]):
            fo.write(f"{str(move)}'s Rank: {rank}\n")


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
    pokemon = get_pokemon()
    pokemon_to_times_defeated = defaultdict(lambda: 0)
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
            attacker_first = attacker_speed_stat > defender_speed_stat

            damage_to_defender, defender_attack = get_max_damage_attacker_can_do_to_defender(
                attacking_pokemon,
                defender_pokemon,
                level=level
            )
            damage_to_attacker, attacker_attack = get_max_damage_attacker_can_do_to_defender(
                defender_pokemon,
                attacking_pokemon,
                level=level
            )

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
                                (attacker_first and defender_pokemon.current_hp > 0) or
                                not attacker_first
                        ):
                            gained_health = math.ceil(damage_to_defender / 2)
                            if attacking_pokemon.current_hp < 0:
                                gained_health += damage_to_attacker + attacking_pokemon.current_hp
                            attacking_pokemon.add_health(gained_health)

                        if attacker_attack.name == "Double-Edge":
                            defender_pokemon.add_damage(math.ceil(damage_to_defender / 4))

                    if defender_attack is not None:
                        if (
                                defender_attack.name == "Giga Drain" and
                                ((not attacker_first and attacking_pokemon.current_hp > 0) or
                                 attacker_first)
                        ):
                            gained_health = math.ceil(damage_to_attacker / 2)
                            if defender_pokemon.current_hp < 0:
                                gained_health += damage_to_defender + defender_pokemon.current_hp
                            defender_pokemon.add_health(gained_health)

                            if defender_attack.name == "Double-Edge":
                                defender_pokemon.add_damage(math.ceil(damage_to_defender / 4))

                    damage_to_defender, defender_attack = get_max_damage_attacker_can_do_to_defender(
                        attacking_pokemon,
                        defender_pokemon,
                        level=level
                    )

                    damage_to_attacker, attacker_attack = get_max_damage_attacker_can_do_to_defender(
                        defender_pokemon,
                        attacking_pokemon,
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

    # Do the ranking
    sum_of_pokemon_defeated_by_all = 0
    for attacker_name, move_to_pokemon_defeated in attacker_to_move_to_pokemon_defeated.items():
        for move, pokemon_defeated in move_to_pokemon_defeated.items():
            sum_of_pokemon_defeated_by_all += len(pokemon_defeated)

    attacker_rank_to_pokemon = defaultdict(list)
    best_moves = defaultdict(lambda: 0)
    for attacker_name, move_to_pokemon_defeated in attacker_to_move_to_pokemon_defeated.items():
        best_attacker_moves = defaultdict(lambda: 0)

        number_of_pokemon_defeated_by_attacker = 0
        for move, pokemon_defeated in move_to_pokemon_defeated.items():
            best_attacker_moves[move] += len(pokemon_defeated)
            number_of_pokemon_defeated_by_attacker += len(pokemon_defeated)

        for move, pokemon_defeated in move_to_pokemon_defeated.items():
            for pokemon in pokemon_defeated:
                best_moves[move] += 1.0 / pokemon_to_times_defeated[pokemon]
            best_attacker_moves[move] /= number_of_pokemon_defeated_by_attacker
        rank = number_of_pokemon_defeated_by_attacker / len(get_pokemon())
        attacker_rank_to_pokemon[rank].append((attacker_name, best_attacker_moves))
    save_move_ranks(config.MOVE_RANKS_FILE_PREFIX + "_" + file_name.split("/")[-1], best_moves)
    save_ranks(attacker_rank_to_pokemon, file_name)


def save_average_of_ranks():
    real_ranks_file = config.REAL_RANKS + ".json"
    opponent_ranks_file = config.OPPONENT_RANKS + ".json"
    player_ranks_file = config.PLAYER_RANKS + ".json"

    with open(real_ranks_file, "r") as fo:
        real_ranks = cattr.structure(
            json.loads(fo.read()),
            typing.DefaultDict[float, list[tuple[str, defaultdict[str, float]]]]
        )
    with open(opponent_ranks_file, "r") as fo:
        opponent_ranks = cattr.structure(
            json.loads(fo.read()),
            typing.DefaultDict[float, list[tuple[str, defaultdict[str, float]]]]
        )
    with open(player_ranks_file, "r") as fo:
        player_ranks = cattr.structure(
            json.loads(fo.read()),
            typing.DefaultDict[float, list[tuple[str, defaultdict[str, float]]]]
        )

    move_to_count = defaultdict(lambda: 0)
    move_to_rank = defaultdict(lambda: 0)
    for ranking in [real_ranks, opponent_ranks, player_ranks]:
        for rank, move_ranks in ranking.items():
            for (pokemon_name, attack_to_rank) in move_ranks:
                move_to_count[pokemon_name] += 1
                move_to_rank[pokemon_name] += rank
    for move, rank in move_to_rank.items():
        move_to_rank[move] /= move_to_count[move]
    save_move_ranks(config.AVERAGE_RANKS_FILE, move_to_rank)

    move_ranks_file_prefix = config.MOVE_RANKS_FILE_PREFIX
    real_move_ranks_file = move_ranks_file_prefix + "_" + real_ranks_file.split("/")[-1]
    opponent_move_ranks_file = move_ranks_file_prefix + "_" + real_ranks_file.split("/")[-1]
    player_move_ranks_file = move_ranks_file_prefix + "_" + real_ranks_file.split("/")[-1]

    with open(real_move_ranks_file, "r") as fo:
        real_move_ranks = cattr.structure(
            json.loads(fo.read()),
            typing.DefaultDict[str, float]
        )
    with open(opponent_move_ranks_file, "r") as fo:
        opponent_move_ranks = cattr.structure(
            json.loads(fo.read()),
            typing.DefaultDict[str, float]
        )
    with open(player_move_ranks_file, "r") as fo:
        player_move_ranks = cattr.structure(
            json.loads(fo.read()),
            typing.DefaultDict[str, float]
        )

    move_to_count = defaultdict(lambda: 0)
    move_to_rank = defaultdict(lambda: 0)
    for ranking in [real_move_ranks, opponent_move_ranks, player_move_ranks]:
        for move_name, rank in ranking.items():
            move_to_count[move_name] += 1
            move_to_rank[move_name] += rank
    for move, rank in move_to_rank.items():
        move_to_rank[move] /= move_to_count[move]
    save_move_ranks(config.AVERAGE_MOVES_RANKS_FILE, move_to_rank)


def rank_pokemon():
    move_ranks_file_prefix = config.MOVE_RANKS_FILE_PREFIX
    player_ranks_file = config.PLAYER_RANKS

    # Modifiers
    # Stats: 25, 28, 33, 40, 50, 66, 100, 150, 200, 250, 300, 350, 400
    # Accuracy and evasion: 33, 36, 43, 50, 66, 75, 100, 133, 166, 200, 233, 266, 300

    min_stat_modifier = 200
    min_accuracy_modifier = 0.33
    min_stat_modifiers = StatModifiers(
        attack_modifier=min_stat_modifier,
        special_attack_modifier=min_stat_modifier,
        defense_modifier=min_stat_modifier,
        special_defense_modifier=min_stat_modifier,
        speed_modifier=min_stat_modifier,
        accuracy_modifier=min_accuracy_modifier,
        evasion_modifier=min_accuracy_modifier
    )

    max_stat_modifier = 400
    max_accuracy_modifier = 300
    max_stat_modifiers = StatModifiers(
        attack_modifier=max_stat_modifier,
        special_attack_modifier=max_stat_modifier,
        defense_modifier=max_stat_modifier,
        special_defense_modifier=max_stat_modifier,
        speed_modifier=max_stat_modifier,
        accuracy_modifier=max_accuracy_modifier,
        evasion_modifier=max_accuracy_modifier
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
            attacker_stat_modifiers=min_stat_modifiers,
            defender_stat_modifiers=max_stat_modifiers
        )

    # save_average_of_ranks()
