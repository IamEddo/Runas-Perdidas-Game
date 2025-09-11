import pygame
from settings import TILE_SIZE, PHYSICAL, FIRE, ICE, WHITE
from status_effects import StatusEffect
from items import Item
import random
from collections import deque

class Enemy:
    def __init__(self, x, y, level=1):
        self.x = x
        self.y = y
        self.level = level
        self.max_hp = 30 + level * 15
        self.hp = self.max_hp
        self.color = (0, 0, 255)
        self.vision_range = 6 # Aumentado para o pathfinding ser mais útil
        self.size = TILE_SIZE
        self.gold_drop = 5 * level
        self.attack_type = PHYSICAL
        self.weaknesses = {FIRE: 1.5}
        self.resistances = {ICE: 0.5}
        self.status_effects = []
        
        self.font = pygame.font.SysFont("Arial", 14)

        # --- NOVOS ATRIBUTOS PARA MOVIMENTO ---
        self.path = []
        self.move_cooldown = 20 # Inimigos se movem a cada 20 frames
        self.move_timer = 0
        # ------------------------------------

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

    def find_path(self, start, goal, game_map):
        """
        Encontra o caminho mais curto usando Breadth-First Search (BFS).
        Retorna uma lista de tuplas (x, y) ou uma lista vazia se não houver caminho.
        """
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            (current_x, current_y), path = queue.popleft()

            if (current_x, current_y) == goal:
                return path[1:] # Retorna o caminho sem o ponto inicial

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current_x + dx, current_y + dy)
                if game_map.is_walkable(neighbor[0], neighbor[1]) and neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append((neighbor, new_path))
        return [] # Nenhum caminho encontrado

    def update(self, player, game_map):
        self.move_timer += 1
        if self.move_timer < self.move_cooldown:
            return
        self.move_timer = 0

        dx, dy = player.x - self.x, player.y - self.y
        dist = abs(dx) + abs(dy)

        if dist <= self.vision_range and dist > 1:
            # Recalcula o caminho se não houver um ou se o jogador se moveu muito
            recalculate = not self.path
            if self.path:
                path_goal_x, path_goal_y = self.path[-1]
                if abs(player.x - path_goal_x) > 2 or abs(player.y - path_goal_y) > 2:
                    recalculate = True
            
            if recalculate:
                self.path = self.find_path((self.x, self.y), (player.x, player.y), game_map)

            # Move-se ao longo do caminho
            if self.path:
                next_x, next_y = self.path.pop(0)
                if game_map.is_walkable(next_x, next_y):
                    self.x = next_x
                    self.y = next_y
                else:
                    self.path = [] # Limpa o caminho se estiver bloqueado

    def draw(self, screen, camera_x, camera_y):
        rect = pygame.Rect(self.x * TILE_SIZE - camera_x, self.y * TILE_SIZE - camera_y, self.size, self.size)
        pygame.draw.rect(screen, self.color, rect)
        hp_text = self.font.render(f"HP: {self.hp}/{self.max_hp}", True, WHITE)
        lvl_text = self.font.render(f"Lv: {self.level}", True, (255, 255, 0))
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
        self.move_cooldown = 45 # Chefes se movem mais lentamente
        self.move_timer = 0
        self.enraged = False

    def decide_action(self):
        # Mecânica de fúria: ativa uma vez quando o HP cai abaixo de 50%
        if not self.enraged and self.hp <= self.max_hp * 0.5:
            return "enrage"
        
        # Ações no estado de fúria
        if self.enraged:
            if random.random() < 0.5: # 50% de chance de usar o ataque esmagador
                return "smash_attack"
            else: # 50% de chance de um ataque normal
                return "attack"
        
        # Ações no estado normal (chefes não se curam)
        return "attack"

    def update(self, player, game_map):
        self.move_timer += 1
        if self.move_timer < self.move_cooldown:
            return
        self.move_timer = 0

        dx, dy = player.x - self.x, player.y - self.y
        dist = abs(dx) + abs(dy)

        # O chefe se move se não estiver adjacente ao jogador
        if dist > 1:
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0

            # Lógica de movimento simples: prioriza o eixo com maior distância
            if abs(dx) > abs(dy):
                if game_map.is_walkable(self.x + step_x, self.y):
                    self.x += step_x
                elif game_map.is_walkable(self.x, self.y + step_y):
                    self.y += step_y
            else:
                if game_map.is_walkable(self.x, self.y + step_y):
                    self.y += step_y
                elif game_map.is_walkable(self.x + step_x, self.y):
                    self.x += step_x
    
    def enrage(self):
        """Ativa o modo de fúria, aumentando o ataque e mudando a cor."""
        self.enraged = True
        self.min_attack += 20
        self.max_attack += 20
        self.color = (255, 0, 128) # Rosa choque para indicar fúria
        return "O Chefe ruge de fúria! Seu ataque aumentou!"

    def smash_attack(self): return random.randint(100, 150), True
