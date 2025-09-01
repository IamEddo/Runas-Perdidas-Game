import pygame
from settings import WHITE, BLACK
from spells import Spell
from status_effects import StatusEffect
from settings import FIRE

# Habilidades disponíveis para aprender
SKILL_LIST = {
    "Guerreiro": [
        Spell("Ataque Poderoso", "damage", 15, 50, "enemy", status_effect=StatusEffect("Defesa Quebrada", 2, stat_mods={'defense': -10}))
    ],
    "Mago": [
        Spell("Relâmpago", "damage", 25, 50, "enemy", damage_type="lightning"),
        Spell("Muralha de Fogo", "damage", 40, 70, "enemy", damage_type=FIRE, status_effect=StatusEffect("Queimadura", 3, 10, (255,165,0)))
    ],
    "Arqueiro": [
        Spell("Tiro Preciso", "damage", 20, 60, "enemy", status_effect=StatusEffect("Vulnerável", 2, stat_mods={'defense': -15}))
    ]
}

class SkillTreeScreen:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.font = pygame.font.SysFont("Arial", 22)
        self.running = True

    def run(self):
        while self.running:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_k: self.running = False
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        self.unlock_skill(event.key - pygame.K_1)

    def unlock_skill(self, index):
        available_skills = [s for s in SKILL_LIST[self.player.character_class] if s.name not in [p.name for p in self.player.spells]]
        if self.player.skill_points > 0 and index < len(available_skills):
            skill_to_learn = available_skills[index]
            self.player.spells.append(skill_to_learn)
            self.player.skill_points -= 1

    def draw(self):
        self.screen.fill(BLACK)
        title_text = self.font.render("Árvore de Habilidades - Pressione [K] para fechar", True, WHITE)
        self.screen.blit(title_text, (50, 50))
        
        sp_text = self.font.render(f"Pontos de Habilidade: {self.player.skill_points}", True, (255, 255, 0))
        self.screen.blit(sp_text, (500, 50))

        y = 120
        # Habilidades já aprendidas
        self.screen.blit(self.font.render("Habilidades Aprendidas:", True, WHITE), (50, y)); y += 40
        for spell in self.player.spells:
            self.screen.blit(self.font.render(f"- {spell.name}", True, (150, 150, 150)), (70, y)); y += 30
        
        y += 20
        # Habilidades para aprender
        self.screen.blit(self.font.render("Habilidades Disponíveis:", True, WHITE), (50, y)); y += 40
        
        available_skills = [s for s in SKILL_LIST[self.player.character_class] if s.name not in [p.name for p in self.player.spells]]
        for i, spell in enumerate(available_skills):
            color = WHITE if self.player.skill_points > 0 else (100, 100, 100)
            text = f"[{i+1}] {spell.name} (Custo: 1 Ponto)"
            self.screen.blit(self.font.render(text, True, color), (70, y)); y += 30
        
        pygame.display.flip()