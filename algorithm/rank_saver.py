import json
import string
import typing
from collections import defaultdict
from itertools import cycle

import cattr

import config


def save_ranks_json(rank_to_pokemon, file_name):
    file_name = "/".join(file_name.split("/")[:-1]) + "/json/" + file_name.split("/")[-1]
    with open(file_name + ".json", "w", encoding="utf-8") as fo:
        fo.write(json.dumps(cattr.unstructure(rank_to_pokemon)))


def save_ranks(rank_to_pokemon, file_name):
    save_ranks_json(rank_to_pokemon, file_name)
    with open(file_name, "w", encoding="utf-8") as fo:
        for k, v in sorted(rank_to_pokemon.items()):
            fo.write(f"Rank: {k}\n")
            for i, (pokemon, attacks) in zip(cycle(string.ascii_lowercase), v):
                fo.write(f"\n    Pokemon\n        {i}: " + str(pokemon) + "\n")
                fo.write("\n           attacks\n")
                for j, (attack, kill_count) in enumerate(sorted(attacks.items(), key=lambda e: e[1])):
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


def save_defeats(pokemon_to_pokemon_lost_to):
    with open(config.POKEMON_DEFEATED_FILE_JSON, "w", encoding="utf-8") as fo:
        fo.write(json.dumps(cattr.unstructure(pokemon_to_pokemon_lost_to)))
    with open(config.POKEMON_DEFEATED_FILE, "w", encoding="utf-8") as fo:
        for pokemon, lost_to_list in pokemon_to_pokemon_lost_to.items():
            fo.write(f"{pokemon}'s threats:\n")
            for lost_to in lost_to_list:
                fo.write(f"    {lost_to}\n")
            fo.write("\n")


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