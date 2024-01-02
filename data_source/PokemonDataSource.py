import json
import random
import time
import urllib.request
from collections import defaultdict
from os.path import exists
from typing import Dict

import cattr
from bs4 import BeautifulSoup

from config import POKEMON_FILE
from data_class.AllStats import AllStats
from data_class.Attack import Attack
from data_class.BaseStats import BaseStats
from data_class.Category import convert_to_attack_category
from data_class.Pokemon import Pokemon
from data_class.PokemonInformation import PokemonInformation
from data_class.PokemonType import convert_to_pokemon_type
from data_class.Stat import get_health_stat, get_non_health_stat
from data_class.Stats import Stats

base_url = "https://www.serebii.net/pokedex-gs/"
num_pokemon = 251


def get_move_power(name, power_string):
    if power_string == '--' or \
            name in ["Sonicboom",
                     "Super Fang",
                     "Dragon Rage",
                     "Mirror Coat",
                     "Counter",
                     "Bide",
                     "SolarBeam",
                     "Dream Eater",
                     "Seismic Toss",
                     "Night Shade",
                     "Flail",
                     "Reversal",
                     "Horn Drill",
                     "Sheer Cold",
                     "Fissure",
                     "Guillotine",
                     "Magnitude",
                     "Low Kick",
                     "Present",
                     "Psywave",
                     "Hidden Power",
                     "Frustration",
                     "Magnitude",
                     "Explosion",
                     "Return"
                     ]:
        power = -1
    else:
        power = int(power_string)
    return power


def get_url(index: int):
    return base_url + str(index).zfill(3) + ".shtml"


def process_general_information(dextable):
    rows = dextable.find_all("tr")
    assert rows[0].text == "\nName\nOther Names\nNo.\nGender Ratio\nType\n"
    first_row_tokens = rows[1].text.split("\n")

    pokemon_index = int(first_row_tokens[8].split("#")[-1].strip())
    pokemon_name = first_row_tokens[1].strip()

    offset = 0
    if len(rows) == 10:
        offset = -2
    elif len(rows) == 12:
        pass
    else:
        assert False

    assert rows[10 + offset].text == '\nClassification\nHeight\nWeight\nCapture Rate\nBase Egg Steps\n'
    pounds = float(rows[11 + offset].text.split()[-2][:-3])

    pokemon_types = []
    type_images = rows[1].find_all("img")
    assert len(type_images) < 3
    for img in type_images:
        pokemon_type = img['src'].split("/")[-1].split(".")[0]
        if pokemon_type != "na":
            pokemon_types.append(
                convert_to_pokemon_type(pokemon_type)
            )

    return PokemonInformation(
        id=pokemon_index,
        name=pokemon_name,
        pokemon_types=pokemon_types,
        pounds=pounds
    )


def get_level_up_attacks(dextable):
    level_to_attacks = defaultdict(lambda: [])
    rows = dextable.find_all("tr")
    assert rows[0].text in [
        'Generation II Level Up',
        'Gold & Silver Level Up',
        'Crystal Level Up'
    ]
    assert rows[1].text == 'LevelAttack NameTypeAtt.Acc.PPEffect %'

    row_index = 2
    while row_index < len(rows):
        columns = rows[row_index].find_all("td")

        level = columns[0].text
        if level == '—':
            level = 0
        else:
            level = int(level)

        name = columns[1].text
        attack_type = columns[2].find("img")['src'].split("/")[-1].split(".")[0]

        power = columns[3].text
        power = get_move_power(name, power)

        accuracy = columns[4].text
        if accuracy == '--':
            accuracy = 0
        else:
            accuracy = int(accuracy)

        effect_chance = columns[6].text
        if effect_chance == "--":
            effect_chance = 0
        effect_chance = int(effect_chance)

        level_to_attacks[level].append(
            Attack(
                name=name,
                pokemon_type=convert_to_pokemon_type(attack_type),
                power=power,
                accuracy=accuracy,
                effect_percent=effect_chance,
                category=convert_to_attack_category(attack_type)
            )
        )

        row_index += 2
    return level_to_attacks


def get_tm_and_hm_attacks(dextable):
    tm_or_hm_to_attack = dict()
    rows = dextable.find_all("tr")
    assert rows[0].text in [
        'TM & HM Attacks'
    ]
    assert rows[1].text == 'TM/HM #Attack NameTypeAtt.Acc.PPEffect %'

    row_index = 2
    while row_index < len(rows):
        columns = rows[row_index].find_all("td")

        tm_or_hm = columns[0].text

        name = columns[1].text.strip()
        attack_type = columns[2].find("img")['src'].split("/")[-1].split(".")[0]

        power = columns[3].text
        power = get_move_power(name, power)

        accuracy = columns[4].text
        if accuracy == '--':
            accuracy = 0
        else:
            accuracy = int(accuracy)

        effect_chance = columns[6].text
        if effect_chance == "--":
            effect_chance = 0
        effect_chance = int(effect_chance)

        tm_or_hm_to_attack[tm_or_hm] = Attack(
            name=name,
            pokemon_type=convert_to_pokemon_type(attack_type),
            power=power,
            accuracy=accuracy,
            effect_percent=effect_chance,
            category=convert_to_attack_category(attack_type)
        )

        row_index += 2
    return tm_or_hm_to_attack


def get_move_tutor_attacks(dextable):
    attacks = []
    rows = dextable.find_all("tr")
    assert rows[0].text in [
        'Crystal Move Tutor Attacks',
        'Emerald Tutor Attacks',
        'Egg Moves (Details)',
        'Special Moves',
        'Gen I Only Moves (Details)',
        'Gen I  Only Moves (Details)',
        'Pre-Evolution Only Moves'
    ]
    assert rows[1].text.strip() == 'Attack NameTypeAtt.Acc.PPEffect %' or \
           rows[1].text.strip() == 'Attack NameTypeAtt.Acc.PPEffect %Method' or \
           rows[1].text.strip() == 'Attack NameTypeAtt.Acc.PPEffect % Method'

    row_index = 2
    if rows[0].text == 'Gen I  Only Moves (Details)':
        row_index = 3

    while row_index < len(rows):
        columns = rows[row_index].find_all("td")

        name = columns[0].text
        attack_type = columns[1].find("img")['src'].split("/")[-1].split(".")[0]

        power = columns[2].text
        power = get_move_power(name, power)

        accuracy = columns[3].text
        if accuracy == '--':
            accuracy = 0
        else:
            accuracy = int(accuracy)

        effect_chance = columns[5].text
        if effect_chance == "--":
            effect_chance = 0
        effect_chance = int(effect_chance)

        attacks.append(
            Attack(
                name=name,
                pokemon_type=convert_to_pokemon_type(attack_type),
                power=power,
                accuracy=accuracy,
                effect_percent=effect_chance,
                category=convert_to_attack_category(attack_type)
            )
        )

        row_index += 2
        if rows[0].text == 'Pre-Evolution Only Moves':
            row_index += 1
    return attacks


def convert_to_level_50_min_stats(base_stats):
    hp = get_health_stat(
        base=base_stats.stats.health,
        iv=0,
        ev=0,
        level=50
    )
    attack = get_non_health_stat(
        base=base_stats.stats.attack,
        iv=0,
        ev=0,
        level=50,
    )

    defense = get_non_health_stat(
        base=base_stats.stats.defense,
        iv=0,
        ev=0,
        level=50,
    )

    special_attack = get_non_health_stat(
        base=base_stats.stats.special_attack,
        iv=0,
        ev=0,
        level=50,
    )

    special_defense = get_non_health_stat(
        base=base_stats.stats.special_defense,
        iv=0,
        ev=0,
        level=50,
    )

    speed = get_non_health_stat(
        base=base_stats.stats.speed,
        iv=0,
        ev=0,
        level=50,
    )

    return Stats(
        name=base_stats.name,
        health=hp,
        attack=attack,
        defense=defense,
        special_attack=special_attack,
        special_defense=special_defense,
        speed=speed
    )


def convert_to_level_50_max_stats(base_stats):
    hp = get_health_stat(
        base=base_stats.stats.health,
        iv=15,
        ev=65535,
        level=50
    )
    attack = get_non_health_stat(
        base=base_stats.stats.attack,
        iv=15,
        ev=65535,
        level=50,
    )

    defense = get_non_health_stat(
        base=base_stats.stats.defense,
        iv=15,
        ev=65535,
        level=50,
    )

    special_attack = get_non_health_stat(
        base=base_stats.stats.special_attack,
        iv=15,
        ev=65535,
        level=50,
    )

    special_defense = get_non_health_stat(
        base=base_stats.stats.special_defense,
        iv=15,
        ev=65535,
        level=50,
    )

    speed = get_non_health_stat(
        base=base_stats.stats.speed,
        iv=15,
        ev=65535,
        level=50,
    )

    return Stats(
        name=base_stats.name,
        health=hp,
        attack=attack,
        defense=defense,
        special_attack=special_attack,
        special_defense=special_defense,
        speed=speed
    )


def convert_to_level_100_min_stats(base_stats):
    hp = get_health_stat(
        base=base_stats.stats.health,
        iv=0,
        ev=0,
        level=100
    )
    attack = get_non_health_stat(
        base=base_stats.stats.attack,
        iv=0,
        ev=0,
        level=100,
    )

    defense = get_non_health_stat(
        base=base_stats.stats.defense,
        iv=0,
        ev=0,
        level=100,
    )

    special_attack = get_non_health_stat(
        base=base_stats.stats.special_attack,
        iv=0,
        ev=0,
        level=100,
    )

    special_defense = get_non_health_stat(
        base=base_stats.stats.special_defense,
        iv=0,
        ev=0,
        level=100,
    )

    speed = get_non_health_stat(
        base=base_stats.stats.speed,
        iv=0,
        ev=0,
        level=100,
    )

    return Stats(
        name=base_stats.name,
        health=hp,
        attack=attack,
        defense=defense,
        special_attack=special_attack,
        special_defense=special_defense,
        speed=speed
    )


def convert_to_level_100_max_stats(base_stats):
    hp = get_health_stat(
        base=base_stats.stats.health,
        iv=15,
        ev=65535,
        level=100
    )
    attack = get_non_health_stat(
        base=base_stats.stats.attack,
        iv=15,
        ev=65535,
        level=100,
    )

    defense = get_non_health_stat(
        base=base_stats.stats.defense,
        iv=15,
        ev=65535,
        level=100,
    )

    special_attack = get_non_health_stat(
        base=base_stats.stats.special_attack,
        iv=15,
        ev=65535,
        level=100,
    )

    special_defense = get_non_health_stat(
        base=base_stats.stats.special_defense,
        iv=15,
        ev=65535,
        level=100,
    )

    speed = get_non_health_stat(
        base=base_stats.stats.speed,
        iv=15,
        ev=65535,
        level=100,
    )

    return Stats(
        name=base_stats.name,
        health=hp,
        attack=attack,
        defense=defense,
        special_attack=special_attack,
        special_defense=special_defense,
        speed=speed
    )


def get_stats(dextable, name):
    rows = dextable.find_all("tr")
    assert rows[0].text in [
        '\nStats',
        'Stats (Attack form)',
        'Stats (Defence Form)',
        'Stats (Speed form)'
    ]
    assert rows[1].text == '\n \nHP\nAttack\nDefense\nSp. Attack\nSp. Defense\nSpeed'
    columns = rows[2].find_all("td")
    assert len(columns) == 7
    assert columns[0].text.split("-")[0] == 'Base Stats '
    base_hp = int(columns[1].text)
    base_attack = int(columns[2].text)
    base_defense = int(columns[3].text)
    base_special_attack = int(columns[4].text)
    base_special_defense = int(columns[5].text)
    base_speed = int(columns[6].text)

    base_stats = BaseStats(
        name=name,
        stats=Stats(
            name=name,
            health=base_hp,
            attack=base_attack,
            defense=base_defense,
            special_attack=base_special_attack,
            special_defense=base_special_defense,
            speed=base_speed
        )
    )

    return AllStats(
        name=name,
        base_stats=base_stats,
        level_50_min_stats=convert_to_level_50_min_stats(base_stats),
        level_50_max_stats=convert_to_level_50_max_stats(base_stats),
        level_100_min_stats=convert_to_level_100_min_stats(base_stats),
        level_100_max_stats=convert_to_level_100_max_stats(base_stats)
    )


def __scrape_serebii_for_move_sets__():
    first_row_text_of_skippable_tables = [
        '\nWild Hold Item\nEgg Groups\n',
        '\n\r\n\t\tDamage Taken\r\n\t\t\n',
        '\n\r\n\t\tFlavor Text\r\n\t\t\n',
        '\nLocations\n',
        '\nEgg Steps to Hatch\nEffort Points from Battling it\nCatch Rate\n',
        'Egg Groups',
        "\nExperience Growth\nBase Happiness\nEffort Values Earned\n",
        '\nPicture\n',
        '\nEvolutionary Chain\n',
        "\nLocations - In-Depth Details\n"
    ]

    pokemon_index_to_pokemon: dict[int, Pokemon] = dict()
    last_url_index = 0
    for pokemon_index in range(last_url_index + 1, num_pokemon + 1):
        url = get_url(pokemon_index)
        genII_level_to_attacks = None
        genI_attacks = None
        tm_or_hm_to_attack = None
        move_tutor_attacks = None
        egg_moves = None
        special_attacks = None
        all_stats = None
        pre_evolution_attacks = None
        gold_level_to_attacks = None
        crystal_level_to_attacks = None
        with urllib.request.urlopen(url) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
            dextables = soup.find_all("table", class_="dextable")
            for dextable in dextables:
                first_row_text = dextable.find("tr").text
                if first_row_text not in first_row_text_of_skippable_tables:
                    if first_row_text == "\nName\nOther Names\nNo.\nGender Ratio\nType\n":
                        pokemon_information = process_general_information(dextable)
                    elif first_row_text == 'Generation II Level Up':
                        genII_level_to_attacks = get_level_up_attacks(dextable)
                    elif first_row_text == 'Gold & Silver Level Up':
                        gold_level_to_attacks = get_level_up_attacks(dextable)
                    elif first_row_text == 'Crystal Level Up':
                        crystal_level_to_attacks = get_level_up_attacks(dextable)
                    elif first_row_text == 'Gen I Only Moves (Details)' or \
                            first_row_text == 'Gen I  Only Moves (Details)':
                        genI_attacks = get_move_tutor_attacks(dextable)
                    elif first_row_text == 'Pre-Evolution Only Moves':
                        pre_evolution_attacks = get_move_tutor_attacks(dextable)
                    elif first_row_text == 'TM & HM Attacks':
                        tm_or_hm_to_attack = get_tm_and_hm_attacks(dextable)
                    elif first_row_text == 'Crystal Move Tutor Attacks':
                        move_tutor_attacks = get_move_tutor_attacks(dextable)
                    elif first_row_text == 'Egg Moves (Details)':
                        egg_moves = get_move_tutor_attacks(dextable)
                    elif first_row_text == 'Special Moves':
                        special_attacks = get_move_tutor_attacks(dextable)
                    elif first_row_text == '\nStats':
                        all_stats = get_stats(dextable, pokemon_information.name)
                    else:
                        assert False

        assert all_stats is not None

        if gold_level_to_attacks is not None:
            if genII_level_to_attacks is None:
                genII_level_to_attacks = defaultdict(list)
            for k, v in gold_level_to_attacks.items():
                genII_level_to_attacks[k] += v
        if crystal_level_to_attacks is not None:
            if genII_level_to_attacks is None:
                genII_level_to_attacks = defaultdict(list)
            for k, v in crystal_level_to_attacks.items():
                genII_level_to_attacks[k] += v
        assert genII_level_to_attacks is not None

        pokemon_index_to_pokemon[pokemon_index] = Pokemon(
            pokemon_information=pokemon_information,
            genII_level_to_attacks=genII_level_to_attacks,
            genI_attacks=genI_attacks,
            tm_or_hm_to_attack=tm_or_hm_to_attack,
            move_tutor_attacks=move_tutor_attacks,
            egg_moves=egg_moves,
            pre_evolution_attacks=pre_evolution_attacks,
            special_attacks=special_attacks,
            all_stats=all_stats,
        )
        time.sleep(0.5 + (random.random() / 2.0))
    return pokemon_index_to_pokemon


def get_pokemon() -> Dict[int, Pokemon]:
    if not exists(POKEMON_FILE):
        pokemon_index_to_pokemon = __scrape_serebii_for_move_sets__()
        with open(POKEMON_FILE, "w") as fo:
            fo.write(json.dumps(cattr.unstructure(pokemon_index_to_pokemon)))
    else:
        with open(POKEMON_FILE, "r") as fo:
            pokemon_index_to_pokemon = cattr.structure(json.loads(fo.read()), Dict[str, Pokemon])
    return pokemon_index_to_pokemon


if __name__ == "__main__":
    pokemon_index_to_pokemon = get_pokemon()
    pass
