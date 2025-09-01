import pygame
from settings import WHITE, BLACK
from items import Item

class Recipe:
    def __init__(self, result_item, ingredients):
        self.result_item = result_item
        self.ingredients = ingredients # Ex: { "Pele de Lobo": 2, "Minério de Ferro": 1 }

RECIPE_LIST = [
    Recipe(Item("Armadura de Couro", "armor", slot="chest", defense=5, price=50), {"Pele de Lobo": 3}),
    Recipe(Item("Elmo de Ferro", "armor", slot="helmet", defense=4, price=80), {"Minério de Ferro": 2}),
    Recipe(Item("Poção Forte", "consumable", price=50), {"Erva Curativa": 2, "Poção": 1})
]

class CraftingScreen:
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
                    if event.key == pygame.K_c: self.running = False
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        self.craft_item(event.key - pygame.K_1)

    def has_ingredients(self, recipe):
        for name, amount in recipe.ingredients.items():
            count = sum(1 for item in self.player.inventory if item.name == name)
            if count < amount:
                return False
        return True

    def craft_item(self, index):
        if index < len(RECIPE_LIST):
            recipe = RECIPE_LIST[index]
            if self.has_ingredients(recipe):
                # Remover ingredientes do inventário
                for name, amount in recipe.ingredients.items():
                    for _ in range(amount):
                        item_to_remove = next(item for item in self.player.inventory if item.name == name)
                        self.player.inventory.remove(item_to_remove)
                # Adicionar item criado
                self.player.inventory.append(recipe.result_item)

    def draw(self):
        self.screen.fill(BLACK)
        title_text = self.font.render("Criação de Itens - Pressione [C] para fechar", True, WHITE)
        self.screen.blit(title_text, (50, 50))

        y = 120
        for i, recipe in enumerate(RECIPE_LIST):
            can_craft = self.has_ingredients(recipe)
            color = WHITE if can_craft else (100, 100, 100)
            
            # Nome da receita
            recipe_name = f"[{i+1}] {recipe.result_item.name}"
            self.screen.blit(self.font.render(recipe_name, True, color), (70, y))
            
            # Ingredientes
            ing_text = "Ingredientes: " + ", ".join([f"{amount}x {name}" for name, amount in recipe.ingredients.items()])
            self.screen.blit(self.font.render(ing_text, True, color), (300, y))
            y += 40
        
        pygame.display.flip()