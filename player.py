import pygame
from settings import *
from items import Item
from spells import Spell
from status_effects import StatusEffect
import random

class Player:
    def __init__(self, character_class):
        self.character_class = character_class
        self.x = 10
        self.y = 10
        self.level = 1
        self.exp = 0
        self.gold = 50
        self.quest = None
        self.color = (255, 0, 0)
        self.status_effects = []
        self.is_defending = False
        self.movement_cooldown = 0
        self.terrain_damage_timer = 0
        self.skill_points = 0

        # --- NOVOS ATRIBUTOS PARA VANTAGEM DO ARQUEIRO ---
        self.last_direction = (0, 1) # (dx, dy), começa olhando para baixo
        self.ranged_shot_cooldown = 0
        # ------------------------------------------------

        if self.character_class == "Guerreiro":
            self.max_hp = 150
            self.max_mana = 30
            self.base_attack = 15
            self.crit_chance = 0.20
            self.inventory = [Item("Espada de Ferro", "weapon", slot="weapon", power=8, damage_type=PHYSICAL, price=20), Item("Poção", "consumable", price=10)]
            self.spells = []
        elif self.character_class == "Mago":
            self.max_hp = 80
            self.max_mana = 100
            self.base_attack = 5
            self.crit_chance = 0.10
            self.inventory = [Item("Cajado Simples", "weapon", slot="weapon", power=4, damage_type=PHYSICAL, price=15), Item("Poção de Mana", "consumable", price=15)]
            self.spells = [Spell("Cura Menor", "heal", 10, 25, "self")]
        elif self.character_class == "Arqueiro":
            self.max_hp = 100
            self.max_mana = 50
            self.base_attack = 10
            self.crit_chance = 0.35
            self.inventory = [Item("Arco Curto", "weapon", slot="weapon", power=6, damage_type=PHYSICAL, price=18), Item("Poção", "consumable", price=10)]
            self.spells = []

        self.hp = self.max_hp
        self.mana = self.max_mana
        self.equipped_weapon = next((item for item in self.inventory if item.slot == "weapon"), None)
        self.equipped_chest = None
        self.equipped_helmet = None
        self.equipped_gloves = None
        self.equipped_boots = None

    @property
    def defense(self):
        base_def = 0
        if self.equipped_chest: base_def += self.equipped_chest.defense
        if self.equipped_helmet: base_def += self.equipped_helmet.defense
        if self.equipped_gloves: base_def += self.equipped_gloves.defense
        if self.equipped_boots: base_def += self.equipped_boots.defense
        mod_def = sum(effect.stat_mods.get('defense', 0) for effect in self.status_effects)
        return base_def + mod_def

    @property
    def attack(self):
        base_atk = self.base_attack + (self.equipped_weapon.power if self.equipped_weapon else 0)
        mod_atk = sum(effect.stat_mods.get('attack', 0) for effect in self.status_effects)
        return base_atk + mod_atk

    def equip(self, item_to_equip):
        if not item_to_equip.slot: return
        
        # Desequipa o item atual, se houver, e o devolve ao inventário
        if item_to_equip.slot == "weapon" and self.equipped_weapon: self.inventory.append(self.equipped_weapon)
        elif item_to_equip.slot == "chest" and self.equipped_chest: self.inventory.append(self.equipped_chest)
        elif item_to_equip.slot == "helmet" and self.equipped_helmet: self.inventory.append(self.equipped_helmet)
        elif item_to_equip.slot == "gloves" and self.equipped_gloves: self.inventory.append(self.equipped_gloves)
        elif item_to_equip.slot == "boots" and self.equipped_boots: self.inventory.append(self.equipped_boots)

        # Equipa o novo item
        if item_to_equip.slot == "weapon": self.equipped_weapon = item_to_equip
        elif item_to_equip.slot == "chest": self.equipped_chest = item_to_equip
        elif item_to_equip.slot == "helmet": self.equipped_helmet = item_to_equip
        elif item_to_equip.slot == "gloves": self.equipped_gloves = item_to_equip
        elif item_to_equip.slot == "boots": self.equipped_boots = item_to_equip
        
        # Remove o novo item do inventário
        self.inventory.remove(item_to_equip)

    def gain_exp(self, amount):
        self.exp += amount
        while self.exp >= 100:
            self.exp -= 100
            self.level += 1
            self.skill_points += 1
            self.max_hp += 20
            self.hp = self.max_hp
            self.max_mana += 10
            self.mana = self.max_mana
            self.inventory.append(Item("Poção", "consumable", price=10))
            self.inventory.append(Item("Poção de Mana", "consumable", price=15))

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
                messages.append(f"Você sofreu {effect.damage_per_turn} de dano de {effect.name}!")
            effect.duration -= 1
            if effect.duration <= 0:
                self.status_effects.remove(effect)
                messages.append(f"O efeito {effect.name} passou.")
        return " ".join(messages)

    def take_damage(self, damage):
        final_damage = max(1, damage - self.defense)
        self.hp -= final_damage
        return final_damage

    def move(self, dx, dy, game_map):
        if self.movement_cooldown > 0:
            return
        
        new_x = self.x + dx
        new_y = self.y + dy
        if game_map.is_walkable(new_x, new_y):
            # --- MODIFICAÇÃO: Armazena a última direção de movimento ---
            if dx != 0 or dy != 0:
                self.last_direction = (dx, dy)
            # ---------------------------------------------------------
            self.x = new_x
            self.y = new_y
            tile_type = game_map.get_tile_type(self.x, self.y)
            if tile_type == SWAMP:
                self.movement_cooldown = 30
            else:
                self.movement_cooldown = 7

    def update(self, keys, game_map):
        if self.movement_cooldown > 0:
            self.movement_cooldown -= 1
        
        # --- MODIFICAÇÃO: Atualiza o cooldown do tiro à distância ---
        if self.ranged_shot_cooldown > 0:
            self.ranged_shot_cooldown -= 1
        # ---------------------------------------------------------

        if keys[pygame.K_UP]: self.move(0, -1, game_map)
        elif keys[pygame.K_DOWN]: self.move(0, 1, game_map)
        elif keys[pygame.K_LEFT]: self.move(-1, 0, game_map)
        elif keys[pygame.K_RIGHT]: self.move(1, 0, game_map)

    def attack_power(self):
        base = self.attack
        if random.random() < self.crit_chance:
            return base * 2, True
        return base, False

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.rect(screen, self.color, (self.x * TILE_SIZE - camera_x, self.y * TILE_SIZE - camera_y, TILE_SIZE, TILE_SIZE))

    def to_dict(self):
        def item_to_dict(item):
            if not item: return None
            item_dict = vars(item).copy()
            if 'type_' in item_dict:
                item_dict['type'] = item_dict.pop('type_')
            return item_dict
        
        return {
            "class": self.character_class, "x": self.x, "y": self.y, "level": self.level,
            "exp": self.exp, "gold": self.gold, "hp": self.hp, "mana": self.mana,
            "skill_points": self.skill_points,
            "inventory": [item_to_dict(item) for item in self.inventory],
            "spells": [s.name for s in self.spells],
            "equipped_weapon": item_to_dict(self.equipped_weapon),
            "equipped_chest": item_to_dict(self.equipped_chest),
            "equipped_helmet": item_to_dict(self.equipped_helmet),
            "equipped_gloves": item_to_dict(self.equipped_gloves),
            "equipped_boots": item_to_dict(self.equipped_boots),
            "quest": vars(self.quest) if self.quest else None
        }
    
    @staticmethod
    def from_dict(data, all_spells_list):
        """Cria uma instância de Player a partir de um dicionário."""
        # Importação local para evitar dependência circular
        from npc import Quest
        
        player = Player(data["class"])
        player.x, player.y, player.level, player.exp, player.gold, player.hp, player.mana, player.skill_points = \
            data["x"], data["y"], data["level"], data["exp"], data["gold"], data["hp"], data["mana"], data.get("skill_points", 0)

        player.inventory = []
        for item_data in data.get("inventory", []):
            if 'type' in item_data: item_data['type_'] = item_data.pop('type')
            player.inventory.append(Item(**item_data))
        
        # Recria as magias
        player.spells = [spell for spell in all_spells_list if spell.name in data.get("spells", [])]

        for slot in ["weapon", "chest", "helmet", "gloves", "boots"]:
            equipped_item_data = data.get(f"equipped_{slot}")
            if equipped_item_data:
                # Procura o item exato no inventário para equipar
                for item_in_inv in player.inventory:
                    if item_in_inv.name == equipped_item_data.get('name') and item_in_inv.slot == equipped_item_data.get('slot'):
                        player.equip(item_in_inv)
                        break

        if data.get("quest"):
            player.quest = Quest(**data["quest"])
        return player