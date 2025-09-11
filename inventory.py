import pygame
from settings import WHITE, BLACK, WIDTH

class InventoryScreen:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.font = pygame.font.SysFont("Arial", 20)
        self.font_small = pygame.font.SysFont("Arial", 16)
        self.running = True
        self.selected_index = 0
        self.equipable_items = []

        self.color_increase = (0, 255, 0)
        self.color_decrease = (255, 0, 0)
        self.color_neutral = (200, 200, 200)

    def run(self):
        self.equipable_items = [item for item in self.player.inventory if item.type in ["weapon", "armor"]]
        
        while self.running:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_i:
                        self.running = False
                    elif event.key == pygame.K_UP:
                        self.selected_index = (self.selected_index - 1) % len(self.equipable_items) if self.equipable_items else 0
                    elif event.key == pygame.K_DOWN:
                        self.selected_index = (self.selected_index + 1) % len(self.equipable_items) if self.equipable_items else 0
                    elif event.key == pygame.K_RETURN:
                        self.equip_item()

    def equip_item(self):
        if self.equipable_items and 0 <= self.selected_index < len(self.equipable_items):
            item_to_equip = self.equipable_items[self.selected_index]
            self.player.equip(item_to_equip)
            self.equipable_items = [item for item in self.player.inventory if item.type in ["weapon", "armor"]]
            if self.selected_index >= len(self.equipable_items):
                self.selected_index = max(0, len(self.equipable_items) - 1)


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

        self.screen.blit(self.font.render("Itens (Setas para mover, Enter para equipar):", True, WHITE), (x, y)); y += 30
   
        other_items = [item for item in self.player.inventory if item.type not in ["weapon", "armor"]]

        for i, item in enumerate(self.equipable_items):
            color = (255, 255, 0) if i == self.selected_index else WHITE
            self.screen.blit(self.font.render(f"{item.name} ({item.slot})", True, color), (x + 20, y)); y += 30
         
        y += 10
        for item in other_items:
            self.screen.blit(self.font.render(f"- {item.name}", True, (180, 180, 180)), (x + 20, y)); y += 30

        if self.equipable_items and 0 <= self.selected_index < len(self.equipable_items):
            selected_item = self.equipable_items[self.selected_index]
            self.draw_comparison_box(selected_item)

        pygame.display.flip()

    def draw_comparison_box(self, item):
            box_rect = pygame.Rect(400, 400, 380, 150)
            pygame.draw.rect(self.screen, (20, 20, 20), box_rect)
            pygame.draw.rect(self.screen, WHITE, box_rect, 2)

            y = box_rect.y + 15
            
            # Nome do item selecionado
            title_text = self.font.render(item.name, True, (255, 255, 0))
            self.screen.blit(title_text, (box_rect.x + 15, y)); y += 35

            # Encontra o item atualmente equipado no mesmo slot
            current_item = None
            if item.slot == "weapon": current_item = self.player.equipped_weapon
            elif item.slot == "chest": current_item = self.player.equipped_chest
            elif item.slot == "helmet": current_item = self.player.equipped_helmet
            elif item.slot == "gloves": current_item = self.player.equipped_gloves
            elif item.slot == "boots": current_item = self.player.equipped_boots

            # Stats do item atual
            current_power = current_item.power if current_item else 0
            current_defense = current_item.defense if current_item else 0

            # Stats do item novo (selecionado)
            new_power = item.power
            new_defense = item.defense

            # Função auxiliar para desenhar a linha de stat
            def draw_stat_line(label, current_val, new_val, pos_y):
                diff = new_val - current_val
                
                # Define a cor com base na diferença
                if diff > 0: color = self.color_increase
                elif diff < 0: color = self.color_decrease
                else: color = self.color_neutral

                # Monta o texto
                base_text = f"{label}: {current_val} -> {new_val}"
                diff_text = f" ({diff:+})" if diff != 0 else ""
                
                # Desenha o texto
                full_text_surf = self.font_small.render(base_text + diff_text, True, color)
                self.screen.blit(full_text_surf, (box_rect.x + 20, pos_y))

            # Desenha a comparação de ataque se for uma arma
            if item.slot == "weapon":
                draw_stat_line("Ataque", current_power, new_power, y)
                y += 25

            # Desenha a comparação de defesa se for uma armadura
            if item.type == "armor":
                draw_stat_line("Defesa", current_defense, new_defense, y)
                y += 25