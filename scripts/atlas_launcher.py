#!/usr/bin/env python3
"""
ATLAS Command Centre - OSRS-Style Interface

A Windows GUI for the ATLAS voice assistant with RuneScape-inspired design.
- 4-zone layout: Main Activity, Chat, HUD, Inventory
- Hold SPACEBAR to record, release to send
- Clickable inventory slots for quick actions

Usage (from Windows):
    python atlas_launcher.py
    # Or double-click atlas_launcher.pyw (hides console)

Dependencies:
    pip install customtkinter sounddevice numpy pillow
"""

import sys
import os
import json
import time
import subprocess
import tkinter as tk
from pathlib import Path
from threading import Thread, Event
from typing import Optional

# Check dependencies
try:
    import customtkinter as ctk
    import sounddevice as sd
    import numpy as np
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError as e:
    if e.name == "PIL" or e.name == "pillow":
        print("WARNING: Pillow not installed. Sprites will show as text.")
        print("  Install with: pip install pillow")
        PIL_AVAILABLE = False
    else:
        print("ERROR: Missing dependencies. Run in Windows PowerShell:")
        print("  pip install customtkinter sounddevice numpy pillow")
        print(f"\nMissing: {e.name}")
        sys.exit(1)

# Configuration
WSL_PATH = Path(r"\\wsl$\Ubuntu\home\squiz\ATLAS")
BRIDGE_DIR = WSL_PATH / ".bridge"
SAMPLE_RATE = 16000

# OSRS-style colors (matched to reference)
OSRS = {
    "bg_dark": "#0e0c0a",        # Darkest background (near black)
    "bg_game": "#494034",        # Game area background
    "panel_stone": "#5d5142",    # Right panel stone tan
    "panel_dark": "#3d3428",     # Darker panel areas
    "slot_bg": "#3d3529",        # Inventory slot background
    "slot_border": "#2a241c",    # Slot border
    "border_dark": "#1a1510",    # Dark borders
    "border_light": "#6d6152",   # Light bevel
    "gold": "#ffff00",           # Gold (XP, levels)
    "gold_dark": "#ff981f",      # Orange-gold (like XP orb)
    "text": "#ff981f",           # Default text (orange)
    "text_white": "#ffffff",     # White text
    "text_muted": "#9a8866",     # Muted tan text
    "orb_green": "#25b525",      # Run energy orb
    "orb_red": "#d42a2a",        # HP orb red
    "orb_blue": "#2a7dd4",       # Prayer orb blue
    "orb_yellow": "#d4b22a",     # Special attack orb
    "minimap_bg": "#c4b998",     # Minimap tan/beige
    "success": "#25b525",
    "warning": "#d4b22a",
    "error": "#d42a2a",
}

# State colors
STATE_COLORS = {
    "idle": "#9a8866",
    "listening": "#25b525",
    "processing": "#d4b22a",
    "speaking": "#2a7dd4",
}


class ATLASLauncher(ctk.CTk):
    """OSRS-style Command Centre."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("ATLAS Command Centre")
        self.geometry("1100x750")
        self.minsize(900, 650)
        self.resizable(True, True)
        ctk.set_appearance_mode("dark")

        # State
        self.server_process: Optional[subprocess.Popen] = None
        self.server_ready = Event()
        self.recording = False
        self.audio_chunks = []
        self.stream = None
        self.processing = False
        self.transcript_history = []
        self.last_exchange_hash = ""
        self.current_state = "idle"

        # Undo history (last 10 actions)
        self._action_history = []
        self._max_history = 10

        # Build UI
        self._build_ui()
        self._bind_keys()
        self._start_polling()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Build OSRS 4-zone interface."""
        self.configure(fg_color=OSRS["bg_dark"])

        # Main container
        main = ctk.CTkFrame(self, fg_color=OSRS["bg_dark"])
        main.pack(fill="both", expand=True, padx=4, pady=4)

        # ==========================================
        # LAYOUT: Left column (game area) + Right column (panel)
        # ==========================================
        left_col = ctk.CTkFrame(main, fg_color=OSRS["bg_game"])
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 4))

        right_col = ctk.CTkFrame(main, fg_color=OSRS["panel_stone"], width=300)
        right_col.pack(side="right", fill="y")
        right_col.pack_propagate(False)

        # ==========================================
        # ZONE 1: MAIN ACTIVITY (top-left) - Game window style
        # ==========================================
        self.zone_main = ctk.CTkFrame(
            left_col, fg_color=OSRS["bg_dark"],
            corner_radius=0, border_width=3, border_color=OSRS["border_dark"]
        )
        self.zone_main.pack(fill="both", expand=True, pady=(0, 4))
        self._build_zone_main()

        # ==========================================
        # ZONE 2: CHAT BOX (bottom-left) - Chat window style
        # ==========================================
        self.zone_chat = ctk.CTkFrame(
            left_col, height=180, fg_color=OSRS["panel_dark"],
            corner_radius=0, border_width=2, border_color=OSRS["border_dark"]
        )
        self.zone_chat.pack(fill="x")
        self.zone_chat.pack_propagate(False)
        self._build_zone_chat()

        # ==========================================
        # ZONE 3: HUD (top-right) - Stats display (EXPANDS to fill space)
        # ==========================================
        self.zone_hud = ctk.CTkFrame(
            right_col, fg_color=OSRS["panel_dark"],
            corner_radius=0, border_width=2, border_color=OSRS["border_dark"]
        )
        self.zone_hud.pack(fill="both", expand=True, pady=(0, 4))
        self._build_zone_hud()

        # ==========================================
        # ZONE 4: INVENTORY (right side) - Fixed max size
        # ==========================================
        # Calculate max inventory height: 7 rows × 70px max + padding + tab bar
        max_inv_height = 7 * 74 + 50  # slots + padding + tab bar
        self.zone_inv = ctk.CTkFrame(
            right_col, fg_color=OSRS["panel_dark"], height=max_inv_height,
            corner_radius=0, border_width=2, border_color=OSRS["border_dark"]
        )
        self.zone_inv.pack(fill="x", side="bottom")
        self.zone_inv.pack_propagate(False)
        self._build_zone_inventory()

    def _build_zone_main(self):
        """Zone 1: Main activity window (game area)."""
        # Title bar with buttons
        title_bar = ctk.CTkFrame(self.zone_main, fg_color=OSRS["panel_dark"], height=36)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        ctk.CTkLabel(
            title_bar, text="ATLAS Command Centre",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=OSRS["gold"]
        ).pack(side="left", padx=10)

        self.stop_btn = ctk.CTkButton(
            title_bar, text="STOP", width=70, height=26,
            command=self._stop_server, fg_color=OSRS["orb_red"],
            hover_color="#ff4444", text_color=OSRS["text_white"],
            corner_radius=2, state="disabled"
        )
        self.stop_btn.pack(side="right", padx=5, pady=5)

        self.start_btn = ctk.CTkButton(
            title_bar, text="START", width=70, height=26,
            command=self._start_server, fg_color=OSRS["orb_green"],
            hover_color="#33dd33", text_color=OSRS["text_white"],
            corner_radius=2
        )
        self.start_btn.pack(side="right", pady=5)

        # Main content area
        self.main_content = ctk.CTkFrame(self.zone_main, fg_color=OSRS["bg_game"])
        self.main_content.pack(fill="both", expand=True, padx=4, pady=4)

        # ═══════════════════════════════════════════════════════
        # WORKOUT/TIMER DISPLAY (hidden by default, shown when active)
        # ═══════════════════════════════════════════════════════
        self.workout_display = ctk.CTkFrame(self.main_content, fg_color=OSRS["bg_dark"])
        # Don't pack initially - will show when workout active

        # Section name (top)
        self.workout_section = ctk.CTkLabel(
            self.workout_display, text="Strength A",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=OSRS["gold"]
        )
        self.workout_section.pack(pady=(10, 2))

        # Progress indicator (exercise X of Y)
        self.workout_progress = ctk.CTkLabel(
            self.workout_display, text="Exercise 1 of 9",
            font=ctk.CTkFont(size=11), text_color=OSRS["text_muted"]
        )
        self.workout_progress.pack()

        # Exercise name (large)
        self.workout_exercise = ctk.CTkLabel(
            self.workout_display, text="Goblet Squat",
            font=ctk.CTkFont(size=28, weight="bold"), text_color=OSRS["text_white"]
        )
        self.workout_exercise.pack(pady=(15, 5))

        # Set/rep info
        self.workout_sets = ctk.CTkLabel(
            self.workout_display, text="Set 1 of 3 • 8 reps",
            font=ctk.CTkFont(size=16), text_color=OSRS["orb_green"]
        )
        self.workout_sets.pack()

        # Large countdown timer (the main visual)
        self.workout_timer = ctk.CTkLabel(
            self.workout_display, text="0:30",
            font=ctk.CTkFont(family="Arial", size=80, weight="bold"),
            text_color=OSRS["gold"]
        )
        self.workout_timer.pack(pady=(20, 10))

        # Timer progress bar
        self.workout_timer_bar = ctk.CTkProgressBar(
            self.workout_display, width=400, height=16,
            progress_color=OSRS["orb_green"], fg_color=OSRS["bg_dark"]
        )
        self.workout_timer_bar.pack(pady=(0, 15))
        self.workout_timer_bar.set(1.0)

        # Form cue (bottom)
        self.workout_form_cue = ctk.CTkLabel(
            self.workout_display, text="Keep chest proud. Drive through heels.",
            font=ctk.CTkFont(size=12, slant="italic"), text_color=OSRS["text_muted"],
            wraplength=450
        )
        self.workout_form_cue.pack(pady=(0, 5))

        # Next exercise preview
        self.workout_next = ctk.CTkLabel(
            self.workout_display, text="Next: Floor Press",
            font=ctk.CTkFont(size=11), text_color=OSRS["text_muted"]
        )
        self.workout_next.pack(pady=(0, 10))

        # Workout control buttons
        self.workout_buttons = ctk.CTkFrame(self.workout_display, fg_color="transparent")
        self.workout_buttons.pack(pady=(0, 15))

        self.btn_pause = ctk.CTkButton(
            self.workout_buttons, text="PAUSE", width=80, height=32,
            fg_color=OSRS["orb_yellow"], hover_color="#e8c838",
            text_color=OSRS["bg_dark"], corner_radius=4,
            command=self._toggle_pause
        )
        self.btn_pause.pack(side="left", padx=5)
        self._is_paused = False  # Track pause state

        self.btn_skip = ctk.CTkButton(
            self.workout_buttons, text="SKIP", width=80, height=32,
            fg_color=OSRS["text_muted"], hover_color=OSRS["panel_dark"],
            text_color=OSRS["text_white"], corner_radius=4,
            command=lambda: self._send_workout_command("SKIP_EXERCISE")
        )
        self.btn_skip.pack(side="left", padx=5)

        self.btn_stop = ctk.CTkButton(
            self.workout_buttons, text="STOP", width=80, height=32,
            fg_color=OSRS["orb_red"], hover_color="#ff4444",
            text_color=OSRS["text_white"], corner_radius=4,
            command=lambda: self._send_workout_command("STOP_ROUTINE")
        )
        self.btn_stop.pack(side="left", padx=5)

        # ═══════════════════════════════════════════════════════
        # DEFAULT VOICE INSTRUCTION (shown when no workout active)
        # ═══════════════════════════════════════════════════════
        self.voice_display = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.voice_display.pack(fill="both", expand=True)

        self.voice_instruction = ctk.CTkLabel(
            self.voice_display, text="Hold SPACE to speak",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=OSRS["gold"]
        )
        self.voice_instruction.pack(expand=True)

        self.recording_indicator = ctk.CTkProgressBar(
            self.voice_display, width=250, height=12,
            progress_color=OSRS["orb_green"], fg_color=OSRS["bg_dark"]
        )
        self.recording_indicator.pack(pady=(0, 20))
        self.recording_indicator.set(0)

        self.status_bar = ctk.CTkLabel(
            self.voice_display, text="Ready - Press START",
            font=ctk.CTkFont(size=13), text_color=OSRS["text"]
        )
        self.status_bar.pack(pady=(0, 15))

        # Track workout display state
        self._workout_display_visible = False

    def _build_zone_chat(self):
        """Zone 2: Chat/transcript (OSRS chat style)."""
        # Tab bar (like OSRS chat tabs)
        tab_bar = ctk.CTkFrame(self.zone_chat, fg_color=OSRS["slot_bg"], height=28)
        tab_bar.pack(fill="x", side="bottom")
        tab_bar.pack_propagate(False)

        chat_tabs = ["All", "Game", "Public", "Private", "Channel", "Clan", "Trade"]
        for i, name in enumerate(chat_tabs):
            btn = ctk.CTkButton(
                tab_bar, text=name, width=38, height=22,
                font=ctk.CTkFont(size=9),
                fg_color="transparent" if i > 0 else OSRS["panel_dark"],
                hover_color=OSRS["panel_dark"],
                text_color=OSRS["gold"] if i == 0 else OSRS["text_muted"],
                corner_radius=0
            )
            btn.pack(side="left", padx=1, pady=3)

        self.exchange_count = ctk.CTkLabel(
            tab_bar, text="(0)", font=ctk.CTkFont(size=9),
            text_color=OSRS["text_muted"]
        )
        self.exchange_count.pack(side="right", padx=5)

        self.clear_btn = ctk.CTkButton(
            tab_bar, text="Clear", width=35, height=20,
            font=ctk.CTkFont(size=9),
            fg_color="transparent", hover_color=OSRS["panel_dark"],
            text_color=OSRS["text_muted"], command=self._clear_transcript,
            corner_radius=0
        )
        self.clear_btn.pack(side="right", padx=2)

        # Transcript area
        self.transcript_box = ctk.CTkTextbox(
            self.zone_chat, font=ctk.CTkFont(size=11),
            fg_color=OSRS["bg_dark"], text_color=OSRS["text"],
            wrap="word", border_width=0
        )
        self.transcript_box.pack(fill="both", expand=True, padx=4, pady=4)
        self.transcript_box.configure(state="disabled")

    def _build_zone_hud(self):
        """Zone 3: OSRS-style HUD with health orbs + life task orbs."""
        # Main HUD container (minimap-style background)
        hud_inner = ctk.CTkFrame(self.zone_hud, fg_color=OSRS["minimap_bg"], corner_radius=0)
        hud_inner.pack(fill="both", expand=True, padx=4, pady=4)

        # ═══════════════════════════════════════════════════════
        # SECTION 1: Health Orbs (from Garmin)
        # Layout:  [SLEEP]  [BATTERY]  [HRV]
        # ═══════════════════════════════════════════════════════
        health_section = ctk.CTkFrame(hud_inner, fg_color="transparent")
        health_section.pack(pady=(6, 2))

        section_lbl = ctk.CTkLabel(health_section, text="─ HEALTH ─",
            font=ctk.CTkFont(size=8), text_color=OSRS["text_muted"])
        section_lbl.pack()

        health_row = ctk.CTkFrame(health_section, fg_color="transparent")
        health_row.pack(pady=2)

        self.sleep_orb = self._create_mini_orb(health_row, "Sleep", "7.5", OSRS["orb_blue"], 70)
        self.sleep_orb.pack(side="left", padx=8)

        # Central Battery orb (larger - the "HP orb")
        orb_size = 95
        battery_frame = ctk.CTkFrame(health_row, fg_color="transparent")
        battery_frame.pack(side="left", padx=10)

        self.hp_canvas = tk.Canvas(
            battery_frame, width=orb_size, height=orb_size,
            bg=OSRS["minimap_bg"], highlightthickness=0
        )
        self.hp_canvas.pack()

        self.hp_canvas.create_oval(2, 2, orb_size-2, orb_size-2,
            fill=OSRS["bg_dark"], outline="#4a4a3a", width=2)
        self.hp_fill = self.hp_canvas.create_arc(
            5, 5, orb_size-5, orb_size-5, start=270, extent=-270,
            fill=OSRS["orb_red"], outline=""
        )
        self.hp_text = self.hp_canvas.create_text(
            orb_size//2, orb_size//2, text="75",
            font=("Arial", 18, "bold"), fill=OSRS["text_white"]
        )
        ctk.CTkLabel(battery_frame, text="Battery",
            font=ctk.CTkFont(size=9), text_color=OSRS["text_muted"]).pack()

        self.hrv_orb = self._create_mini_orb(health_row, "HRV", "56", OSRS["orb_green"], 70)
        self.hrv_orb.pack(side="left", padx=8)

        # ═══════════════════════════════════════════════════════
        # SECTION 2: Life Orbs (depleting tasks)
        # Layout:  [MEAL]  [DOG]  [BABY]
        # ═══════════════════════════════════════════════════════
        life_section = ctk.CTkFrame(hud_inner, fg_color="transparent")
        life_section.pack(pady=(4, 2))

        life_lbl = ctk.CTkLabel(life_section, text="─ LIFE TASKS ─",
            font=ctk.CTkFont(size=8), text_color=OSRS["text_muted"])
        life_lbl.pack()

        life_row = ctk.CTkFrame(life_section, fg_color="transparent")
        life_row.pack(pady=2)

        # These orbs DEPLETE over time - clicking them logs the action
        self.meal_orb = self._create_life_orb(life_row, "🍽️", "Meal", 65, OSRS["orb_green"], "log meal")
        self.meal_orb.pack(side="left", padx=8)

        self.dog_orb = self._create_life_orb(life_row, "🐕", "Dog", 30, OSRS["orb_yellow"], "walked the dog")
        self.dog_orb.pack(side="left", padx=8)

        self.baby_orb = self._create_life_orb(life_row, "👶", "Baby", 0, OSRS["orb_red"], "baby activity")
        self.baby_orb.pack(side="left", padx=8)

        # ═══════════════════════════════════════════════════════
        # SECTION 3: Progress Stats
        # Layout:  [STREAK]  [TOTAL]  [XP]
        # ═══════════════════════════════════════════════════════
        stats_section = ctk.CTkFrame(hud_inner, fg_color="transparent")
        stats_section.pack(pady=(4, 2))

        stats_lbl = ctk.CTkLabel(stats_section, text="─ PROGRESS ─",
            font=ctk.CTkFont(size=8), text_color=OSRS["text_muted"])
        stats_lbl.pack()

        stats_row = ctk.CTkFrame(stats_section, fg_color="transparent")
        stats_row.pack(pady=2)

        self.streak_orb = self._create_mini_orb(stats_row, "Streak", "14", OSRS["orb_yellow"], 58)
        self.streak_orb.pack(side="left", padx=8)

        # Total Level (larger display)
        total_frame = ctk.CTkFrame(stats_row, fg_color=OSRS["panel_dark"],
            corner_radius=6, border_width=2, border_color=OSRS["border_dark"])
        total_frame.pack(side="left", padx=10)
        ctk.CTkLabel(total_frame, text="Lv",
            font=ctk.CTkFont(size=10), text_color=OSRS["text_muted"]).pack(side="left", padx=(10,0))
        self.total_level_label = ctk.CTkLabel(total_frame, text="12",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=OSRS["gold"])
        self.total_level_label.pack(side="left", padx=(4, 10), pady=6)

        self.xp_orb = self._create_mini_orb(stats_row, "XP", "+250", OSRS["gold_dark"], 58)
        self.xp_orb.pack(side="left", padx=8)

        # ═══════════════════════════════════════════════════════
        # Status bar at bottom
        # ═══════════════════════════════════════════════════════
        status_frame = ctk.CTkFrame(self.zone_hud, fg_color=OSRS["panel_dark"], height=22)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)

        self.server_status = ctk.CTkLabel(
            status_frame, text="● Offline", font=ctk.CTkFont(size=8),
            text_color=OSRS["text_muted"]
        )
        self.server_status.pack(side="left", padx=4)

        self.gpu_status = ctk.CTkLabel(
            status_frame, text="GPU:--", font=ctk.CTkFont(size=8),
            text_color=OSRS["text_muted"]
        )
        self.gpu_status.pack(side="left")

        # Undo button
        self.undo_btn = ctk.CTkButton(
            status_frame, text="↩ Undo", width=50, height=18,
            font=ctk.CTkFont(size=8),
            fg_color="transparent", hover_color=OSRS["panel_dark"],
            text_color=OSRS["text_muted"], corner_radius=2,
            command=self._undo_last_action, state="disabled"
        )
        self.undo_btn.pack(side="right", padx=4)

        self.cost_label = ctk.CTkLabel(
            status_frame, text="$0.00", font=ctk.CTkFont(size=8),
            text_color=OSRS["gold_dark"]
        )
        self.cost_label.pack(side="right", padx=4)

    def _create_life_orb(self, parent, emoji, label, fill_pct, color, command):
        """Create a clickable life task orb that depletes over time."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        size = 65

        # Determine color based on fill level
        if fill_pct > 60:
            fill_color = OSRS["orb_green"]
        elif fill_pct > 30:
            fill_color = OSRS["orb_yellow"]
        else:
            fill_color = OSRS["orb_red"]

        canvas = tk.Canvas(frame, width=size, height=size,
                          bg=OSRS["minimap_bg"], highlightthickness=0)
        canvas.pack()

        # Draw orb background
        canvas.create_oval(1, 1, size-1, size-1,
                          fill=OSRS["bg_dark"], outline="#4a4a3a", width=2)

        # Draw filled portion (depletes clockwise from top)
        extent = -int(fill_pct * 3.6)  # Convert percentage to degrees
        canvas.create_arc(3, 3, size-3, size-3, start=270, extent=extent,
                         fill=fill_color, outline="")

        # Emoji in center
        canvas.create_text(size//2, size//2, text=emoji,
                          font=("Segoe UI Emoji", 14), fill=OSRS["text_white"])

        # Label below
        lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=7),
                          text_color=OSRS["text_muted"], height=12)
        lbl.pack()

        # Click to refill (log action)
        def on_click(e):
            self._send_text_command(command)
            # Visual feedback - flash green
            canvas.create_oval(1, 1, size-1, size-1, fill=OSRS["orb_green"],
                             outline="#4a4a3a", width=2, tags="flash")
            canvas.after(200, lambda: canvas.delete("flash"))

        canvas.bind("<Button-1>", on_click)
        frame.bind("<Button-1>", on_click)

        return frame

    def _create_mini_orb(self, parent, label, value, color, size):
        """Create a mini orb for HUD with label."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")

        canvas = tk.Canvas(frame, width=size, height=size,
                          bg=OSRS["minimap_bg"], highlightthickness=0)
        canvas.pack()

        # Draw orb background
        canvas.create_oval(1, 1, size-1, size-1,
                          fill=OSRS["bg_dark"], outline="#4a4a3a", width=2)

        # Calculate fill extent based on value
        try:
            val = float(value.replace("+", ""))
            extent = min(-360, -int(val * 3.6)) if val <= 100 else -360
        except:
            extent = -360

        # Draw filled portion
        canvas.create_arc(3, 3, size-3, size-3, start=270, extent=extent,
                         fill=color, outline="")

        # Value text (scale font with orb size)
        font_size = max(9, size // 4)
        canvas.create_text(size//2, size//2, text=value,
                          font=("Arial", font_size, "bold"), fill=OSRS["text_white"])

        # Label below
        lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=8),
                          text_color=OSRS["text_muted"], height=14)
        lbl.pack()

        return frame

    def _build_zone_inventory(self):
        """Zone 4: Inventory with dual tab bars (top + bottom) like OSRS."""
        self.current_tab = "inventory"

        # ═══════════════════════════════════════════════════════
        # TOP TAB BAR - Action tabs (Combat, Stats, Quest, Inventory)
        # ═══════════════════════════════════════════════════════
        top_tab_bar = ctk.CTkFrame(self.zone_inv, fg_color=OSRS["panel_stone"], height=36)
        top_tab_bar.pack(fill="x", side="top")
        top_tab_bar.pack_propagate(False)

        for i in range(4):
            top_tab_bar.columnconfigure(i, weight=1)

        self.top_tab_buttons = {}
        # Tab order: Inventory (leftmost), Skills, Quests, Protocols (rightmost)
        # Icons: combat_icon for protocols (combat/workouts), quest_point_icon for quests
        top_tabs = [
            ("inventory", "combat_icon.png", "🎒"),        # Inventory (first/leftmost)
            ("skills", "stats_icon.png", "📊"),            # Stats/Skills
            ("quests", "quest_point_icon.png", "📜"),      # Quests/Daily tasks
            ("protocols", None, "⚔️"),                     # Combat/Workout protocols
        ]

        for col, (key, sprite, fallback) in enumerate(top_tabs):
            icon_img = self._load_sprite(sprite, (20, 20)) if sprite else None
            is_active = (key == "inventory")

            if icon_img:
                btn = ctk.CTkButton(
                    top_tab_bar, image=icon_img, text="", height=30,
                    fg_color=OSRS["slot_bg"] if is_active else OSRS["panel_stone"],
                    hover_color=OSRS["slot_bg"], corner_radius=0,
                    border_width=2,
                    border_color=OSRS["orb_red"] if is_active else OSRS["border_dark"],
                    command=lambda k=key: self._switch_tab(k)
                )
            else:
                btn = ctk.CTkButton(
                    top_tab_bar, text=fallback, height=30,
                    font=ctk.CTkFont(size=12),
                    fg_color=OSRS["slot_bg"] if is_active else OSRS["panel_stone"],
                    hover_color=OSRS["slot_bg"],
                    text_color=OSRS["gold"] if is_active else OSRS["text_muted"],
                    corner_radius=0, border_width=2,
                    border_color=OSRS["orb_red"] if is_active else OSRS["border_dark"],
                    command=lambda k=key: self._switch_tab(k)
                )
            btn.grid(row=0, column=col, sticky="ew", padx=2, pady=2)
            self.top_tab_buttons[key] = btn

        # ═══════════════════════════════════════════════════════
        # CONTENT AREA - Scrollable for small windows
        # ═══════════════════════════════════════════════════════
        self.inv_content = ctk.CTkScrollableFrame(
            self.zone_inv, fg_color=OSRS["slot_bg"],
            corner_radius=0, border_width=0
        )
        self.inv_content.pack(padx=4, pady=2, fill="both", expand=True)

        # Build all panels
        self._build_inventory_panel()
        self._build_skills_panel()
        self._build_quests_panel()

        # Show inventory by default
        self.skills_frame.pack_forget()
        self.quests_frame.pack_forget()

        # ═══════════════════════════════════════════════════════
        # BOTTOM TAB BAR - Utility tabs (Settings, etc.)
        # ═══════════════════════════════════════════════════════
        bottom_tab_bar = ctk.CTkFrame(self.zone_inv, fg_color=OSRS["panel_stone"], height=36)
        bottom_tab_bar.pack(fill="x", side="bottom")
        bottom_tab_bar.pack_propagate(False)

        for i in range(4):
            bottom_tab_bar.columnconfigure(i, weight=1)

        self.bottom_tab_buttons = {}
        bottom_tabs = [
            ("equipment", None, "👤"),           # Player equipment (future)
            ("prayer", "focus_mode.png", "🎯"),  # Focus modes (custom icon)
            ("settings", "wrench.png", "⚙️"),    # Settings
            ("logout", None, "🚪"),              # Logout/Exit
        ]

        for col, (key, sprite, fallback) in enumerate(bottom_tabs):
            icon_img = self._load_sprite(sprite, (20, 20)) if sprite else None

            if icon_img:
                btn = ctk.CTkButton(
                    bottom_tab_bar, image=icon_img, text="", height=30,
                    fg_color=OSRS["panel_stone"], hover_color=OSRS["slot_bg"],
                    corner_radius=0, border_width=2, border_color=OSRS["border_dark"],
                    command=lambda k=key: self._switch_tab(k)
                )
            else:
                btn = ctk.CTkButton(
                    bottom_tab_bar, text=fallback, height=30,
                    font=ctk.CTkFont(size=12),
                    fg_color=OSRS["panel_stone"], hover_color=OSRS["slot_bg"],
                    text_color=OSRS["text_muted"], corner_radius=0,
                    border_width=2, border_color=OSRS["border_dark"],
                    command=lambda k=key: self._switch_tab(k)
                )
            btn.grid(row=0, column=col, sticky="ew", padx=2, pady=2)
            self.bottom_tab_buttons[key] = btn

        # Combine tab button references
        self.tab_buttons = {**self.top_tab_buttons, **self.bottom_tab_buttons}
        self.tab_icons = {}

    def _switch_tab(self, tab_key):
        """Switch between all tabs (top + bottom bars)."""
        # Handle special actions first
        if tab_key == "logout":
            self._on_close()
            return

        self.current_tab = tab_key

        # Update ALL tab button styles (both bars)
        all_buttons = {**self.top_tab_buttons, **self.bottom_tab_buttons}
        for key, btn in all_buttons.items():
            if key == tab_key:
                btn.configure(
                    fg_color=OSRS["slot_bg"],
                    border_color=OSRS["orb_red"]
                )
            else:
                btn.configure(
                    fg_color=OSRS["panel_stone"],
                    border_color=OSRS["border_dark"]
                )

        # Hide all panels first
        if hasattr(self, 'inv_frame'):
            self.inv_frame.pack_forget()
        if hasattr(self, 'skills_frame'):
            self.skills_frame.pack_forget()
        if hasattr(self, 'protocols_frame'):
            self.protocols_frame.pack_forget()
        if hasattr(self, 'settings_frame'):
            self.settings_frame.pack_forget()
        if hasattr(self, 'quests_frame'):
            self.quests_frame.pack_forget()
        if hasattr(self, 'equipment_frame'):
            self.equipment_frame.pack_forget()
        if hasattr(self, 'prayer_frame'):
            self.prayer_frame.pack_forget()

        # Show selected panel
        if tab_key == "inventory":
            self.inv_frame.pack(fill="both", expand=True)
        elif tab_key == "skills":
            self.skills_frame.pack(fill="both", expand=True)
        elif tab_key == "protocols":
            if not hasattr(self, 'protocols_frame'):
                self._build_protocols_panel()
            self.protocols_frame.pack(fill="both", expand=True)
        elif tab_key == "quests":
            if not hasattr(self, 'quests_frame'):
                self._build_quests_panel()
            self.quests_frame.pack(fill="both", expand=True)
        elif tab_key == "settings":
            if not hasattr(self, 'settings_frame'):
                self._build_settings_panel()
            self.settings_frame.pack(fill="both", expand=True)
        elif tab_key == "equipment":
            if not hasattr(self, 'equipment_frame'):
                self._build_equipment_panel()
            self.equipment_frame.pack(fill="both", expand=True)
        elif tab_key == "prayer":
            if not hasattr(self, 'prayer_frame'):
                self._build_prayer_panel()
            self.prayer_frame.pack(fill="both", expand=True)

    def _build_inventory_panel(self):
        """Build 28-slot inventory grid - fixed size slots in scrollable container."""
        self.inv_frame = ctk.CTkFrame(self.inv_content, fg_color="transparent")
        self.inv_frame.pack(fill="both", expand=True)

        # Inventory slots with sprites: (label, command, sprite, full_name, category)
        self.inventory_slots = [
            # Row 1: Workouts
            ("Str A", "start workout", "abyssal_whip.png", "Strength A", "Workout"),
            ("Str B", "start workout", "dragon_scimitar.png", "Strength B", "Workout"),
            ("Str C", "start workout", "dharoks_greataxe.png", "Strength C", "Workout"),
            ("Zone2", "zone 2 cardio", "boots_of_lightness.png", "Zone 2 Cardio", "Workout"),
            # Row 2: Supplements
            ("AM", "took my morning supps", "strength_potion.png", "Pre-Workout Supps", "Supplement"),
            ("Bfast", "took my breakfast supps", "saradomin_brew.png", "Breakfast Supps", "Supplement"),
            ("Bed", "took my bedtime supps", "prayer_potion.png", "Bedtime Supps", "Supplement"),
            ("Ice", "ice bath done", "icefiend.png", "Ice Bath", "Recovery"),
            # Row 3: Nutrition
            ("Bfast", "log breakfast", "breakfast.png", "Breakfast", "Meal"),
            ("Lunch", "log lunch", "lunch.png", "Lunch", "Meal"),
            ("Dinner", "log dinner", "shark.png", "Dinner", "Meal"),
            ("Snack", "log snack", "banana.png", "Snack", "Meal"),
            # Row 4: Mind
            ("Focus", "focus timer", "ancient_staff.png", "Deep Focus", "Mind"),
            ("Learn", "learning", "zamorak_book.png", "Learning Session", "Mind"),
            ("Jrnl", "journal", "quill.png", "Journal Entry", "Mind"),
            ("Rflt", "reflection", "reflect_mode.png", "Seneca Trial", "Mind"),
            # Row 5: Routines
            ("Rtn", "start routine", "amulet_of_glory.png", "Morning Routine", "Protocol"),
            ("Test", "start baseline", "crafting.png", "Baseline Test", "Protocol"),
            ("Sauna", "sauna", "fire_cape.png", "Sauna Session", "Recovery"),
            ("Wgt", "log weight", "gold_bar.png", "Log Weight", "Health"),
            # Row 6: Soul
            ("Dad", "baby activity", "toy_horsey.png", "Baby Activity", "Soul"),
            ("Dog", "walked the dog", "amulet_of_power.png", "Dog Walk", "Soul"),
            ("Serve", "service", "holy_wrench.png", "Service", "Soul"),
            ("Brave", "courage", "berserker_ring.png", "Courage", "Soul"),
            # Row 7: Meta
            ("Rest", "rest day", "agility.png", "Rest Day", "Health"),
            ("Stats", "skill status", "coins.png", "Skill Status", "Meta"),
            ("XP", "what's my XP", "quest_cape.png", "XP Summary", "Meta"),
            ("Status", "my status", "attack.png", "Health Status", "Meta"),
        ]

        # Grid with fixed 55px slots (fits 4 across in ~240px width)
        self.inv_grid = ctk.CTkFrame(self.inv_frame, fg_color="transparent")
        self.inv_grid.pack(expand=True)

        slot_size = 55
        sprite_size = 40

        for i, slot_data in enumerate(self.inventory_slots):
            label, cmd, sprite, full_name, category = slot_data
            row, col = i // 4, i % 4
            slot = self._make_square_slot(
                self.inv_grid, label, cmd, sprite, slot_size, sprite_size,
                full_name=full_name, category=category
            )
            slot.grid(row=row, column=col, padx=2, pady=2)

    def _make_square_slot(self, parent, label, command, sprite_file, size, sprite_size,
                          full_name=None, category=None):
        """Create a fixed-size square inventory slot with tooltip."""
        slot = ctk.CTkFrame(
            parent, fg_color=OSRS["slot_bg"],
            width=size, height=size,
            corner_radius=0, border_width=1, border_color=OSRS["slot_border"]
        )
        slot.pack_propagate(False)

        # Load sprite
        sprite_img = self._load_sprite(sprite_file, (sprite_size, sprite_size)) if sprite_file else None

        # Create click handler with full_name for undo
        def make_click_handler(s, c, fn):
            return lambda e: self._on_slot_click(s, c, fn)

        click_handler = make_click_handler(slot, command, full_name)

        if sprite_img:
            img_lbl = ctk.CTkLabel(slot, image=sprite_img, text="")
            img_lbl.place(relx=0.5, rely=0.5, anchor="center")
            img_lbl.bind("<Button-1>", click_handler)
        else:
            lbl = ctk.CTkLabel(slot, text=label,
                font=ctk.CTkFont(size=9, weight="bold"), text_color=OSRS["gold"])
            lbl.place(relx=0.5, rely=0.5, anchor="center")
            lbl.bind("<Button-1>", click_handler)

        slot.bind("<Button-1>", click_handler)

        # Add inventory tooltip if metadata provided
        if full_name and category:
            self._bind_inventory_tooltip(slot, full_name, command, category)

        return slot

    def _build_skills_panel(self):
        """Build 12-skill (4x3) virtues grid with DYNAMIC sizing that fills space."""
        self.skills_frame = ctk.CTkFrame(self.inv_content, fg_color="transparent")

        # 12 Virtues across 3 domains
        skills = [
            # BODY (Row 1)
            ("STR", "Strength", "strength.png", 1, 0),
            ("END", "Endurance", "defence.png", 1, 0),
            ("MOB", "Mobility", "agility.png", 1, 0),
            ("NUT", "Nutrition", "hitpoints.png", 1, 0),
            # MIND (Row 2)
            ("FOC", "Focus", "focus_skill.png", 1, 0),
            ("LRN", "Learning", "learn_skill.png", 1, 0),
            ("REF", "Reflection", "reflect_skill.png", 1, 0),
            ("CRE", "Creation", "create_skill.png", 1, 0),
            # SOUL (Row 3)
            ("PRS", "Presence", "presence_skill.png", 1, 0),
            ("SRV", "Service", "service_skill.png", 1, 0),
            ("CRG", "Courage", "courage_skill.png", 1, 0),
            ("CON", "Consistency", "consistency_skill.png", 1, 0),
        ]

        # Domain headers and colors
        domains = ["BODY", "MIND", "SOUL"]
        domain_colors = [OSRS["orb_red"], OSRS["orb_blue"], OSRS["gold_dark"]]

        # Configure grid for dynamic sizing
        for col in range(4):
            self.skills_frame.columnconfigure(col, weight=1)

        row_idx = 0
        for domain_idx, domain in enumerate(domains):
            # Domain label (minimal height)
            self.skills_frame.rowconfigure(row_idx, weight=0)
            domain_lbl = ctk.CTkLabel(
                self.skills_frame, text=f"─ {domain} ─",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=domain_colors[domain_idx]
            )
            domain_lbl.grid(row=row_idx, column=0, columnspan=4, pady=(4, 1), sticky="ew")
            row_idx += 1

            # Skill row (expandable)
            self.skills_frame.rowconfigure(row_idx, weight=1)

            # 4 skills per domain - dynamic size cards
            for col in range(4):
                skill_idx = domain_idx * 4 + col
                abbrev, name, sprite, level, xp = skills[skill_idx]
                skill_card = self._make_dynamic_skill_card(
                    self.skills_frame, abbrev, name, sprite, level, xp
                )
                skill_card.grid(row=row_idx, column=col, padx=2, pady=2, sticky="nsew")

            row_idx += 1

    def _make_dynamic_skill_card(self, parent, abbrev, name, sprite, level, xp):
        """Create skill card that fills its cell (for dynamic sizing)."""
        card = ctk.CTkFrame(
            parent, fg_color=OSRS["slot_bg"],
            corner_radius=0, border_width=1, border_color=OSRS["slot_border"]
        )

        # Store skill data
        card.skill_name = name
        card.skill_xp = xp
        card.skill_level = level

        # Icon (centered at top, larger for visibility)
        sprite_img = self._load_sprite(sprite, (32, 32))
        if sprite_img:
            icon = ctk.CTkLabel(card, image=sprite_img, text="")
            icon.pack(pady=(6, 0))
        else:
            abbrev_lbl = ctk.CTkLabel(card, text=abbrev,
                font=ctk.CTkFont(size=10, weight="bold"), text_color=OSRS["gold"])
            abbrev_lbl.pack(pady=(6, 0))

        # Level number (prominent, centered)
        level_lbl = ctk.CTkLabel(card, text=str(level),
            font=ctk.CTkFont(size=14, weight="bold"), text_color=OSRS["text_white"])
        level_lbl.pack()

        # XP progress bar
        xp_bar = ctk.CTkProgressBar(card, width=45, height=4,
            progress_color=OSRS["orb_green"], fg_color=OSRS["bg_dark"])
        xp_bar.pack(pady=(2, 6))
        xp_bar.set(0.3)  # Demo value

        # Bind tooltip to ENTIRE card
        self._bind_skill_tooltip(card, name, level, xp)

        return card

    def _build_protocols_panel(self):
        """Build Protocols tab - launch interactive protocols in main window."""
        self.protocols_frame = ctk.CTkFrame(self.inv_content, fg_color="transparent")

        # Header
        header = ctk.CTkLabel(
            self.protocols_frame, text="─ PROTOCOLS ─",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=OSRS["gold"]
        )
        header.pack(pady=(4, 2))

        # Protocol launcher buttons
        protocols_list = ctk.CTkFrame(
            self.protocols_frame, fg_color=OSRS["slot_bg"],
            corner_radius=0, border_width=1, border_color=OSRS["slot_border"]
        )
        protocols_list.pack(fill="both", expand=True, padx=2, pady=2)

        # Protocol definitions: (name, icon/emoji, command, description, domain_color)
        protocols = [
            ("Start Workout", "⚔", "start workout", "Strength A/B/C or Zone 2", OSRS["orb_red"]),
            ("Morning Routine", "🌅", "start routine", "18-min ATLAS Protocol", OSRS["gold_dark"]),
            ("Seneca Reflection", "📖", "start reflection", "Stoic evening review", OSRS["orb_blue"]),
            ("Baseline Test", "🧪", "start baseline", "Assessment protocol", OSRS["orb_green"]),
            ("Deep Focus", "🎯", "start focus", "Pomodoro + device-free", OSRS["orb_blue"]),
            ("Daily Quests", "📜", "show quests", "View today's tasks", OSRS["gold"]),
        ]

        for proto_name, icon, command, desc, color in protocols:
            self._make_protocol_button(protocols_list, proto_name, icon, command, desc, color)

        # Quick stats at bottom
        stats_frame = ctk.CTkFrame(self.protocols_frame, fg_color=OSRS["panel_dark"], height=32)
        stats_frame.pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(
            stats_frame, text="Today: 2 completed",
            font=ctk.CTkFont(size=9), text_color=OSRS["text_muted"]
        ).pack(side="left", padx=6, pady=4)

        ctk.CTkLabel(
            stats_frame, text="Streak: 14 days",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=OSRS["orb_green"]
        ).pack(side="right", padx=6, pady=4)

    def _make_protocol_button(self, parent, name, icon, command, desc, color):
        """Create a protocol launcher button."""
        btn_frame = ctk.CTkFrame(parent, fg_color=OSRS["panel_dark"],
            corner_radius=4, border_width=1, border_color=OSRS["slot_border"])
        btn_frame.pack(fill="x", padx=4, pady=3)

        # Icon
        icon_lbl = ctk.CTkLabel(btn_frame, text=icon, font=ctk.CTkFont(size=18),
            text_color=color, width=30)
        icon_lbl.pack(side="left", padx=(8, 4), pady=6)

        # Text container
        text_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True, pady=4)

        name_lbl = ctk.CTkLabel(text_frame, text=name,
            font=ctk.CTkFont(size=11, weight="bold"), text_color=color, anchor="w")
        name_lbl.pack(fill="x")

        desc_lbl = ctk.CTkLabel(text_frame, text=desc,
            font=ctk.CTkFont(size=8), text_color=OSRS["text_muted"], anchor="w")
        desc_lbl.pack(fill="x")

        # Arrow indicator
        arrow = ctk.CTkLabel(btn_frame, text="▶", font=ctk.CTkFont(size=10),
            text_color=OSRS["text_muted"], width=20)
        arrow.pack(side="right", padx=8)

        # Click handler - launches protocol
        def on_click(e):
            self._launch_protocol(command, name)
            # Visual feedback
            btn_frame.configure(fg_color=OSRS["slot_bg"])
            self.after(150, lambda: btn_frame.configure(fg_color=OSRS["panel_dark"]))

        # Bind to all elements
        for widget in [btn_frame, icon_lbl, text_frame, name_lbl, desc_lbl, arrow]:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", lambda e: btn_frame.configure(fg_color=OSRS["slot_bg"]))
            widget.bind("<Leave>", lambda e: btn_frame.configure(fg_color=OSRS["panel_dark"]))

    def _launch_protocol(self, command, name):
        """Launch a protocol - send command and update main window."""
        # Special handling for workout - show selection menu
        if command == "start workout":
            self._show_workout_menu()
            return

        # Special handling for reflection - show modes
        if command == "start reflection":
            self._show_reflection_menu()
            return

        # Send the voice command to bridge
        self._send_text_command(command)

        # Update main window with clean display name (remove "Start" prefix for display)
        display_name = name.replace("Start ", "").replace("start ", "")
        self.voice_instruction.configure(text=f"Starting {display_name}...")
        self.status_bar.configure(text=f"Protocol: {display_name}", text_color=OSRS["gold"])

    def _show_workout_menu(self):
        """Show workout selection dialog."""
        menu = ctk.CTkToplevel(self)
        menu.title("Select Workout")
        menu.geometry("280x360")
        menu.transient(self)
        menu.grab_set()

        # Center on parent
        menu.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 280) // 2
        y = self.winfo_y() + (self.winfo_height() - 360) // 2
        menu.geometry(f"+{x}+{y}")
        menu.configure(fg_color=OSRS["bg_dark"])

        ctk.CTkLabel(menu, text="─ SELECT WORKOUT ─",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OSRS["gold"]).pack(pady=(15, 10))

        # Workout options
        workouts = [
            ("Strength A", "start workout", OSRS["orb_red"], "Mon - Upper Focus"),
            ("Strength B", "start strength b", OSRS["orb_red"], "Wed - Lower Focus"),
            ("Strength C", "start strength c", OSRS["orb_red"], "Fri - Full Body"),
            ("Zone 2 (Bike)", "start zone 2 bike", OSRS["orb_green"], "30-45 min steady"),
            ("Zone 2 (Walk/Ruck)", "start zone 2 walk", OSRS["orb_green"], "45-60 min outdoor"),
            ("HIIT (Post-GATE)", "start hiit", OSRS["text_muted"], "Requires GATE 1 clearance"),
        ]

        for wo_name, wo_cmd, color, desc in workouts:
            btn_frame = ctk.CTkFrame(menu, fg_color=OSRS["panel_dark"],
                corner_radius=4, height=45)
            btn_frame.pack(fill="x", padx=15, pady=3)
            btn_frame.pack_propagate(False)

            ctk.CTkLabel(btn_frame, text=wo_name,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=color).pack(anchor="w", padx=10, pady=(6,0))
            ctk.CTkLabel(btn_frame, text=desc,
                font=ctk.CTkFont(size=8),
                text_color=OSRS["text_muted"]).pack(anchor="w", padx=10)

            def make_click(cmd, n, m):
                def handler(e):
                    self._send_text_command(cmd)
                    self.voice_instruction.configure(text=f"Starting {n}...")
                    self.status_bar.configure(text=f"Workout: {n}", text_color=OSRS["gold"])
                    m.destroy()
                return handler

            btn_frame.bind("<Button-1>", make_click(wo_cmd, wo_name, menu))
            for child in btn_frame.winfo_children():
                child.bind("<Button-1>", make_click(wo_cmd, wo_name, menu))

        # Cancel button
        ctk.CTkButton(menu, text="Cancel", width=100, height=28,
            fg_color=OSRS["text_muted"], hover_color=OSRS["panel_dark"],
            text_color=OSRS["text_white"], corner_radius=4,
            command=menu.destroy).pack(pady=(15, 10))

    def _show_reflection_menu(self):
        """Show reflection mode selection."""
        menu = ctk.CTkToplevel(self)
        menu.title("Seneca Trial")
        menu.geometry("260x200")
        menu.transient(self)
        menu.grab_set()

        menu.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 260) // 2
        y = self.winfo_y() + (self.winfo_height() - 200) // 2
        menu.geometry(f"+{x}+{y}")
        menu.configure(fg_color=OSRS["bg_dark"])

        ctk.CTkLabel(menu, text="─ SENECA TRIAL ─",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=OSRS["gold"]).pack(pady=(15, 10))

        modes = [
            ("Full Reflection", "start reflection", "~10 min - 60 XP"),
            ("Quick Review", "quick reflection", "~3 min - 35 XP"),
        ]

        for mode_name, cmd, desc in modes:
            btn = ctk.CTkButton(menu, text=f"{mode_name}\n{desc}",
                width=200, height=50,
                font=ctk.CTkFont(size=11),
                fg_color=OSRS["panel_dark"], hover_color=OSRS["slot_bg"],
                text_color=OSRS["orb_blue"], corner_radius=4,
                command=lambda c=cmd, n=mode_name, m=menu: self._start_reflection_mode(c, n, m))
            btn.pack(pady=5)

        ctk.CTkButton(menu, text="Cancel", width=100, height=26,
            fg_color=OSRS["text_muted"], hover_color=OSRS["panel_dark"],
            corner_radius=4, command=menu.destroy).pack(pady=(10, 10))

    def _start_reflection_mode(self, cmd, name, menu):
        """Start a reflection mode."""
        self._send_text_command(cmd)
        self.voice_instruction.configure(text=f"Starting {name}...")
        self.status_bar.configure(text=f"Reflection: {name}", text_color=OSRS["orb_blue"])
        menu.destroy()

    def _build_settings_panel(self):
        """Build Settings tab - preferences and integrations."""
        self.settings_frame = ctk.CTkFrame(self.inv_content, fg_color="transparent")

        # Header
        header = ctk.CTkLabel(
            self.settings_frame, text="─ SETTINGS ─",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=OSRS["gold"]
        )
        header.pack(pady=(4, 2))

        # Scrollable settings list
        settings_list = ctk.CTkScrollableFrame(
            self.settings_frame, fg_color=OSRS["slot_bg"],
            corner_radius=0, border_width=1, border_color=OSRS["slot_border"]
        )
        settings_list.pack(fill="both", expand=True, padx=2, pady=2)

        # Settings sections
        sections = [
            ("INTEGRATIONS", [
                ("Garmin Sync", "garmin_sync", True, "Auto-sync health data"),
                ("Voice Enabled", "voice_enabled", True, "Enable voice commands"),
            ]),
            ("NOTIFICATIONS", [
                ("Workout Reminders", "workout_remind", True, "Daily workout alerts"),
                ("Supplement Alerts", "supp_remind", False, "Timing reminders"),
            ]),
            ("DISPLAY", [
                ("Dark Mode", "dark_mode", True, "OSRS aesthetic"),
                ("Show XP Popups", "xp_popups", True, "XP award notifications"),
            ]),
        ]

        for section_name, settings in sections:
            # Section header
            section_lbl = ctk.CTkLabel(settings_list, text=section_name,
                font=ctk.CTkFont(size=9, weight="bold"), text_color=OSRS["gold_dark"])
            section_lbl.pack(anchor="w", padx=8, pady=(8, 2))

            for setting_name, setting_key, default_val, tooltip in settings:
                self._make_setting_toggle(settings_list, setting_name, setting_key, default_val, tooltip)

        # Voice selection section
        voice_section = ctk.CTkLabel(settings_list, text="VOICE",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=OSRS["gold_dark"])
        voice_section.pack(anchor="w", padx=8, pady=(8, 2))

        voice_row = ctk.CTkFrame(settings_list, fg_color="transparent", height=40)
        voice_row.pack(fill="x", padx=4, pady=2)

        ctk.CTkLabel(voice_row, text="TTS Voice",
            font=ctk.CTkFont(size=10), text_color=OSRS["text"]).pack(side="left", padx=8)

        # Voice options: Kokoro (bm_lewis, bf_emma) and Qwen (jeremy_irons, thomas_shelby)
        voice_options = [
            "Jeremy Irons",      # jeremy_irons (Qwen3-TTS clone)
            "Thomas Shelby",     # thomas_shelby (Qwen3-TTS clone)
            "Lewis (British M)", # bm_lewis (Kokoro)
            "Emma (British F)",  # bf_emma (Kokoro)
        ]
        self._voice_map = {
            "Jeremy Irons": "jeremy_irons",
            "Thomas Shelby": "thomas_shelby",
            "Lewis (British M)": "bm_lewis",
            "Emma (British F)": "bf_emma",
        }
        self._voice_map_reverse = {v: k for k, v in self._voice_map.items()}

        self.voice_dropdown = ctk.CTkComboBox(
            voice_row, values=voice_options, width=130, height=26,
            font=ctk.CTkFont(size=9),
            fg_color=OSRS["slot_bg"], border_color=OSRS["slot_border"],
            button_color=OSRS["panel_dark"], button_hover_color=OSRS["slot_bg"],
            dropdown_fg_color=OSRS["panel_dark"], dropdown_hover_color=OSRS["slot_bg"],
            text_color=OSRS["gold"], dropdown_text_color=OSRS["text"],
            command=self._on_voice_change
        )
        self.voice_dropdown.pack(side="right", padx=8)

        # Load current voice preference
        current_voice = self._load_voice_preference()
        display_name = self._voice_map_reverse.get(current_voice, "Lewis (British M)")
        self.voice_dropdown.set(display_name)

        # Version info at bottom
        version_frame = ctk.CTkFrame(self.settings_frame, fg_color=OSRS["panel_dark"], height=28)
        version_frame.pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(
            version_frame, text="ATLAS v2.0",
            font=ctk.CTkFont(size=9), text_color=OSRS["text_muted"]
        ).pack(side="left", padx=6, pady=4)

        ctk.CTkLabel(
            version_frame, text="Jan 2026",
            font=ctk.CTkFont(size=9), text_color=OSRS["text_muted"]
        ).pack(side="right", padx=6, pady=4)

    def _make_setting_toggle(self, parent, name, key, default, tooltip):
        """Create a setting toggle row."""
        row = ctk.CTkFrame(parent, fg_color="transparent", height=30)
        row.pack(fill="x", padx=4, pady=1)

        # Setting name
        name_lbl = ctk.CTkLabel(row, text=name,
            font=ctk.CTkFont(size=10), text_color=OSRS["text"], anchor="w")
        name_lbl.pack(side="left", padx=8)

        # Toggle switch
        toggle = ctk.CTkSwitch(row, text="", width=40, height=20,
            fg_color=OSRS["slot_border"], progress_color=OSRS["orb_green"],
            button_color=OSRS["text_white"], button_hover_color=OSRS["gold"])
        toggle.pack(side="right", padx=8)
        if default:
            toggle.select()

        # Store reference
        if not hasattr(self, 'settings_toggles'):
            self.settings_toggles = {}
        self.settings_toggles[key] = toggle

    def _build_quests_panel(self):
        """Build Quests tab - daily tasks that award XP."""
        self.quests_frame = ctk.CTkFrame(self.inv_content, fg_color="transparent")

        header = ctk.CTkLabel(self.quests_frame, text="─ DAILY QUESTS ─",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=OSRS["gold"])
        header.pack(pady=(4, 2))

        quest_list = ctk.CTkFrame(self.quests_frame, fg_color=OSRS["slot_bg"],
            corner_radius=0, border_width=1, border_color=OSRS["slot_border"])
        quest_list.pack(fill="both", expand=True, padx=2, pady=2)

        # Daily quests with XP rewards
        quests = [
            ("Complete Morning Routine", 50, "body", False, "start routine"),
            ("Log All 3 Meals", 30, "body", False, "log meal"),
            ("Walk the Dog (AM)", 25, "soul", False, "walked the dog"),
            ("Walk the Dog (PM)", 25, "soul", False, "walked the dog"),
            ("Baby Activity", 40, "soul", False, "baby activity"),
            ("30 Min Deep Work", 40, "mind", False, "start focus"),
            ("Take Supplements", 20, "body", True, "took my supps"),
            ("Workout", 60, "body", False, "start workout"),
        ]

        for name, xp, domain, done, cmd in quests:
            self._make_quest_row(quest_list, name, xp, domain, done, cmd)

        # Summary
        summary = ctk.CTkFrame(self.quests_frame, fg_color=OSRS["panel_dark"], height=26)
        summary.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(summary, text="1/8 Complete", font=ctk.CTkFont(size=9),
            text_color=OSRS["text_muted"]).pack(side="left", padx=6, pady=2)
        ctk.CTkLabel(summary, text="+20 XP", font=ctk.CTkFont(size=9, weight="bold"),
            text_color=OSRS["orb_green"]).pack(side="right", padx=6, pady=2)

    def _make_quest_row(self, parent, name, xp, domain, done, cmd):
        """Create a quest row item with click-to-complete functionality."""
        colors = {"body": OSRS["orb_red"], "mind": OSRS["orb_blue"], "soul": OSRS["gold_dark"]}
        color = colors.get(domain, OSRS["text"])

        row = ctk.CTkFrame(parent, fg_color="transparent", height=26)
        row.pack(fill="x", pady=1)

        # Track completion state
        quest_state = {"done": done, "name": name, "xp": xp, "domain": domain, "cmd": cmd}

        # Status indicator (checkbox style)
        status = ctk.CTkLabel(row, text="✓" if done else "○",
            font=ctk.CTkFont(size=11),
            text_color=OSRS["orb_green"] if done else OSRS["text_muted"], width=18)
        status.pack(side="left", padx=(4, 2))

        # Quest name (with strikethrough if done)
        name_text = f"̶{name}̶" if done else name  # Unicode strikethrough
        name_lbl = ctk.CTkLabel(row, text=name,
            font=ctk.CTkFont(size=9, overstrike=done),
            text_color=OSRS["text_muted"] if done else color, anchor="w")
        name_lbl.pack(side="left", fill="x", expand=True)

        # XP reward
        xp_lbl = ctk.CTkLabel(row, text=f"✓{xp}" if done else f"+{xp}",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=OSRS["orb_green"] if done else OSRS["gold"], width=35)
        xp_lbl.pack(side="right", padx=4)

        # Store references for updating
        row._quest_widgets = {"status": status, "name": name_lbl, "xp": xp_lbl, "state": quest_state, "color": color}

        # Click to toggle completion
        def on_click(e):
            is_done = quest_state["done"]
            new_done = not is_done
            quest_state["done"] = new_done

            # Update visual state
            status.configure(
                text="✓" if new_done else "○",
                text_color=OSRS["orb_green"] if new_done else OSRS["text_muted"]
            )
            name_lbl.configure(
                font=ctk.CTkFont(size=9, overstrike=new_done),
                text_color=OSRS["text_muted"] if new_done else color
            )
            xp_lbl.configure(
                text=f"✓{xp}" if new_done else f"+{xp}",
                text_color=OSRS["orb_green"] if new_done else OSRS["gold"]
            )

            # Record action for undo
            self._record_action("quest_toggle", {"row": row, "was_done": is_done, "name": name})

            # Visual feedback
            row.configure(fg_color=OSRS["slot_bg"])
            self.after(150, lambda: row.configure(fg_color="transparent"))

            # Optionally send command to server if completing
            if new_done:
                self._send_text_command(cmd)

        for w in [row, status, name_lbl, xp_lbl]:
            w.bind("<Button-1>", on_click)

    def _build_equipment_panel(self):
        """Build Equipment tab - worn items/active buffs (placeholder)."""
        self.equipment_frame = ctk.CTkFrame(self.inv_content, fg_color="transparent")

        header = ctk.CTkLabel(self.equipment_frame, text="─ EQUIPMENT ─",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=OSRS["gold"])
        header.pack(pady=(4, 2))

        # Placeholder - equipment slots would go here
        content = ctk.CTkFrame(self.equipment_frame, fg_color=OSRS["slot_bg"],
            corner_radius=0, border_width=1, border_color=OSRS["slot_border"])
        content.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(content, text="Coming Soon\n\nActive buffs and\nequipment status",
            font=ctk.CTkFont(size=11), text_color=OSRS["text_muted"]).pack(expand=True)

    def _build_prayer_panel(self):
        """Build Prayer tab - meditation/focus modes."""
        self.prayer_frame = ctk.CTkFrame(self.inv_content, fg_color="transparent")

        header = ctk.CTkLabel(self.prayer_frame, text="─ FOCUS MODES ─",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=OSRS["gold"])
        header.pack(pady=(4, 2))

        content = ctk.CTkFrame(self.prayer_frame, fg_color=OSRS["slot_bg"],
            corner_radius=0, border_width=1, border_color=OSRS["slot_border"])
        content.pack(fill="both", expand=True, padx=2, pady=2)

        # Focus mode toggles
        modes = [
            ("🧘", "Deep Focus", "Device-free mode", "start focus"),
            ("📵", "Do Not Disturb", "Silence notifications", "dnd mode"),
            ("🎯", "Pomodoro", "25/5 work cycles", "start pomodoro"),
            ("🌙", "Wind Down", "Evening routine", "start wind down"),
        ]

        for emoji, name, desc, cmd in modes:
            self._make_mode_toggle(content, emoji, name, desc, cmd)

    def _make_mode_toggle(self, parent, emoji, name, desc, cmd):
        """Create a focus mode toggle button."""
        row = ctk.CTkFrame(parent, fg_color=OSRS["panel_dark"],
            corner_radius=4, border_width=1, border_color=OSRS["slot_border"])
        row.pack(fill="x", padx=4, pady=3)

        icon = ctk.CTkLabel(row, text=emoji, font=ctk.CTkFont(size=16),
            text_color=OSRS["orb_blue"], width=30)
        icon.pack(side="left", padx=(8, 4), pady=4)

        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True, pady=2)

        ctk.CTkLabel(text_frame, text=name, font=ctk.CTkFont(size=10, weight="bold"),
            text_color=OSRS["text"], anchor="w").pack(fill="x")
        ctk.CTkLabel(text_frame, text=desc, font=ctk.CTkFont(size=8),
            text_color=OSRS["text_muted"], anchor="w").pack(fill="x")

        # Toggle switch
        toggle = ctk.CTkSwitch(row, text="", width=36, height=18,
            fg_color=OSRS["slot_border"], progress_color=OSRS["orb_blue"])
        toggle.pack(side="right", padx=8)

    def _bind_skill_tooltip(self, card, name, level, xp):
        """Bind OSRS-style tooltip to ENTIRE skill card area."""
        def show_tooltip(event):
            # Destroy any existing tooltip first
            if hasattr(self, 'tooltip') and self.tooltip:
                try:
                    self.tooltip.destroy()
                except:
                    pass

            # Calculate XP for current and next level (OSRS formula)
            xp_for_level = lambda l: int(sum(int(i + 300 * 2**(i/7)) for i in range(1, l)) / 4) if l > 1 else 0
            current_xp = xp_for_level(level)
            next_xp = xp_for_level(level + 1) if level < 99 else current_xp
            remaining = max(0, next_xp - current_xp)

            # Create tooltip window
            self.tooltip = tk.Toplevel(self)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+15}")
            self.tooltip.configure(bg=OSRS["bg_dark"])

            # Tooltip content (OSRS style)
            frame = tk.Frame(self.tooltip, bg=OSRS["bg_dark"], bd=2, relief="solid")
            frame.pack()

            tk.Label(frame, text=name, font=("Arial", 11, "bold"),
                    fg=OSRS["gold"], bg=OSRS["bg_dark"]).pack(anchor="w", padx=6, pady=(4,0))
            tk.Label(frame, text=f"Level: {level}", font=("Arial", 10),
                    fg=OSRS["text_white"], bg=OSRS["bg_dark"]).pack(anchor="w", padx=6)
            tk.Label(frame, text=f"XP: {current_xp:,}", font=("Arial", 10),
                    fg=OSRS["text_white"], bg=OSRS["bg_dark"]).pack(anchor="w", padx=6)
            if level < 99:
                tk.Label(frame, text=f"Next: {next_xp:,}", font=("Arial", 10),
                        fg=OSRS["text_muted"], bg=OSRS["bg_dark"]).pack(anchor="w", padx=6)
                tk.Label(frame, text=f"Remaining: {remaining:,}", font=("Arial", 10),
                        fg=OSRS["orb_green"], bg=OSRS["bg_dark"]).pack(anchor="w", padx=6, pady=(0,4))

        def hide_tooltip(event):
            if hasattr(self, 'tooltip') and self.tooltip:
                try:
                    self.tooltip.destroy()
                except:
                    pass
                self.tooltip = None

        # Bind to card and ALL children recursively
        def bind_recursive(widget):
            widget.bind("<Enter>", show_tooltip)
            widget.bind("<Leave>", hide_tooltip)
            for child in widget.winfo_children():
                bind_recursive(child)

        bind_recursive(card)

    def _bind_inventory_tooltip(self, slot, name, command, category):
        """Bind OSRS-style tooltip to inventory slot."""
        # Category colors
        cat_colors = {
            "Workout": OSRS["orb_red"],
            "Supplement": OSRS["orb_green"],
            "Recovery": OSRS["orb_blue"],
            "Meal": OSRS["gold_dark"],
            "Mind": OSRS["orb_blue"],
            "Protocol": OSRS["gold"],
            "Soul": OSRS["gold_dark"],
            "Health": OSRS["orb_green"],
            "Meta": OSRS["text_muted"],
        }
        color = cat_colors.get(category, OSRS["text"])

        def show_tooltip(event):
            # Destroy any existing tooltip first
            if hasattr(self, 'inv_tooltip') and self.inv_tooltip:
                try:
                    self.inv_tooltip.destroy()
                except:
                    pass

            # Create tooltip window
            self.inv_tooltip = tk.Toplevel(self)
            self.inv_tooltip.wm_overrideredirect(True)
            self.inv_tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+15}")
            self.inv_tooltip.configure(bg=OSRS["bg_dark"])

            # Tooltip content
            frame = tk.Frame(self.inv_tooltip, bg=OSRS["bg_dark"], bd=2, relief="solid")
            frame.pack()

            tk.Label(frame, text=name, font=("Arial", 11, "bold"),
                    fg=color, bg=OSRS["bg_dark"]).pack(anchor="w", padx=6, pady=(4,0))
            tk.Label(frame, text=f"Category: {category}", font=("Arial", 9),
                    fg=OSRS["text_muted"], bg=OSRS["bg_dark"]).pack(anchor="w", padx=6)
            tk.Label(frame, text=f'Say: "{command}"', font=("Arial", 10),
                    fg=OSRS["orb_green"], bg=OSRS["bg_dark"]).pack(anchor="w", padx=6, pady=(0,4))

        def hide_tooltip(event):
            if hasattr(self, 'inv_tooltip') and self.inv_tooltip:
                try:
                    self.inv_tooltip.destroy()
                except:
                    pass
                self.inv_tooltip = None

        # Bind to slot and ALL children recursively
        def bind_recursive(widget):
            widget.bind("<Enter>", show_tooltip)
            widget.bind("<Leave>", hide_tooltip)
            for child in widget.winfo_children():
                bind_recursive(child)

        bind_recursive(slot)

    def _on_slot_click(self, slot, command, full_name=None):
        """Handle inventory slot click."""
        # Record for undo
        self._record_action("inventory_click", {"name": full_name or command, "command": command})

        # Send command
        self._send_text_command(command)

        # Visual feedback
        slot.configure(fg_color=OSRS["border_light"])
        self.after(100, lambda: slot.configure(fg_color=OSRS["slot_bg"]))

    def _load_sprite(self, filename, size):
        """Load a sprite image from WSL path."""
        if not filename:
            return None
        if not PIL_AVAILABLE:
            print(f"[Sprite] PIL not available, skipping {filename}")
            return None
        try:
            sprite_path = WSL_PATH / "assets" / "sprites" / filename
            print(f"[Sprite] Loading: {sprite_path}")

            if not sprite_path.exists():
                print(f"[Sprite] NOT FOUND: {sprite_path}")
                return None

            # Read file as bytes first (helps with UNC paths on Windows)
            with open(str(sprite_path), 'rb') as f:
                img = Image.open(f)
                img.load()  # Force load while file is open
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                result = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                print(f"[Sprite] SUCCESS: {filename}")
                return result
        except Exception as e:
            print(f"[Sprite] ERROR loading {filename}: {type(e).__name__}: {e}")
        return None

    def _send_text_command(self, cmd):
        """Send text command to bridge."""
        try:
            BRIDGE_DIR.mkdir(exist_ok=True)
            (BRIDGE_DIR / "text_command.txt").write_text(cmd)
            (BRIDGE_DIR / "command.txt").write_text("TEXT_COMMAND")
            print(f"[UI] Sent: {cmd}")
        except Exception as e:
            print(f"[UI] Error: {e}")

    def _load_voice_preference(self) -> str:
        """Load voice preference from bridge directory."""
        try:
            voice_file = BRIDGE_DIR / "voice.txt"
            if voice_file.exists():
                return voice_file.read_text().strip()
        except Exception:
            pass
        return "bm_lewis"  # Default

    def _on_voice_change(self, choice):
        """Handle voice selection change."""
        voice_id = self._voice_map.get(choice, "bm_lewis")
        try:
            BRIDGE_DIR.mkdir(exist_ok=True)
            (BRIDGE_DIR / "voice.txt").write_text(voice_id)
            print(f"[UI] Voice changed to: {voice_id}")
        except Exception as e:
            print(f"[UI] Error saving voice: {e}")

    def _send_workout_command(self, cmd):
        """Send workout control command (PAUSE/SKIP/STOP) to bridge."""
        try:
            BRIDGE_DIR.mkdir(exist_ok=True)
            (BRIDGE_DIR / "command.txt").write_text(cmd)
            print(f"[UI] Workout command: {cmd}")
        except Exception as e:
            print(f"[UI] Error: {e}")

    def _toggle_pause(self):
        """Toggle pause/resume for workout."""
        if self._is_paused:
            self._send_workout_command("RESUME_ROUTINE")
        else:
            self._send_workout_command("PAUSE_ROUTINE")
        # State will be updated from timer data on next poll

    def _record_action(self, action_type, data):
        """Record an action for undo functionality."""
        self._action_history.append({"type": action_type, "data": data, "time": time.time()})
        if len(self._action_history) > self._max_history:
            self._action_history.pop(0)
        # Update undo button state
        if hasattr(self, 'undo_btn'):
            self.undo_btn.configure(state="normal", text_color=OSRS["gold"])

    def _undo_last_action(self):
        """Undo the last recorded action."""
        if not self._action_history:
            return

        action = self._action_history.pop()
        action_type = action["type"]
        data = action["data"]

        if action_type == "quest_toggle":
            # Revert quest completion state
            row = data["row"]
            was_done = data["was_done"]
            widgets = row._quest_widgets
            state = widgets["state"]
            color = widgets["color"]

            state["done"] = was_done
            widgets["status"].configure(
                text="✓" if was_done else "○",
                text_color=OSRS["orb_green"] if was_done else OSRS["text_muted"]
            )
            widgets["name"].configure(
                font=ctk.CTkFont(size=9, overstrike=was_done),
                text_color=OSRS["text_muted"] if was_done else color
            )
            widgets["xp"].configure(
                text=f"✓{state['xp']}" if was_done else f"+{state['xp']}",
                text_color=OSRS["orb_green"] if was_done else OSRS["gold"]
            )
            # Visual feedback
            row.configure(fg_color=OSRS["orb_yellow"])
            self.after(200, lambda: row.configure(fg_color="transparent"))

        elif action_type == "inventory_click":
            # Just show that it was undone
            self.status_bar.configure(text=f"Undid: {data.get('name', 'action')}")

        # Update undo button if no more history
        if not self._action_history and hasattr(self, 'undo_btn'):
            self.undo_btn.configure(state="disabled", text_color=OSRS["text_muted"])

    def _bind_keys(self):
        """Bind keyboard shortcuts."""
        self.bind("<KeyPress-space>", self._on_space_press)
        self.bind("<KeyRelease-space>", self._on_space_release)
        self.bind("<FocusOut>", self._on_focus_lost)

    def _on_focus_lost(self, event):
        """Stop recording if focus lost."""
        if self.recording:
            self._on_space_release(None)

    def _set_state(self, state):
        """Update state display."""
        self.current_state = state
        texts = {"idle": "Ready", "listening": "● Listening...",
                 "processing": "● Processing...", "speaking": "● Speaking..."}
        self.status_bar.configure(
            text=texts.get(state, "Ready"),
            text_color=STATE_COLORS.get(state, OSRS["text_muted"])
        )

    def _clear_transcript(self):
        """Clear transcript."""
        self.transcript_history = []
        self.last_exchange_hash = ""
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.configure(state="disabled")
        self.exchange_count.configure(text="(0)")

    def _start_polling(self):
        """Start status polling."""
        self._poll_status()

    def _poll_status(self):
        """Poll status files and update UI."""
        status_file = BRIDGE_DIR / "session_status.json"
        try:
            if status_file.exists():
                data = json.loads(status_file.read_text())
                cost = data.get('session_cost', 0)
                self.cost_label.configure(text=f"${cost:.2f}")

                gpu = data.get("gpu", "?")
                color = OSRS["orb_green"] if gpu == "CUDA" else OSRS["warning"]
                self.gpu_status.configure(text=f"GPU:{gpu}", text_color=color)

                # Check for timer data and update workout display
                timer = data.get("timer", {})
                if timer.get("active"):
                    self._update_workout_display(timer)
                else:
                    self._hide_workout_display()

                # Check for new exchange
                exchange = data.get("last_exchange", {})
                user_text = exchange.get("user", "")
                atlas_text = exchange.get("atlas", "")
                updated_at = data.get("updated_at", "")

                exchange_hash = f"{updated_at}:{user_text[:20] if user_text else ''}"
                if exchange_hash != self.last_exchange_hash and user_text:
                    self.last_exchange_hash = exchange_hash
                    self.transcript_history.append((updated_at, user_text, atlas_text))
                    if len(self.transcript_history) > 20:
                        self.transcript_history = self.transcript_history[-20:]
                    self._update_transcript()

        except Exception as e:
            pass  # Silent fail on poll errors

        self.after(100, self._poll_status)  # Poll faster for smooth timer updates

    def _update_workout_display(self, timer):
        """Update the workout visual display with timer data."""
        # Show workout display, hide voice display
        if not self._workout_display_visible:
            self.voice_display.pack_forget()
            self.workout_display.pack(fill="both", expand=True)
            self._workout_display_visible = True

        # Update section/workout name
        section = timer.get("section_name", "Workout")
        self.workout_section.configure(text=section)

        # Update progress
        ex_idx = timer.get("exercise_idx", 1)
        total_ex = timer.get("total_exercises", 1)
        self.workout_progress.configure(text=f"Exercise {ex_idx} of {total_ex}")

        # Update exercise name
        exercise = timer.get("exercise_name", "")
        self.workout_exercise.configure(text=exercise)

        # Update set/rep info
        current_set = timer.get("current_set", 1)
        total_sets = timer.get("total_sets", 3)
        reps = timer.get("reps")
        weight = timer.get("weight")
        per_side = timer.get("per_side", False)

        set_text = f"Set {current_set} of {total_sets}"
        if reps:
            set_text += f" • {reps} reps"
            if per_side:
                set_text += " each side"
        if weight:
            set_text += f" • {weight}kg"
        self.workout_sets.configure(text=set_text)

        # Update timer
        remaining = timer.get("remaining_seconds", 0)
        duration = timer.get("duration_seconds", 0)

        if remaining > 0 or timer.get("pending_ready"):
            mins = remaining // 60
            secs = remaining % 60
            timer_text = f"{mins}:{secs:02d}" if mins > 0 else f"0:{secs:02d}"
        else:
            timer_text = "READY"

        self.workout_timer.configure(text=timer_text)

        # Timer color based on state
        is_paused = timer.get("is_paused", False)
        pending = timer.get("pending_ready", False)

        if pending:
            self.workout_timer.configure(text_color=OSRS["orb_yellow"])
            self.workout_timer.configure(text="READY?")
        elif is_paused:
            self.workout_timer.configure(text_color=OSRS["orb_yellow"])
        elif remaining <= 10 and remaining > 0:
            self.workout_timer.configure(text_color=OSRS["orb_red"])
        else:
            self.workout_timer.configure(text_color=OSRS["gold"])

        # Progress bar
        if duration > 0:
            progress = (duration - remaining) / duration
            self.workout_timer_bar.set(min(1.0, max(0.0, progress)))
        else:
            self.workout_timer_bar.set(1.0)

        # Form cue
        form_cue = timer.get("form_cue", "")
        if form_cue:
            self.workout_form_cue.configure(text=form_cue)
        else:
            self.workout_form_cue.configure(text="")

        # Next exercise
        next_ex = timer.get("next_exercise", "")
        if next_ex:
            self.workout_next.configure(text=f"Next: {next_ex}")
        else:
            self.workout_next.configure(text="")

        # Button states
        can_skip = timer.get("can_skip", True)
        self.btn_skip.configure(state="normal" if can_skip else "disabled")

        # Pause button text and track state
        self._is_paused = is_paused
        if is_paused:
            self.btn_pause.configure(text="RESUME", fg_color=OSRS["orb_green"])
        else:
            self.btn_pause.configure(text="PAUSE", fg_color=OSRS["orb_yellow"])

    def _hide_workout_display(self):
        """Hide workout display and show default voice display."""
        if self._workout_display_visible:
            self.workout_display.pack_forget()
            self.voice_display.pack(fill="both", expand=True)
            self._workout_display_visible = False

    def _update_transcript(self):
        """Update transcript display."""
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")

        for i, (ts, user, atlas) in enumerate(self.transcript_history):
            if i > 0:
                self.transcript_box.insert("end", "─" * 35 + "\n")
            self.transcript_box.insert("end", f"You: {user}\n")
            self.transcript_box.insert("end", f"ATLAS: {atlas}\n")

        self.exchange_count.configure(text=f"({len(self.transcript_history)})")
        self.transcript_box.see("end")
        self.transcript_box.configure(state="disabled")

    def _start_server(self):
        """Start WSL server."""
        if self.server_process:
            return

        self.server_ready.clear()
        self.status_bar.configure(text="Starting...", text_color=OSRS["warning"])
        self.start_btn.configure(state="disabled")

        if not WSL_PATH.exists():
            self.status_bar.configure(text="ERROR: WSL not accessible", text_color=OSRS["error"])
            self.start_btn.configure(state="normal")
            return

        cmd = (
            "cd /home/squiz/ATLAS && "
            "source /home/squiz/ATLAS/venv/bin/activate && "
            "export ANTHROPIC_API_KEY=\"$(cat /home/squiz/ATLAS/.env | tr -d '\\n')\" && "
            "pgrep -x ollama >/dev/null 2>&1 || { ollama serve >/dev/null 2>&1 & sleep 3; } && "
            "python -u -m atlas.voice.bridge_file_server"
        )

        try:
            self.server_process = subprocess.Popen(
                ["wsl", "-d", "Ubuntu", "bash", "-c", cmd],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            Thread(target=self._monitor_server, daemon=True).start()
        except Exception as e:
            self.status_bar.configure(text=f"ERROR: {e}", text_color=OSRS["error"])
            self.start_btn.configure(state="normal")
            self.server_process = None

    def _monitor_server(self):
        """Monitor server output."""
        if not self.server_process:
            return

        try:
            for line in iter(self.server_process.stdout.readline, ""):
                if not line:
                    break
                line = line.strip()
                print(f"[Server] {line}")

                if "Loading" in line:
                    self.after(0, lambda l=line: self.status_bar.configure(
                        text=l[:40], text_color=OSRS["warning"]))

                if "Components loaded and ready." in line:
                    self.server_ready.set()
                    self.after(0, self._on_server_ready)

            self.after(0, self._on_server_stopped)
        except Exception as e:
            print(f"Monitor error: {e}")
            self.after(0, self._on_server_stopped)

    def _on_server_ready(self):
        """Server ready callback."""
        self.server_status.configure(text="● Online", text_color=OSRS["orb_green"])
        self.status_bar.configure(text="Hold SPACE to speak", text_color=OSRS["text"])
        self.stop_btn.configure(state="normal")

    def _on_server_stopped(self):
        """Server stopped callback."""
        self.server_process = None
        self.server_ready.clear()
        self.server_status.configure(text="● Offline", text_color=OSRS["text_muted"])
        self.status_bar.configure(text="Server stopped", text_color=OSRS["text_muted"])
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def _stop_server(self):
        """Stop server."""
        if not self.server_process:
            return

        self.status_bar.configure(text="Stopping...")
        try:
            BRIDGE_DIR.mkdir(exist_ok=True)
            (BRIDGE_DIR / "command.txt").write_text("QUIT")
        except:
            pass

        try:
            self.server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.server_process.kill()

        self._on_server_stopped()

    def _on_space_press(self, event):
        """Start recording."""
        if not self.server_ready.is_set() or self.recording or self.processing:
            return

        self.recording = True
        self.audio_chunks = []

        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype=np.float32,
                callback=self._audio_callback
            )
            self.stream.start()
            self.recording_indicator.configure(progress_color=OSRS["orb_green"])
            self.recording_indicator.set(1)
            self.voice_instruction.configure(text="Recording...")
            self._set_state("listening")
        except Exception as e:
            self.recording = False
            self.status_bar.configure(text=f"Mic error: {e}", text_color=OSRS["error"])

    def _audio_callback(self, indata, frames, time_info, status):
        """Audio callback."""
        if self.recording:
            self.audio_chunks.append(indata.copy())

    def _on_space_release(self, event):
        """Stop recording and send."""
        if not self.recording:
            return

        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.recording_indicator.set(0)
        self.voice_instruction.configure(text="Processing...")
        self._set_state("processing")

        if self.audio_chunks:
            audio = np.concatenate(self.audio_chunks)
            Thread(target=self._send_audio, args=(audio,), daemon=True).start()
        else:
            self.voice_instruction.configure(text="Hold SPACE to speak")
            self._set_state("idle")

    def _send_audio(self, audio):
        """Send audio to server."""
        self.processing = True

        try:
            self.after(0, lambda: self._set_state("processing"))
            BRIDGE_DIR.mkdir(exist_ok=True)

            # Save audio
            audio.astype(np.float32).tofile(BRIDGE_DIR / "audio_in.raw")
            time.sleep(0.1)

            # Send command
            status_file = BRIDGE_DIR / "status.txt"
            if status_file.exists():
                status_file.unlink()
            (BRIDGE_DIR / "command.txt").write_text("PROCESS")

            # Wait for response
            start = time.time()
            while time.time() - start < 60:
                if status_file.exists() and status_file.read_text().strip() == "DONE":
                    break
                time.sleep(0.1)
            else:
                self.after(0, lambda: self.status_bar.configure(
                    text="Timeout", text_color=OSRS["error"]))
                return

            # Play response
            audio_out = BRIDGE_DIR / "audio_out.raw"
            if audio_out.exists():
                metadata = BRIDGE_DIR / "metadata.txt"
                rate = 24000
                if metadata.exists():
                    for line in metadata.read_text().splitlines():
                        if "sample_rate=" in line:
                            rate = int(line.split("=")[1])

                response = np.fromfile(audio_out, dtype=np.float32)
                if len(response) > 0:
                    self.after(0, lambda: self._set_state("speaking"))
                    sd.play(response, rate)
                    sd.wait()
                audio_out.unlink()

            self.after(0, lambda: [
                self.voice_instruction.configure(text="Hold SPACE to speak"),
                self._set_state("idle")
            ])

        except Exception as e:
            self.after(0, lambda: self.status_bar.configure(
                text=f"Error: {e}", text_color=OSRS["error"]))
        finally:
            self.processing = False
            self.after(0, lambda: self.voice_instruction.configure(
                text="Hold SPACE to speak"))

    def _on_close(self):
        """Handle close."""
        if self.server_process:
            self._stop_server()
        self.destroy()


def main():
    """Entry point."""
    if not WSL_PATH.exists():
        print("ERROR: Cannot access WSL at:", WSL_PATH)
        input("Press Enter to exit...")
        sys.exit(1)

    app = ATLASLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()
