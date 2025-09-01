class StatusEffect:
    def __init__(self, name, duration, damage_per_turn=0, stat_mods=None, color=(255, 255, 255)):
        self.name = name
        self.duration = duration
        self.damage_per_turn = damage_per_turn
        self.stat_mods = stat_mods if stat_mods else {} # Ex: {'defense': 10, 'attack': -5}
        self.color = color

    def __str__(self):
        return f"{self.name} ({self.duration})"