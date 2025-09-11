import pygame, sys, random, json, os
from settings import *
from player import Player
from enemy import Enemy, Boss
from map import GameMap
from battle import Battle
from inventory import InventoryScreen
from npc import NPC, Quest
from items import Item
from spells import Spell
from status_effects import StatusEffect
from chest import TreasureChest
from skill_tree import SkillTreeScreen, SKILL_LIST
from crafting import CraftingScreen

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Runas Perdidas")
battle_background = pygame.image.load("assets/battle_background.png").convert()
clock = pygame.time.Clock()
SAVE_FILE = "savegame.json"

def save_game(player, enemies, npcs, chests, current_level):
    # Função para converter um item para um dicionário, trocando 'type_' por 'type'
    def item_to_dict(item):
        if not item: return None
        item_dict = vars(item).copy()
        if 'type_' in item_dict:
            item_dict['type'] = item_dict.pop('type_')
        return item_dict

    player_data = player.to_dict()

    enemies_data = [{"x": e.x, "y": e.y, "level": e.level, "is_boss": isinstance(e, Boss)} for e in enemies]
    npcs_data = [{"x": n.x, "y": n.y, "name": n.name, "quest": vars(n.quest) if n.quest else None} for n in npcs]
    chests_data = [
        {
            "x": c.x, "y": c.y, "gold": c.gold, "is_opened": c.is_opened,
            "items": [item_to_dict(i) for i in c.items]
        } for c in chests
    ]
    
    save_data = {"player": player_data, "enemies": enemies_data, "npcs": npcs_data, "chests": chests_data, "current_level": current_level}
    with open(SAVE_FILE, 'w') as f:
        json.dump(save_data, f, indent=4)

def load_game():
    with open(SAVE_FILE, 'r') as f:
        save_data = json.load(f)
    
    all_spells = SKILL_LIST["Guerreiro"] + SKILL_LIST["Mago"] + SKILL_LIST["Arqueiro"]

    player = Player.from_dict(save_data["player"], all_spells)

    chests = []
    for c_data in save_data.get("chests", []):
        items = []
        for item_data in c_data.get("items", []):
            if 'type' in item_data:
                item_data['type_'] = item_data.pop('type')
            items.append(Item(**item_data))
        
        chest = TreasureChest(c_data['x'], c_data['y'], items, c_data.get('gold', 0))
        chest.is_opened = c_data.get('is_opened', False)
        chests.append(chest)
        
    current_level = save_data.get("current_level", 1)
    game_map = GameMap(current_level, chests)

    enemies = []
    for e_data in save_data.get("enemies", []):
        if e_data.get("is_boss"): enemies.append(Boss(e_data["x"], e_data["y"]))
        else: enemies.append(Enemy(e_data["x"], e_data["y"], e_data["level"]))
    
    npcs = []
    for n_data in save_data.get("npcs", []):
        quest = Quest(**n_data["quest"]) if n_data.get("quest") else None
        npcs.append(NPC(n_data["x"], n_data["y"], n_data["name"], quest))

    return player, game_map, enemies, npcs, chests, current_level

def reset_game():
    chosen_class = choose_class_screen()
    player = Player(chosen_class)
    current_level = 1
    chests = []
    game_map = GameMap(current_level, chests)
    enemies = spawn_enemies(game_map, player)
    quest1 = Quest("Caçador de Ratos", "Cace 5 inimigos.", 'kill', 'Enemy', 5, 100, 50)
    npcs = [NPC(12, 8, "Aldric", quest=quest1)]
    return player, game_map, enemies, npcs, chests, current_level

def spawn_enemies(game_map, player, num=20):
    enemies = []
    for _ in range(num):
        while True:
            x, y = random.randint(1, MAP_WIDTH - 2), random.randint(1, MAP_HEIGHT - 2)
            if game_map.is_walkable(x, y) and game_map.get_tile_type(x, y) == FLOOR:
                enemies.append(Enemy(x, y, random.randint(game_map.level, game_map.level + 2)))
                break
    return enemies

def start_menu():
    font = pygame.font.SysFont("Arial", 40)
    title = font.render("Runas Perdidas", True, WHITE)
    new_game_rect = pygame.Rect(WIDTH/2 - 100, 250, 200, 50)
    load_game_rect = pygame.Rect(WIDTH/2 - 100, 320, 200, 50)
    while True:
        screen.fill(BLACK)
        screen.blit(title, (WIDTH/2 - title.get_width()/2, 150))
        pygame.draw.rect(screen, (100,100,100), new_game_rect)
        screen.blit(font.render("Novo Jogo", True, WHITE), (new_game_rect.x + 20, new_game_rect.y + 5))
        if os.path.exists(SAVE_FILE):
            pygame.draw.rect(screen, (100,100,100), load_game_rect)
            screen.blit(font.render("Carregar", True, WHITE), (load_game_rect.x + 35, load_game_rect.y + 5))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if new_game_rect.collidepoint(event.pos): return "new"
                if os.path.exists(SAVE_FILE) and load_game_rect.collidepoint(event.pos): return "load"
        pygame.display.flip()
        clock.tick(FPS)

def choose_class_screen():
    font_title = pygame.font.SysFont("Arial", 40)
    font_desc = pygame.font.SysFont("Arial", 22)
    classes = {
        "Guerreiro": {"desc": "HP Alto, Ataque Alto, Pouca Mana.", "rect": pygame.Rect(WIDTH/2 - 150, 200, 300, 50)},
        "Mago": {"desc": "HP Baixo, Mana Alta, Mestre das Magias.", "rect": pygame.Rect(WIDTH/2 - 150, 300, 300, 50)},
        "Arqueiro": {"desc": "Ataque balanceado, Alta Chance de Crítico.", "rect": pygame.Rect(WIDTH/2 - 150, 400, 300, 50)}
    }
    while True:
        screen.fill(BLACK)
        title_text = font_title.render("Escolha sua Classe", True, WHITE)
        screen.blit(title_text, (WIDTH/2 - title_text.get_width()/2, 100))
        for name, data in classes.items():
            pygame.draw.rect(screen, (100, 100, 100), data["rect"])
            pygame.draw.rect(screen, WHITE, data["rect"], 2)
            class_text = font_title.render(name, True, WHITE)
            screen.blit(class_text, (data["rect"].x + 10, data["rect"].y + 5))
            desc_text = font_desc.render(data["desc"], True, (200, 200, 200))
            screen.blit(desc_text, (data["rect"].x + 10, data["rect"].y + 55))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for name, data in classes.items():
                    if data["rect"].collidepoint(pos): return name
        pygame.display.flip()
        clock.tick(FPS)

def shop_screen(screen, player):
    shop_items = [Item("Poção", "consumable", price=10), Item("Poção de Mana", "consumable", price=15), Item("Armadura de Couro", "armor", slot="chest", defense=5, price=50), Item("Espada Longa", "weapon", slot="weapon", power=12, damage_type=PHYSICAL, price=100)]
    font = pygame.font.SysFont("Arial", 22)
    shopping = True
    while shopping:
        screen.fill(BLACK)
        text = font.render("Loja - Pressione [E] para sair", True, WHITE)
        screen.blit(text, (50, 50))
        text = font.render(f"Seu Ouro: {player.gold}", True, (255, 255, 0))
        screen.blit(text, (550, 50))
        for i, item in enumerate(shop_items):
            item_text = f"{i+1}. {item.name} - Preço: {item.price} Ouro"
            color = WHITE if player.gold >= item.price else (150, 150, 150)
            screen.blit(font.render(item_text, True, color), (50, 100 + i * 40))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e: shopping = False
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    if idx < len(shop_items):
                        item = shop_items[idx]
                        if player.gold >= item.price:
                            player.gold -= item.price
                            player.inventory.append(Item(name=item.name, type_=item.type, slot=item.slot, power=item.power, defense=item.defense, damage_type=item.damage_type, price=item.price))

def spawn_boss(game_map):
    boss_x, boss_y = MAP_WIDTH - 5, MAP_HEIGHT - 5
    return Boss(boss_x, boss_y)

# --- MELHORIA: Função para desenhar o HUD ---
def draw_hud(screen, player):
    # Fundo semi-transparente para o HUD
    hud_surface = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
    hud_surface.fill((0, 0, 0, 150))
    screen.blit(hud_surface, (0, HEIGHT - 80))

    font = pygame.font.SysFont("Arial", 18)
    
    # Vida
    hp_text = font.render(f"HP: {player.hp} / {player.max_hp}", True, WHITE)
    screen.blit(hp_text, (20, HEIGHT - 65))
    # Barra de Vida
    pygame.draw.rect(screen, (100,0,0), (120, HEIGHT - 65, 200, 15))
    hp_fill = 0
    if player.max_hp > 0:
        hp_fill = (player.hp / player.max_hp) * 200
    pygame.draw.rect(screen, (255,0,0), (120, HEIGHT - 65, hp_fill, 15))

    # Mana
    mp_text = font.render(f"MP: {player.mana} / {player.max_mana}", True, WHITE)
    screen.blit(mp_text, (20, HEIGHT - 40))
    # Barra de Mana
    pygame.draw.rect(screen, (0,0,100), (120, HEIGHT - 40, 150, 15))
    mp_fill = 0
    if player.max_mana > 0:
        mp_fill = (player.mana / player.max_mana) * 150
    pygame.draw.rect(screen, (0,100,255), (120, HEIGHT - 40, mp_fill, 15))

    # Ouro e Nível
    gold_text = font.render(f"Ouro: {player.gold}", True, (255, 223, 0))
    level_text = font.render(f"Nível: {player.level} ({player.exp}/100)", True, WHITE)
    screen.blit(gold_text, (WIDTH - 150, HEIGHT - 65))
    screen.blit(level_text, (WIDTH - 150, HEIGHT - 40))
# -------------------------------------------

# --- Início do Jogo ---
game_mode = start_menu()
if game_mode == "new":
    player, game_map, enemies, npcs, chests, current_level = reset_game()
elif game_mode == "load" and os.path.exists(SAVE_FILE):
    try:
        player, game_map, enemies, npcs, chests, current_level = load_game()
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Arquivo de save corrompido ou inválido ({e}). Iniciando novo jogo.")
        if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)
        player, game_map, enemies, npcs, chests, current_level = reset_game()
else:
    player, game_map, enemies, npcs, chests, current_level = reset_game()

battle = None
player_dead = False
running = True
map_message = ""
map_message_timer = 0
# --- NOVAS VARIÁVEIS PARA VANTAGEM DO ARQUEIRO ---
projectile_path = []
projectile_timer = 0
# ------------------------------------------------

while running:
    screen.fill(BLACK)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game(player, enemies, npcs, chests, current_level)
            running = False
        if not battle and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i: InventoryScreen(screen, player).run()
            if event.key == pygame.K_k: SkillTreeScreen(screen, player).run()
            if event.key == pygame.K_c: CraftingScreen(screen, player).run()
            
            # --- LÓGICA DA VANTAGEM DO ARQUEIRO ---
            if event.key == pygame.K_a:
                if player.character_class == "Arqueiro" and player.ranged_shot_cooldown == 0:
                    player.ranged_shot_cooldown = 60  # Cooldown de 60 frames (aprox. 1 segundo)
                    projectile_path.clear()
                    projectile_timer = 20  # Duração visual do rastro da flecha
                    
                    dx, dy = player.last_direction
                    shot_hit = False
                    for i in range(1, 8):  # Alcance de 7 tiles
                        check_x, check_y = player.x + dx * i, player.y + dy * i
                        
                        if not game_map.is_walkable(check_x, check_y):
                            projectile_path.append((check_x, check_y))
                            break  # Flecha atinge a parede

                        projectile_path.append((check_x, check_y))

                        for enemy in enemies:
                            if enemy.x == check_x and enemy.y == check_y:
                                damage_dealt = 20  # Dano base do tiro à distância
                                enemy.hp -= damage_dealt
                                map_message = f"Tiro certeiro! Você causou {damage_dealt} de dano!"
                                map_message_timer = 100
                                
                                battle = Battle(screen, player, enemy, battle_background)
                                shot_hit = True
                                break
                        if shot_hit:
                            break
            # -----------------------------------------

            if event.key == pygame.K_e:
                if game_map.get_tile_type(player.x, player.y) == SHOP: shop_screen(screen, player)
                for npc in npcs:
                    if abs(player.x - npc.x) <= 1 and abs(player.y - npc.y) <= 1: npc.interact(screen, player)
                for chest in chests:
                    if not chest.is_opened and abs(player.x - chest.x) <= 1 and abs(player.y - chest.y) <= 1:
                        map_message = chest.interact(player)
                        map_message_timer = 100

    if player_dead:
        font = pygame.font.SysFont("Arial", 50)
        text = font.render("Você morreu! Pressione R para reiniciar.", True, (255, 0, 0))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
        if keys[pygame.K_r]:
            if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)
            player, game_map, enemies, npcs, chests, current_level = reset_game()
            player_dead = False
        pygame.display.flip()
        clock.tick(FPS)
        continue

    if not battle:
        player.update(keys, game_map)
        current_tile = game_map.get_tile_type(player.x, player.y)
        if current_tile == LAVA:
            player.terrain_damage_timer += 1
            if player.terrain_damage_timer > 15:
                player.take_damage(5)
                map_message = "Você se queima na lava!"
                map_message_timer = 50
                player.terrain_damage_timer = 0
        if current_tile == STAIRS_DOWN:
            current_level += 1; chests.clear(); game_map = GameMap(current_level, chests)
            enemies = spawn_enemies(game_map, player); player.x, player.y = 5, 6
            if current_level == 3: enemies.append(spawn_boss(game_map))
        elif current_tile == STAIRS_UP:
            current_level -= 1; chests.clear(); game_map = GameMap(current_level, chests)
            enemies = spawn_enemies(game_map, player); player.x, player.y = MAP_WIDTH - 5, MAP_HEIGHT - 6

    if player.hp <= 0:
        player_dead = True
        continue

    camera_x = max(0, min(player.x * TILE_SIZE - WIDTH // 2, MAP_WIDTH * TILE_SIZE - WIDTH))
    camera_y = max(0, min(player.y * TILE_SIZE - HEIGHT // 2, MAP_HEIGHT * TILE_SIZE - HEIGHT))

    game_map.draw(screen, camera_x, camera_y)
    player.draw(screen, camera_x, camera_y)

    # --- DESENHO DO PROJÉTIL DO ARQUEIRO ---
    if projectile_timer > 0:
        for pos in projectile_path:
            px, py = pos
            rect = pygame.Rect(px * TILE_SIZE - camera_x + TILE_SIZE // 4, 
                               py * TILE_SIZE - camera_y + TILE_SIZE // 4, 
                               TILE_SIZE // 2, TILE_SIZE // 2)
            pygame.draw.rect(screen, (200, 200, 0), rect) # Cor amarela para o rastro
        projectile_timer -= 1
        if projectile_timer == 0:
            projectile_path.clear()
    # -----------------------------------------

    view_start_col = camera_x // TILE_SIZE
    view_end_col = view_start_col + (WIDTH // TILE_SIZE) + 1
    view_start_row = camera_y // TILE_SIZE
    view_end_row = view_start_row + (HEIGHT // TILE_SIZE) + 1

    if current_level == 1:
        for npc in npcs:
            if view_start_col <= npc.x <= view_end_col and view_start_row <= npc.y <= view_end_row:
                npc.draw(screen, camera_x, camera_y)

    visible_enemies = [e for e in enemies if view_start_col <= e.x <= view_end_col and view_start_row <= e.y <= view_end_row]
    
    for enemy in visible_enemies:
        if not battle:
            enemy.update(player, game_map)
        enemy.draw(screen, camera_x, camera_y)
        if not battle and pygame.Rect(player.x, player.y, 1, 1).colliderect(pygame.Rect(enemy.x, enemy.y, enemy.size/TILE_SIZE, enemy.size/TILE_SIZE)):
            if game_map.get_tile_type(player.x, player.y) not in [TOWN, SHOP]:
                battle = Battle(screen, player, enemy, battle_background)

    if battle:
        battle.run()
        if battle.player.hp <= 0: player_dead = True
        if not battle.running:
            if battle.enemy.hp <= 0: enemies.remove(battle.enemy)
            elif battle.fled: player.move(0, -1, game_map)
            battle = None

    if map_message_timer > 0:
        font = pygame.font.SysFont("Arial", 20)
        text = font.render(map_message, True, WHITE)
        pygame.draw.rect(screen, BLACK, (10, 10, text.get_width() + 20, 40))
        screen.blit(text, (20, 20))
        map_message_timer -= 1

    # --- MELHORIA: Desenha o HUD por cima de tudo ---
    if not battle and not player_dead:
        draw_hud(screen, player)
    # -----------------------------------------------

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
