# inventory.py
import math
from definitions import ITEMS, get_item_max_stack # Import definitions

DEFAULT_INVENTORY_SIZE = 28

class Inventory:

    """Manages the player's inventory using slots and stacking."""
    def __init__(self, size=DEFAULT_INVENTORY_SIZE):
        self.size = size
        # Each slot holds {'item_name': str, 'count': int} or None if empty
        self.slots = [None] * self.size
    
    def _find_first_empty_slot(self):
        """Finds the index of the first empty slot, or -1 if none."""
        try:
            return self.slots.index(None)
        except ValueError:
            return -1
    
    def add_item(self, item_name, count):
        """Adds an item to the inventory, handling stacking and finding empty slots."""
        if item_name not in ITEMS:
            print(f"Warning: Attempted to add unknown item '{item_name}'")
            return 0
        if count <= 0:
            return 0
        
        max_stack = get_item_max_stack(item_name)
        if max_stack <= 0:
            print(f"Warning: Item '{item_name}' has invalid max_stack <= 0!")
            return 0
        added_count = 0
        remaining_to_add = count
        for i, slot in enumerate(self.slots):
            if slot and slot['item_name'] == item_name and slot['count'] < max_stack:
                can_add_to_stack = max_stack - slot['count']
                add_now = min(remaining_to_add, can_add_to_stack)
                self.slots[i]['count'] += add_now
                added_count += add_now
                remaining_to_add -= add_now
                if remaining_to_add <= 0:
                    return added_count
        while remaining_to_add > 0:
            empty_slot_index = self._find_first_empty_slot()
            if empty_slot_index == -1:
                print(f"DEBUG: Inventory full. Could not add remaining {remaining_to_add} of {item_name}.")
                return added_count
            add_now = min(remaining_to_add, max_stack)
            self.slots[empty_slot_index] = {'item_name': item_name, 'count': add_now}
            added_count += add_now
            remaining_to_add -= add_now
        return added_count

    def remove_item(self, item_name, count=1):
        """Remove an item from the inventory across potentially multiple stacks."""
        if count <= 0:
            return True
        if not self.has_item(item_name, count):
            return False
        
        remaining_to_remove = count
        for i in range(self.size - 1, -1, -1):
            slot = self.slots[i]
            if slot and slot['item_name'] == item_name:
                remove_from_stack = min(remaining_to_remove, slot['count'])
                slot['count'] -= remove_from_stack
                remaining_to_remove -= remove_from_stack
                if slot['count'] <= 0:
                    self.slots[i] = None
                if remaining_to_remove <= 0:
                    return True
        
        return remaining_to_remove <= 0
    
    def get_item_count(self, item_name):
        """Returns the total count of a specific item across all slots."""
        total = 0
        for slot in self.slots:
            if slot and slot['item_name'] == item_name:
                total += slot['count']
        return total

    def has_item(self, item_name, count=1):
        """Checks if the inventory contains at least 'count' of the item."""
        return self.get_item_count(item_name) >= count

    def is_full(self):
         """Checks if there are no empty slots."""
         return self._find_first_empty_slot() == -1

    def get_all_items(self):
        """
        Returns a consolidated dictionary of all items and their total counts.
        Useful for display compatibility with old format.
        """
        consolidated = {}
        for slot in self.slots:
            if slot:
                name = slot['item_name']
                count = slot['count']
                consolidated[name] = consolidated.get(name, 0) + count
        return consolidated

    def is_empty(self):
        """Checks if all inventory slots are empty."""
        return all(slot is None for slot in self.slots)

    # Optional: Method to get the raw slot list if needed elsewhere
    # def get_slots(self):
    #     return self.slots