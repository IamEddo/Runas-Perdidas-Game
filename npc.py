import pygame
from settings import TILE_SIZE, WHITE, BLACK

class Quest:
    def __init__(self, title, description, goal_type, goal_target, goal_amount, reward_exp, reward_gold):
        self.title = title
        self.description = description
        self.goal_type = goal_type # 'kill'
        self.goal_target = goal_target # 'Enemy'
        self.goal_amount = goal_amount
        self.reward_exp = reward_exp
        self.reward_gold = reward_gold
        self.current_amount = 0
        self.completed = False

class NPC:
    def __init__(self, x, y, name, quest=None):
        self.x = x
        self.y = y
        self.name = name
        self.quest = quest
        self.color = (0, 255, 255) # Ciano
        self.size = TILE_SIZE
        self.font = pygame.font.SysFont("Arial", 18)
        self.dialog_active = False

    def draw(self, screen, camera_x, camera_y):
        rect = pygame.Rect(
            self.x * TILE_SIZE - camera_x,
            self.y * TILE_SIZE - camera_y,
            self.size,
            self.size
        )
        pygame.draw.rect(screen, self.color, rect)
        name_text = self.font.render(self.name, True, WHITE)
        screen.blit(name_text, (rect.x, rect.y - 20))

    def interact(self, screen, player):
        self.dialog_active = True
        while self.dialog_active:
            self.draw_dialog_box(screen, player)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e: # Pressionar E para fechar
                        self.dialog_active = False
                    if event.key == pygame.K_y and self.quest and not player.quest: # Aceitar quest
                        player.quest = self.quest
                        self.dialog_active = False
                    if event.key == pygame.K_c and player.quest and player.quest.completed: # Completar quest
                        player.gain_exp(self.quest.reward_exp)
                        player.gold += self.quest.reward_gold
                        player.quest = None
                        self.quest = None # NPC não oferece mais a quest
                        self.dialog_active = False

    def draw_dialog_box(self, screen, player):
        box_rect = pygame.Rect(100, 400, 600, 150)
        pygame.draw.rect(screen, BLACK, box_rect)
        pygame.draw.rect(screen, WHITE, box_rect, 2)

        if self.quest:
            if not player.quest:
                text1 = self.font.render(f"{self.name}: Olá, aventureiro! Preciso de ajuda.", True, WHITE)
                text2 = self.font.render(self.quest.description, True, WHITE)
                text3 = self.font.render("Pressione [Y] para aceitar ou [E] para sair.", True, WHITE)
                screen.blit(text1, (120, 420))
                screen.blit(text2, (120, 450))
                screen.blit(text3, (120, 500))
            elif player.quest and not player.quest.completed:
                progress = f"Progresso: {player.quest.current_amount}/{player.quest.goal_amount}"
                text1 = self.font.render(f"{self.name}: Como vai a caçada? {progress}", True, WHITE)
                text2 = self.font.render("Continue assim! Pressione [E] para sair.", True, WHITE)
                screen.blit(text1, (120, 420))
                screen.blit(text2, (120, 450))
            elif player.quest and player.quest.completed:
                text1 = self.font.render(f"{self.name}: Você conseguiu! Ótimo trabalho!", True, WHITE)
                text2 = self.font.render(f"Recompensa: {self.quest.reward_exp} EXP, {self.quest.reward_gold} Ouro.", True, WHITE)
                text3 = self.font.render("Pressione [C] para completar ou [E] para sair.", True, WHITE)
                screen.blit(text1, (120, 420))
                screen.blit(text2, (120, 450))
                screen.blit(text3, (120, 500))
        else:
            text1 = self.font.render(f"{self.name}: Obrigado pela ajuda, herói!", True, WHITE)
            screen.blit(text1, (120, 420))

        pygame.display.flip()