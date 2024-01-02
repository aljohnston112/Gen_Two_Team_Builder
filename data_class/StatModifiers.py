class StatModifiers:

    def __init__(
            self,
            attack_modifier: float,
            special_attack_modifier: float,
            defense_modifier: float,
            special_defense_modifier: float,
            speed_modifier: float,
            accuracy_modifier: float,
            evasion_modifier: float,
    ):
        self.attack_modifier = attack_modifier
        self.special_attack_modifier = special_attack_modifier
        self.defense_modifier = defense_modifier
        self.special_defense_modifier = special_defense_modifier
        self.speed_modifier = speed_modifier
        self.accuracy_modifier = accuracy_modifier
        self.evasion_modifier = evasion_modifier
