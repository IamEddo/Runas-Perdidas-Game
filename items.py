class Item:
    def __init__(self, name, type_, slot=None, power=0, defense=0, damage_type=None, price=0):
        self.name = name
        self.type = type_
        self.slot = slot
        self.power = power
        self.defense = defense
        self.damage_type = damage_type
        self.price = price

    def __str__(self):
        return f"{self.name} ({self.type})"