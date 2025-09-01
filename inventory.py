import pygame
from settings import WHITE, BLACK

class InventoryScreen:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.font = pygame.font.SysFont("Arial", 20)
        self.running = True

    def run(self):
        while self.running:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_i: self.running = False
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        self.equip_item(event.key - pygame.K_1)

    def equip_item(self, index):
        equipable_items = [item for item in self.player.inventory if item.type in ["weapon", "armor"]]
        if index < len(equipable_items):
            item_to_equip = equipable_items[index]
            self.player.equip(item_to_equip)

    def draw(self):
        self.screen.fill(BLACK)
        title_text = self.font.render("Inventário e Equipamento - Pressione [I] para fechar", True, WHITE)
        self.screen.blit(title_text, (50, 50))

        # Coluna de Equipamentos
        y = 120
        self.screen.blit(self.font.render("Equipado:", True, WHITE), (50, y)); y += 30
        
        def get_name(item): return item.name if item else "Vazio"
        
        self.screen.blit(self.font.render(f"Arma: {get_name(self.player.equipped_weapon)}", True, WHITE), (70, y)); y += 30
        self.screen.blit(self.font.render(f"Elmo: {get_name(self.player.equipped_helmet)}", True, WHITE), (70, y)); y += 30
        self.screen.blit(self.font.render(f"Peitoral: {get_name(self.player.equipped_chest)}", True, WHITE), (70, y)); y += 30
        self.screen.blit(self.font.render(f"Luvas: {get_name(self.player.equipped_gloves)}", True, WHITE), (70, y)); y += 30
        self.screen.blit(self.font.render(f"Botas: {get_name(self.player.equipped_boots)}", True, WHITE), (70, y)); y += 30

        # Coluna do Inventário
        x = 400
        y = 120
        self.screen.blit(self.font.render("Itens (Pressione número para equipar):", True, WHITE), (x, y)); y += 30
        
        equipable_items = [item for item in self.player.inventory if item.type in ["weapon", "armor"]]
        other_items = [item for item in self.player.inventory if item.type not in ["weapon", "armor"]]

        for i, item in enumerate(equipable_items):
            self.screen.blit(self.font.render(f"[{i+1}] {item.name} ({item.slot})", True, WHITE), (x + 20, y)); y += 30
        
        y += 10
        for item in other_items:
            self.screen.blit(self.font.render(f"- {item.name}", True, (180, 180, 180)), (x + 20, y)); y += 30

        pygame.display.flip()