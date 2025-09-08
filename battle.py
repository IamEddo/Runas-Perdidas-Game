import pygame
from settings import *
from items import Item
from spells import Spell
from enemy import Boss
import random

class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = (100, 100, 100)

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        text_surface = font.render(self.text, True, WHITE)
        screen.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))

    def click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()

class Battle:
    def __init__(self, screen, player, enemy, background):
        self.screen = screen
        self.player = player
        self.enemy = enemy
        self.background = background
        self.font = pygame.font.SysFont("Arial", 20)
        self.running = True
        self.message = ""
        self.fled = False
        self.turn = "player"

        self.buttons = [ 
            Button(50, 400, 120, 40, "Atacar", self.attack),
            Button(180, 400, 120, 40, "Magias", self.choose_spell),
            Button(310, 400, 120, 40, "Defender", self.defend),
            Button(440, 400, 120, 40, "Poção", self.use_potion),
            Button(570, 400, 120, 40, "Fugir", self.flee)
        ]

    def draw_health_bar(self, x, y, current, max_health, color):
        width = 200
        height = 20
        pygame.draw.rect(self.screen, (50, 50, 50), (x, y, width, height))
        if max_health > 0:
            fill = (current / max_health) * width
            pygame.draw.rect(self.screen, color, (x, y, fill, height))
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)

    def draw_mana_bar(self, x, y, current, max_mana, color):
        width = 150
        height = 15
        pygame.draw.rect(self.screen, (50, 50, 50), (x, y, width, height))
        if max_mana > 0:
            fill = (current / max_mana) * width
            pygame.draw.rect(self.screen, color, (x, y, fill, height))
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)

    def handle_status_effects(self, character):
        status_message = character.update_status_effects()
        if status_message:
            self.message += " " + status_message

    def next_turn(self):
        if self.turn == "player":
            self.turn = "enemy"
            self.handle_status_effects(self.enemy)
            if self.enemy.hp <= 0:
                self.end_battle(win=True)
            else:
                self.enemy_turn()
        elif self.turn == "enemy":
            self.turn = "player"
            self.player.is_defending = False # Reseta a defesa no início do turno do jogador
            self.handle_status_effects(self.player)
            if self.player.hp <= 0:
                self.end_battle(win=False)

    def attack(self):
        damage, player_crit = self.player.attack_power()
        damage_type = self.player.equipped_weapon.damage_type if self.player.equipped_weapon else PHYSICAL
        final_damage, weak, resist = self.enemy.take_damage(damage, damage_type)
        
        self.message = f"Você causou {final_damage} de dano!"
        if player_crit: self.message = f"CRÍTICO! {self.message}"
        if weak: self.message += " (Super Efetivo!)"
        if resist: self.message += " (Pouco Efetivo...)"
        
        self.next_turn()

    def defend(self):
        self.player.is_defending = True
        self.message = "Você se prepara para defender!"
        self.next_turn()

    def flee(self):
        if isinstance(self.enemy, Boss):
            self.message = "Não se pode fugir de um chefe!"
            return
        if random.random() < 0.5:
            self.message = "Você conseguiu fugir!"
            self.fled = True
            self.running = False
        else:
            self.message = "A fuga falhou!"
            self.next_turn()

    def enemy_turn(self):
        action = self.enemy.decide_action()
        
        if action == "heal":
            heal_amount = self.enemy.heal(20) # Inimigos curam uma quantidade fixa
            self.message += f" O inimigo se curou em {heal_amount} HP!"
        else: # action == "attack"
            enemy_attack, enemy_crit = self.enemy.attack_power
            
            if self.player.is_defending:
                enemy_attack //= 2 # Reduz o dano pela metade
                self.message = "Você defendeu o ataque!"

            final_damage = self.player.take_damage(enemy_attack)
            
            if enemy_crit: self.message += f" O inimigo acertou CRÍTICO causando {final_damage} de dano!"
            else: self.message += f" O inimigo te atacou com {final_damage} de dano!"
        
        self.next_turn()

    def end_battle(self, win):
        self.player.status_effects.clear() # Limpa buffs/debuffs ao final da batalha
        if win:
            if self.player.quest and self.player.quest.goal_type == 'kill' and not self.player.quest.completed:
                self.player.quest.current_amount += 1
                if self.player.quest.current_amount >= self.player.quest.goal_amount:
                    self.player.quest.completed = True
            gold_gain = self.enemy.gold_drop
            self.player.gold += gold_gain
            if isinstance(self.enemy, Boss):
                self.message += " CHEFE DERROTADO!"
                self.player.gain_exp(1000)
                item = Item("Lâmina do Rei Caído", "weapon", power=50, damage_type=PHYSICAL)
            else:
                self.message += " Inimigo derrotado!"
                self.player.gain_exp(50)
                # CORREÇÃO: O loot do inimigo agora vem da sua loot_table
                if self.enemy.loot_table:
                    item = random.choice(self.enemy.loot_table)
                else: # Fallback caso a loot_table esteja vazia
                    item = Item("Poeira Mágica", "material")
            self.player.inventory.append(item)
            self.message += f" Você ganhou {gold_gain} de ouro e recebeu {item.name}!"
        self.running = False

    def use_potion(self):
        for item in self.player.inventory:
            if item.name == "Poção":
                # CORREÇÃO: A poção agora cura 40% da vida máxima do jogador.
                heal_amount = int(self.player.max_hp * 0.40)
                self.player.hp = min(self.player.max_hp, self.player.hp + heal_amount)
                self.player.inventory.remove(item)
                self.message = f"Você usou uma Poção e recuperou {heal_amount} de HP!"
                self.next_turn()
                return
        self.message = "Você não tem poções!"

    def choose_spell(self):
        spells = self.player.spells
        if not spells:
            self.message = "Você não conhece nenhuma magia!"
            return
        choosing = True
        while choosing:
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.background, (0, 0))
            text = self.font.render("Escolha uma magia (ESC para voltar):", True, WHITE)
            self.screen.blit(text, (50, 50))
            for i, spell in enumerate(spells):
                spell_text = f"{i+1}. {spell.name} (Custo: {spell.mana_cost} MP)"
                color = WHITE if self.player.mana >= spell.mana_cost else (150, 150, 150)
                text = self.font.render(spell_text, True, color)
                self.screen.blit(text, (50, 100 + i*30))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: choosing = False
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        if idx < len(spells):
                            spell = spells[idx]
                            if self.player.mana >= spell.mana_cost:
                                self.use_spell(spell)
                                choosing = False
    
    def use_spell(self, spell):
        self.player.mana -= spell.mana_cost
        if spell.type == "damage":
            final_damage, weak, resist = self.enemy.take_damage(spell.power, spell.damage_type)
            self.message = f"Você usou {spell.name} e causou {final_damage} de dano!"
            if weak: self.message += " (Super Efetivo!)"
            if resist: self.message += " (Pouco Efetivo...)"
            if spell.status_effect:
                self.enemy.apply_status(spell.status_effect)
                self.message += f" O inimigo está com {spell.status_effect.name}!"
        elif spell.type == "heal":
            self.player.hp = min(self.player.max_hp, self.player.hp + spell.power)
            self.message = f"Você usou {spell.name} e curou {spell.power} de HP!"
        elif spell.type == "support":
            target = self.player if spell.target == "self" else self.enemy
            target.apply_status(spell.status_effect)
            self.message = f"Você usou {spell.name}!"
        self.next_turn()

    def run(self):
        self.handle_status_effects(self.player)
        while self.running and self.player.hp > 0 and self.enemy.hp > 0:
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.background, (0, 0))
            self.draw_health_bar(50, 50, self.player.hp, self.player.max_hp, (0, 255, 0))
            self.draw_mana_bar(50, 75, self.player.mana, self.player.max_mana, (0, 150, 255))
            self.draw_health_bar(WIDTH - 250, 50, self.enemy.hp, self.enemy.max_hp, self.enemy.color)
            p_text = self.font.render(f"Você (Lv {self.player.level}) - HP: {self.player.hp}/{self.player.max_hp} | MP: {self.player.mana}/{self.player.max_mana}", True, WHITE)
            e_text = self.font.render(f"Inimigo (Lv {self.enemy.level}) - HP: {self.enemy.hp}/{self.enemy.max_hp}", True, WHITE)
            self.screen.blit(p_text, (50, 20))
            self.screen.blit(e_text, (WIDTH - 250, 20))
            message_surface = self.font.render(self.message, True, WHITE)
            self.screen.blit(message_surface, (50, 300))
            for button in self.buttons:
                button.draw(self.screen, self.font)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                elif self.turn == "player" and event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    for button in self.buttons:
                        button.click(pos)
        pygame.time.wait(1500)
        
import pygame
from settings import *
from items import Item
from spells import Spell
from enemy import Boss
import random

class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = (100, 100, 100)

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        text_surface = font.render(self.text, True, WHITE)
        screen.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))

    def click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()

class Battle:
    def __init__(self, screen, player, enemy, background):
        self.screen = screen
        self.player = player
        self.enemy = enemy
        self.background = background
        self.font = pygame.font.SysFont("Arial", 20)
        self.running = True
        self.message = ""
        self.fled = False
        self.turn = "player"

        self.buttons = [ 
            Button(50, 400, 120, 40, "Atacar", self.attack),
            Button(180, 400, 120, 40, "Magias", self.choose_spell),
            Button(310, 400, 120, 40, "Defender", self.defend),
            Button(440, 400, 120, 40, "Poção", self.use_potion),
            Button(570, 400, 120, 40, "Fugir", self.flee)
        ]

    def draw_health_bar(self, x, y, current, max_health, color):
        width = 200
        height = 20
        pygame.draw.rect(self.screen, (50, 50, 50), (x, y, width, height))
        if max_health > 0:
            fill = (current / max_health) * width
            pygame.draw.rect(self.screen, color, (x, y, fill, height))
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)

    def draw_mana_bar(self, x, y, current, max_mana, color):
        width = 150
        height = 15
        pygame.draw.rect(self.screen, (50, 50, 50), (x, y, width, height))
        if max_mana > 0:
            fill = (current / max_mana) * width
            pygame.draw.rect(self.screen, color, (x, y, fill, height))
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)

    def handle_status_effects(self, character):
        status_message = character.update_status_effects()
        if status_message:
            self.message += " " + status_message

    def next_turn(self):
        if self.turn == "player":
            self.turn = "enemy"
            self.handle_status_effects(self.enemy)
            if self.enemy.hp <= 0:
                self.end_battle(win=True)
            else:
                self.enemy_turn()
        elif self.turn == "enemy":
            self.turn = "player"
            self.player.is_defending = False # Reseta a defesa no início do turno do jogador
            self.handle_status_effects(self.player)
            if self.player.hp <= 0:
                self.end_battle(win=False)

    def attack(self):
        damage, player_crit = self.player.attack_power()
        damage_type = self.player.equipped_weapon.damage_type if self.player.equipped_weapon else PHYSICAL
        final_damage, weak, resist = self.enemy.take_damage(damage, damage_type)
        
        self.message = f"Você causou {final_damage} de dano!"
        if player_crit: self.message = f"CRÍTICO! {self.message}"
        if weak: self.message += " (Super Efetivo!)"
        if resist: self.message += " (Pouco Efetivo...)"
        
        self.next_turn()

    def defend(self):
        self.player.is_defending = True
        self.message = "Você se prepara para defender!"
        self.next_turn()

    def flee(self):
        if isinstance(self.enemy, Boss):
            self.message = "Não se pode fugir de um chefe!"
            return
        if random.random() < 0.5:
            self.message = "Você conseguiu fugir!"
            self.fled = True
            self.running = False
        else:
            self.message = "A fuga falhou!"
            self.next_turn()

    def enemy_turn(self):
        action = self.enemy.decide_action()
        
        if action == "heal":
            heal_amount = self.enemy.heal(20) # Inimigos curam uma quantidade fixa
            self.message += f" O inimigo se curou em {heal_amount} HP!"
        else: # action == "attack"
            enemy_attack, enemy_crit = self.enemy.attack_power
            
            if self.player.is_defending:
                enemy_attack //= 2 # Reduz o dano pela metade
                self.message = "Você defendeu o ataque!"

            final_damage = self.player.take_damage(enemy_attack)
            
            if enemy_crit: self.message += f" O inimigo acertou CRÍTICO causando {final_damage} de dano!"
            else: self.message += f" O inimigo te atacou com {final_damage} de dano!"
        
        self.next_turn()

    def end_battle(self, win):
        self.player.status_effects.clear() # Limpa buffs/debuffs ao final da batalha
        if win:
            if self.player.quest and self.player.quest.goal_type == 'kill' and not self.player.quest.completed:
                self.player.quest.current_amount += 1
                if self.player.quest.current_amount >= self.player.quest.goal_amount:
                    self.player.quest.completed = True
            gold_gain = self.enemy.gold_drop
            self.player.gold += gold_gain
            if isinstance(self.enemy, Boss):
                self.message += " CHEFE DERROTADO!"
                self.player.gain_exp(1000)
                item = Item("Lâmina do Rei Caído", "weapon", power=50, damage_type=PHYSICAL)
            else:
                self.message += " Inimigo derrotado!"
                self.player.gain_exp(50)
                # CORREÇÃO: O loot do inimigo agora vem da sua loot_table
                if self.enemy.loot_table:
                    item = random.choice(self.enemy.loot_table)
                else: # Fallback caso a loot_table esteja vazia
                    item = Item("Poeira Mágica", "material")
            self.player.inventory.append(item)
            self.message += f" Você ganhou {gold_gain} de ouro e recebeu {item.name}!"
        self.running = False

    def use_potion(self):
        for item in self.player.inventory:
            if item.name == "Poção":
                # CORREÇÃO: A poção agora cura 40% da vida máxima do jogador.
                heal_amount = int(self.player.max_hp * 0.40)
                self.player.hp = min(self.player.max_hp, self.player.hp + heal_amount)
                self.player.inventory.remove(item)
                self.message = f"Você usou uma Poção e recuperou {heal_amount} de HP!"
                self.next_turn()
                return
        self.message = "Você não tem poções!"

    def choose_spell(self):
        spells = self.player.spells
        if not spells:
            self.message = "Você não conhece nenhuma magia!"
            return
        choosing = True
        while choosing:
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.background, (0, 0))
            text = self.font.render("Escolha uma magia (ESC para voltar):", True, WHITE)
            self.screen.blit(text, (50, 50))
            for i, spell in enumerate(spells):
                spell_text = f"{i+1}. {spell.name} (Custo: {spell.mana_cost} MP)"
                color = WHITE if self.player.mana >= spell.mana_cost else (150, 150, 150)
                text = self.font.render(spell_text, True, color)
                self.screen.blit(text, (50, 100 + i*30))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: choosing = False
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        if idx < len(spells):
                            spell = spells[idx]
                            if self.player.mana >= spell.mana_cost:
                                self.use_spell(spell)
                                choosing = False
    
    def use_spell(self, spell):
        self.player.mana -= spell.mana_cost
        if spell.type == "damage":
            final_damage, weak, resist = self.enemy.take_damage(spell.power, spell.damage_type)
            self.message = f"Você usou {spell.name} e causou {final_damage} de dano!"
            if weak: self.message += " (Super Efetivo!)"
            if resist: self.message += " (Pouco Efetivo...)"
            if spell.status_effect:
                self.enemy.apply_status(spell.status_effect)
                self.message += f" O inimigo está com {spell.status_effect.name}!"
        elif spell.type == "heal":
            self.player.hp = min(self.player.max_hp, self.player.hp + spell.power)
            self.message = f"Você usou {spell.name} e curou {spell.power} de HP!"
        elif spell.type == "support":
            target = self.player if spell.target == "self" else self.enemy
            target.apply_status(spell.status_effect)
            self.message = f"Você usou {spell.name}!"
        self.next_turn()

    def run(self):
        self.handle_status_effects(self.player)
        while self.running and self.player.hp > 0 and self.enemy.hp > 0:
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.background, (0, 0))
            self.draw_health_bar(50, 50, self.player.hp, self.player.max_hp, (0, 255, 0))
            self.draw_mana_bar(50, 75, self.player.mana, self.player.max_mana, (0, 150, 255))
            self.draw_health_bar(WIDTH - 250, 50, self.enemy.hp, self.enemy.max_hp, self.enemy.color)
            p_text = self.font.render(f"Você (Lv {self.player.level}) - HP: {self.player.hp}/{self.player.max_hp} | MP: {self.player.mana}/{self.player.max_mana}", True, WHITE)
            e_text = self.font.render(f"Inimigo (Lv {self.enemy.level}) - HP: {self.enemy.hp}/{self.enemy.max_hp}", True, WHITE)
            self.screen.blit(p_text, (50, 20))
            self.screen.blit(e_text, (WIDTH - 250, 20))
            message_surface = self.font.render(self.message, True, WHITE)
            self.screen.blit(message_surface, (50, 300))
            for button in self.buttons:
                button.draw(self.screen, self.font)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                elif self.turn == "player" and event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    for button in self.buttons:
                        button.click(pos)
        pygame.time.wait(1500)