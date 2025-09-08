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

    player_data = {
        "class": player.character_class, "x": player.x, "y": player.y, "level": player.level,
        "exp": player.exp, "gold": player.gold, "hp": player.hp, "mana": player.mana,
        "skill_points": player.skill_points,
        "inventory": [item_to_dict(item) for item in player.inventory],
        "spells": [s.name for s in player.spells],
        "equipped_weapon": item_to_dict(player.equipped_weapon) if player.equipped_weapon else None,
        "equipped_chest": item_to_dict(player.equipped_chest) if player.equipped_chest else None,
        "equipped_helmet": item_to_dict(player.equipped_helmet) if player.equipped_helmet else None,
        "equipped_gloves": item_to_dict(player.equipped_gloves) if player.equipped_gloves else None,
        "equipped_boots": item_to_dict(player.equipped_boots) if player.equipped_boots else None,
        "quest": vars(player.quest) if player.quest else None
    }
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
    
    p_data = save_data["player"]
    player = Player(p_data["class"])
    player.x, player.y, player.level, player.exp, player.gold, player.hp, player.mana, player.skill_points = \
        p_data["x"], p_data["y"], p_data["level"], p_data["exp"], p_data["gold"], p_data["hp"], p_data["mana"], p_data.get("skill_points", 0)
    
    player.inventory = []
    for item_data in p_data.get("inventory", []):
        if 'type' in item_data:
            item_data['type_'] = item_data.pop('type')
        player.inventory.append(Item(**item_data))
    
    all_spells = SKILL_LIST["Guerreiro"] + SKILL_LIST["Mago"] + SKILL_LIST["Arqueiro"]
    player.spells = [spell for spell in all_spells if spell.name in p_data.get("spells", [])]

    def find_and_equip(slot_name):
        saved_item_data = p_data.get(f"equipped_{slot_name}")
        if saved_item_data:
            if 'type' in saved_item_data:
                saved_item_data['type_'] = saved_item_data.pop('type')
            
            for item_in_inv in player.inventory:
                inv_item_dict = vars(item_in_inv).copy()
                if 'type_' in inv_item_dict:
                    inv_item_dict['type'] = inv_item_dict.pop('type_')
                
                if inv_item_dict == saved_item_data:
                    player.equip(item_in_inv)
                    return

    find_and_equip("weapon")
    find_and_equip("chest")
    find_and_equip("helmet")
    find_and_equip("gloves")
    find_and_equip("boots")

    if p_data.get("quest"): player.quest = Quest(**p_data["quest"])

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
                            # CORREÇÃO: Usa item.type para ler e passa para o parâmetro type_ do construtor.
                            player.inventory.append(Item(name=item.name, type_=item.type, slot=item.slot, power=item.power, defense=item.defense, damage_type=item.damage_type, price=item.price))

def spawn_boss(game_map):
    boss_x, boss_y = MAP_WIDTH - 5, MAP_HEIGHT - 5
    return Boss(boss_x, boss_y)

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

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()