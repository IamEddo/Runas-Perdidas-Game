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
pygame.display.set_caption("Reino Perdido 2.0")
battle_background = pygame.image.load("assets/battle_background.png").convert()
clock = pygame.time.Clock()
SAVE_FILE = "savegame.json"

def save_game(player, enemies, npcs, chests, current_level):
    player_data = {
        "class": player.character_class, "x": player.x, "y": player.y, "level": player.level,
        "exp": player.exp, "gold": player.gold, "hp": player.hp, "mana": player.mana,
        "skill_points": player.skill_points,
        "inventory": [vars(item) for item in player.inventory],
        "spells": [s.name for s in player.spells],
        "equipped_weapon": vars(player.equipped_weapon) if player.equipped_weapon else None,
        "equipped_chest": vars(player.equipped_chest) if player.equipped_chest else None,
        "equipped_helmet": vars(player.equipped_helmet) if player.equipped_helmet else None,
        "equipped_gloves": vars(player.equipped_gloves) if player.equipped_gloves else None,
        "equipped_boots": vars(player.equipped_boots) if player.equipped_boots else None,
        "quest": vars(player.quest) if player.quest else None
    }
    enemies_data = [{"x": e.x, "y": e.y, "level": e.level, "is_boss": isinstance(e, Boss)} for e in enemies]
    npcs_data = [{"x": n.x, "y": n.y, "name": n.name, "quest": vars(n.quest) if n.quest else None} for n in npcs]
    chests_data = [vars(c) for c in chests]
    
    save_data = {"player": player_data, "enemies": enemies_data, "npcs": npcs_data, "chests": chests_data, "current_level": current_level}
    with open(SAVE_FILE, 'w') as f:
        json.dump(save_data, f, indent=4)

def load_game():
    with open(SAVE_FILE, 'r') as f:
        save_data = json.load(f)
    
    p_data = save_data["player"]
    player = Player(p_data["class"])
    player.x, player.y, player.level, player.exp, player.gold, player.hp, player.mana, player.skill_points = \
        p_data["x"], p_data["y"], p_data["level"], p_data["exp"], p_data["gold"], p_data["hp"], p_data["mana"], p_data.get("skill_points", 0)
    
    player.inventory = [Item(**item_data) for item_data in p_data["inventory"]]
    
    # Reconstruir magias
    all_spells = SKILL_LIST["Guerreiro"] + SKILL_LIST["Mago"] + SKILL_LIST["Arqueiro"]
    player.spells = [spell for spell in all_spells if spell.name in p_data.get("spells", [])]

    # Re-equipar itens
    def find_and_equip(slot_name):
        item_data = p_data.get(f"equipped_{slot_name}")
        if item_data:
            item_to_equip = next((item for item in player.inventory if vars(item) == item_data), None)
            if item_to_equip:
                player.equip(item_to_equip)

    find_and_equip("weapon")
    find_and_equip("chest")
    find_and_equip("helmet")
    find_and_equip("gloves")
    find_and_equip("boots")

    if p_data["quest"]: player.quest = Quest(**p_data["quest"])

    chests = [TreasureChest(c['x'], c['y'], [Item(**i) for i in c['items']], c['gold']) for c in save_data.get("chests", [])]
    current_level = save_data.get("current_level", 1)
    game_map = GameMap(current_level, chests)

    enemies = []
    for e_data in save_data["enemies"]:
        if e_data["is_boss"]: enemies.append(Boss(e_data["x"], e_data["y"]))
        else: enemies.append(Enemy(e_data["x"], e_data["y"], e_data["level"]))
    
    npcs = []
    for n_data in save_data["npcs"]:
        quest = Quest(**n_data["quest"]) if n_data["quest"] else None
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
    title = font.render("Reino Perdido", True, WHITE)
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
                            player.inventory.append(Item(item.name, item.type, slot=item.slot, power=item.power, defense=item.defense, damage_type=item.damage_type, price=item.price))

def spawn_boss(game_map):
    boss_x, boss_y = MAP_WIDTH - 5, MAP_HEIGHT - 5
    return Boss(boss_x, boss_y)

# --- Início do Jogo ---
game_mode = start_menu()
if game_mode == "new":
    player, game_map, enemies, npcs, chests, current_level = reset_game()
elif game_mode == "load":
    player, game_map, enemies, npcs, chests, current_level = load_game()
else:
    pygame.quit(); sys.exit()

battle = None
player_dead = False
running = True
map_message = ""
map_message_timer = 0

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
    if current_level == 1:
        for npc in npcs: npc.draw(screen, camera_x, camera_y)

    for enemy in enemies[:]:
        if not battle: enemy.update(player, game_map)
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

    pygame.display.flip()