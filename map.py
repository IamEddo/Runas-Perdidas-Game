import pygame
from settings import *
from chest import TreasureChest
from items import Item
import random

class GameMap:
    def __init__(self, level, chests):
        self.cols = MAP_WIDTH
        self.rows = MAP_HEIGHT
        self.tiles = [[FLOOR for _ in range(self.cols)] for _ in range(self.rows)]
        self.chests = chests
        self.level = level

        self.background_tile = pygame.image.load("assets/background_tile.png").convert()
        self.shop_tile = pygame.image.load("assets/shop.png").convert_alpha()
        self.lava_tile = pygame.Surface((TILE_SIZE, TILE_SIZE)); self.lava_tile.fill((255, 69, 0))
        self.swamp_tile = pygame.Surface((TILE_SIZE, TILE_SIZE)); self.swamp_tile.fill((88, 60, 33))
        self.stairs_down_tile = pygame.Surface((TILE_SIZE, TILE_SIZE)); self.stairs_down_tile.fill((70, 70, 70))
        self.stairs_up_tile = pygame.Surface((TILE_SIZE, TILE_SIZE)); self.stairs_up_tile.fill((150, 150, 150))

        self.generate_map()

    def generate_map(self):
        # Bordas
        for y in range(self.rows):
            for x in range(self.cols):
                if x == 0 or y == 0 or x == self.cols - 1 or y == self.rows - 1:
                    self.tiles[y][x] = WALL

        if self.level == 1:
            # Cidade e Loja
            for y in range(5, 15):
                for x in range(5, 15): self.tiles[y][x] = TOWN
            self.tiles[8][12] = SHOP
            # Escada para o próximo nível
            self.tiles[MAP_HEIGHT - 5][MAP_WIDTH - 5] = STAIRS_DOWN
        
        if self.level == 2:
            # Escada para voltar
            self.tiles[5][5] = STAIRS_UP
            # Escada para o próximo nível
            self.tiles[MAP_HEIGHT - 5][MAP_WIDTH - 5] = STAIRS_DOWN
            # Adicionar pântano
            for _ in range(5):
                rx, ry = random.randint(10, MAP_WIDTH-10), random.randint(10, MAP_HEIGHT-10)
                for y in range(ry-3, ry+3):
                    for x in range(rx-3, rx+3):
                        if self.is_on_map(x, y): self.tiles[y][x] = SWAMP
        
        if self.level == 3:
            # Escada para voltar
            self.tiles[5][5] = STAIRS_UP
            # Adicionar lava
            for _ in range(5):
                rx, ry = random.randint(10, MAP_WIDTH-10), random.randint(10, MAP_HEIGHT-10)
                for y in range(ry-3, ry+3):
                    for x in range(rx-3, rx+3):
                        if self.is_on_map(x, y): self.tiles[y][x] = LAVA

        # Obstáculos e Baús genéricos para todos os níveis (exceto cidade)
        for y in range(self.rows):
            for x in range(self.cols):
                if self.tiles[y][x] == FLOOR:
                    if random.random() < 0.05: self.tiles[y][x] = WALL
                    elif random.random() < 0.005:
                        gold = random.randint(10, 50)
                        item = Item("Poção", "consumable", price=10) if random.random() < 0.5 else None
                        self.chests.append(TreasureChest(x, y, items=[item] if item else [], gold=gold))

    def is_on_map(self, x, y):
        return 0 <= x < self.cols and 0 <= y < self.rows

    def is_walkable(self, x, y):
        return self.is_on_map(x, y) and self.tiles[y][x] != WALL

    def get_tile_type(self, x, y):
        if self.is_on_map(x, y):
            return self.tiles[y][x]
        return -1

    def draw(self, screen, camera_x, camera_y):
        # CORREÇÃO: Calcula os tiles visíveis na tela
        start_col = camera_x // TILE_SIZE
        end_col = start_col + (WIDTH // TILE_SIZE) + 2
        start_row = camera_y // TILE_SIZE
        end_row = start_row + (HEIGHT // TILE_SIZE) + 2

        # CORREÇÃO: Itera apenas sobre os tiles visíveis
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if self.is_on_map(x, y):
                    draw_x = x * TILE_SIZE - camera_x
                    draw_y = y * TILE_SIZE - camera_y
                    tile_type = self.tiles[y][x]

                    # Desenha o chão base
                    screen.blit(self.background_tile, (draw_x, draw_y))

                    if tile_type == WALL: pygame.draw.rect(screen, (50, 50, 50), (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
                    elif tile_type == TOWN: pygame.draw.rect(screen, (210, 180, 140), (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
                    elif tile_type == SHOP: screen.blit(self.shop_tile, (draw_x, draw_y))
                    elif tile_type == LAVA: screen.blit(self.lava_tile, (draw_x, draw_y))
                    elif tile_type == SWAMP: screen.blit(self.swamp_tile, (draw_x, draw_y))
                    elif tile_type == STAIRS_DOWN: screen.blit(self.stairs_down_tile, (draw_x, draw_y))
                    elif tile_type == STAIRS_UP: screen.blit(self.stairs_up_tile, (draw_x, draw_y))
        
        for chest in self.chests:
            # Otimização: só desenha baús que estão na tela
            if start_col <= chest.x <= end_col and start_row <= chest.y <= end_row:
                chest.draw(screen, camera_x, camera_y)