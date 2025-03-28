# definitions.py

from PIL import Image, ImageTk
# Import constants needed by Scene class
from constants import IMG_WIDTH, IMG_HEIGHT

# --- Item Definitions ---
# (Name: {sell_price, image_path, equippable_slot (None if not), buy_price (optional)}, 
# max_stack (optional, defaults to 99, 1 for equip)})
ITEMS = {
    "Apple": {"sell_price": 2, "image_path": "item_apple.png", "equippable_slot": None},
    "Berries": {"sell_price": 1, "image_path": "item_berries.png", "equippable_slot": None},
    "Mushroom": {"sell_price": 3, "image_path": "item_mushroom.png", "equippable_slot": None},
    "Strange Leaf": {"sell_price": 5, "image_path": "item_strange_leaf.png", "equippable_slot": None},
    "Copper Ore": {"sell_price": 5, "image_path": "item_copper_ore.png", "equippable_slot": None},
    "Tin Ore": {"sell_price": 8, "image_path": "item_tin_ore.png", "equippable_slot": None},
    "Iron Ore": {"sell_price": 15, "image_path": "item_iron_ore.png", "equippable_slot": None},
    "Basic Pickaxe": {"sell_price": 25, "buy_price": 100, "image_path": "item_basic_pickaxe.png", "equippable_slot": "main_hand"},
    "Iron Helmet": {"sell_price": 95, "buy_price": 150, "image_path": "item_iron_helmet.png", "equippable_slot": "head"},
    "Iron Chestplate": {"sell_price": 150, "buy_price": 550, "image_path": "item_iron_chestplate.png", "equippable_slot": "chest"},
    "Iron Leggings": {"sell_price": 100, "buy_price": 350, "image_path": "item_iron_leggings.png", "equippable_slot": "legs"},
}

def get_item_max_stack(item_name):

    """Gets the max stack size for an item, defaulting appropriatley."""
    if item_name not in ITEMS:
        return 0
    item_info = ITEMS[item_name]
    if item_info.get("equippable_slot"):
        return item_info.get("max_stack", 1)
    else:
        return item_info.get("max_stack", 99)

# --- Scene Definition Class ---
class Scene:
    """Represents a single location in the game."""
    def __init__(self, name, description, image_path, connections,
                 forage_table=None, mine_table=None, store_available=False):

         self.name = name
         self.description = description
         self.image_path = image_path
         self.connections = connections # List of scene names (strings)
         self.forage_table = forage_table # List of tuples: (item_name, weight, xp)
         self.mine_table = mine_table     # List of tuples: (ore_name, req_level, xp)
         self.store_available = store_available
         self._image = None # Cached loaded image (PhotoImage)

    def get_image(self):
        """Loads and returns the scene image (Tkinter PhotoImage), caching it."""
        if self._image is None:
            try:
                # Use constants for dimensions
                img = Image.open(self.image_path)
                img = img.resize((IMG_WIDTH, IMG_HEIGHT), Image.LANCZOS)
                self._image = ImageTk.PhotoImage(img)
            except FileNotFoundError:
                print(f"Warning: Image file not found: {self.image_path}")
                # Create a placeholder image if file not found
                img = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), color='grey')
                self._image = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading image {self.image_path}: {e}")
                img = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), color='red')
                self._image = ImageTk.PhotoImage(img)
        return self._image

# --- Scene Instances ---
# Defines the actual game world map and content
SCENES = {
    "Forest": Scene(name="Forest",
                    description="A dense forest surrounds you. Sunlight filters through the canopy. Paths lead deeper, back towards the entrance, and towards a shimmering lake.",
                    image_path="ForestScene.png",
                    connections=["Deep Forest", "Forest Path", "Forest Lake"],
                    forage_table=[("Apple", 60, 10), ("Berries", 35, 5), ("Strange Leaf", 5, 25)]
                    ),
    "Forest Lake": Scene(name="Forest Lake",
              description="A calm lake lies before you, reflecting the tall trees. The water looks clear. You can forage around the edge.",
              image_path="ForestLakeScene.png",
              connections=["Forest"],
              forage_table=[("Berries", 70, 5), ("Mushroom", 25, 15), ("Strange Leaf", 5, 25)]
            ),
    "Deep Forest": Scene(name="Deep Forest",
              description="The forest grows thicker here. Strange plants grow in the shadows. It feels a bit unsettling.",
              image_path="DeepForestScene.png",
              connections=["Forest"],
              forage_table=[("Mushroom", 50, 15), ("Strange Leaf", 40, 25),
                            ("Berries", 10, 5)]
            ),
    "Forest Path": Scene(name="Forest Path",
              description="A well-trodden path leading out of the forest towards the mountains and a small town.",
              image_path="ForestPathScene.png",
              connections=["Forest", "Mountain Pass", "Town"],
            ),
    "Mountain Pass": Scene(name="Mountain Pass",
              description="A narrow pass winds through the mountains. You see the dark entrance to a mine nearby.",
              image_path="MountainPassScene.png",
              connections=["Forest Path", "Mine Entrance"],
            ),
    "Mine Entrance": Scene(name="Mine Entrance",
              description="The entrance to an old mine shaft. It looks dark and potentially dangerous. A cool breeze drifts out.",
              image_path="MineEntranceScene.png",
              connections=["Mountain Pass", "Mine Lv 1"],
            ),
    "Mine Lv 1": Scene(name="Mine Level 1",
              description="The first level of the mine. Rickety wooden supports hold up the ceiling. You spot some coppery veins in the rock.",
              image_path="MineLv1Scene.png",
              connections=["Mine Entrance", "Mine Lv 2"],
              mine_table=[("Copper Ore", 1, 15)]
            ),
    "Mine Lv 2": Scene(name="Mine Level 2",
              description="Deeper into the mine. Water drips steadily. The air is damp. Tin deposits glitter faintly in the torchlight.",
              image_path="MineLv2Scene.png",
              connections=["Mine Lv 1", "Mine Lv 3"],
              mine_table=[("Tin Ore", 3, 30)]
            ),
    "Mine Lv 3": Scene(name="Mine Level 3",
              description="Very deep now. The rock changes color, showing signs of iron. It's much hotter here.",
              image_path="MineLv3Scene.png",
              connections=["Mine Lv 2"],
              mine_table=[("Iron Ore", 8, 65)] # Corrected from forage_table
            ),
    "Town": Scene(name="Town",
              description="A small, bustling town square. Merchants hawk their wares. You see a general store.",
              image_path="TownScene.png",
              connections=["Forest Path"],
              store_available=True
            ),
}

# --- Store Inventory ---
# (Item Name: {buy_price, stock (-1 for infinite)})
# Needs ITEMS to be defined first to reference buy_prices
STORE_INVENTORY = {
    "Basic Pickaxe": {"buy_price": ITEMS["Basic Pickaxe"]["buy_price"],
                      "stock": -1},
    "Iron Helmet": {"buy_price": ITEMS["Iron Helmet"]["buy_price"],
                    "stock": 5},
    "Iron Chestplate": {"buy_price": ITEMS["Iron Chestplate"]["buy_price"],
                        "stock": 3},
    "Iron Leggings": {"buy_price": ITEMS["Iron Leggings"]["buy_price"],
                      "stock": 4},
}