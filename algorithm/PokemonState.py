from data_class.Pokemon import Pokemon
from data_class.StatModifiers import StatModifiers


class PokemonState:

    def __init__(
            self,
            pokemon: Pokemon,
            stat_modifiers: StatModifiers,
            buffed,
            min_stats
    ):
        self.buffed = buffed
        self.stat_modifiers = stat_modifiers
        self.attacker = pokemon
        if min_stats:
            self.current_hp = pokemon.all_stats.level_50_min_stats.health
            self.attack_stat = pokemon.all_stats.level_50_min_stats.attack
            self.defense_stat = pokemon.all_stats.level_50_min_stats.defense
            self.special_attack = pokemon.all_stats.level_50_min_stats.special_attack
            self.special_defense = pokemon.all_stats.level_50_min_stats.special_defense
            self.speed = pokemon.all_stats.level_50_min_stats.speed
        else:
            self.current_hp = pokemon.all_stats.level_50_max_stats.health
            self.attack_stat = pokemon.all_stats.level_50_max_stats.attack
            self.defense_stat = pokemon.all_stats.level_50_max_stats.defense
            self.special_attack = pokemon.all_stats.level_50_max_stats.special_attack
            self.special_defense = pokemon.all_stats.level_50_max_stats.special_defense
            self.speed = pokemon.all_stats.level_50_max_stats.speed
        self.max_hp = self.current_hp
        self.pokemon = pokemon

    def get_max_hp(self):
        return self.max_hp

    def get_pokemon(self):
        return self.pokemon

    def add_damage(self, damage):
        self.current_hp -= damage

    def add_health(self, health):
        self.current_hp += health
        self.current_hp = min(self.current_hp, self.max_hp)

    def restore(self):
        self.current_hp = self.max_hp

