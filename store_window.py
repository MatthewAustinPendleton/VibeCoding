# store_window.py

import tkinter as tk
from tkinter import messagebox, simpledialog # Added simpledialog for consistency

# Import game data needed by the store
# Assuming these are correctly defined and accessible
# from definitions import ITEMS, STORE_INVENTORY, get_item_max_stack
# --- Mock these imports if definitions.py isn't available for testing ---
try:
    from definitions import ITEMS, STORE_INVENTORY, get_item_max_stack
except ImportError:
    print("Warning: Could not import from definitions. Using mock data.")
    ITEMS = {
        "Apple": {"sell_price": 2, "image_path": "...", "equippable_slot": None},
        "Berries": {"sell_price": 1, "image_path": "...", "equippable_slot": None},
        "Basic Pickaxe": {"sell_price": 25, "buy_price": 100, "image_path": "...", "equippable_slot": "main_hand"},
        "Iron Helmet": {"sell_price": 95, "buy_price": 150, "image_path": "...", "equippable_slot": "head"},
        # ... add more mock items as needed
    }
    STORE_INVENTORY = {
        "Basic Pickaxe": {"buy_price": ITEMS["Basic Pickaxe"]["buy_price"], "stock": -1},
        "Iron Helmet": {"buy_price": ITEMS["Iron Helmet"]["buy_price"], "stock": 5},
        # ... add more mock store items
    }
    def get_item_max_stack(item_name):
        item_info = ITEMS.get(item_name, {})
        if item_info.get("equippable_slot"):
            return item_info.get("max_stack", 1)
        else:
            return item_info.get("max_stack", 99)
# --- End Mock Imports ---


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

        # Data - Get references to the global definitions
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

        # Configure columns to expand equally
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1) # Allow listboxes to expand vertically

        # Player Inventory Section (Left)
        self.sell_frame = tk.LabelFrame(main_frame, text="Your Inventory")
        self.sell_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 5))
        # Make sell_frame's content area expand
        self.sell_frame.rowconfigure(0, weight=1)
        self.sell_frame.columnconfigure(0, weight=1)


        self.player_inv_list = tk.Listbox(self.sell_frame)
        # Make listbox expand within its frame area
        self.player_inv_list.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        sell_buttons_frame = tk.Frame(self.sell_frame)
        # Place buttons frame below the listbox
        sell_buttons_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.sell_buttons_frame = sell_buttons_frame # Store reference for highlighting

        self.sell_one_btn = tk.Button(sell_buttons_frame, text="Sell 1", command=lambda: self.sell_item(1))
        self.sell_one_btn.pack(side=tk.LEFT, padx=2)

        self.sell_custom_btn = tk.Button(sell_buttons_frame, text="Sell X", command=self.sell_custom_amount)
        self.sell_custom_btn.pack(side=tk.LEFT, padx=2)

        self.sell_all_btn = tk.Button(sell_buttons_frame, text="Sell All", command=self.sell_all)
        self.sell_all_btn.pack(side=tk.LEFT, padx=2)

        self.player_gold_label = tk.Label(self.sell_frame, text=f"Your Gold: {self.player.gold}")
        # Place gold label below the buttons frame
        self.player_gold_label.grid(row=2, column=0, sticky="ew", pady=5)

        # Store Inventory Section (Right)
        self.buy_frame = tk.LabelFrame(main_frame, text="Store Stock")
        self.buy_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(5, 0))
        # Make buy_frame's content area expand
        self.buy_frame.rowconfigure(0, weight=1)
        self.buy_frame.columnconfigure(0, weight=1)

        self.store_inv_list = tk.Listbox(self.buy_frame)
        # Make listbox expand within its frame area
        self.store_inv_list.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.store_feedback_label = tk.Label(self.buy_frame, text="", height=2, anchor='center') # Give it some height
        # Place feedback label below listbox
        self.store_feedback_label.grid(row=1, column=0, sticky="ew", pady=5)

        self.buy_btn = tk.Button(self.buy_frame, text="Buy Item", command=self.show_buy_dialog)
        # Place buy button below feedback label
        self.buy_btn.grid(row=2, column=0, pady=5)

        # --- Set Initial Backgrounds ---
        default_bg = self.sell_frame.cget('bg') # Get default frame background
        self.sell_buttons_frame.config(bg=default_bg)
        for btn in (self.sell_one_btn, self.sell_custom_btn, self.sell_all_btn):
             btn.config(bg=default_bg)
        self.player_gold_label.config(bg=default_bg)

        default_buy_bg = self.buy_frame.cget('bg')
        self.store_feedback_label.config(bg=default_buy_bg)
        self.buy_btn.config(bg=default_buy_bg)
        # --- End Initial Backgrounds ---


        # Bind events
        self.bind('<Left>', self.switch_to_sell_panel)
        self.bind('<Right>', self.switch_to_buy_panel)
        self.bind('<Up>', self.move_selection_up)
        self.bind('<Down>', self.move_selection_down)
        self.bind('<Return>', self.handle_enter)

        # Initial state - activate sell panel
        self.switch_to_sell_panel()

    def center_window(self):
        """Centers the window on the parent."""
        self.update_idletasks() # Ensure window dimensions are calculated
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        win_width = self.winfo_width()
        win_height = self.winfo_height()
        x = parent_x + (parent_width // 2) - (win_width // 2)
        y = parent_y + (parent_height // 2) - (win_height // 2)
        # Clamp position
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        x = max(0, min(x, screen_width - win_width))
        y = max(0, min(y, screen_height - win_height))
        self.geometry(f"{win_width}x{win_height}+{x}+{y}")

    def update_player_list(self):
        """Updates the listbox showing player's inventory contents."""
        self.player_inv_list.delete(0, tk.END)  # Clear current contents

        # Get inventory contents as dictionary {item_name: count}
        inventory_contents = self.player.get_inventory_contents()

        # If inventory has items, show them
        if inventory_contents:
            # ***** CORRECTED: Use .items() to iterate over key-value pairs *****
            for item_name, count in inventory_contents.items():
                # Only add items with a sell price defined and > 0
                if item_name in self.item_definitions and self.item_definitions[item_name].get('sell_price', 0) > 0:
                    sell_price = self.item_definitions[item_name]['sell_price']
                    self.player_inv_list.insert(tk.END, f"{item_name} x{count} ({sell_price}g each)")
        # If empty, leave the listbox empty (no "Inventory is empty" message)


    def update_store_list(self):
        """Updates the listbox showing store's inventory."""
        self.store_inv_list.delete(0, tk.END)  # Clear current contents

        # If store has items, show them
        if self.store_items:
            for item_name, data in self.store_items.items():
                if 'buy_price' in data and data['buy_price'] > 0:  # Only show items that can be bought
                    # Make sure stock is defined, default to 0 if not (though it should be)
                    stock_count = data.get('stock', 0)
                    stock_text = f" (Stock: {stock_count})" if stock_count >= 0 else " (Stock: ∞)" # Use infinity symbol
                    self.store_inv_list.insert(tk.END, f"{item_name} - {data['buy_price']}g{stock_text}")
        # If empty, leave the listbox empty


    def update_gold_display(self):
        """Updates the player's gold label."""
        self.player_gold_label.config(text=f"Your Gold: {self.player.gold}")


    def switch_to_sell_panel(self, event=None):
        """Activate sell panel and update visuals."""
        self.buy_panel_active = False
        active_bg = 'lightblue'
        inactive_bg = 'SystemButtonFace' # Use the default system color

        # Activate Sell Frame and its contents
        self.sell_frame.config(bg=active_bg)
        self.sell_buttons_frame.config(bg=active_bg) # Highlight the button frame
        for btn in (self.sell_one_btn, self.sell_custom_btn, self.sell_all_btn):
            btn.config(bg=active_bg) # Highlight the buttons themselves
        self.player_gold_label.config(bg=active_bg) # Also highlight the gold label

        # Deactivate Buy Frame and its contents
        self.buy_frame.config(bg=inactive_bg)
        self.store_feedback_label.config(bg=inactive_bg, text="") # Reset feedback label bg and text
        self.buy_btn.config(bg=inactive_bg)

        self.player_inv_list.focus_set()
        # Select first item if list is not empty
        if self.player_inv_list.size() > 0:
            self.player_inv_list.select_clear(0, tk.END)
            self.player_inv_list.select_set(0)
            self.player_inv_list.see(0)


    def switch_to_buy_panel(self, event=None):
        """Activate buy panel and update visuals."""
        self.buy_panel_active = True
        active_bg = 'lightblue'
        inactive_bg = 'SystemButtonFace' # Use the default system color

        # Deactivate Sell Frame and its contents
        self.sell_frame.config(bg=inactive_bg)
        self.sell_buttons_frame.config(bg=inactive_bg)
        for btn in (self.sell_one_btn, self.sell_custom_btn, self.sell_all_btn):
            btn.config(bg=inactive_bg)
        self.player_gold_label.config(bg=inactive_bg)

        # Activate Buy Frame and its contents
        self.buy_frame.config(bg=active_bg)
        self.store_feedback_label.config(bg=active_bg, text="") # Highlight and clear feedback label
        self.buy_btn.config(bg=active_bg)          # Highlight the buy button

        self.store_inv_list.focus_set()
        # Select first item if list is not empty
        if self.store_inv_list.size() > 0:
            self.store_inv_list.select_clear(0, tk.END)
            self.store_inv_list.select_set(0)
            self.store_inv_list.see(0)


    def move_selection_up(self, event=None):
        """Move selection up in active listbox with wrapping."""
        listbox = self.store_inv_list if self.buy_panel_active else self.player_inv_list
        if listbox.size() == 0: return # Do nothing if list is empty

        current = listbox.curselection()
        if not current:
            listbox.select_set(listbox.size() - 1) # Select last item if none selected
            listbox.see(listbox.size() - 1)
            return

        current_index = current[0]
        new_index = (current_index - 1) % listbox.size()
        listbox.select_clear(0, tk.END)
        listbox.select_set(new_index)
        listbox.see(new_index) # Make sure the new selection is visible

    def move_selection_down(self, event=None):
        """Move selection down in active listbox with wrapping."""
        listbox = self.store_inv_list if self.buy_panel_active else self.player_inv_list
        if listbox.size() == 0: return # Do nothing if list is empty

        current = listbox.curselection()
        if not current:
            listbox.select_set(0) # Select first item if none selected
            listbox.see(0)
            return

        current_index = current[0]
        new_index = (current_index + 1) % listbox.size()
        listbox.select_clear(0, tk.END)
        listbox.select_set(new_index)
        listbox.see(new_index) # Make sure the new selection is visible

    def handle_enter(self, event=None):
        """Handle Enter key based on active panel."""
        if self.buy_panel_active:
            # Buy action needs quantity, show dialog
            self.show_buy_dialog()
        else:
            # Sell action, default to selling 1 on Enter for safety/consistency
            # (Selling all could be accidental)
            self.sell_item(1)


    def _get_selected_player_item(self):
        """Helper to get the name and count of the selected player item."""
        selected_indices = self.player_inv_list.curselection()
        if not selected_indices:
            self.set_feedback("Please select an item from your inventory.", "orange")
            return None, 0

        item_text = self.player_inv_list.get(selected_indices[0])
        try:
            # Parse "Item Name xCount (Priceg each)"
            parts = item_text.split(" x")
            item_name = parts[0]
            count_part = parts[1].split(" (")[0]
            current_count = int(count_part)
            return item_name, current_count
        except (IndexError, ValueError):
            print(f"Error parsing player item text: {item_text}")
            self.set_feedback("Error reading selected item.", "red")
            return None, 0


    def sell_custom_amount(self):
        """Show dialog to sell custom amount."""
        item_name, current_count = self._get_selected_player_item()
        if not item_name:
            return

        # Use simpledialog for consistency with potential future amount dialogs
        amount = simpledialog.askinteger("Sell Amount",
                                         f"How many {item_name} to sell? (Max: {current_count})",
                                         parent=self,
                                         minvalue=1,
                                         maxvalue=current_count)

        if amount is not None and amount > 0:
            self.sell_item(amount)
        elif amount is not None: # User entered 0 or cancelled
             self.set_feedback("Sell cancelled.", "grey")


    def sell_all(self):
        """Sell entire stack of selected item."""
        item_name, current_count = self._get_selected_player_item()
        if item_name and current_count > 0:
            self.sell_item(current_count)


    def _get_selected_store_item(self):
        """Helper to get the name and stock of the selected store item."""
        selected_indices = self.store_inv_list.curselection()
        if not selected_indices:
            self.set_feedback("Please select an item from the store stock.", "orange")
            return None, 0

        selected_text = self.store_inv_list.get(selected_indices[0])
        try:
            # Parse "Item Name - Priceg (Stock: Count)" or "Item Name - Priceg (Stock: ∞)"
            item_name = selected_text.split(" -")[0]
            store_data = self.store_items.get(item_name)

            if not store_data:
                self.set_feedback(f"Error: Store data for {item_name} not found.", "red")
                return None, 0

            stock = store_data.get('stock', 0) # Default to 0 if missing
            return item_name, stock
        except (IndexError, ValueError):
             print(f"Error parsing store item text: {selected_text}")
             self.set_feedback("Error reading selected store item.", "red")
             return None, 0


    def show_buy_dialog(self):
        """Show dialog to specify buy amount."""
        item_name, stock = self._get_selected_store_item()
        if not item_name:
            return

        store_data = self.store_items.get(item_name)
        if not store_data or 'buy_price' not in store_data:
            self.set_feedback(f"Cannot buy {item_name}.", "red")
            return

        buy_price = store_data['buy_price']
        max_affordable = self.player.gold // buy_price if buy_price > 0 else 9999 # Avoid division by zero

        # Determine the actual maximum buyable amount
        if stock == -1: # Infinite stock
            max_buyable = max_affordable
            stock_limit_text = "∞ available"
        else: # Limited stock
            max_buyable = min(stock, max_affordable)
            stock_limit_text = f"{stock} in stock"

        if max_buyable <= 0:
             if max_affordable <= 0:
                 self.set_feedback(f"You cannot afford any {item_name}.", "orange")
             else: # Must be out of stock
                  self.set_feedback(f"{item_name} is out of stock.", "orange")
             return

        amount = simpledialog.askinteger("Buy Amount",
                                         f"How many {item_name} to buy?\n"
                                         f"Price: {buy_price}g each ({stock_limit_text})\n"
                                         f"You can afford {max_affordable}.\n"
                                         f"(Max buyable: {max_buyable})",
                                         parent=self,
                                         minvalue=1,
                                         maxvalue=max_buyable)

        if amount is not None and amount > 0:
            self.buy_item(item_name, amount)
        elif amount is not None:
             self.set_feedback("Buy cancelled.", "grey")


    def buy_item(self, item_name, amount=1):
        """Buy specified amount of items."""
        store_data = self.store_items.get(item_name)
        if not store_data or 'buy_price' not in store_data:
            self.set_feedback(f"Error: {item_name} not available for purchase.", "red")
            return

        buy_price = store_data['buy_price']
        total_cost = buy_price * amount

        if self.player.gold < total_cost:
            self.set_feedback(f"Need {total_cost}g, you only have {self.player.gold}g.", "orange")
            return

        # Check stock again just before purchase (in case it changed)
        current_stock = store_data.get('stock', 0)
        if current_stock != -1 and amount > current_stock:
             self.set_feedback(f"Store only has {current_stock} {item_name} left.", "orange")
             # Offer to buy remaining? For now, just fail.
             return

        # Attempt to add item to player inventory
        added_count = self.player.add_item(item_name, amount)

        if added_count == amount:
            # Successfully added all items
            self.player.gold -= total_cost
            if current_stock != -1: # Don't decrement infinite stock
                store_data['stock'] -= amount

            # --- Update UI ---
            self.set_feedback(f"Bought {amount} {item_name} for {total_cost}g.", "green")
            self.update_store_list()
            self.update_player_list()
            self.update_gold_display()
            self.app.update_inventory_display() # Update main game inventory
            self.app.update_stats_display()     # Update main game gold display
            # self.app.update_button_panel() # No buttons change based on buying/selling typically

        elif added_count > 0:
            # Partially added items (inventory likely became full)
            partial_cost = buy_price * added_count
            self.player.gold -= partial_cost
            if current_stock != -1:
                store_data['stock'] -= added_count

            self.set_feedback(f"Inventory full! Bought {added_count}/{amount} {item_name} for {partial_cost}g.", "orange")
            # --- Update UI ---
            self.update_store_list()
            self.update_player_list()
            self.update_gold_display()
            self.app.update_inventory_display()
            self.app.update_stats_display()

        else:
            # Could not add any items (inventory was full from the start)
            self.set_feedback(f"Inventory full! Could not buy any {item_name}.", "orange")
            # No state change, but maybe refresh lists just in case
            self.update_store_list()
            self.update_player_list()
            self.update_gold_display()

        # Reselect item in store list if possible after update
        self.select_listbox_item_by_name(self.store_inv_list, item_name)


    def sell_item(self, amount=1):
        """Sell specified amount of items."""
        item_name, current_count = self._get_selected_player_item()
        if not item_name:
            return # Feedback already given by helper

        if amount > current_count:
             self.set_feedback(f"You only have {current_count} {item_name} to sell.", "orange")
             return

        sell_price = self.item_definitions.get(item_name, {}).get('sell_price', 0)

        if sell_price <= 0:
            self.set_feedback(f"Cannot sell {item_name}.", "orange")
            return

        # Attempt to remove from player inventory
        if self.player.remove_item(item_name, amount):
            total_price = sell_price * amount
            self.player.gold += total_price

            # --- Update UI ---
            self.set_feedback(f"Sold {amount} {item_name} for {total_price}g.", "green")
            self.update_player_list() # Update player list in store
            self.update_gold_display() # Update gold in store
            self.app.update_inventory_display()  # Update main game inventory
            self.app.update_stats_display()      # Update main game gold
            # self.app.update_button_panel() # No buttons change

            # Reselect item in player list if possible after update
            self.select_listbox_item_by_name(self.player_inv_list, item_name)

        else:
            # Should not happen if checks passed, but handle defensively
            self.set_feedback(f"Error selling {item_name}.", "red")


    def set_feedback(self, message, color="black"):
         """Updates the feedback label."""
         self.store_feedback_label.config(text=message, fg=color)
         # Optionally clear after a delay
         # self.after(3000, lambda: self.store_feedback_label.config(text=""))


    def select_listbox_item_by_name(self, listbox, item_name_to_select):
        """Tries to find and select an item in a listbox based on its name prefix."""
        current_selection = listbox.curselection()
        original_index = current_selection[0] if current_selection else -1

        for i in range(listbox.size()):
            text = listbox.get(i)
            # Check if the list item starts with the item name we interacted with
            if text.startswith(item_name_to_select):
                listbox.select_clear(0, tk.END)
                listbox.select_set(i)
                listbox.see(i)
                return # Found and selected

        # If not found (e.g., sold the last one), try selecting the original index or nearby
        if original_index != -1:
             if original_index < listbox.size():
                 listbox.select_clear(0, tk.END)
                 listbox.select_set(original_index)
                 listbox.see(original_index)
             elif listbox.size() > 0: # Select last item if original index is now out of bounds
                 new_index = listbox.size() -1
                 listbox.select_clear(0, tk.END)
                 listbox.select_set(new_index)
                 listbox.see(new_index)


    def close_store(self):
        """Called when the store window is closed."""
        self.grab_release() # Release the modal grab
        self.destroy()      # Close the window