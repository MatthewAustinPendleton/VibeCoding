import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from PIL import Image, ImageTk
import random
import time
import traceback

# --- Import Project Modules ---
import constants as const
import skills
# Need Scene class, ITEMS, SCENES for type hint/check if desired and functionality
# Make sure these imports work in your environment
try:
    from definitions import ITEMS, SCENES, Scene
    from player import Player
    from store_window import StoreWindow
except ImportError as e:
    print(f"Import Error: {e}. Make sure all game files are present.")
    import sys
    sys.exit(1) # Exit if core components are missing


# --- Main Application Class ---

# --- Constants within GameApp ---
ICON_TARGET_WIDTH = 40
ICON_TARGET_HEIGHT = 40
MIN_SLOT_HEIGHT = 80
MIN_SLOT_WIDTH = 80


class GameApp:
    """The main game application window and logic controller."""

    def __init__(self, root):
        """Initializes the main game application."""
        self.root = root
        self.root.title("Adventure Game")
        self.root.geometry(f"{const.WIN_WIDTH}x{const.WIN_HEIGHT}")
        self.root.resizable(False, False)

        self.player = Player(start_scene_name="Forest")

        self.item_icons = {}
        self._placeholder_icon = None
        self._action_job = None
        self._clear_feedback_job = None
        self._tooltip_active = False
        self.selected_inv_slot_index = None

        self._setup_ui()
        self.update_scene_display()
        self.update_inventory_display() # Call AFTER UI setup
        self.update_stats_display()

    def _get_placeholder_icon(self):
        """Creates and caches a placeholder icon for missing items."""
        if self._placeholder_icon is None:
            try:
                img = Image.new('RGBA', (ICON_TARGET_WIDTH, ICON_TARGET_HEIGHT),
                                (128, 128, 128, 150))
                self._placeholder_icon = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error creating placeholder icon: {e}")
                return None
        return self._placeholder_icon

    def _get_item_icon(self, item_name):
        """Loads, resizes (up or down) to target size, caches, and returns a PhotoImage."""
        if item_name in self.item_icons:
            return self.item_icons[item_name]

        image_path = None
        try:
            if item_name not in ITEMS:
                print(f"Warning: Item '{item_name}' not in ITEMS definition.")
                return self._get_placeholder_icon()

            item_data = ITEMS[item_name]
            image_path = item_data.get("image_path")

            if not image_path:
                print(f"Warning: No image_path defined for item '{item_name}'.")
                return self._get_placeholder_icon()

            img = Image.open(image_path)
            img = img.resize((ICON_TARGET_WIDTH, ICON_TARGET_HEIGHT), Image.LANCZOS)
            photo_image = ImageTk.PhotoImage(img)

            self.item_icons[item_name] = photo_image
            return photo_image

        except FileNotFoundError:
            path_info = f": {image_path}" if image_path else ""
            print(f"Warning: Image file not found{path_info} for item '{item_name}'.")
            return self._get_placeholder_icon()
        except Exception as e:
            print(f"Error loading image for item '{item_name}': {e}")
            traceback.print_exc()
            return self._get_placeholder_icon()

    def _setup_ui(self):
        """Creates and arranges the main UI widgets."""
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.right_frame = tk.Frame(self.root, width=const.RIGHT_PANEL_WIDTH)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        self.right_frame.pack_propagate(False)
        self.scene_image_label = tk.Label(self.main_frame)
        self.scene_image_label.pack(pady=(0, 10))
        self.scene_desc_label = tk.Label(self.main_frame, text="", wraplength=const.IMG_WIDTH - 20, justify=tk.LEFT, anchor="nw", height=6)
        self.scene_desc_label.pack(fill=tk.X, pady=(0, 10)); self.scene_desc_label.pack_propagate(False)
        self.action_feedback_label = tk.Label(self.main_frame, text="", fg="blue", height=2, anchor='center')
        self.action_feedback_label.pack(fill=tk.X, pady=5)
        self.button_frame = tk.Frame(self.main_frame, height=const.BOTTOM_PANEL_HEIGHT)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        self.button_frame.grid_columnconfigure(0, weight=1); self.button_frame.grid_columnconfigure(1, weight=0); self.button_frame.grid_columnconfigure(2, weight=0)
        self.button_frame.grid_columnconfigure(3, weight=0); self.button_frame.grid_columnconfigure(4, weight=0); self.button_frame.grid_columnconfigure(5, weight=1)
        self.button_frame.grid_rowconfigure(0, weight=1)
        self.notebook = ttk.Notebook(self.right_frame)
        self._setup_inventory_tab(); self._setup_stats_equip_tab()
        self.notebook.pack(fill=tk.BOTH, expand=True)

    def _setup_inventory_tab(self):
        """Sets up widgets for the Inventory tab using a grid of 80x80 Frames."""
        self.inv_tab = tk.Frame(self.notebook)
        self.notebook.add(self.inv_tab, text="Inventory")
        self.inv_grid_frame = tk.Frame(self.inv_tab)
        self.inv_grid_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))
        self.inv_slot_widgets = []
        cols = 4; rows = (self.player.inventory.size + cols - 1) // cols
        for i in range(self.player.inventory.size): self.create_slot_frame(self.inv_grid_frame, i, cols)
        for c in range(cols): self.inv_grid_frame.grid_columnconfigure(c, minsize=MIN_SLOT_WIDTH)
        for r in range(rows): self.inv_grid_frame.grid_rowconfigure(r, minsize=MIN_SLOT_HEIGHT)
        self.inv_action_frame = tk.Frame(self.inv_tab)
        self.inv_action_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.selected_item_label = tk.Label(self.inv_action_frame, text="Selected: None")
        self.selected_item_label.pack(side=tk.LEFT, padx=(5, 10))
        self.equip_button = tk.Button(self.inv_action_frame, text="Equip", command=self.equip_selected_item, state=tk.DISABLED)
        self.equip_button.pack(side=tk.LEFT, padx=5)

    def _setup_stats_equip_tab(self):
        """Sets up widgets for the Stats & Equipment tab."""
        self.stats_tab = tk.Frame(self.notebook)
        self.notebook.add(self.stats_tab, text="Stats & Equip")

        # Gold Label
        self.gold_label = tk.Label(self.stats_tab, text=f"Gold: {self.player.gold}", anchor="w"); 
        self.gold_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Skills Frame
        self.skills_frame = tk.LabelFrame(self.stats_tab, text="Skills")
        self.skills_frame.pack(fill=tk.X, padx=5, pady=5)

        # Store both labels
        self.skill_labels = {}
        self.skill_icons = {}

        # Icon size for skills 
        SKILL_ICON_SIZE = 50

        for skill_name in self.player.skills:
            frame = tk.Frame(self.skills_frame)
            frame.pack(fill=tk.X)
            try:
                icon_path = f"icon_{skill_name.lower()}.png"
                img = Image.open(icon_path)
                img = img.resize((SKILL_ICON_SIZE, SKILL_ICON_SIZE), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                icon_label = tk.Label(frame, image=photo)
                icon_label.image = photo
                icon_label.pack(side=tk.LEFT, padx=(5, 2))
                self.skill_icons[skill_name] = icon_label
            except Exception as e:
                print(f"Could not load icon for {skill_name}: {e}")

            # Skill level label
            lbl = tk.Label(frame, text=f"{skill_name}: ...", anchor="w")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            self.skill_labels[skill_name] = lbl
        
        # Equipment Frame
        self.equip_frame = tk.LabelFrame(self.stats_tab, text="Equipment")
        self.equip_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.equip_labels = {}
        self.equip_buttons = {}

        # Equipment Slots
        for slot in const.EQUIPMENT_SLOTS:
            frame = tk.Frame(self.equip_frame)
            frame.pack(fill=tk.X)

            # Slot name label
            slot_display_name = slot.replace("_", " ").title()
            slot_label = tk.Label(frame, text=f"{slot_display_name}:", width=10, anchor="w")
            slot_label.pack(side=tk.LEFT, padx=(5, 0))

            # Item label (shows equipped item or "Empty")
            item_label = tk.Label(frame, text="Empty", anchor="w")
            item_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            self.equip_labels[slot] = item_label

            # Unequip Button
            unequip_btn = tk.Button(frame, text="Unequip", width=7, 
                                    command=lambda s=slot: self.unequip_from_slot(s),
                                    state=tk.DISABLED)
            unequip_btn.pack(side=tk.RIGHT, padx=(0, 5))
            self.equip_buttons[slot] = unequip_btn

    def create_slot_frame(self, parent, index, cols):
        """Creates the 80x80 frame and packs icon (48x48) and text inside."""
        frame = tk.Frame(parent, borderwidth=1, relief=tk.SUNKEN, height=MIN_SLOT_HEIGHT, width=MIN_SLOT_WIDTH, bg="grey85")
        frame.pack_propagate(False); frame.grid(row=index // cols, column=index % cols, padx=2, pady=2, sticky="nsew")
        frame.bind('<Button-1>', lambda e, i=index: self.on_slot_click(i))
        frame.bind('<Button-3>', lambda e, i=index: self.on_slot_right_click(i, e))
        icon_lbl = tk.Label(frame, anchor=tk.CENTER, bg=frame.cget('bg'))
        icon_lbl.pack(side=tk.TOP, pady=(2, 0), fill=tk.X)
        icon_lbl.bind('<Button-1>', lambda e, i=index: self.on_slot_click(i)); icon_lbl.bind('<Button-3>', lambda e, i=index: self.on_slot_right_click(i, e))
        text_wraplength = MIN_SLOT_WIDTH - 10
        text_lbl = tk.Label(frame, text="", anchor=tk.N, justify=tk.CENTER, wraplength=text_wraplength, bg=frame.cget('bg'), font=("TkDefaultFont", 8))
        text_lbl.pack(side=tk.TOP, fill=tk.X, expand=True, pady=(2, 2))
        text_lbl.bind('<Button-1>', lambda e, i=index: self.on_slot_click(i))
        text_lbl.bind('<Button-3>', lambda e, i=index: self.on_slot_right_click(i, e))
        self.inv_slot_widgets.append({'frame': frame, 'icon': icon_lbl, 'text': text_lbl})

    # --- UI Update Functions ---
    def update_scene_display(self):
        try: current_scene = SCENES[self.player.current_scene_name]
        except KeyError: print(f"Error: Scene '{self.player.current_scene_name}' not found."); self.scene_desc_label.config(text=f"Error: Scene '{self.player.current_scene_name}' not found!"); self.scene_image_label.config(image=None); self.scene_image_label.image = None; self.update_button_panel(); return
        scene_image = current_scene.get_image()
        if scene_image: self.scene_image_label.config(image=scene_image); self.scene_image_label.image = scene_image
        else: self.scene_image_label.config(image=None); self.scene_image_label.image = None
        self.scene_desc_label.config(text=current_scene.description); self.update_button_panel(); self.clear_action_feedback()
    def update_button_panel(self):
        for widget in self.button_frame.winfo_children(): widget.destroy()
        try: current_scene = SCENES[self.player.current_scene_name]
        except KeyError: print(f"Error updating buttons: Scene '{self.player.current_scene_name}' not found."); return
        buttons_to_add = []; button_tooltips = {}
        if current_scene.connections: buttons_to_add.append(tk.Button(self.button_frame, text="Move", command=self.show_move_options, width=10))
        if current_scene.forage_table: buttons_to_add.append(tk.Button(self.button_frame, text="Forage", command=self.forage, width=10))
        if current_scene.mine_table:
             mine_state = tk.NORMAL if self.player.has_pickaxe_equipped() else tk.DISABLED; tooltip = "" if mine_state == tk.NORMAL else "Requires Pickaxe Equipped"
             mine_button = tk.Button(self.button_frame, text="Mine", command=self.show_mine_options, width=10, state=mine_state); button_tooltips[mine_button] = tooltip if tooltip else None; buttons_to_add.append(mine_button)
        if current_scene.store_available: buttons_to_add.append(tk.Button(self.button_frame, text="Store", command=self.open_store, width=10))
        num_buttons = len(buttons_to_add); start_col = 1 + (4 - num_buttons) // 2
        for i, button in enumerate(buttons_to_add):
            button.grid(row=0, column=start_col + i, padx=5, pady=5); tooltip_text = button_tooltips.get(button);
            if tooltip_text: button.bind("<Enter>", lambda e, t=tooltip_text: self.show_tooltip(t)); button.bind("<Leave>", lambda e: self.hide_tooltip())
        if self.player.action_in_progress: self.disable_action_buttons()
    def update_inventory_display(self):
        if not hasattr(self, 'inv_slot_widgets') or not self.inv_slot_widgets: print("Warning: Inventory widgets not initialized yet."); return
        default_bg = self.root.cget('bg'); empty_bg = "grey85"
        for i, slot_data in enumerate(self.player.inventory.slots):
            if i >= len(self.inv_slot_widgets): continue
            widgets = self.inv_slot_widgets[i]; frame = widgets['frame']; icon_lbl = widgets['icon']; text_lbl = widgets['text']
            if self.selected_inv_slot_index == i: bg_color = "lightblue"; relief_style = tk.SUNKEN
            elif slot_data is None: bg_color = empty_bg; relief_style = tk.SUNKEN
            else: bg_color = default_bg; relief_style = tk.RAISED
            frame.config(bg=bg_color, relief=relief_style)
            if slot_data is None: icon_lbl.config(image='', bg=bg_color); icon_lbl.image = None; text_lbl.config(text='', bg=bg_color)
            else: item_name = slot_data['item_name']; count = slot_data['count']; icon = self._get_item_icon(item_name); icon_lbl.config(image=icon, bg=bg_color); icon_lbl.image = icon; text_lbl.config(text=f"{item_name}\nx{count}", bg=bg_color)
    def update_slot_visual_state(self, slot_index, selected):
        if slot_index is None or slot_index >= len(self.inv_slot_widgets): return
        widgets = self.inv_slot_widgets[slot_index]; frame = widgets['frame']; icon_lbl = widgets['icon']; text_lbl = widgets['text']; slot_data = self.player.inventory.slots[slot_index]
        if selected: bg_color = "lightblue"; relief_style = tk.SUNKEN
        elif slot_data is None: bg_color = "grey85"; relief_style = tk.SUNKEN
        else: bg_color = self.root.cget('bg'); relief_style = tk.RAISED
        frame.config(bg=bg_color, relief=relief_style); icon_lbl.config(bg=bg_color); text_lbl.config(bg=bg_color)
    def on_slot_click(self, slot_index):
        if self.selected_inv_slot_index is not None and self.selected_inv_slot_index != slot_index:
            self.update_slot_visual_state(self.selected_inv_slot_index, selected=False)
        if slot_index < 0 or slot_index >= len(self.player.inventory.slots):
            print(f"Error: Invalid slot index {slot_index} clicked.")
            return
        if self.selected_inv_slot_index == slot_index:
            self.update_slot_visual_state(slot_index, selected=False)
            self.selected_inv_slot_index = None
            self.equip_button.config(state=tk.DISABLED)
            self.selected_item_label.config(text="Selected: None")
        else:
            slot_data = self.player.inventory.slots[slot_index]
            if slot_data:
                self.selected_inv_slot_index = slot_index
                self.update_slot_visual_state(slot_index, selected=True)
                item_name = slot_data['item_name']
                count = slot_data['count']
                self.selected_item_label.config(text=f"Selected: {item_name} x{count}")
                item_info = ITEMS.get(item_name, {})
                self.equip_button.config(state=tk.NORMAL if item_info.get("equippable_slot") else tk.DISABLED)
            else:
                if self.selected_inv_slot_index is not None:
                    self.update_slot_visual_state(self.selected_inv_slot_index, selected=False)
                self.selected_inv_slot_index = None
                self.update_slot_visual_state(slot_index, selected=False)
                self.equip_button.config(state=tk.DISABLED)
                self.selected_item_label.config(text="Selected: None")
    def on_slot_right_click(self, slot_index, event):
        if slot_index < 0 or slot_index >= len(self.player.inventory.slots):
            return
        slot_data = self.player.inventory.slots[slot_index]
        if not slot_data:
            return
        item_name = slot_data['item_name']
        item_info = ITEMS.get(item_name, {})
        menu = tk.Menu(self.root, tearoff=0)
        can_equip = item_info.get('equippable_slot')
        if can_equip:
            menu.add_command(label=f"Equip {item_name}", command=lambda idx=slot_index: self.equip_item_from_slot(idx))
        if menu.index(tk.END) is not None:
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        else:
            menu.destroy()
    def equip_item_from_slot(self, slot_index):
        if slot_index < 0 or slot_index >= len(self.player.inventory.slots):
            self.set_action_feedback("Invalid slot.", "red")
            return
        slot_data = self.player.inventory.slots[slot_index]
        if not slot_data:
            self.set_action_feedback("Empty slot.", "red")
            return
        item_name = slot_data['item_name']
        success, message = self.player.equip_item(item_name)
        feedback_color = "green" if success else "orange"
        duration = 4000 if "full" in message.lower() else 2500
        self.set_action_feedback(message, feedback_color, duration=duration)
        if success:
            self.update_inventory_display()
            self.update_stats_display()
            self.update_button_panel()
            if self.selected_inv_slot_index == slot_index:
                self.selected_inv_slot_index = None
                self.selected_item_label.config(text="Selected: None")
                self.equip_button.config(state=tk.DISABLED)
    def update_stats_display(self):
        self.gold_label.config(text=f"Gold: {self.player.gold}")
        for skill_name in self.player.skills:
            if skill_name in self.skill_labels:
                level = self.player.get_level(skill_name)
                xp = self.player.get_xp(skill_name)
                xp_prog = skills.xp_progress_in_level(xp)
                xp_next = skills.xp_for_level(level + 1)
                xp_curr = skills.xp_for_level(level)
                needed = xp_next - xp_curr if xp_next > xp_curr else 0
                if level < const.MAX_SKILL_LEVEL and needed > 0:
                    display = f"{int(xp_prog)}/{int(needed)}"
                elif level == const.MAX_SKILL_LEVEL:
                    display = f"{int(xp_prog)} (Max)"
                else:
                    display = f"{int(xp_prog)}"
                self.skill_labels[skill_name].config(text=f"{skill_name}: Lv {level} ({display} XP)")
        for slot in const.EQUIPMENT_SLOTS:
            item = self.player.equipment.get(slot)
            text = item if item else "Empty"
            if slot in self.equip_labels:
                self.equip_labels[slot].config(text=text)
            if slot in self.equip_buttons:
                state = tk.NORMAL if item else tk.DISABLED
                self.equip_buttons[slot].config(state=state)
    def set_action_feedback(self, text, color="blue", duration=3000):
        self.action_feedback_label.config(text=text, fg=color)
        if self._clear_feedback_job:
            self.root.after_cancel(self._clear_feedback_job)
        self._clear_feedback_job = duration > 0 and self.root.after(duration, self.clear_action_feedback) or None
    def clear_action_feedback(self):
        self.action_feedback_label.config(text="")
        self._clear_feedback_job = None

    # --- Action Methods ---
    def show_move_options(self):
        if self.player.action_in_progress:
            self.set_action_feedback("Cannot move while acting.", "orange")
            return
        try:
            current_scene = SCENES[self.player.current_scene_name]
            connections = current_scene.connections
        except KeyError:
            messagebox.showerror("Error", f"Scene '{self.player.current_scene_name}' not found!")
            return
        if not connections:
            messagebox.showinfo("Move", "Nowhere to move.")
            return
        dlg = tk.Toplevel(self.root)
        dlg.title("Move Where?")
        dlg.geometry("250x200")
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Label(dlg, text="Choose destination:").pack(pady=10)
        listbox = tk.Listbox(dlg, selectmode=tk.SINGLE, exportselection=False)
        listbox.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        name_to_key = {SCENES[k].name: k for k in connections if k in SCENES}
        [listbox.insert(tk.END, name) for name in sorted(name_to_key.keys())]
        listbox.size() > 0 and listbox.select_set(0) and listbox.focus_set()

        def handle_move():
            sel = listbox.curselection()
            key = name_to_key.get(listbox.get(sel[0])) if sel else None
            if key:
                dlg.grab_release()
                dlg.destroy()
                self.move_to_scene(key)

        def handle_arrow_key(event):
            cur = listbox.curselection()
            sz = listbox.size()
            new = -1
            (not cur and sz > 0 and (new := 0)) or (cur and (idx := cur[0], new := (idx - 1) % sz if event.keysym == 'Up' else (idx + 1) % sz if event.keysym == 'Down' else -1))
            new != -1 and (listbox.select_clear(0, tk.END), listbox.select_set(new), listbox.see(new))
            return "break"

        def close_dialog():
            dlg.grab_release()
            dlg.destroy()

        listbox.bind('<Double-Button-1>', lambda e: handle_move())
        listbox.bind('<Return>', lambda e: handle_move())
        listbox.bind('<Up>', handle_arrow_key)
        listbox.bind('<Down>', handle_arrow_key)
        dlg.bind('<Escape>', lambda e: close_dialog())
        dlg.protocol("WM_DELETE_WINDOW", close_dialog)
        btns = tk.Frame(dlg)
        btns.pack(pady=10)
        tk.Button(btns, text="Move", command=handle_move, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Cancel", command=close_dialog, width=10).pack(side=tk.LEFT, padx=5)
        self.center_widget_on_root(dlg)
        listbox.focus_set()
        self.root.wait_window(dlg)

    def move_to_scene(self, scene_name):
        if scene_name in SCENES:
            self.player.current_scene_name = scene_name
            self.update_scene_display()
            self.set_action_feedback(f"Moved to {SCENES[scene_name].name}.", "green", 2000)
        else:
            print(f"Error: Invalid move to '{scene_name}'.")
            messagebox.showerror("Move Error", f"Cannot move to '{scene_name}'.")

    def forage(self):
        if self.player.action_in_progress:
            self.set_action_feedback("Already acting.", "orange")
            return
        try:
            current_scene = SCENES[self.player.current_scene_name]
        except KeyError:
            self.set_action_feedback("Scene invalid.", "red")
            return
        if not current_scene.forage_table:
            self.set_action_feedback("Nothing to forage.", "red")
            return
        self.player.action_in_progress = True
        self.disable_action_buttons()
        level = self.player.get_level("Foraging")
        base = 5.0
        min_t = 0.5
        max_l = const.MAX_SKILL_LEVEL
        lvl_range = max(1, max_l - 1)
        eff_lvl = min(level, max_l)
        reduction = (base - min_t) * (eff_lvl - 1) / lvl_range
        time_s = max(min_t, base - reduction)
        time_ms = int(time_s * 1000)
        self.set_action_feedback(f"Foraging... ({time_s:.1f}s)", "blue", 0)
        self._action_job = self.root.after(time_ms, self.complete_forage)

    def complete_forage(self):
        self._action_job = None
        if not self.player.action_in_progress:
            return
        try:
            scene = SCENES[self.player.current_scene_name]
            table = scene.forage_table
            assert table
            items = [i[0] for i in table]
            weights = [i[1] for i in table]
            xp_map = {i[0]: i[2] for i in table}
            if not items or not weights or sum(weights) <= 0:
                self.set_action_feedback("Found nothing.", "grey")
            else:
                item = random.choices(items, weights=weights, k=1)[0]
                xp = xp_map.get(item, 0)
                added = self.player.add_item(item)
                if added > 0:
                    lvl_up, new_lvl = self.player.add_xp("Foraging", xp)
                    msg = f"Found {item}! (+{xp} XP)"
                    msg += f"\nLevel up! Foraging {new_lvl}!" if lvl_up else ""
                    self.set_action_feedback(msg, "purple" if lvl_up else "green", 5000 if lvl_up else 2500)
                    self.update_inventory_display()
                    self.update_stats_display()
                else:
                    self.set_action_feedback(f"Inv full! No {item}.", "orange", 4000)
                    self.update_inventory_display()
                    self.update_stats_display()
        except Exception as e:
            print(f"Forage error: {e}")
            traceback.print_exc()
            self.set_action_feedback("Forage error.", "red")
        finally:
            self.player.action_in_progress = False
            self.enable_action_buttons()

    # Corrected show_mine_options Method
    def show_mine_options(self):
        if self.player.action_in_progress:
            self.set_action_feedback("Already acting.", "orange")
            return
        try:
            current_scene = SCENES[self.player.current_scene_name]
        except KeyError:
            self.set_action_feedback("Scene invalid.", "red")
            return
        if not current_scene.mine_table:
            self.set_action_feedback("Nothing to mine.", "red")
            return
        if not self.player.has_pickaxe_equipped():
            self.set_action_feedback("Need pickaxe.", "red")
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("Select Ore")
        dlg.geometry("300x250")
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Label(dlg, text="Choose ore:").pack(pady=10)
        listbox = tk.Listbox(dlg, exportselection=False)
        listbox.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        level = self.player.get_level("Mining")
        valid = {}
        has_valid = False

        # Populate listbox and store valid options
        for ore, req, xp in current_scene.mine_table:
            text = f"{ore} (Lv {req})"
            color = 'black' if level >= req else 'grey'
            listbox.insert(tk.END, text)
            listbox.itemconfig(tk.END, {'fg': color})
            if level >= req:
                valid[ore] = (req, xp)  # Store req and xp for valid ores
                has_valid = True

        def on_select():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Select Error", "Select ore.", parent=dlg)
                return
                
            ore = listbox.get(sel[0]).split(" (Lv")[0]
            if ore in valid:
                _, xp = valid[ore]
                dlg.grab_release()
                dlg.destroy()
                self.mine_ore(ore, xp)
            else:
                messagebox.showerror("Error", "Level too low.", parent=dlg)

        def close_dialog():  # Use consistent name
            dlg.grab_release()
            dlg.destroy()

        # Buttons and Bindings
        btns = tk.Frame(dlg)
        btns.pack(pady=10)
        ok_state = tk.NORMAL if has_valid else tk.DISABLED
        tk.Button(btns, text="Mine", command=on_select, width=8, state=ok_state).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Cancel", command=close_dialog, width=8).pack(side=tk.LEFT, padx=5)  # Use consistent name

        if has_valid:  # Only bind Double-click/Return if there are options to select
            listbox.bind('<Double-1>', lambda e: on_select())
            listbox.bind('<Return>', lambda e: on_select())

        dlg.bind('<Escape>', lambda e: close_dialog())  # Use consistent name
        dlg.protocol("WM_DELETE_WINDOW", close_dialog)  # Use consistent name
        self.center_widget_on_root(dlg)

        # Select first available option
        first = next((i for i, c in enumerate(listbox.get(0, tk.END)) if listbox.itemcget(i, 'fg') == 'black'), -1)
        if first != -1:
            listbox.select_set(first)

        listbox.focus_set()
        self.root.wait_window(dlg)

    def mine_ore(self, ore_name, xp_gain):
        if self.player.action_in_progress:
            self.set_action_feedback("Already acting.", "orange")
            return
        self.player.action_in_progress = True
        self.disable_action_buttons()
        level = self.player.get_level("Mining")
        base = 7.0
        min_t = 1.0
        max_l = const.MAX_SKILL_LEVEL
        lvl_range = max(1, max_l - 1)
        eff_lvl = min(level, max_l)
        reduction = (base - min_t) * (eff_lvl - 1) / lvl_range
        time_s = max(min_t, base - reduction)
        time_ms = int(time_s * 1000)
        self.set_action_feedback(f"Mining {ore_name}... ({time_s:.1f}s)", "blue", 0)
        self._action_job = self.root.after(time_ms, lambda: self.complete_mine(ore_name, xp_gain))

    def complete_mine(self, ore_name, xp_gain):
        self._action_job = None
        if not self.player.action_in_progress:
            return
        try:
            added = self.player.add_item(ore_name)
            if added > 0:
                lvl_up, new_lvl = self.player.add_xp("Mining", xp_gain)
                msg = f"Mined {ore_name}! (+{xp_gain} XP)"
                msg += f"\nLevel up! Mining {new_lvl}!" if lvl_up else ""
                self.set_action_feedback(msg, "purple" if lvl_up else "green", 5000 if lvl_up else 2500)
                self.update_inventory_display()
                self.update_stats_display()
            else:
                self.set_action_feedback(f"Inv full! No {ore_name}.", "orange", 4000)
                self.update_inventory_display()
                self.update_stats_display()
        except Exception as e:
            print(f"Mine error: {e}")
            traceback.print_exc()
            self.set_action_feedback("Mine error.", "red")
        finally:
            self.player.action_in_progress = False
            self.enable_action_buttons()

    def equip_selected_item(self):
        if self.player.action_in_progress:
            self.set_action_feedback("Cannot equip.", "orange")
            return
        if self.selected_inv_slot_index is None:
            self.set_action_feedback("No item selected.", "red")
            return
        try:
            idx = self.selected_inv_slot_index
            slot_data = self.player.inventory.slots[idx]
            assert slot_data, "Empty slot selected"
            item_name = slot_data['item_name']
        except (AssertionError, IndexError, TypeError) as e:
            self.set_action_feedback(f"Select error: {e}.", "red")
            self.selected_inv_slot_index = None
            self.update_inventory_display()
            self.selected_item_label.config(text="Selected: None")
            self.equip_button.config(state=tk.DISABLED)
            return
        success, message = self.player.equip_item(item_name)
        color = "green" if success else "orange"
        duration = 4000 if "full" in message.lower() else 2500
        self.set_action_feedback(message, color, duration=duration)
        if success:
            self.update_inventory_display()
            self.update_stats_display()
            self.update_button_panel()
            self.selected_inv_slot_index = None
            self.selected_item_label.config(text="Selected: None")
            self.equip_button.config(state=tk.DISABLED)

    def unequip_from_slot(self, slot):
        if self.player.action_in_progress:
            self.set_action_feedback("Cannot unequip.", "orange")
            return
        success, message = self.player.unequip_item(slot)
        color = "green" if success else "orange"
        duration = 4000 if "full" in message.lower() else 2500
        self.set_action_feedback(message, color, duration=duration)
        if success:
            self.update_inventory_display()
            self.update_stats_display()
            self.update_button_panel()

    def open_store(self):
        if self.player.action_in_progress:
            self.set_action_feedback("Cannot open store.", "orange")
            return
        StoreWindow(self.root, self.player, self)

    def disable_action_buttons(self):
        [w.config(state=tk.DISABLED) for w in self.button_frame.winfo_children() if isinstance(w, (tk.Button, ttk.Button))]

    def enable_action_buttons(self):
        self.update_button_panel()

    def show_tooltip(self, text):
        current_text = self.action_feedback_label.cget("text")
        current_color = self.action_feedback_label.cget("fg")
        
        # Check if we should show the tooltip
        should_show = (not current_text or 
                      current_color == 'grey' or 
                      (current_text == text and current_color == 'grey'))
        
        if should_show and (not self._tooltip_active or current_text != text):
            self._tooltip_active = True
            
            # Cancel existing feedback job if any
            if self._clear_feedback_job:
                self.root.after_cancel(self._clear_feedback_job)
                self._clear_feedback_job = None
            
            # Show tooltip
            self.action_feedback_label.config(text=text, fg='grey')

    def hide_tooltip(self):
        self._tooltip_active and (self.action_feedback_label.cget('fg') == 'grey' and self.clear_action_feedback(), setattr(self, '_tooltip_active', False))

    def center_widget_on_root(self, widget):
        widget.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        ww = widget.winfo_width()
        wh = widget.winfo_height()
        x = rx + (rw // 2) - (ww // 2)
        y = ry + (rh // 2) - (wh // 2)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, min(x, sw - ww))
        y = max(0, min(y, sh - wh))
        widget.geometry(f"+{x}+{y}")