class Spell:
    def __init__(self, name, type_, mana_cost, power, target, damage_type=None, status_effect=None):
        self.name = name
        self.type = type_ # "damage", "heal", "support"
        self.mana_cost = mana_cost
        self.power = power
        self.target = target
        self.damage_type = damage_type
        self.status_effect = status_effect

    def __str__(self):
        return f"{self.name} (Custo: {self.mana_cost} MP)"