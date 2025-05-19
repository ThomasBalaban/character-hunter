#!/usr/bin/env python3
# status_window.py
# Status window UI component for Character Hunter

import tkinter as tk
import logging

logger = logging.getLogger("CharacterHunter.StatusWindow")

class StatusWindow:
    """Small floating status window to display app status"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Character Hunter")
        
        # Make window small and float on top
        self.root.geometry("200x70+10+10")  # Width x Height + X + Y
        self.root.attributes("-topmost", True)
        self.root.configure(bg='#333333')
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Add a small title bar for dragging
        self.title_bar = tk.Frame(self.root, bg='#222222', height=15)
        self.title_bar.pack(fill=tk.X)
        
        # Add close button
        self.close_button = tk.Label(self.title_bar, text="×", bg='#222222', fg='white')
        self.close_button.pack(side=tk.RIGHT)
        self.close_button.bind('<Button-1>', self.close_window)
        
        # Bind drag events
        self.title_bar.bind('<ButtonPress-1>', self.start_move)
        self.title_bar.bind('<ButtonRelease-1>', self.stop_move)
        self.title_bar.bind('<B1-Motion>', self.on_motion)
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_var.set("Waiting for user search...")
        self.status_label = tk.Label(
            self.root, 
            textvariable=self.status_var,
            bg='#333333',
            fg='#00FF00',
            font=('Helvetica', 10),
            wraplength=180,
            justify='left'
        )
        self.status_label.pack(pady=10, padx=5, fill=tk.BOTH, expand=True)
        
        # Variables to track window movement
        self.x = 0
        self.y = 0
        
        logger.info("Status window initialized")
    
    def start_move(self, event):
        """Begin window drag operation"""
        self.x = event.x
        self.y = event.y
    
    def stop_move(self, event):
        """End window drag operation"""
        self.x = None
        self.y = None
    
    def on_motion(self, event):
        """Handle window movement"""
        dx = event.x - self.x
        dy = event.y - self.y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")
    
    def close_window(self, event=None):
        """Close the application"""
        logger.info("Closing status window and application")
        self.root.quit()
    
    def update_status(self, message):
        """Update the status display with a new message"""
        try:
            self.status_var.set(message)
            self.root.update_idletasks()  # Use update_idletasks to avoid blocking
            logger.debug(f"Status updated: {message}")
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def start(self):
        """Start the main UI loop"""
        logger.info("Starting status window main loop")
        self.root.mainloop()
        
    def get_window_position(self):
        """Get the current window position and size for click detection"""
        return {
            'x': self.root.winfo_x(),
            'y': self.root.winfo_y(),
            'width': self.root.winfo_width(),
            'height': self.root.winfo_height()
        }