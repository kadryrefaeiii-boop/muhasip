#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Splash Screen
Professional loading screen for application startup
"""

import tkinter as tk
from tkinter import Canvas, PhotoImage
import threading
import time
import os
import customtkinter as ctk

class SplashScreen:
    """Professional splash screen with loading animation"""

    def __init__(self, root):
        """
        Initialize splash screen

        Args:
            root: Root tkinter window
        """
        self.root = root
        self.splash_window = None
        self.progress = 0
        self.loading_messages = [
            "Loading database...",
            "Initializing managers...",
            "Setting up themes...",
            "Loading language files...",
            "Preparing interface...",
            "Almost ready..."
        ]
        self.current_message_index = 0

    def show(self):
        """Show splash screen"""
        try:
            # Create splash window
            self.splash_window = tk.Toplevel(self.root)
            self.splash_window.title("Professional Accounting ERP")

            # Center window on screen
            width, height = 600, 400
            screen_width = self.splash_window.winfo_screenwidth()
            screen_height = self.splash_window.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.splash_window.geometry(f"{width}x{height}+{x}+{y}")

            # Remove window decorations
            self.splash_window.overrideredirect(True)
            self.splash_window.attributes('-alpha', 0.95)

            # Create content
            self.create_splash_content()

            # Start animation
            self.start_animation()

        except Exception as e:
            print(f"Failed to show splash screen: {e}")
            if self.splash_window:
                self.splash_window.destroy()

    def create_splash_content(self):
        """Create splash screen content"""

        try:
            # Main frame
            main_frame = tk.Frame(self.splash_window, bg='#1a1a2e')
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Logo placeholder (using text for now)
            logo_frame = tk.Frame(main_frame, bg='#1a1a2e')
            logo_frame.pack(pady=(50, 30))

            # Company name with large font
            company_label = tk.Label(
                logo_frame,
                text="المحاسبة الاحترافية",
                font=("Arial", 28, "bold"),
                fg='#ffffff',
                bg='#1a1a2e'
            )
            company_label.pack()

            subtitle_label = tk.Label(
                logo_frame,
                text="Professional Accounting ERP",
                font=("Arial", 14),
                fg='#b0b0b0',
                bg='#1a1a2e'
            )
            subtitle_label.pack(pady=(5, 0))

            # Progress frame
            progress_frame = tk.Frame(main_frame, bg='#1a1a2e')
            progress_frame.pack(pady=30, padx=50, fill=tk.X)

            # Loading message
            self.message_label = tk.Label(
                progress_frame,
                text="Initializing...",
                font=("Arial", 12),
                fg='#ffffff',
                bg='#1a1a2e'
            )
            self.message_label.pack(pady=(0, 10))

            # Progress bar background
            progress_bg = tk.Frame(progress_frame, bg='#0f3460', height=6)
            progress_bg.pack(fill=tk.X, pady=(0, 10))

            # Progress bar fill
            self.progress_fill = tk.Frame(progress_bg, bg='#00d4ff', height=6, width=0)
            self.progress_fill.place(x=0, y=0)

            # Percentage label
            self.percentage_label = tk.Label(
                progress_frame,
                text="0%",
                font=("Arial", 10),
                fg='#b0b0b0',
                bg='#1a1a2e'
            )
            self.percentage_label.pack()

            # Version info
            version_frame = tk.Frame(main_frame, bg='#1a1a2e')
            version_frame.pack(side=tk.BOTTOM, pady=20)

            version_label = tk.Label(
                version_frame,
                text="Version 1.0.0",
                font=("Arial", 9),
                fg='#808080',
                bg='#1a1a2e'
            )
            version_label.pack()

            # Copyright info
            copyright_label = tk.Label(
                version_frame,
                text="© 2024 Professional Accounting ERP",
                font=("Arial", 8),
                fg='#606060',
                bg='#1a1a2e'
            )
            copyright_label.pack()

        except Exception as e:
            print(f"Failed to create splash content: {e}")

    def start_animation(self):
        """Start loading animation"""
        try:
            self.animate_loading()
        except Exception as e:
            print(f"Failed to start animation: {e}")

    def animate_loading(self):
        """Animate loading progress"""
        try:
            # Update progress
            self.progress += 2
            if self.progress > 100:
                self.progress = 100

            # Update progress bar
            progress_bg_width = 500  # Approximate width
            fill_width = int((self.progress / 100) * progress_bg_width)
            self.progress_fill.config(width=fill_width)

            # Update percentage
            self.percentage_label.config(text=f"{self.progress}%")

            # Update message
            if self.progress % 15 == 0 and self.current_message_index < len(self.loading_messages):
                self.message_label.config(text=self.loading_messages[self.current_message_index])
                self.current_message_index += 1

            # Continue animation or complete
            if self.progress < 100:
                self.splash_window.after(100, self.animate_loading)
            else:
                self.message_label.config(text="Ready!")
                self.splash_window.after(500, self.close)

        except Exception as e:
            print(f"Animation error: {e}")

    def close(self):
        """Close splash screen"""
        try:
            if self.splash_window:
                self.splash_window.destroy()
                self.splash_window = None

        except Exception as e:
            print(f"Failed to close splash screen: {e}")

    def set_progress(self, value):
        """Set progress value manually"""
        try:
            self.progress = max(0, min(100, value))
            if self.progress_fill:
                progress_bg_width = 500
                fill_width = int((self.progress / 100) * progress_bg_width)
                self.progress_fill.config(width=fill_width)

            if self.percentage_label:
                self.percentage_label.config(text=f"{self.progress}%")

        except Exception as e:
            print(f"Failed to set progress: {e}")

    def set_message(self, message):
        """Set loading message"""
        try:
            if self.message_label:
                self.message_label.config(text=message)

        except Exception as e:
            print(f"Failed to set message: {e}")

    def add_loading_step(self, step_name):
        """Add a loading step and update progress"""
        try:
            if self.message_label:
                self.message_label.config(text=step_name)

            # Auto-increment progress
            increment = 100 // len(self.loading_messages)
            self.set_progress(min(100, self.progress + increment))

        except Exception as e:
            print(f"Failed to add loading step: {e}")

class CustomSplashScreen:
    """CustomTkinter-based splash screen"""

    def __init__(self, root):
        """
        Initialize CustomTkinter splash screen

        Args:
            root: Root tkinter window
        """
        self.root = root
        self.splash_window = None

    def show(self):
        """Show CustomTkinter splash screen"""
        try:
            # Create splash window with CustomTkinter
            self.splash_window = ctk.CTkToplevel(self.root)
            self.splash_window.title("Professional Accounting ERP")

            # Configure window
            self.splash_window.overrideredirect(True)
            self.splash_window.attributes('-alpha', 0.98)

            # Size and center
            width, height = 500, 350
            screen_width = self.splash_window.winfo_screenwidth()
            screen_height = self.splash_window.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.splash_window.geometry(f"{width}x{height}+{x}+{y}")

            # Create content
            self.create_ctk_content()

            # Auto-close after delay
            self.splash_window.after(3000, self.close)

        except Exception as e:
            print(f"Failed to show CTk splash: {e}")
            if self.splash_window:
                self.splash_window.destroy()

    def create_ctk_content(self):
        """Create CustomTkinter splash content"""

        try:
            # Main frame
            main_frame = ctk.CTkFrame(self.splash_window, corner_radius=15)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Logo area
            logo_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            logo_frame.pack(pady=(30, 20))

            # Company name
            title_label = ctk.CTkLabel(
                logo_frame,
                text="المحاسبة الاحترافية",
                font=ctk.CTkFont(size=28, weight="bold")
            )
            title_label.pack()

            subtitle_label = ctk.CTkLabel(
                logo_frame,
                text="Professional Accounting ERP",
                font=ctk.CTkFont(size=14)
            )
            subtitle_label.pack(pady=(5, 0))

            # Loading indicator
            loading_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            loading_frame.pack(pady=20)

            # Progress bar
            self.progress_bar = ctk.CTkProgressBar(loading_frame, width=300)
            self.progress_bar.set(0)
            self.progress_bar.pack()

            # Loading text
            self.loading_label = ctk.CTkLabel(
                loading_frame,
                text="Loading application...",
                font=ctk.CTkFont(size=12)
            )
            self.loading_label.pack(pady=(10, 0))

            # Version info
            version_label = ctk.CTkLabel(
                main_frame,
                text="Version 1.0.0",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            version_label.pack(side=tk.BOTTOM, pady=(0, 10))

            # Start progress animation
            self.animate_progress()

        except Exception as e:
            print(f"Failed to create CTK content: {e}")

    def animate_progress(self):
        """Animate progress bar"""
        try:
            current_value = self.progress_bar.get()
            new_value = current_value + 0.02

            if new_value >= 1.0:
                self.progress_bar.set(1.0)
                self.loading_label.configure(text="Ready!")
            else:
                self.progress_bar.set(new_value)
                self.splash_window.after(50, self.animate_progress)

        except Exception as e:
            print(f"Progress animation error: {e}")

    def close(self):
        """Close splash screen"""
        try:
            if self.splash_window:
                self.splash_window.destroy()
                self.splash_window = None

        except Exception as e:
            print(f"Failed to close CTk splash: {e}")

def create_splash_screen(root, use_customtkinter=True):
    """
    Factory function to create splash screen

    Args:
        root: Root tkinter window
        use_customtkinter: Use CustomTkinter version

    Returns:
        Splash screen instance
    """
    if use_customtkinter:
        return CustomSplashScreen(root)
    else:
        return SplashScreen(root)