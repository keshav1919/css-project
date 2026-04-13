"""
Instagram-Style Camera App - Python Edition
A complete camera application with modern UI, filters, and gallery features
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageFilter, ImageEnhance
import cv2
import threading
import time
import os
from datetime import datetime
import json
from pathlib import Path

class InstagramCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("InstaCam - Instagram Style Camera")
        self.root.geometry("400x700")
        self.root.configure(bg='#000000')
        self.root.resizable(False, False)
        
        # Camera variables
        self.cap = None
        self.is_running = False
        self.current_camera = 0  # 0 for back, 1 for front
        self.is_front_camera = False
        self.photo_taken = False
        self.current_frame = None
        self.video_loop_id = None
        
        # Filters and effects
        self.current_filter = "Normal"
        self.filters = ["Normal", "Clarendon", "Gingham", "Moon", "Lark", "Reyes", "Juno"]
        self.filter_index = 0
        
        # Gallery
        self.photos = []
        self.photos_dir = Path.home() / "InstaCam_Photos"
        self.photos_dir.mkdir(exist_ok=True)
        self.load_gallery()
        
        # Flash simulation
        self.flash_on = False
        self.flash_timer = None
        
        # UI Setup
        self.setup_ui()
        
        # Start camera
        self.start_camera()
        
    def setup_ui(self):
        """Setup the modern Instagram-like UI"""
        
        # Top bar with flash and settings
        self.top_frame = tk.Frame(self.root, bg='#000000', height=80)
        self.top_frame.pack(fill='x', padx=15, pady=10)
        self.top_frame.pack_propagate(False)
        
        # Flash button
        self.flash_btn = tk.Button(
            self.top_frame, 
            text="⚡", 
            font=('Arial', 18),
            bg='#000000', 
            fg='white',
            bd=0,
            activebackground='#333333',
            cursor='hand2',
            command=self.toggle_flash
        )
        self.flash_btn.pack(side='left', padx=5)
        
        # Title
        self.title_label = tk.Label(
            self.top_frame,
            text="InstaCam",
            font=('Helvetica', 20, 'bold'),
            bg='#000000',
            fg='white'
        )
        self.title_label.pack(side='left', expand=True)
        
        # Gallery button (top right)
        self.gallery_top_btn = tk.Button(
            self.top_frame,
            text="📷",
            font=('Arial', 18),
            bg='#000000',
            fg='white',
            bd=0,
            activebackground='#333333',
            cursor='hand2',
            command=self.show_gallery
        )
        self.gallery_top_btn.pack(side='right', padx=5)
        
        # Camera view finder
        self.camera_frame = tk.Frame(self.root, bg='#000000', width=380, height=500)
        self.camera_frame.pack(pady=10)
        self.camera_frame.pack_propagate(False)
        
        self.video_label = tk.Label(self.camera_frame, bg='#000000')
        self.video_label.pack(expand=True, fill='both')
        
        # Filter bar
        self.filter_frame = tk.Frame(self.root, bg='#1a1a1a', height=60)
        self.filter_frame.pack(fill='x', pady=5)
        
        # Scrollable filter buttons
        self.filter_canvas = tk.Canvas(
            self.filter_frame, 
            bg='#1a1a1a', 
            height=60,
            highlightthickness=0
        )
        self.filter_scrollbar = ttk.Scrollbar(
            self.filter_frame, 
            orient="horizontal", 
            command=self.filter_canvas.xview
        )
        self.filter_canvas.configure(xscrollcommand=self.filter_scrollbar.set)
        
        self.filter_canvas.pack(side='top', fill='x', expand=True)
        self.filter_scrollbar.pack(side='bottom', fill='x')
        
        self.filter_inner = tk.Frame(self.filter_canvas, bg='#1a1a1a')
        self.filter_canvas.create_window((0, 0), window=self.filter_inner, anchor='nw')
        
        # Create filter buttons
        for i, filter_name in enumerate(self.filters):
            btn = tk.Button(
                self.filter_inner,
                text=filter_name,
                font=('Arial', 11),
                bg='#2a2a2a',
                fg='white',
                padx=15,
                pady=5,
                bd=0,
                cursor='hand2',
                command=lambda f=filter_name: self.apply_filter(f)
            )
            btn.pack(side='left', padx=5)
        
        self.filter_inner.update_idletasks()
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))
        
        # Bottom controls
        self.controls_frame = tk.Frame(self.root, bg='#000000', height=100)
        self.controls_frame.pack(fill='x', side='bottom', padx=20, pady=20)
        
        # Gallery preview button
        self.gallery_preview = tk.Button(
            self.controls_frame,
            text="📸",
            font=('Arial', 24),
            bg='#1a1a1a',
            fg='white',
            width=3,
            height=1,
            bd=0,
            cursor='hand2',
            command=self.show_gallery
        )
        self.gallery_preview.pack(side='left')
        
        # Shutter button
        self.shutter_btn = tk.Button(
            self.controls_frame,
            text="⭕",
            font=('Arial', 50),
            bg='#000000',
            fg='white',
            bd=0,
            cursor='hand2',
            command=self.take_photo
        )
        self.shutter_btn.pack(side='left', expand=True)
        
        # Flip camera button
        self.flip_btn = tk.Button(
            self.controls_frame,
            text="🔄",
            font=('Arial', 24),
            bg='#1a1a1a',
            fg='white',
            width=3,
            height=1,
            bd=0,
            cursor='hand2',
            command=self.switch_camera
        )
        self.flip_btn.pack(side='right')
        
        # Update gallery preview
        self.update_gallery_preview()
        
    def apply_filter(self, filter_name):
        """Apply selected filter to camera feed"""
        self.current_filter = filter_name
        
        # Update filter button styles
        for child in self.filter_inner.winfo_children():
            if child['text'] == filter_name:
                child.configure(bg='#4a4a8a')
            else:
                child.configure(bg='#2a2a2a')
    
    def apply_image_filter(self, image):
        """Apply the selected filter to an image"""
        if self.current_filter == "Normal":
            return image
        elif self.current_filter == "Clarendon":
            # Increase contrast and brightness
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
        elif self.current_filter == "Gingham":
            # Slight sepia + vignette
            image = image.convert('L').convert('RGB')
        elif self.current_filter == "Moon":
            # Cool blue tone
            r, g, b = image.split()
            b = b.point(lambda i: i * 1.2)
            image = Image.merge('RGB', (r, g, b))
        elif self.current_filter == "Lark":
            # Warm tones
            r, g, b = image.split()
            r = r.point(lambda i: i * 1.15)
            g = g.point(lambda i: i * 1.05)
            image = Image.merge('RGB', (r, g, b))
        elif self.current_filter == "Reyes":
            # Vintage faded look
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(0.7)
        elif self.current_filter == "Juno":
            # High contrast warm
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.2)
        
        return image
    
    def start_camera(self):
        """Start the camera capture"""
        self.cap = cv2.VideoCapture(self.current_camera)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.is_running = True
        self.update_camera_feed()
    
    def update_camera_feed(self):
        """Update the camera feed in the UI"""
        if not self.is_running:
            return
            
        ret, frame = self.cap.read()
        if ret:
            # Flip frame for front camera
            if self.is_front_camera:
                frame = cv2.flip(frame, 1)
            
            # Convert frame to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.current_frame = frame_rgb
            
            # Convert to PIL Image
            image = Image.fromarray(frame_rgb)
            
            # Apply current filter
            image = self.apply_image_filter(image)
            
            # Resize for display
            display_size = (380, 500)
            image.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Update label
            self.video_label.configure(image=photo)
            self.video_label.image = photo
        
        # Schedule next update
        self.video_loop_id = self.root.after(33, self.update_camera_feed)  # ~30 FPS
    
    def take_photo(self):
        """Capture a photo with flash effect"""
        if self.current_frame is None:
            return
        
        # Flash effect
        if self.flash_on:
            self.show_flash_effect()
        
        # Capture the current frame
        image = Image.fromarray(self.current_frame)
        
        # Apply filter
        image = self.apply_image_filter(image)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"instacam_{timestamp}.jpg"
        filepath = self.photos_dir / filename
        
        # Save photo
        image.save(filepath, "JPEG", quality=95)
        
        # Add to gallery
        self.photos.insert(0, {
            'path': str(filepath),
            'timestamp': timestamp,
            'filter': self.current_filter
        })
        
        # Save gallery metadata
        self.save_gallery_metadata()
        
        # Update gallery preview
        self.update_gallery_preview()
        
        # Show success message
        self.show_toast("📸 Photo saved to InstaCam_Photos folder!", 1500)
    
    def show_flash_effect(self):
        """Show a white flash overlay"""
        flash_overlay = tk.Frame(self.camera_frame, bg='white')
        flash_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        def remove_flash():
            flash_overlay.destroy()
        
        self.root.after(100, remove_flash)
    
    def show_toast(self, message, duration=2000):
        """Show a temporary toast message"""
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.configure(bg='#333333')
        
        label = tk.Label(
            toast, 
            text=message, 
            font=('Arial', 12), 
            bg='#333333', 
            fg='white',
            padx=20,
            pady=10
        )
        label.pack()
        
        # Position toast at bottom center
        toast.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (toast.winfo_width() // 2)
        y = self.root.winfo_y() + self.root.winfo_height() - 80
        toast.geometry(f"+{x}+{y}")
        
        # Auto close after duration
        self.root.after(duration, toast.destroy)
    
    def toggle_flash(self):
        """Toggle flash on/off"""
        self.flash_on = not self.flash_on
        if self.flash_on:
            self.flash_btn.configure(text="⚡ ON", fg='#FFD700')
            self.show_toast("Flash: ON", 1000)
        else:
            self.flash_btn.configure(text="⚡ OFF", fg='white')
            self.show_toast("Flash: OFF", 1000)
    
    def switch_camera(self):
        """Switch between front and back camera"""
        self.is_front_camera = not self.is_front_camera
        self.current_camera = 1 if self.is_front_camera else 0
        
        # Restart camera
        self.is_running = False
        if self.video_loop_id:
            self.root.after_cancel(self.video_loop_id)
        if self.cap:
            self.cap.release()
        
        # Small delay for camera to release
        self.root.after(200, self.start_camera)
        
        # Show message
        camera_type = "Front" if self.is_front_camera else "Back"
        self.show_toast(f"Switched to {camera_type} Camera", 1000)
    
    def update_gallery_preview(self):
        """Update the gallery preview button with the latest photo"""
        if self.photos:
            try:
                img = Image.open(self.photos[0]['path'])
                img.thumbnail((50, 50), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.gallery_preview.configure(image=photo, text="")
                self.gallery_preview.image = photo
                self.gallery_top_btn.configure(text="📷")
            except:
                self.gallery_preview.configure(text="📸", image='')
                self.gallery_top_btn.configure(text="📷")
        else:
            self.gallery_preview.configure(text="📸", image='')
            self.gallery_top_btn.configure(text="📷")
    
    def load_gallery(self):
        """Load existing photos from the photos directory"""
        # Load metadata
        metadata_file = self.photos_dir / "gallery_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                for photo_data in data:
                    # Check if file still exists
                    if Path(photo_data['path']).exists():
                        self.photos.append(photo_data)
        else:
            # Scan directory for existing photos
            for img_file in sorted(self.photos_dir.glob("instacam_*.jpg"), reverse=True):
                self.photos.append({
                    'path': str(img_file),
                    'timestamp': img_file.stem.replace('instacam_', ''),
                    'filter': 'Normal'
                })
    
    def save_gallery_metadata(self):
        """Save gallery metadata to file"""
        metadata_file = self.photos_dir / "gallery_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.photos, f, indent=2)
    
    def show_gallery(self):
        """Display the gallery in a new window"""
        if not self.photos:
            messagebox.showinfo("Gallery", "No photos yet!\nTake your first photo to see it here.")
            return
        
        # Create gallery window
        gallery_win = tk.Toplevel(self.root)
        gallery_win.title("InstaCam Gallery")
        gallery_win.geometry("400x600")
        gallery_win.configure(bg='#000000')
        
        # Header
        header = tk.Frame(gallery_win, bg='#000000', height=60)
        header.pack(fill='x', padx=15, pady=10)
        
        title = tk.Label(header, text="Your Photos", font=('Helvetica', 20, 'bold'), bg='#000000', fg='white')
        title.pack(side='left')
        
        close_btn = tk.Button(
            header,
            text="✕",
            font=('Arial', 16),
            bg='#000000',
            fg='white',
            bd=0,
            cursor='hand2',
            command=gallery_win.destroy
        )
        close_btn.pack(side='right')
        
        # Canvas for scrolling gallery
        canvas = tk.Canvas(gallery_win, bg='#000000', highlightthickness=0)
        scrollbar = ttk.Scrollbar(gallery_win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#000000')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display photos in grid
        cols = 3
        for i, photo_data in enumerate(self.photos):
            try:
                img = Image.open(photo_data['path'])
                img.thumbnail((120, 120), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                row = i // cols
                col = i % cols
                
                # Photo frame
                frame = tk.Frame(scrollable_frame, bg='#1a1a1a', relief='flat', bd=2)
                frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
                
                # Photo button
                btn = tk.Button(
                    frame,
                    image=photo,
                    bg='#1a1a1a',
                    bd=0,
                    cursor='hand2',
                    command=lambda p=photo_data['path']: self.view_photo(p, gallery_win)
                )
                btn.image = photo
                btn.pack(padx=5, pady=5)
                
                # Date label
                date_label = tk.Label(
                    frame,
                    text=photo_data['timestamp'][:8],
                    font=('Arial', 8),
                    bg='#1a1a1a',
                    fg='#888888'
                )
                date_label.pack()
                
            except Exception as e:
                print(f"Error loading photo: {e}")
        
        # Configure grid weights
        for i in range(cols):
            scrollable_frame.grid_columnconfigure(i, weight=1)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
    
    def view_photo(self, photo_path, gallery_window):
        """View a single photo in full size"""
        view_win = tk.Toplevel(gallery_window)
        view_win.title("Photo Viewer")
        view_win.geometry("400x600")
        view_win.configure(bg='#000000')
        
        # Load and display photo
        img = Image.open(photo_path)
        
        # Calculate display size
        display_size = (380, 500)
        img.thumbnail(display_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        
        # Photo label
        photo_label = tk.Label(view_win, image=photo, bg='#000000')
        photo_label.image = photo
        photo_label.pack(expand=True, pady=20)
        
        # Action buttons
        btn_frame = tk.Frame(view_win, bg='#000000')
        btn_frame.pack(pady=20)
        
        # Delete button
        def delete_photo():
            if messagebox.askyesno("Delete Photo", "Are you sure you want to delete this photo?"):
                try:
                    os.remove(photo_path)
                    # Remove from gallery list
                    for i, p in enumerate(self.photos):
                        if p['path'] == photo_path:
                            self.photos.pop(i)
                            break
                    self.save_gallery_metadata()
                    self.update_gallery_preview()
                    view_win.destroy()
                    gallery_window.destroy()
                    self.show_gallery()  # Refresh gallery
                    self.show_toast("Photo deleted", 1000)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not delete photo: {e}")
        
        delete_btn = tk.Button(
            btn_frame,
            text="🗑️ Delete",
            font=('Arial', 12),
            bg='#ff3b30',
            fg='white',
            padx=20,
            pady=10,
            bd=0,
            cursor='hand2',
            command=delete_photo
        )
        delete_btn.pack(side='left', padx=10)
        
        close_btn = tk.Button(
            btn_frame,
            text="Close",
            font=('Arial', 12),
            bg='#4a4a4a',
            fg='white',
            padx=20,
            pady=10,
            bd=0,
            cursor='hand2',
            command=view_win.destroy
        )
        close_btn.pack(side='left', padx=10)
    
    def on_closing(self):
        """Clean up when closing the app"""
        self.is_running = False
        if self.video_loop_id:
            self.root.after_cancel(self.video_loop_id)
        if self.cap:
            self.cap.release()
        self.root.destroy()


def main():
    """Main function to run the Instagram Camera App"""
    # Check if required packages are installed
    try:
        import cv2
        from PIL import Image, ImageTk, ImageFilter, ImageEnhance
    except ImportError as e:
        print("Error: Required packages not installed!")
        print("Please install them using:")
        print("pip install opencv-python pillow")
        return
    
    root = tk.Tk()
    app = InstagramCameraApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()