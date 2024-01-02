import math
from enum import unique, Enum
from math import floor

import attr


@unique
class StatEnum(Enum):
    """
       Represents Pokemon stats.
    """

    HEALTH = "health"
    ATTACK = "attack"
    DEFENSE = "defense"
    SPECIAL_ATTACK = "special_attack"
    SPECIAL_DEFENSE = "special_defense"
    SPEED = "speed"
    NO_STAT = "no_stat"


@attr.define
class Stat:
    stat_type: StatEnum
    value: int


__STAT_DICT__ = {
    "health": StatEnum.HEALTH,
    "attack": StatEnum.ATTACK,
    "defense": StatEnum.DEFENSE,
    "special_attack": StatEnum.SPECIAL_ATTACK,
    "special_defense": StatEnum.SPECIAL_DEFENSE,
    "speed": StatEnum.SPEED,
}


def get_stat_enum(stat):
    return __STAT_DICT__[stat.lower()]


def get_non_health_stat(base, iv, ev, level):
    return floor(
        (floor(
            ((2.0 * (base + iv) + floor(math.sqrt(ev) / 4.0)) * level) / 100.0
        ) + 5)
    )


def get_health_stat(base, iv, ev, level):
    return floor((((2.0 * (base + iv) + floor(math.sqrt(ev) / 4.0)) * level) / 100.0)) + level + 10
