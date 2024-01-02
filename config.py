import os

ROOT = os.path.dirname(os.path.abspath(__file__))
POKEMON_FILE = ROOT + "/all_pokemon.json"
TYPE_FILE = ROOT + "/types"

RAW_TYPE_FILE = ROOT + "/data/raw/type_chart"
FRESH_ATTACKER_TYPE_FILE = ROOT + "/data/generated/attacker_types"
FRESH_DEFENDER_TYPE_FILE = ROOT + "/data/generated/defender_types"
PLAYER_RANKS = ROOT + "/data/generated/player_ranks"
OPPONENT_RANKS = ROOT + "/data/generated/opponent_ranks"
REAL_RANKS = ROOT + "/data/generated/real_ranks"
MOVE_RANKS_FILE_PREFIX = ROOT + "/data/generated/move_ranks"
AVERAGE_RANKS_FILE = ROOT + "/data/generated/average_ranks"
AVERAGE_MOVES_RANKS_FILE = ROOT + "/data/generated/average_move_ranks"
