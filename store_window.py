# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox, simpledialog

# Import game data needed by the store
try:
    from definitions import ITEMS, STORE_INVENTORY, get_item_max_stack
except ImportError:
    print("Warning: Could not import from definitions. Using mock data.")
    # --- Mock Data (if definitions.py isn't available) ---
    ITEMS = {
        "Apple": {"sell_price": 2, "image_path": "...", "equippable_slot": None},
        "Berries": {"sell_price": 1, "image_path": "...", "equippable_slot": None},
        "Basic Pickaxe": {"sell_price": 25, "buy_price": 100, "image_path": "...", "equippable_slot": "main_hand"},
        "Iron Helmet": {"sell_price": 95, "buy_price": 150, "image_path": "...", "equippable_slot": "head"},
        "Iron Chestplate": {"sell_price": 150, "buy_price": 550, "image_path": "...", "equippable_slot": "chest"},
        "Iron Leggings": {"sell_price": 100, "buy_price": 350, "image_path": "...", "equippable_slot": "legs"},
    }
    STORE_INVENTORY = {
        "Basic Pickaxe": {"buy_price": ITEMS["Basic Pickaxe"]["buy_price"], "stock": -1},
        "Iron Helmet": {"buy_price": ITEMS["Iron Helmet"]["buy_price"], "stock": 5},
        "Iron Chestplate": {"buy_price": ITEMS["Iron Chestplate"]["buy_price"], "stock": 3},
        "Iron Leggings": {"buy_price": ITEMS["Iron Leggings"]["buy_price"], "stock": 4},
    }
    def get_item_max_stack(item_name):
        item_info = ITEMS.get(item_name, {})
        if item_info.get("equippable_slot"):
            return item_info.get("max_stack", 1)
        else:
            return item_info.get("max_stack", 99)
    # --- End Mock Data ---


class StoreWindow(tk.Toplevel):
    """UI Window for the General Store."""
    def __init__(self, parent, player, app):
        """
        Initializes the store window.
        Args:
            parent: The parent widget (main application window).
            player: The player object instance (with Inventory class).
            app: The main GameApp instance (for callbacks).
        """
        super().__init__(parent)
        self.parent = parent
        self.player = player
        self.app = app # Reference to main app to call updates

        self.title("General Store")
        self.geometry("600x400") # Width x Height
        self.transient(parent) # Keep store on top of parent
        self.grab_set()        # Make store modal (block interaction with parent)

        # Data - Make a copy to potentially modify stock (though currently modifies original if imported)
        # For true independent stock, use deepcopy: import copy; self.store_items = copy.deepcopy(STORE_INVENTORY)
        self.store_items = STORE_INVENTORY.copy()
        self.item_definitions = ITEMS

        # Track which panel is active (buy=True, sell=False)
        self.buy_panel_active = False

        # --- UI Setup ---
        self._setup_ui()

        # --- Initial Population ---
        self.update_player_list()
        self.update_store_list()
        self.update_gold_display() # Update gold display initially

        # --- Window Management ---
        self.center_window()
        self.protocol("WM_DELETE_WINDOW", self.close_store) # Handle closing with 'X'

    def _setup_ui(self):
        """Creates and arranges the widgets in the store window."""
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1) # Allow listboxes row to expand

        # Player Inventory Section (Left)
        self.sell_frame = tk.LabelFrame(main_frame, text="Your Inventory")
        self.sell_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.sell_frame.rowconfigure(0, weight=1) # Listbox row
        self.sell_frame.columnconfigure(0, weight=1) # Listbox column

        self.player_inv_list = tk.Listbox(self.sell_frame)
        self.player_inv_list.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        sell_buttons_frame = tk.Frame(self.sell_frame)
        sell_buttons_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(5,0)) # Buttons below listbox

        self.sell_one_btn = tk.Button(sell_buttons_frame, text="Sell 1", command=lambda: self.sell_item(1))
        self.sell_one_btn.pack(side=tk.LEFT, padx=2)
        self.sell_custom_btn = tk.Button(sell_buttons_frame, text="Sell X", command=self.sell_custom_amount)
        self.sell_custom_btn.pack(side=tk.LEFT, padx=2)
        self.sell_all_btn = tk.Button(sell_buttons_frame, text="Sell All", command=self.sell_all)
        self.sell_all_btn.pack(side=tk.LEFT, padx=2)

        self.player_gold_label = tk.Label(self.sell_frame, text=f"Your Gold: {self.player.gold}")
        self.player_gold_label.grid(row=2, column=0, sticky="ew", pady=(0,5)) # Gold below buttons

        # Store Inventory Section (Right)
        self.buy_frame = tk.LabelFrame(main_frame, text="Store Stock")
        self.buy_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.buy_frame.rowconfigure(0, weight=1) # Listbox row
        self.buy_frame.columnconfigure(0, weight=1) # Listbox column

        self.store_inv_list = tk.Listbox(self.buy_frame)
        self.store_inv_list.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.store_feedback_label = tk.Label(self.buy_frame, text="", height=2, anchor='center')
        self.store_feedback_label.grid(row=1, column=0, sticky="ew", pady=(5,0)) # Feedback below listbox

        self.buy_btn = tk.Button(self.buy_frame, text="Buy Item", command=self.show_buy_dialog)
        self.buy_btn.grid(row=2, column=0, pady=(0,5)) # Buy button below feedback

        # Bind frame clicks for switching panels (more intuitive)
        # Use lambda to ignore the event argument passed by bind
        self.sell_frame.bind('<Button-1>', lambda e: self.switch_to_sell_panel())
        self.buy_frame.bind('<Button-1>', lambda e: self.switch_to_buy_panel())
        # Bind listbox clicks too, in case user clicks directly on list
        self.player_inv_list.bind('<Button-1>', lambda e: self.switch_to_sell_panel())
        self.store_inv_list.bind('<Button-1>', lambda e: self.switch_to_buy_panel())


        # Bind keyboard events to the Toplevel window itself
        self.bind('<Left>', lambda e: self.switch_to_sell_panel())
        self.bind('<Right>', lambda e: self.switch_to_buy_panel())
        self.bind('<Up>', self.move_selection_up)
        self.bind('<Down>', self.move_selection_down)
        self.bind('<Return>', self.handle_enter)

        # Initial state - activate sell panel
        self.switch_to_sell_panel()

    def center_window(self):
        """Centers the window on the parent."""
        self.update_idletasks()
        parent_x = self.parent.winfo_rootx(); parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width(); parent_height = self.parent.winfo_height()
        win_width = self.winfo_width(); win_height = self.winfo_height()
        x = parent_x + (parent_width // 2) - (win_width // 2)
        y = parent_y + (parent_height // 2) - (win_height // 2)
        screen_width = self.parent.winfo_screenwidth(); screen_height = self.parent.winfo_screenheight()
        x = max(0, min(x, screen_width - win_width)); y = max(0, min(y, screen_height - win_height))
        self.geometry(f"{win_width}x{win_height}+{x}+{y}")

    def update_player_list(self):
        """Updates the listbox showing player's sellable inventory contents."""
        # Store current selection
        selected_index = self.player_inv_list.curselection()
        current_selection_index = selected_index[0] if selected_index else -1

        self.player_inv_list.delete(0, tk.END)
        inventory_contents = self.player.get_inventory_contents()

        if inventory_contents:
            for item_name, count in sorted(inventory_contents.items()): # Sort alphabetically
                if item_name in self.item_definitions and self.item_definitions[item_name].get('sell_price', 0) > 0:
                    sell_price = self.item_definitions[item_name]['sell_price']
                    self.player_inv_list.insert(tk.END, f"{item_name} x{count} ({sell_price}g each)")

        # Try to restore selection
        if current_selection_index != -1 and current_selection_index < self.player_inv_list.size():
            self.player_inv_list.select_set(current_selection_index)
            self.player_inv_list.see(current_selection_index)
        elif self.player_inv_list.size() > 0: # If old selection invalid, select first
            self.player_inv_list.select_set(0)
            self.player_inv_list.see(0)

    def update_store_list(self):
        """Updates the listbox showing store's buyable inventory."""
         # Store current selection
        selected_index = self.store_inv_list.curselection()
        current_selection_index = selected_index[0] if selected_index else -1

        self.store_inv_list.delete(0, tk.END)
        if self.store_items:
            for item_name, data in sorted(self.store_items.items()): # Sort alphabetically
                if 'buy_price' in data and data['buy_price'] > 0:
                    stock_count = data.get('stock', 0)
                    stock_text = f" (Stock: {stock_count})" if stock_count >= 0 else " (Stock: ∞)"
                    self.store_inv_list.insert(tk.END, f"{item_name} - {data['buy_price']}g{stock_text}")

        # Try to restore selection
        if current_selection_index != -1 and current_selection_index < self.store_inv_list.size():
            self.store_inv_list.select_set(current_selection_index)
            self.store_inv_list.see(current_selection_index)
        elif self.store_inv_list.size() > 0: # If old selection invalid, select first
            self.store_inv_list.select_set(0)
            self.store_inv_list.see(0)

    def update_gold_display(self):
        """Updates the player's gold label."""
        self.player_gold_label.config(text=f"Your Gold: {self.player.gold}")

    def switch_to_sell_panel(self, event=None):
        """Activate sell panel and update visuals."""
        if not self.buy_panel_active: return # Already active, do nothing

        self.buy_panel_active = False
        active_bg = 'lightblue'
        inactive_bg = 'SystemButtonFace'

        self.sell_frame.config(bg=active_bg)
        self.buy_frame.config(bg=inactive_bg)
        self.store_feedback_label.config(text="") # Clear feedback

        self.store_inv_list.select_clear(0, tk.END) # Clear selection in buy list
        self.player_inv_list.focus_set()

        # Select first item if list not empty and nothing is selected
        if self.player_inv_list.size() > 0 and not self.player_inv_list.curselection():
            self.player_inv_list.select_set(0)
            self.player_inv_list.see(0)

    def switch_to_buy_panel(self, event=None):
        """Activate buy panel and update visuals."""
        if self.buy_panel_active: return # Already active, do nothing

        self.buy_panel_active = True
        active_bg = 'lightblue'
        inactive_bg = 'SystemButtonFace'

        self.buy_frame.config(bg=active_bg)
        self.sell_frame.config(bg=inactive_bg)
        self.store_feedback_label.config(text="") # Clear feedback

        self.player_inv_list.select_clear(0, tk.END) # Clear selection in sell list
        self.store_inv_list.focus_set()

        # Select first item if list not empty and nothing is selected
        if self.store_inv_list.size() > 0 and not self.store_inv_list.curselection():
            self.store_inv_list.select_set(0)
            self.store_inv_list.see(0)

    # --- CORRECTED NAVIGATION METHODS ---
    def move_selection_up(self, event=None):
        """Move selection up one item in the active listbox, stopping at the top."""
        listbox = self.store_inv_list if self.buy_panel_active else self.player_inv_list
        if listbox.size() == 0:
            return # Nothing to select

        current = listbox.curselection()
        new_index = -1 # Default to invalid/no change

        if not current:
            # If nothing selected, select the last item
            if listbox.size() > 0:
                new_index = listbox.size() - 1
        else:
            # If something is selected, try to move up
            current_index = int(current[0])
            if current_index > 0: # Check if we can move up
                new_index = current_index - 1
            # else: we are at index 0, do nothing (don't set new_index)

        # If a valid new index was determined, apply the change
        if new_index != -1:
            listbox.select_clear(0, tk.END) # Clear ALL selections first
            listbox.select_set(new_index)
            listbox.see(new_index)
        # Implicitly return None if no move happened

    def move_selection_down(self, event=None):
        """Move selection down one item in the active listbox, stopping at the bottom."""
        listbox = self.store_inv_list if self.buy_panel_active else self.player_inv_list
        if listbox.size() == 0:
            return # Nothing to select

        current = listbox.curselection()
        new_index = -1 # Default to invalid/no change

        if not current:
            # If nothing selected, select the first item
            if listbox.size() > 0:
                 new_index = 0
        else:
            # If something is selected, try to move down
            current_index = int(current[0])
            if current_index < listbox.size() - 1: # Check if we can move down
                new_index = current_index + 1
            # else: we are at the last item, do nothing (don't set new_index)

        # If a valid new index was determined, apply the change
        if new_index != -1:
            listbox.select_clear(0, tk.END) # Clear ALL selections first
            listbox.select_set(new_index)
            listbox.see(new_index)

    def handle_enter(self, event=None):
        """Handle Enter key based on active panel."""
        if self.buy_panel_active:
            self.show_buy_dialog()
        else:
            self.sell_item(1) # Default to selling 1

    def _get_selected_player_item(self):
        """Helper to get the name and count of the selected player item."""
        selected_indices = self.player_inv_list.curselection()
        if not selected_indices:
            self.set_feedback("Please select an item from your inventory.", "orange")
            return None, 0
        item_text = self.player_inv_list.get(selected_indices[0])
        try:
            parts = item_text.split(" x"); item_name = parts[0]
            count_part = parts[1].split(" (")[0]; current_count = int(count_part)
            return item_name, current_count
        except (IndexError, ValueError):
            print(f"Error parsing player item text: {item_text}")
            self.set_feedback("Error reading selected item.", "red")
            return None, 0

    def sell_custom_amount(self):
        """Show dialog to sell custom amount."""
        item_name, current_count = self._get_selected_player_item()
        if not item_name: return
        amount = simpledialog.askinteger("Sell Amount", f"How many {item_name} to sell? (Max: {current_count})", parent=self, minvalue=1, maxvalue=current_count)
        if amount is not None and amount > 0: self.sell_item(amount)
        elif amount is not None: self.set_feedback("Sell cancelled.", "grey")

    def sell_all(self):
        """Sell entire stack of selected item."""
        item_name, current_count = self._get_selected_player_item()
        if item_name and current_count > 0: self.sell_item(current_count)

    def _get_selected_store_item(self):
        """Helper to get the name and stock of the selected store item."""
        selected_indices = self.store_inv_list.curselection()
        if not selected_indices:
            self.set_feedback("Please select an item from the store stock.", "orange")
            return None, 0
        selected_text = self.store_inv_list.get(selected_indices[0])
        try:
            item_name = selected_text.split(" -")[0]; store_data = self.store_items.get(item_name)
            if not store_data: self.set_feedback(f"Error: Store data for {item_name} not found.", "red"); return None, 0
            stock = store_data.get('stock', 0); return item_name, stock
        except (IndexError, ValueError):
             print(f"Error parsing store item text: {selected_text}"); self.set_feedback("Error reading selected store item.", "red"); return None, 0

    def show_buy_dialog(self):
        """Show dialog to specify buy amount."""
        item_name, stock = self._get_selected_store_item()
        if not item_name: return
        store_data = self.store_items.get(item_name)
        if not store_data or 'buy_price' not in store_data: self.set_feedback(f"Cannot buy {item_name}.", "red"); return
        buy_price = store_data['buy_price']
        max_affordable = self.player.gold // buy_price if buy_price > 0 else 9999
        if stock == -1: max_buyable = max_affordable; stock_limit_text = "∞ available"
        else: max_buyable = min(stock, max_affordable); stock_limit_text = f"{stock} in stock"
        if max_buyable <= 0: self.set_feedback(f"You cannot afford any {item_name}." if max_affordable <= 0 else f"{item_name} is out of stock.", "orange"); return
        amount = simpledialog.askinteger("Buy Amount", f"How many {item_name} to buy?\nPrice: {buy_price}g each ({stock_limit_text})\nYou can afford {max_affordable}.\n(Max buyable: {max_buyable})", parent=self, minvalue=1, maxvalue=max_buyable)
        if amount is not None and amount > 0: self.buy_item(item_name, amount)
        elif amount is not None: self.set_feedback("Buy cancelled.", "grey")

    def buy_item(self, item_name, amount=1):
        """Buy specified amount of items."""
        store_data = self.store_items.get(item_name)
        if not store_data or 'buy_price' not in store_data: self.set_feedback(f"Error: {item_name} not available.", "red"); return
        buy_price = store_data['buy_price']; total_cost = buy_price * amount
        if self.player.gold < total_cost: self.set_feedback(f"Need {total_cost}g, have {self.player.gold}g.", "orange"); return
        current_stock = store_data.get('stock', 0)
        if current_stock != -1 and amount > current_stock: self.set_feedback(f"Store only has {current_stock} {item_name}.", "orange"); return

        added_count = self.player.add_item(item_name, amount)
        if added_count == amount:
            self.player.gold -= total_cost; store_data['stock'] -= amount if current_stock != -1 else 0
            self.set_feedback(f"Bought {amount} {item_name} for {total_cost}g.", "green")
            self._update_ui_after_transaction(item_name)
        elif added_count > 0:
            partial_cost = buy_price * added_count; self.player.gold -= partial_cost; store_data['stock'] -= added_count if current_stock != -1 else 0
            self.set_feedback(f"Inv full! Bought {added_count}/{amount} {item_name} for {partial_cost}g.", "orange")
            self._update_ui_after_transaction(item_name)
        else:
            self.set_feedback(f"Inventory full! Could not buy any {item_name}.", "orange")
            # Optional: Refresh lists even on failure
            # self.update_store_list(); self.update_player_list(); self.update_gold_display()

        # Reselect item in store list if possible after update
        self.select_listbox_item_by_name(self.store_inv_list, item_name)

    def sell_item(self, amount=1):
        """Sell specified amount of items."""
        item_name, current_count = self._get_selected_player_item()
        if not item_name: return
        if amount > current_count: self.set_feedback(f"You only have {current_count} {item_name}.", "orange"); return
        sell_price = self.item_definitions.get(item_name, {}).get('sell_price', 0)
        if sell_price <= 0: self.set_feedback(f"Cannot sell {item_name}.", "orange"); return

        if self.player.remove_item(item_name, amount):
            total_price = sell_price * amount; self.player.gold += total_price
            self.set_feedback(f"Sold {amount} {item_name} for {total_price}g.", "green")
            self._update_ui_after_transaction(item_name)
            # Reselect item in player list if possible after update
            self.select_listbox_item_by_name(self.player_inv_list, item_name)
        else:
            self.set_feedback(f"Error selling {item_name}.", "red")

    def _update_ui_after_transaction(self, item_name_involved):
        """Consolidated UI updates after a successful buy/sell."""
        self.update_store_list()
        self.update_player_list()
        self.update_gold_display()
        self.app.update_inventory_display() # Update main game inventory
        self.app.update_stats_display()     # Update main game gold display

    def set_feedback(self, message, color="black"):
         """Updates the feedback label."""
         self.store_feedback_label.config(text=message, fg=color)
         # Optionally clear after delay: self.after(3000, lambda: self.store_feedback_label.config(text=""))

    def select_listbox_item_by_name(self, listbox, item_name_to_select):
        """Tries to find and select an item in a listbox based on its name prefix."""
        current_selection = listbox.curselection()
        original_index = current_selection[0] if current_selection else -1
        found_index = -1

        for i in range(listbox.size()):
            text = listbox.get(i)
            if text.startswith(item_name_to_select):
                found_index = i
                break # Found the item

        if found_index != -1:
            listbox.select_clear(0, tk.END)
            listbox.select_set(found_index)
            listbox.see(found_index)
        elif original_index != -1: # If item not found (e.g. sold last one)
             if original_index < listbox.size(): # Try original position
                 listbox.select_clear(0, tk.END)
                 listbox.select_set(original_index)
                 listbox.see(original_index)
             elif listbox.size() > 0: # Try last item if original is now invalid
                 new_index = listbox.size() -1
                 listbox.select_clear(0, tk.END)
                 listbox.select_set(new_index)
                 listbox.see(new_index)
        # Else: If nothing was selected and item not found, leave selection empty

    def close_store(self):
        """Called when the store window is closed."""
        self.grab_release()
        self.destroy()