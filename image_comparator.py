#!/usr/bin/env python3
"""
Image Comparator with ELO Rating System
A GUI application for comparing images and ranking them using ELO ratings.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import random
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class ImageComparator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Comparator - ELO Rating System")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Data storage
        self.images_dir: Optional[str] = None
        self.image_files: List[str] = []
        self.ratings: Dict[str, float] = {}  # filename -> ELO rating
        self.comparison_history: List[Tuple[str, str]] = []  # Track compared pairs
        
        # Current comparison state
        self.current_left_image: Optional[str] = None
        self.current_right_image: Optional[str] = None
        self.left_photo: Optional[ImageTk.PhotoImage] = None
        self.right_photo: Optional[ImageTk.PhotoImage] = None
        
        # Rankings view state
        self.preview_photo: Optional[ImageTk.PhotoImage] = None
        self.selected_image_path: Optional[str] = None
        
        # UI state
        self.current_view = "comparison"  # "comparison" or "ranking"
        
        # Constants
        self.INITIAL_ELO = 1500
        self.K_FACTOR = 32
        self.IMAGE_SIZE = (400, 400)
        self.THUMBNAIL_SIZE = (100, 100)
        
        self.setup_ui()
        self.bind_keyboard_events()
        
    def setup_ui(self):
        """Initialize the user interface."""
        # Main menu
        self.create_menu()
        
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Directory selection
        ttk.Label(self.control_frame, text="Image Directory:").pack(side=tk.LEFT)
        self.dir_label = ttk.Label(self.control_frame, text="No directory selected", 
                                  foreground="gray")
        self.dir_label.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(self.control_frame, text="Browse", 
                  command=self.select_directory).pack(side=tk.LEFT)
        
        # View toggle buttons
        self.view_frame = ttk.Frame(self.control_frame)
        self.view_frame.pack(side=tk.RIGHT)
        
        ttk.Button(self.view_frame, text="Comparison View", 
                  command=self.show_comparison_view).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.view_frame, text="Rankings", 
                  command=self.show_ranking_view).pack(side=tk.LEFT, padx=2)
        
        # Content area - will hold different views
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize with comparison view
        self.create_comparison_view()
        
    def create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Directory...", command=self.select_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Export Rankings...", command=self.export_rankings)
        file_menu.add_command(label="Import Rankings...", command=self.import_rankings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_comparison_view(self):
        """Create the side-by-side image comparison interface."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Instructions
        instructions = ttk.Label(self.content_frame, 
                               text="Click on an image to select the winner, or use arrow keys. Press Space to skip.",
                               font=("Arial", 10))
        instructions.pack(pady=(0, 10))
        
        # Image comparison frame
        self.comparison_frame = ttk.Frame(self.content_frame)
        self.comparison_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left image frame
        self.left_frame = ttk.Frame(self.comparison_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.left_canvas = tk.Canvas(self.left_frame, bg="white", relief=tk.RAISED, bd=2)
        self.left_canvas.pack(fill=tk.BOTH, expand=True, pady=5)
        self.left_canvas.bind("<Button-1>", lambda e: self.select_winner("left"))
        
        # Right image frame
        self.right_frame = ttk.Frame(self.comparison_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.right_canvas = tk.Canvas(self.right_frame, bg="white", relief=tk.RAISED, bd=2)
        self.right_canvas.pack(fill=tk.BOTH, expand=True, pady=5)
        self.right_canvas.bind("<Button-1>", lambda e: self.select_winner("right"))
        
        # Control buttons
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="← Left Wins", 
                  command=lambda: self.select_winner("left")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Skip (Space)", 
                  command=self.skip_pair).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Right Wins →", 
                  command=lambda: self.select_winner("right")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="New Pair", 
                  command=self.load_new_pair).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(self.content_frame, text="Select a directory to begin", 
                                    foreground="gray")
        self.status_label.pack(pady=5)
        
    def bind_keyboard_events(self):
        """Bind keyboard shortcuts."""
        self.root.bind('<Left>', lambda e: self.select_winner("left") if self.current_view == "comparison" else None)
        self.root.bind('<Right>', lambda e: self.select_winner("right") if self.current_view == "comparison" else None)
        self.root.bind('<space>', lambda e: self.skip_pair() if self.current_view == "comparison" else None)
        self.root.bind('<Control-o>', lambda e: self.select_directory())
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<Escape>', lambda e: self.root.quit())
        self.root.focus_set()  # Ensure window can receive key events
        
    def select_directory(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(title="Select Image Directory")
        if directory:
            self.load_images_from_directory(directory)
            
    def show_comparison_view(self):
        """Switch to comparison view."""
        self.current_view = "comparison"
        self.create_comparison_view()
        if self.image_files:
            self.load_new_pair()
            
    def show_ranking_view(self):
        """Switch to ranking view."""
        self.current_view = "ranking"
        self.create_ranking_view()
        
    def create_ranking_view(self):
        """Create the rankings display with thumbnails and scores."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        if not self.image_files:
            ttk.Label(self.content_frame, text="No images loaded. Please select a directory first.", 
                     font=("Arial", 14)).pack(expand=True)
            return
        
        # Title
        title_frame = ttk.Frame(self.content_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="Image Rankings", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        # Stats
        total_comparisons = len(self.comparison_history)
        ttk.Label(title_frame, text=f"Total Comparisons: {total_comparisons}", 
                 font=("Arial", 10)).pack(side=tk.RIGHT)
        
        # Main content - split into left (rankings) and right (preview) with resizable panes
        main_content = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_content.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Rankings list
        left_panel = ttk.Frame(main_content)
        main_content.add(left_panel, weight=1)
        
        # Create scrollable frame for rankings
        canvas = tk.Canvas(left_panel)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Right side - Image preview
        right_panel = ttk.Frame(main_content)
        main_content.add(right_panel, weight=1)
        
        # Preview title
        ttk.Label(right_panel, text="Image Preview", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Create scrollable preview area
        preview_frame = ttk.Frame(right_panel)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Preview canvas with scrollbars
        self.preview_canvas = tk.Canvas(preview_frame, bg="white", relief=tk.SUNKEN, bd=1)
        
        # Scrollbars for preview
        v_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_canvas.yview)
        h_scrollbar = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.preview_canvas.xview)
        
        self.preview_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.preview_canvas.pack(side="left", fill="both", expand=True)
        
        # Preview info
        self.preview_info = ttk.Label(right_panel, text="Click on an image to preview", 
                                    font=("Arial", 10), foreground="gray")
        self.preview_info.pack(pady=5)
        
        # Sort images by rating (descending)
        sorted_images = sorted(self.image_files, 
                             key=lambda x: self.ratings.get(os.path.basename(x), self.INITIAL_ELO), 
                             reverse=True)
        
        # Create ranking entries
        for rank, image_path in enumerate(sorted_images, 1):
            self.create_ranking_entry(scrollable_frame, rank, image_path)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    def create_ranking_entry(self, parent: ttk.Frame, rank: int, image_path: str):
        """Create a single ranking entry with thumbnail and info."""
        filename = os.path.basename(image_path)
        rating = self.ratings.get(filename, self.INITIAL_ELO)
        
        # Main frame for this entry
        entry_frame = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=1)
        entry_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Make the entire entry clickable for preview
        entry_frame.bind("<Button-1>", lambda e: self.show_image_preview(image_path))
        
        # Rank number
        rank_label = ttk.Label(entry_frame, text=f"#{rank}", font=("Arial", 12, "bold"), width=4)
        rank_label.pack(side=tk.LEFT, padx=(10, 5), pady=10)
        rank_label.bind("<Button-1>", lambda e: self.show_image_preview(image_path))
        
        # Thumbnail
        thumbnail_frame = ttk.Frame(entry_frame)
        thumbnail_frame.pack(side=tk.LEFT, padx=5, pady=5)
        thumbnail_frame.bind("<Button-1>", lambda e: self.show_image_preview(image_path))
        
        try:
            thumbnail = self.load_image_for_display(image_path, self.THUMBNAIL_SIZE)
            if thumbnail:
                thumbnail_label = ttk.Label(thumbnail_frame, image=thumbnail)
                thumbnail_label.image = thumbnail  # Keep a reference
                thumbnail_label.pack()
                thumbnail_label.bind("<Button-1>", lambda e: self.show_image_preview(image_path))
            else:
                no_preview = ttk.Label(thumbnail_frame, text="No\nPreview", width=10)
                no_preview.pack()
                no_preview.bind("<Button-1>", lambda e: self.show_image_preview(image_path))
        except Exception:
            error_label = ttk.Label(thumbnail_frame, text="Error\nLoading", width=10)
            error_label.pack()
            error_label.bind("<Button-1>", lambda e: self.show_image_preview(image_path))
        
        # Info frame
        info_frame = ttk.Frame(entry_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        info_frame.bind("<Button-1>", lambda e: self.show_image_preview(image_path))
        
        # Filename
        filename_label = ttk.Label(info_frame, text=filename, font=("Arial", 11, "bold"))
        filename_label.pack(anchor=tk.W)
        filename_label.bind("<Button-1>", lambda e: self.show_image_preview(image_path))
        
        # Rating
        rating_color = self.get_rating_color(rating)
        rating_label = ttk.Label(info_frame, text=f"ELO Rating: {rating:.0f}", 
                               font=("Arial", 10), foreground=rating_color)
        rating_label.pack(anchor=tk.W)
        rating_label.bind("<Button-1>", lambda e: self.show_image_preview(image_path))
        
        # Comparison count
        comparisons = sum(1 for pair in self.comparison_history 
                         if filename in pair)
        comp_label = ttk.Label(info_frame, text=f"Comparisons: {comparisons}", 
                             font=("Arial", 9), foreground="gray")
        comp_label.pack(anchor=tk.W)
        comp_label.bind("<Button-1>", lambda e: self.show_image_preview(image_path))
    
    def show_image_preview(self, image_path: str):
        """Show large preview of selected image."""
        if not hasattr(self, 'preview_canvas'):
            return
            
        self.selected_image_path = image_path
        filename = os.path.basename(image_path)
        rating = self.ratings.get(filename, self.INITIAL_ELO)
        
        # Load image for preview at original size
        self.preview_photo = self.load_image_for_display(image_path)
        
        # Clear and update preview canvas
        self.preview_canvas.delete("all")
        if self.preview_photo:
            # Get image dimensions
            img_width = self.preview_photo.width()
            img_height = self.preview_photo.height()
            
            # Set scroll region to image size
            self.preview_canvas.configure(scrollregion=(0, 0, img_width, img_height))
            
            # Place image at top-left of scrollable area
            self.preview_canvas.create_image(0, 0, image=self.preview_photo, anchor=tk.NW)
            
            # Center the view on the image initially
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:  # Canvas is drawn
                # Calculate center position
                center_x = max(0, (img_width - canvas_width) / 2 / img_width) if img_width > canvas_width else 0
                center_y = max(0, (img_height - canvas_height) / 2 / img_height) if img_height > canvas_height else 0
                
                self.preview_canvas.xview_moveto(center_x)
                self.preview_canvas.yview_moveto(center_y)
        
        # Update info
        comparisons = sum(1 for pair in self.comparison_history if filename in pair)
        info_text = f"{filename}\nELO: {rating:.0f} | Comparisons: {comparisons}"
        self.preview_info.config(text=info_text, foreground="black")
    
    def get_rating_color(self, rating: float) -> str:
        """Get color based on rating relative to initial rating."""
        if rating > self.INITIAL_ELO + 100:
            return "green"
        elif rating < self.INITIAL_ELO - 100:
            return "red"
        else:
            return "black"
    
    def show_help(self):
        """Show keyboard shortcuts help."""
        help_text = """Keyboard Shortcuts:
        
← (Left Arrow)     - Left image wins (comparison view)
→ (Right Arrow)    - Right image wins (comparison view)
Space              - Skip this pair (comparison view)
Ctrl+O             - Open directory
F1                 - Show this help
Esc                - Exit application

Mouse Controls:
• Click on images to select winners
• Use scroll wheel in rankings view

Tips:
• The ELO system gives better ratings to images that win against stronger opponents
• Avoid comparing the same pairs repeatedly - the algorithm will try to minimize repetition
• Export your rankings to save progress between sessions"""
        messagebox.showinfo("Keyboard Shortcuts", help_text)
        
    def show_about(self):
        """Show about dialog."""
        about_text = """Image Comparator v1.0

A tool for comparing and ranking images using 
the ELO rating system.

Features:
• Side-by-side image comparison
• ELO rating system
• Keyboard shortcuts
• Rankings view"""
        messagebox.showinfo("About", about_text)
        
    def export_rankings(self):
        """Export rankings to JSON file."""
        if not self.ratings:
            messagebox.showwarning("No Data", "No ratings to export.")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Export Rankings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                export_data = {
                    "ratings": self.ratings,
                    "comparison_history": self.comparison_history,
                    "images_dir": self.images_dir,
                    "total_comparisons": len(self.comparison_history)
                }
                
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
                messagebox.showinfo("Export Successful", f"Rankings exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export rankings: {e}")
        
    def import_rankings(self):
        """Import rankings from JSON file."""
        filename = filedialog.askopenfilename(
            title="Import Rankings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    import_data = json.load(f)
                
                self.ratings = import_data.get("ratings", {})
                self.comparison_history = import_data.get("comparison_history", [])
                
                # Optionally load the directory if it exists
                imported_dir = import_data.get("images_dir")
                if imported_dir and os.path.exists(imported_dir):
                    if messagebox.askyesno("Load Directory", 
                                         f"Also load images from {imported_dir}?"):
                        self.load_images_from_directory(imported_dir)
                
                messagebox.showinfo("Import Successful", 
                                  f"Imported {len(self.ratings)} ratings and {len(self.comparison_history)} comparisons")
                
                # Refresh current view
                if self.current_view == "ranking":
                    self.show_ranking_view()
                    
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import rankings: {e}")
        
    def load_images_from_directory(self, directory: str):
        """Load all image files from the specified directory."""
        self.images_dir = directory
        self.dir_label.config(text=os.path.basename(directory))
        
        # Supported image formats
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        
        # Find all image files
        self.image_files = []
        try:
            for file_path in Path(directory).rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                    self.image_files.append(str(file_path))
        except Exception as e:
            messagebox.showerror("Error", f"Error loading directory: {e}")
            return
            
        if not self.image_files:
            messagebox.showwarning("No Images", "No supported image files found in the selected directory.")
            return
            
        # Initialize ratings for new images
        self.initialize_ratings()
        
        # Load first pair
        if len(self.image_files) >= 2:
            self.load_new_pair()
            self.status_label.config(text=f"Loaded {len(self.image_files)} images")
        else:
            messagebox.showwarning("Insufficient Images", "Need at least 2 images for comparison.")
    
    def initialize_ratings(self):
        """Initialize ELO ratings for all images."""
        for image_path in self.image_files:
            filename = os.path.basename(image_path)
            if filename not in self.ratings:
                self.ratings[filename] = self.INITIAL_ELO
    
    def load_image_for_display(self, image_path: str, size: Tuple[int, int] = None) -> Optional[ImageTk.PhotoImage]:
        """Load and optionally resize an image for display."""
        try:
            # Open image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (handles various formats)
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Only resize if size is specified (for thumbnails)
                if size:
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Create PhotoImage
                return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def display_image_on_canvas(self, canvas: tk.Canvas, photo: ImageTk.PhotoImage):
        """Display an image on a canvas, centered."""
        canvas.delete("all")
        if photo:
            # Center the image on canvas
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            # If canvas not yet drawn, use default size
            if canvas_width <= 1:
                canvas_width = 400
                canvas_height = 400
                
            x = canvas_width // 2
            y = canvas_height // 2
            
            canvas.create_image(x, y, image=photo, anchor=tk.CENTER)
        
    def get_pair_frequency(self, img1: str, img2: str) -> int:
        """Get how many times this pair has been compared."""
        pair = tuple(sorted([os.path.basename(img1), os.path.basename(img2)]))
        return self.comparison_history.count(pair)
    
    def select_smart_pair(self) -> Tuple[Optional[str], Optional[str]]:
        """Select a pair of images, avoiding recently compared pairs when possible."""
        if len(self.image_files) < 2:
            return None, None
            
        # Try to find a pair that hasn't been compared yet (or least compared)
        min_frequency = float('inf')
        best_pairs = []
        
        # Sample pairs to avoid checking all combinations for large datasets
        max_attempts = min(100, len(self.image_files) * 2)
        
        for _ in range(max_attempts):
            img1 = random.choice(self.image_files)
            img2 = random.choice(self.image_files)
            
            if img1 == img2:
                continue
                
            frequency = self.get_pair_frequency(img1, img2)
            
            if frequency < min_frequency:
                min_frequency = frequency
                best_pairs = [(img1, img2)]
            elif frequency == min_frequency:
                best_pairs.append((img1, img2))
        
        if best_pairs:
            return random.choice(best_pairs)
        else:
            # Fallback to random selection
            img1 = random.choice(self.image_files)
            img2 = random.choice(self.image_files)
            while img2 == img1 and len(self.image_files) > 1:
                img2 = random.choice(self.image_files)
            return img1, img2
    def load_new_pair(self):
        """Load a new pair of images for comparison."""
        if len(self.image_files) < 2:
            return
            
        # Use smart pair selection
        self.current_left_image, self.current_right_image = self.select_smart_pair()
        
        if not self.current_left_image or not self.current_right_image:
            return
        
        # Load and display images
        self.left_photo = self.load_image_for_display(self.current_left_image)  # No size limit for comparison
        self.right_photo = self.load_image_for_display(self.current_right_image)  # No size limit for comparison
        
        # Update canvases
        self.root.after(1, self.update_canvas_display)  # Delay to ensure canvas is drawn
    
    def update_canvas_display(self):
        """Update the canvas display with current images."""
        if self.left_photo:
            self.display_image_on_canvas(self.left_canvas, self.left_photo)
        if self.right_photo:
            self.display_image_on_canvas(self.right_canvas, self.right_photo)
        
    def calculate_elo_update(self, winner_rating: float, loser_rating: float) -> Tuple[float, float]:
        """Calculate new ELO ratings after a match."""
        # Expected scores
        expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
        expected_loser = 1 / (1 + 10 ** ((winner_rating - loser_rating) / 400))
        
        # New ratings (winner gets 1 point, loser gets 0)
        new_winner_rating = winner_rating + self.K_FACTOR * (1 - expected_winner)
        new_loser_rating = loser_rating + self.K_FACTOR * (0 - expected_loser)
        
        return new_winner_rating, new_loser_rating
    
    def update_ratings(self, winner_path: str, loser_path: str):
        """Update ELO ratings after a comparison."""
        winner_filename = os.path.basename(winner_path)
        loser_filename = os.path.basename(loser_path)
        
        winner_rating = self.ratings.get(winner_filename, self.INITIAL_ELO)
        loser_rating = self.ratings.get(loser_filename, self.INITIAL_ELO)
        
        new_winner_rating, new_loser_rating = self.calculate_elo_update(winner_rating, loser_rating)
        
        self.ratings[winner_filename] = new_winner_rating
        self.ratings[loser_filename] = new_loser_rating
        
        # Record this comparison
        pair = tuple(sorted([winner_filename, loser_filename]))
        self.comparison_history.append(pair)
        
    def select_winner(self, winner: str):
        """Handle winner selection."""
        if not self.current_left_image or not self.current_right_image:
            return
            
        if winner == "left":
            winner_path = self.current_left_image
            loser_path = self.current_right_image
        else:
            winner_path = self.current_right_image
            loser_path = self.current_left_image
            
        # Update ratings
        self.update_ratings(winner_path, loser_path)
        
        # Show brief feedback
        winner_name = os.path.basename(winner_path)
        self.status_label.config(text=f"Winner: {winner_name} (New rating: {self.ratings[winner_name]:.0f})")
        
        # Load next pair
        self.root.after(1500, self.load_new_pair)  # Brief delay to show result
        
    def skip_pair(self):
        """Skip the current pair without rating."""
        if self.image_files and len(self.image_files) >= 2:
            self.load_new_pair()
            self.status_label.config(text="Pair skipped - loaded new comparison")


def main():
    """Main entry point."""
    app = ImageComparator()
    app.root.mainloop()


if __name__ == "__main__":
    main()