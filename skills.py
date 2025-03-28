# skills.py
import math

# --- Skill XP Calculation ---

def xp_for_level(level):
    """Calculates the total XP required to reach a given level."""
    if level <= 1:
        return 0
    xp = 0
    for i in range(1, level):
        # Using the Runescape formula structure
        xp += math.floor(i + 300 * (2 ** (i / 7.0)))
    return math.floor(xp / 4)

def level_for_xp(xp):
    """Calculates the level for a given amount of total XP."""
    level = 1
    # Use MAX_SKILL_LEVEL if defined, otherwise calculate indefinitely
    # from constants import MAX_SKILL_LEVEL # Import if needed here, or pass as arg
    while xp_for_level(level + 1) <= xp:
        level += 1
        # Optional: Cap level if MAX_SKILL_LEVEL is defined and used
        # if level >= MAX_SKILL_LEVEL:
        #     break
    return level

def xp_to_next_level(current_xp):
    """Calculates the XP remaining until the next level."""
    current_level = level_for_xp(current_xp)
    xp_for_current = xp_for_level(current_level)
    xp_for_next = xp_for_level(current_level + 1)
    
    if xp_for_next <= xp_for_current: # Handle max level case
        return 0 # No more XP needed
        
    return xp_for_next - current_xp

def xp_progress_in_level(current_xp):
    """Calculates the XP earned within the current level."""
    current_level = level_for_xp(current_xp)
    xp_for_current_level_start = xp_for_level(current_level)
    return current_xp - xp_for_current_level_start

def xp_needed_for_level(level):
    """Calculates the amount of XP needed to gain just this level."""
    if level <= 1:
        return 0
    return xp_for_level(level) - xp_for_level(level - 1)