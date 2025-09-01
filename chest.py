import pygame
from settings import TILE_SIZE, WHITE
from items import Item
import random

class TreasureChest:
    def __init__(self, x, y, items=None, gold=0):
        self.x = x
        self.y = y
        self.items = items if items else []
        self.gold = gold
        self.is_opened = False
        self.color_closed = (139, 69, 19) # Marrom
        self.color_opened = (90, 45, 10)
        self.font = pygame.font.SysFont("Arial", 16)

    def draw(self, screen, camera_x, camera_y):
        color = self.color_opened if self.is_opened else self.color_closed
        rect = pygame.Rect(self.x * TILE_SIZE - camera_x, self.y * TILE_SIZE - camera_y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (255, 223, 0), (rect.x + 12, rect.y + 8, 8, 5)) # Fechadura dourada

    def interact(self, player):
        if not self.is_opened:
            message = "Você encontrou "
            if self.gold > 0:
                player.gold += self.gold
                message += f"{self.gold} de ouro"
            if self.items:
                if self.gold > 0: message += " e "
                for item in self.items:
                    player.inventory.append(item)
                    message += f"um(a) {item.name}"
            message += "!"
            self.is_opened = True
            return message
        return "Este baú já foi aberto."