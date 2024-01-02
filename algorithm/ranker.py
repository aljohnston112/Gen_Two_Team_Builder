import json
import math
import os.path
import string
import typing
from collections import defaultdict

import cattr

import config
from algorithm.damage_calculator import get_max_damage_opponent_pokemon_can_do_to_player, \
    get_max_damage_attacker_pokemon_can_do_to_defender
from parser.PokemonDataSource import get_pokemon


def save_ranks_json(rank_to_pokemon, file_name):
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
        attacker_is_min_stat=False,
        defender_is_min_stat=False,
        attacker_buff=True,
        defender_buff=True,
        level=50,
):
    pokemon = get_pokemon()
    pokemon_to_times_defeated = defaultdict(lambda: 0)
    attacker_to_move_to_pokemon_defeated = defaultdict(lambda: defaultdict(list))
    for attacking_pokemon in pokemon.values():
        if attacker_is_min_stat:
            attacker_speed_stat = attacking_pokemon.all_stats.level_50_min_stats.speed
        else:
            attacker_speed_stat = attacking_pokemon.all_stats.level_50_max_stats.speed

        for defender_pokemon in pokemon.values():
            if attacker_is_min_stat:
                attacker_health_stat = attacking_pokemon.all_stats.level_50_min_stats.health
            else:
                attacker_health_stat = attacking_pokemon.all_stats.level_50_max_stats.health

            if defender_is_min_stat:
                defender_speed_stat = defender_pokemon.all_stats.level_50_min_stats.speed
                defender_health_stat = defender_pokemon.all_stats.level_50_min_stats.health
            else:
                defender_speed_stat = defender_pokemon.all_stats.level_50_max_stats.speed
                defender_health_stat = defender_pokemon.all_stats.level_50_max_stats.health
            attacker_first = attacker_speed_stat > defender_speed_stat

            if attacker_buff:
                damage_to_defender, player_move = get_max_damage_opponent_pokemon_can_do_to_player(
                    attacking_pokemon,
                    defender_pokemon,
                    attacker_health_stat,
                    level=level
                )
            else:
                damage_to_defender, player_move = get_max_damage_attacker_pokemon_can_do_to_defender(
                    attacking_pokemon,
                    defender_pokemon,
                    attacker_health_stat,
                    level=level
                )

            if defender_buff:
                damage_to_attacker, opponent_move = get_max_damage_opponent_pokemon_can_do_to_player(
                    defender_pokemon,
                    attacking_pokemon,
                    defender_health_stat,
                    level=level
                )
            else:
                damage_to_attacker, opponent_move = get_max_damage_attacker_pokemon_can_do_to_defender(
                    defender_pokemon,
                    attacking_pokemon,
                    defender_health_stat,
                    level=level
                )

            if damage_to_attacker != 0 or damage_to_defender != 0:
                while attacker_health_stat > 0 and defender_health_stat > 0:
                    attacker_health_stat = attacker_health_stat - damage_to_attacker
                    defender_health_stat = defender_health_stat - damage_to_defender

                    # TODO the moves should not be None
                    if (opponent_move is not None and
                            (opponent_move.name == "Giga Drain" and
                             ((attacker_first and defender_health_stat > 0) or
                              not attacker_first))):
                        gained_health = math.ceil(damage_to_defender / 2)
                        if attacker_health_stat < 0:
                            gained_health += damage_to_attacker + attacker_health_stat
                        defender_health_stat += gained_health
                    if (player_move is not None and
                            (player_move.name == "Giga Drain" and
                             ((not attacker_first and attacker_health_stat > 0) or
                              attacker_first))):
                        gained_health = math.ceil(damage_to_attacker / 2)
                        if defender_health_stat < 0:
                            gained_health += damage_to_defender + defender_health_stat
                        defender_health_stat += gained_health

                    if opponent_move is not None and opponent_move.name == "Double-Edge":
                        defender_health_stat -= math.ceil(damage_to_defender / 4)
                    if player_move is not None and player_move.name == "Double-Edge":
                        attacker_health_stat -= math.ceil(damage_to_defender / 4)

                    if attacker_buff:
                        damage_to_defender, player_move = get_max_damage_opponent_pokemon_can_do_to_player(
                            attacking_pokemon,
                            defender_pokemon,
                            attacker_health_stat,
                            level=level
                        )
                    else:
                        damage_to_defender, player_move = get_max_damage_attacker_pokemon_can_do_to_defender(
                            attacking_pokemon,
                            defender_pokemon,
                            attacker_health_stat,
                            level=level
                        )

                    if defender_buff:
                        damage_to_attacker, opponent_move = get_max_damage_opponent_pokemon_can_do_to_player(
                            defender_pokemon,
                            attacking_pokemon,
                            defender_health_stat,
                            level=level
                        )
                    else:
                        damage_to_attacker, opponent_move = get_max_damage_attacker_pokemon_can_do_to_defender(
                            defender_pokemon,
                            attacking_pokemon,
                            defender_health_stat,
                            level=level
                        )
            else:
                attacker_health_stat = 0

            if attacker_health_stat > 0 or \
                    (
                            attacker_health_stat <= 0 and
                            defender_health_stat <= 0 and
                            attacker_first
                    ):
                attacker_to_move_to_pokemon_defeated[
                    attacking_pokemon.pokemon_information.name
                ][
                    player_move.name
                ].append(defender_pokemon.pokemon_information.name)
                pokemon_to_times_defeated[defender_pokemon.pokemon_information.name] += 1

    # Do the ranking
    sum_of_pokemon_defeated_by_all = 0
    for attacker_name, move_to_pokemon_defeated in attacker_to_move_to_pokemon_defeated.items():
        for move, pokemon_defeated in move_to_pokemon_defeated.items():
            sum_of_pokemon_defeated_by_all += len(pokemon_defeated)

    attacker_rank_to_pokemon = defaultdict(list)
    best_moves = defaultdict(lambda: 0)
    for attacker_name, move_to_pokemon_defeated in attacker_to_move_to_pokemon_defeated.items():
        rank = 0
        best_player_moves = defaultdict(lambda: 0)

        number_of_pokemon_defeated_by_attacker = 0
        for move, pokemon_defeated in move_to_pokemon_defeated.items():
            best_player_moves[move] += len(pokemon_defeated)
            number_of_pokemon_defeated_by_attacker += len(pokemon_defeated)

        for move, pokemon_defeated in move_to_pokemon_defeated.items():
            for pokemon in pokemon_defeated:
                best_moves[move] += 1.0 / pokemon_to_times_defeated[pokemon]
            rank += number_of_pokemon_defeated_by_attacker / sum_of_pokemon_defeated_by_all
            best_player_moves[move] /= number_of_pokemon_defeated_by_attacker
        attacker_rank_to_pokemon[rank].append((attacker_name, best_player_moves))
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

    if not os.path.isfile(player_ranks_file):
        __rank_pokemon__(
            player_ranks_file,
            attacker_is_min_stat=True,
            defender_is_min_stat=False,
            attacker_buff=False,
            defender_buff=True
        )

    opponent_ranks_file = config.OPPONENT_RANKS
    if not os.path.isfile(opponent_ranks_file):
        __rank_pokemon__(
            opponent_ranks_file,
            attacker_is_min_stat=False,
            defender_is_min_stat=False,
            attacker_buff=False,
            defender_buff=False
        )

    real_ranks_file = config.REAL_RANKS
    if not os.path.isfile(real_ranks_file):
        __rank_pokemon__(
            real_ranks_file,
            attacker_is_min_stat=False,
            defender_is_min_stat=False,
            attacker_buff=False,
            defender_buff=True
        )
    save_average_of_ranks()
