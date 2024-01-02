import json
import typing
from collections import defaultdict
from os.path import exists

import cattr

from config import FRESH_ATTACKER_TYPE_FILE, RAW_TYPE_FILE, FRESH_DEFENDER_TYPE_FILE
from data_class.PokemonType import PokemonType, convert_to_pokemon_type


def parse_type_chart_for_attack():
    with open(RAW_TYPE_FILE, "r", encoding="UTF-8") as f:
        done = False
        defender = f.readline().split()
        super_eff = defaultdict(list)
        normal_eff = defaultdict(list)
        not_eff = defaultdict(list)
        no_eff = defaultdict(list)

        s = f.readline().replace("×", "").replace("½", "0.5").split()
        while not done:
            attacker = convert_to_pokemon_type(s[0])
            for i, mul in enumerate(s[1:]):
                m = float(mul)
                if m == 0.5:
                    not_eff[attacker].append(convert_to_pokemon_type(defender[i]))
                if m == 0:
                    no_eff[attacker].append(convert_to_pokemon_type(defender[i]))
                if m == 2:
                    super_eff[attacker].append(convert_to_pokemon_type(defender[i]))
                if m == 1:
                    normal_eff[attacker].append(convert_to_pokemon_type(defender[i]))
            s = f.readline()
            if s == "":
                done = True
            s = s.replace("×", "").replace("½", "0.5").split()
        with open(FRESH_ATTACKER_TYPE_FILE, "w") as fo:
            list_ = [no_eff, not_eff, normal_eff, super_eff]
            fo.write(json.dumps(cattr.unstructure(list_)))


# [no_eff, not_eff, normal_eff, super_eff]
def get_attack_type_dict() -> list[typing.DefaultDict[PokemonType, list[PokemonType]]]:
    if not exists(FRESH_ATTACKER_TYPE_FILE):
        parse_type_chart_for_attack()
    with open(FRESH_ATTACKER_TYPE_FILE, "r") as fo:
        return cattr.structure(
            json.loads(fo.read()),
            typing.List[typing.DefaultDict[PokemonType, typing.List[PokemonType]]]
        )


# [no_eff, not_eff, super_eff]
def parse_type_chart_for_defense():
    super_eff = defaultdict(list)
    normal_eff = defaultdict(list)
    not_eff = defaultdict(list)
    no_eff = defaultdict(list)
    type_chart_attack = get_attack_type_dict()
    for k, vs in type_chart_attack[0].items():
        for v in vs:
            no_eff[v].append(k)
    for k, vs in type_chart_attack[1].items():
        for v in vs:
            not_eff[v].append(k)
    for k, vs in type_chart_attack[2].items():
        for v in vs:
            normal_eff[v].append(k)
    for k, vs in type_chart_attack[3].items():
        for v in vs:
            super_eff[v].append(k)

    with open(FRESH_DEFENDER_TYPE_FILE, "w") as fo:
        list_ = [no_eff, not_eff, normal_eff, super_eff]
        fo.write(json.dumps(cattr.unstructure(list_)))


def get_defend_type_dict() -> list[typing.DefaultDict[PokemonType, list[PokemonType]]]:
    if not exists(FRESH_DEFENDER_TYPE_FILE):
        parse_type_chart_for_defense()
    with open(FRESH_DEFENDER_TYPE_FILE, "r") as fo:
        return cattr.structure(
            json.loads(fo.read()),
            typing.List[typing.DefaultDict[PokemonType, typing.List[PokemonType]]])


if __name__ == "__main__":
    get_defend_type_dict()
    get_attack_type_dict()
