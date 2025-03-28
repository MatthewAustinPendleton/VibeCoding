# player.py
from skills import level_for_xp, xp_for_level
from constants import EQUIPMENT_SLOTS
from definitions import ITEMS # Keep for item info access
from inventory import Inventory # Import the new class

class Player:
    """Represents the player character and their state."""

    def __init__(self, start_scene_name):
        self.current_scene_name = start_scene_name
        # Replace dict with Inventory instance
        self.inventory = Inventory() # Uses default size
        self.skills = {
            "Foraging": {"xp": 0},
            "Mining": {"xp": 0}
        }
        self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        self.gold = 100
        self.action_in_progress = False

    # --- Skill Methods (remain the same) ---
    def get_level(self, skill_name):
        if skill_name not in self.skills: return 1
        return level_for_xp(self.skills[skill_name]["xp"])
    def get_xp(self, skill_name):
        return self.skills.get(skill_name, {}).get("xp", 0)
    def get_xp_for_next_level(self, skill_name):
        current_level = self.get_level(skill_name)
        return xp_for_level(current_level + 1)
    def add_xp(self, skill_name, amount):
        if skill_name not in self.skills:
            print(f"Warning: Attempted to add XP to unknown skill '{skill_name}'")
            return False, 1
        current_level = self.get_level(skill_name)
        self.skills[skill_name]["xp"] += amount
        new_level = self.get_level(skill_name)
        leveled_up = new_level > current_level
        return leveled_up, new_level

    # --- Inventory Methods (Use Inventory class) ---
    def add_item(self, item_name, count=1):
        """
        Adds item(s) to the inventory.
        Returns:
             int: Number of items actually added (0 if failed or inventory full).
        """
        added_count = self.inventory.add_item(item_name, count)
        if added_count > 0:
             print(f"DEBUG: Added {added_count}/{count} of {item_name}. Inv total: {self.inventory.get_item_count(item_name)}")
        else:
             print(f"DEBUG: Failed to add {item_name} (Inventory full or invalid item?).")
        return added_count

    def remove_item(self, item_name, count=1):
        """
        Removes item(s) from the inventory.
        Returns:
             bool: True if removal was successful, False otherwise.
        """
        success = self.inventory.remove_item(item_name, count)
        if success:
             print(f"DEBUG: Removed {count} {item_name}. Inv total: {self.inventory.get_item_count(item_name)}")
        else:
             print(f"DEBUG: Failed to remove {count} {item_name} (Not enough?). Inv total: {self.inventory.get_item_count(item_name)}")
        return success

    def has_item(self, item_name, count=1):
         """Checks if the player has enough of an item."""
         return self.inventory.has_item(item_name, count)

    def get_inventory_contents(self):
        """Returns a dictionary summary {item_name: total_count}."""
        return self.inventory.get_all_items()

    # --- Equipment Methods (Need inventory full checks) ---
    def has_pickaxe_equipped(self):
        # Check item definition for a "tool_type": "pickaxe" property in future?
        main_hand = self.equipment.get("main_hand")
        off_hand = self.equipment.get("off_hand")
        return (main_hand and ITEMS.get(main_hand, {}).get("equippable_slot") == "main_hand" and "Pickaxe" in main_hand) or \
               (off_hand and ITEMS.get(off_hand, {}).get("equippable_slot") == "off_hand" and "Pickaxe" in off_hand)
        # Simplified check: return self.equipment.get("main_hand") == "Basic Pickaxe" # For now

    def equip_item(self, item_name):
        """Equips an item from inventory. Returns (success_bool, message_str)."""
        if item_name not in ITEMS:
            return False, "Item definition not found."
        item_info = ITEMS[item_name]
        slot = item_info.get("equippable_slot")

        if not slot:
            return False, f"{item_name} is not equippable."
        if slot not in self.equipment:
            return False, f"Invalid equipment slot type defined: {slot}"

        # Check if player has the item using the new method
        if not self.has_item(item_name, 1):
             return False, f"You don't have {item_name} in your inventory."

        # Attempt to remove item from inventory first
        if not self.remove_item(item_name):
            # This backup check handles potential race conditions or logic errors
            return False, f"Failed to remove {item_name} from inventory before equipping (unexpected)."

        # Item successfully removed, proceed with equipping
        currently_equipped = self.equipment.get(slot)
        if currently_equipped:
            # Try to add the old item back - crucial check for inventory full!
            added_back_count = self.add_item(currently_equipped)
            if added_back_count < 1:
                 # Inventory is full! Cannot unequip the old item.
                 # We MUST put the item we tried to equip back!
                 self.add_item(item_name) # Put it back (should succeed unless logic error)
                 return False, f"Inventory full! Cannot unequip {currently_equipped}."

        # If we got here, either no item was equipped, or the old item was successfully added back.
        self.equipment[slot] = item_name
        return True, f"You equipped {item_name} to {slot.replace('_',' ').title()}." # Nicer slot name

    def unequip_item(self, slot):
        """Unequips an item from a slot. Returns (success_bool, message_str)."""
        if slot not in self.equipment:
            return False, "Invalid equipment slot."

        item_to_unequip = self.equipment.get(slot)
        if not item_to_unequip:
            return False, f"No item equipped in {slot.replace('_',' ').title()}."

        # Try to add the item to inventory - check for space!
        added_count = self.add_item(item_to_unequip)
        if added_count < 1:
            # Cannot unequip, inventory is full
            return False, f"Inventory full! Cannot unequip {item_to_unequip}."

        # Success! Clear the slot.
        self.equipment[slot] = None
        return True, f"You unequipped {item_to_unequip} from {slot.replace('_',' ').title()}."