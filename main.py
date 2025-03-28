# main.py

import tkinter as tk
from main_app import GameApp # Import the main application class

# --- Run the Application ---
if __name__ == "__main__":
    # Create the main Tkinter window
    root = tk.Tk()

    # Create the Game Application instance, passing it the root window
    app = GameApp(root)

    # Start the Tkinter event loop
    root.mainloop()