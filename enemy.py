import pygame
from settings import TILE_SIZE, PHYSICAL, FIRE, ICE
from status_effects import StatusEffect
from items import Item
import random

class Enemy:
    def __init__(self, x, y, level=1):
        self.x = x
        self.y = y
        self.level = level
        self.max_hp = 30 + level * 15
        self.hp = self.max_hp
        self.color = (0, 0, 255)
        self.vision_range = 4
        self.size = TILE_SIZE
        self.gold_drop = 5 * level
        self.attack_type = PHYSICAL
        self.weaknesses = {FIRE: 1.5}
        self.resistances = {ICE: 0.5}
        self.status_effects = []
        
        # Tabela de Loot
        self.loot_table = [Item("Pele de Lobo", "material")]
        if level >= 2: self.loot_table.append(Item("Minério de Ferro", "material"))
        if level >= 3: self.loot_table.append(Item("Erva Curativa", "material"))

        if level == 1: self.min_attack, self.max_attack = 10, 30
        elif level == 2: self.min_attack, self.max_attack = 30, 50
        elif level == 3: self.min_attack, self.max_attack = 50, 70
        else: self.min_attack, self.max_attack = 70, 90

    def decide_action(self):
        if self.hp < self.max_hp * 0.3 and random.random() < 0.5:
            return "heal"
        return "attack"

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
        return amount

    @property
    def defense(self):
        base_def = 0
        mod_def = sum(effect.stat_mods.get('defense', 0) for effect in self.status_effects)
        return base_def + mod_def

    @property
    def attack(self):
        base_atk = random.randint(self.min_attack, self.max_attack)
        mod_atk = sum(effect.stat_mods.get('attack', 0) for effect in self.status_effects)
        return base_atk + mod_atk

    def apply_status(self, effect):
        for existing_effect in self.status_effects:
            if existing_effect.name == effect.name:
                existing_effect.duration = effect.duration
                return
        self.status_effects.append(StatusEffect(effect.name, effect.duration, effect.damage_per_turn, effect.stat_mods, effect.color))

    def update_status_effects(self):
        messages = []
        for effect in self.status_effects[:]:
            if effect.damage_per_turn > 0:
                self.hp -= effect.damage_per_turn
                messages.append(f"Inimigo sofreu {effect.damage_per_turn} de dano de {effect.name}!")
            effect.duration -= 1
            if effect.duration <= 0:
                self.status_effects.remove(effect)
        return " ".join(messages)

    def take_damage(self, damage, damage_type):
        multiplier = self.weaknesses.get(damage_type, 1.0)
        multiplier *= self.resistances.get(damage_type, 1.0)
        final_damage = int(damage * multiplier)
        self.hp -= final_damage
        return final_damage, multiplier > 1.0, multiplier < 1.0

    @property
    def attack_power(self):
        base_attack = self.attack
        if random.random() < 0.10:
            return base_attack * 2, True
        return base_attack, False

    def update(self, player, game_map):
        dx, dy = player.x - self.x, player.y - self.y
        dist = abs(dx) + abs(dy)
        if dist <= self.vision_range and dist > 1:
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0
            if abs(dx) > abs(dy):
                if game_map.is_walkable(self.x + step_x, self.y): self.x += step_x
                elif game_map.is_walkable(self.x, self.y + step_y): self.y += step_y
            else:
                if game_map.is_walkable(self.x, self.y + step_y): self.y += step_y
                elif game_map.is_walkable(self.x + step_x, self.y): self.x += step_x

    def draw(self, screen, camera_x, camera_y):
        rect = pygame.Rect(self.x * TILE_SIZE - camera_x, self.y * TILE_SIZE - camera_y, self.size, self.size)
        pygame.draw.rect(screen, self.color, rect)
        font = pygame.font.SysFont("Arial", 14)
        hp_text = font.render(f"HP: {self.hp}/{self.max_hp}", True, (255, 255, 255))
        lvl_text = font.render(f"Lv: {self.level}", True, (255, 255, 0))
        screen.blit(hp_text, (rect.x, rect.y - 20))
        screen.blit(lvl_text, (rect.x, rect.y - 35))

class Boss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, level=10)
        self.max_hp = 800
        self.hp = self.max_hp
        self.min_attack, self.max_attack = 50, 80
        self.color = (128, 0, 128)
        self.size = TILE_SIZE * 2
        self.gold_drop = 500
        self.weaknesses = {}
        self.resistances = {PHYSICAL: 0.7, FIRE: 0.7, ICE: 0.7}
        self.loot_table = [Item("Fragmento de Poder", "material")]

    def update(self, player, game_map): pass
    def smash_attack(self): return random.randint(100, 150), True