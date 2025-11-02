import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import os
import json
import pyttsx3
import threading
import csv
from datetime import datetime
import random

class MemoraLite:
    def __init__(self):
        # Initialize
        self.root = tk.Tk()
        self.root.title("MEMORA - Smart Memory Assistant")
        self.root.geometry("800x700")
        
        # Modern Theme Colors
        self.theme = {
            'primary': "#7C4DFF",    # Rich Purple
            'secondary': "#00BFA5",  # Teal
            'bg': "#F0F7FF",        # Soft Sky Blue
            'card': "#FFFFFF",      # Pure White
            'text': "#2C3E50",      # Dark Blue-Gray
            'accent': "#FF6B6B",    # Coral Pink
            'hover': "#6B42E8",     # Deep Purple
            'gradient1': "#7C4DFF",  # Gradient Start
            'gradient2': "#448AFF"   # Gradient End
        }
        
        # No emoji/sticker decorations for stable, minimal UI
        self.stickers = None
        
        # Settings file path: prefer Windows %APPDATA% (user-specific), fallback to script dir
        appdata = os.getenv('APPDATA') or os.path.dirname(os.path.abspath(__file__))
        settings_dir = os.path.join(appdata, 'Memora')
        try:
            os.makedirs(settings_dir, exist_ok=True)
        except Exception:
            settings_dir = os.path.dirname(os.path.abspath(__file__))

        self.settings_path = os.path.join(settings_dir, 'memora_settings.json')
        self.current_theme_key = 'violet'
        # Voice enabled default
        self.voice_enabled = True
        # Load persisted settings (if any) and apply theme & voice setting
        self.load_settings()
        # Tk variable for the voice toggle (used in the menu)
        try:
            self.voice_var = tk.BooleanVar(value=self.voice_enabled)
        except Exception:
            # fallback if tk not fully initialized
            self.voice_var = None
        self.root.configure(bg=self.theme['bg'])

        # Text-to-speech
        self.voice = pyttsx3.init()
        self.voice.setProperty("rate", 165)
        
        # Create frames
        self.frames = {}
        for page in ["home", "menu", "content"]:
            self.frames[page] = tk.Frame(self.root, bg=self.theme['bg'])
        
        self.setup_ui()
        self.show_frame("home")
        self.voice.say("Welcome to Memora Lite")
    
    def create_button(self, parent, text, command, is_primary=True, width=None):
        btn = tk.Button(parent, text=text, command=command,
                       bg=self.theme['primary'] if is_primary else self.theme['secondary'],
                       fg="white",
                       font=("Helvetica", 11, "bold"),
                       relief="flat",
                       activebackground=self.theme['hover'],
                       activeforeground="white",
                       padx=20, pady=8)
        if width:
            btn.config(width=width)
        # announce option when hovered — debounce so rapid moves don't queue many speaks
        try:
            def on_enter(e, t=text, b=btn):
                # schedule speak after 300ms, store id on widget
                try:
                    if hasattr(b, '_speak_after') and b._speak_after:
                        b.after_cancel(b._speak_after)
                except Exception:
                    pass
                b._speak_after = b.after(300, lambda: self.speak(t))

            def on_leave(e, b=btn):
                try:
                    if hasattr(b, '_speak_after') and b._speak_after:
                        b.after_cancel(b._speak_after)
                        b._speak_after = None
                except Exception:
                    pass

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        except Exception:
            pass
        return btn

    def speak(self, text):
        """Speak text in background thread to avoid blocking the UI."""
        if not text or not getattr(self, 'voice_enabled', True):
            return
        threading.Thread(target=self._speak, args=(text,), daemon=True).start()

    def _speak(self, text):
        try:
            self.voice.say(text)
            self.voice.runAndWait()
        except Exception:
            # ignore TTS errors
            pass
    
    def create_card(self, parent, gradient=False):
        frame = tk.Frame(parent, bg=self.theme['card'],
                        relief="groove", bd=1, padx=20, pady=15)
        if gradient:
            canvas = tk.Canvas(frame, height=4, width=200, 
                             bg=self.theme['gradient1'], highlightthickness=0)
            canvas.pack(side="top", fill="x")
        frame.lift()
        return frame

    def set_theme(self, key='violet'):
        """Set theme from code-defined presets. No user color input."""
        presets = {
            'violet': {'primary': '#7C4DFF', 'secondary': '#00BFA5', 'bg': '#F0F7FF', 'card': '#FFFFFF', 'text': '#2C3E50', 'accent': '#FF6B6B', 'hover': '#6B42E8', 'gradient1':'#7C4DFF', 'gradient2':'#448AFF'},
            'teal':   {'primary': '#00BFA5', 'secondary': '#7C4DFF', 'bg': '#F5FFFB', 'card': '#FFFFFF', 'text': '#10302B', 'accent': '#FFD166', 'hover': '#009688', 'gradient1':'#00BFA5', 'gradient2':'#64FFDA'},
            'sunset': {'primary': '#FF7043', 'secondary': '#FFD54F', 'bg': '#FFF8F0', 'card': '#FFFFFF', 'text': '#4E342E', 'accent': '#FF6B6B', 'hover': '#FF5722', 'gradient1':'#FF7043', 'gradient2':'#FF8A65'},
            'forest': {'primary': '#2E7D32', 'secondary': '#A5D6A7', 'bg': '#F5FFF6', 'card': '#FFFFFF', 'text': '#1B5E20', 'accent': '#4CAF50', 'hover': '#1B5E20', 'gradient1':'#2E7D32', 'gradient2':'#66BB6A'}
        }
        self.theme.update(presets.get(key, {}))
        self.current_theme_key = key

    def load_settings(self):
        """Load settings from JSON file and apply theme. If file missing, apply default."""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    key = data.get('theme', 'violet')
                    self.set_theme(key)
                    # voice setting persisted
                    self.voice_enabled = data.get('voice', True)
                    return
        except Exception:
            pass
        # fallback to default
        self.set_theme(self.current_theme_key)

    def save_settings(self):
        """Persist current settings (theme key) to disk."""
        try:
            data = {'theme': self.current_theme_key, 'voice': self.voice_enabled}
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception:
            # non-fatal; ignore write errors
            pass

    def open_theme_picker(self):
        """Open a small Toplevel theme picker with preset buttons."""
        presets = {
            'violet': 'Violet',
            'teal': 'Teal',
            'sunset': 'Sunset',
            'forest': 'Forest'
        }
        win = tk.Toplevel(self.root)
        win.title('Pick Theme')
        win.geometry('360x220')
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text='Choose a theme preset', font=("Helvetica", 12, 'bold')).pack(pady=8)
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=6, padx=10, fill='x')

        for key, label in presets.items():
            b = tk.Button(btn_frame, text=label, command=(lambda k=key: (self.switch_theme(k), win.destroy())),
                          bg=self._preset_color(key, 'primary'), fg='white')
            b.pack(side='left', expand=True, fill='x', padx=6)
            # speak theme name when hovered
            try:
                b.bind('<Enter>', lambda e, t=label: self.speak(t))
            except Exception:
                pass

        # announce available themes
        try:
            self.speak('Theme picker. Available themes: Violet, Teal, Sunset, and Forest. Click a button to apply.')
        except Exception:
            pass

        # Close button
        try:
            tk.Button(win, text='Close', command=win.destroy).pack(pady=8)
        except Exception:
            pass

    def _preset_color(self, key, field='primary'):
        map_presets = {
            'violet': {'primary': '#7C4DFF'},
            'teal': {'primary': '#00BFA5'},
            'sunset': {'primary': '#FF7043'},
            'forest': {'primary': '#2E7D32'}
        }
        return map_presets.get(key, {}).get(field, self.theme['primary'])

    def switch_theme(self, key):
        """Change preset, rebuild frames and reapply UI so theme updates immediately."""
        # update theme values
        self.set_theme(key)
        # destroy existing frames
        for f in list(self.frames.values()):
            try:
                f.destroy()
            except Exception:
                pass
        # recreate frames
        self.frames = {}
        for page in ["home", "menu", "content"]:
            self.frames[page] = tk.Frame(self.root, bg=self.theme['bg'])
        # rebuild UI
        self.setup_ui()
        # show menu so user can continue
        self.show_frame('menu')
        # persist theme choice
        try:
            self.save_settings()
        except Exception:
            pass
        # announce new theme
        try:
            self.speak(f"Theme switched to {key}")
        except Exception:
            pass
        # Save voice setting as well
        try:
            self.save_settings()
        except Exception:
            pass

    def toggle_voice(self):
        """Toggle voice on/off from the menu checkbox and persist setting."""
        try:
            if hasattr(self, 'voice_var') and self.voice_var is not None:
                self.voice_enabled = bool(self.voice_var.get())
            else:
                self.voice_enabled = not getattr(self, 'voice_enabled', True)
            self.save_settings()
            if self.voice_enabled:
                self.speak('Voice enabled')
            else:
                # speak using direct thread to ensure the disabled state doesn't stop announcement
                threading.Thread(target=lambda: self._speak('Voice disabled'), daemon=True).start()
        except Exception:
            pass
    
    def add_floating_stickers(self, parent, count=3):
        # Decorations and animations disabled for stability
        return
    
    def show_frame(self, name):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True, padx=20, pady=20)
        # Announce the page and its options
        try:
            self.announce_page(name)
        except Exception:
            pass

    def announce_page(self, name):
        """Speak a short summary of the page and available options."""
        if name == 'home':
            self.speak('Welcome to Memora. Press Begin Your Journey to continue.')
        elif name == 'menu':
            self.speak('Main menu. Options are Reminders, Notes, Contacts and Journal. Use the buttons to open a section. There is also a Theme button to change the appearance.')
        elif name == 'content':
            # when content page is shown the open_category call already sets a header; give a generic hint
            self.speak('Content page. You can save entries, view recent items, or search.')
    
    def setup_ui(self):
        # Add floating stickers to all pages
        for frame in self.frames.values():
            self.add_floating_stickers(frame)

        # Home Page
        title_frame = self.create_card(self.frames["home"], gradient=True)
        title_frame.pack(pady=50, padx=30, ipady=20)
        
        # Decorative header (no emojis)
        header_frame = tk.Frame(title_frame, bg=self.theme['card'])
        header_frame.pack(fill="x", pady=(0,20))
        tk.Label(header_frame, text=' ', bg=self.theme['card']).pack(side='left', padx=20)

        tk.Label(title_frame, 
                text="MEMORA",
                font=("Helvetica", 48, "bold"),
                bg=self.theme['card'],
                fg=self.theme['primary']).pack(pady=(0,5))

        tk.Label(title_frame,
                text="Your Intelligent Memory Companion",
                font=("Helvetica", 16),
                bg=self.theme['card'],
                fg=self.theme['text']).pack(pady=(0,30))

        # Feature highlights
        features_frame = tk.Frame(title_frame, bg=self.theme['card'])
        features_frame.pack(fill="x", pady=(0,30))

        features = [
            ("Smart Organization", "Keep everything in order"),
            ("Timely Reminders", "Never miss important tasks"),
            ("Easy Access", "Simple and intuitive interface")
        ]

        for title, text in features:
            feature_card = tk.Frame(features_frame, bg=self.theme['card'])
            feature_card.pack(side="left", expand=True, padx=10)
            tk.Label(feature_card, text=title,
                    font=("Arial", 14, "bold"),
                    bg=self.theme['card']).pack()
            tk.Label(feature_card, text=text,
                    font=("Helvetica", 10),
                    bg=self.theme['card'],
                    fg=self.theme['text']).pack()
        
        # Start button with animation effect
        btn_frame = tk.Frame(title_frame, bg=self.theme['card'])
        btn_frame.pack(pady=20)
        
        start_btn = self.create_button(btn_frame, "Begin Your Journey →", 
                                     lambda: self.show_frame("menu"))
        start_btn.pack()
        
        # Menu Page (themed buttons)
        menu_header = tk.Frame(self.frames["menu"], bg=self.theme['bg'])
        menu_header.pack(fill='x', pady=(10,0), padx=20)

        tk.Label(menu_header, text="Choose Category", font=("Helvetica", 18, "bold"), bg=self.theme['bg'], fg=self.theme['text']).pack(side='left')
        # Theme button on the right of the menu header
        theme_btn = self.create_button(menu_header, "Theme", lambda: self.open_theme_picker(), is_primary=False, width=10)
        theme_btn.pack(side='right')

        # Voice toggle (persistent)
        try:
            if hasattr(self, 'voice_var') and self.voice_var is not None:
                voice_chk = tk.Checkbutton(menu_header, text='Voice', variable=self.voice_var,
                                           command=self.toggle_voice, bg=self.theme['bg'], fg=self.theme['text'], selectcolor=self.theme['card'])
            else:
                # fallback: disabled checkbox
                voice_chk = tk.Checkbutton(menu_header, text='Voice', state='disabled', bg=self.theme['bg'], fg=self.theme['text'])
            voice_chk.pack(side='right', padx=(6, 12))
        except Exception:
            pass

        menu_container = tk.Frame(self.frames["menu"], bg=self.theme['bg'])
        menu_container.pack(pady=20)
        categories = ["Reminders", "Notes", "Contacts", "Journal"]
        for cat in categories:
            btn = self.create_button(menu_container, cat, lambda c=cat: self.open_category(c), is_primary=True, width=24)
            btn.pack(pady=12)

        # Back button (secondary)
        back_btn = self.create_button(self.frames["menu"], "← Back to Home", lambda: self.show_frame("home"), is_primary=False)
        back_btn.pack(side="bottom", pady=20)
        
        # Content Page (will show forms & actions)
        self.content_label = tk.Label(self.frames["content"],
                                    font=("Helvetica", 20, "bold"),
                                    bg=self.theme['bg'],
                                    fg=self.theme['primary'])
        self.content_label.pack(pady=20)
        
        self.content_buttons = tk.Frame(self.frames["content"], bg=self.theme['bg'])
        self.content_buttons.pack(pady=20)
        
        # Back button (secondary)
        back_content = self.create_button(self.frames["content"], "← Back to Menu", lambda: self.show_frame("menu"), is_primary=False)
        back_content.pack(side="bottom", pady=20)
    
    def open_category(self, category):
        # Update header
        self.content_label.config(text=f"{category} — Quick Entry")

        # Clear existing content
        for widget in self.content_buttons.winfo_children():
            widget.destroy()

        # Create form area
        form = tk.Frame(self.content_buttons, bg=self.theme['card'], bd=1, relief='flat', padx=12, pady=12)
        form.pack(fill='x', padx=10, pady=10)

        entries = {}
        if category == 'Reminders':
            tk.Label(form, text='Title', bg=self.theme['card'], fg=self.theme['text']).pack(anchor='w')
            entries['title'] = tk.Entry(form, width=40)
            entries['title'].pack(pady=4)
            tk.Label(form, text='Time (HH:MM)', bg=self.theme['card'], fg=self.theme['text']).pack(anchor='w')
            entries['time'] = tk.Entry(form, width=20)
            entries['time'].pack(pady=4)

        elif category == 'Notes':
            tk.Label(form, text='Title', bg=self.theme['card'], fg=self.theme['text']).pack(anchor='w')
            entries['title'] = tk.Entry(form, width=40)
            entries['title'].pack(pady=4)
            tk.Label(form, text='Content', bg=self.theme['card'], fg=self.theme['text']).pack(anchor='w')
            entries['content'] = tk.Text(form, width=60, height=6)
            entries['content'].pack(pady=4)

        elif category == 'Contacts':
            tk.Label(form, text='Name', bg=self.theme['card'], fg=self.theme['text']).pack(anchor='w')
            entries['name'] = tk.Entry(form, width=40)
            entries['name'].pack(pady=4)
            tk.Label(form, text='Phone', bg=self.theme['card'], fg=self.theme['text']).pack(anchor='w')
            entries['phone'] = tk.Entry(form, width=30)
            entries['phone'].pack(pady=4)

        elif category == 'Journal':
            tk.Label(form, text='Mood (one word)', bg=self.theme['card'], fg=self.theme['text']).pack(anchor='w')
            entries['mood'] = tk.Entry(form, width=30)
            entries['mood'].pack(pady=4)
            tk.Label(form, text='Notes', bg=self.theme['card'], fg=self.theme['text']).pack(anchor='w')
            entries['notes'] = tk.Text(form, width=60, height=6)
            entries['notes'].pack(pady=4)

        # Save and utility buttons
        btn_row = tk.Frame(self.content_buttons, bg=self.theme['bg'])
        btn_row.pack(fill='x', padx=10, pady=(6,0))

        save_btn = self.create_button(btn_row, 'Save Entry', lambda e=entries, c=category: self.save_item_form(c, e), is_primary=True)
        save_btn.pack(side='left', padx=6)

        view_btn = self.create_button(btn_row, 'View Recent', lambda c=category: self.view_items(c), is_primary=False)
        view_btn.pack(side='left', padx=6)

        search_btn = self.create_button(btn_row, 'Search', lambda c=category: self.search_items(c), is_primary=False)
        search_btn.pack(side='left', padx=6)

        # announce available actions for this category
        try:
            self.speak(f"{category} options: Save Entry, View Recent, and Search.")
        except Exception:
            pass

        self.show_frame('content')
    
    def view_items(self, category):
        try:
            with open(f"{category.lower()}.csv", 'r') as f:
                data = list(csv.reader(f))[-5:]  # Show last 5 entries
                text = "\n".join([" | ".join(row) for row in data])
                messagebox.showinfo(category, text if data else "No entries found")
        except FileNotFoundError:
            messagebox.showinfo(category, "No entries found")
    
    def add_item(self, category):
        if category == "Reminders":
            title = simpledialog.askstring("New Reminder", "What to remind?")
            time = simpledialog.askstring("New Reminder", "When? (HH:MM)")
            if title and time:
                self.save_item("reminders.csv", [datetime.now().date(), time, title])
        
        elif category == "Notes":
            note = simpledialog.askstring("New Note", "Enter your note:")
            if note:
                self.save_item("notes.csv", [datetime.now(), note])
        
        elif category == "Contacts":
            name = simpledialog.askstring("New Contact", "Name:")
            phone = simpledialog.askstring("New Contact", "Phone:")
            if name and phone:
                self.save_item("contacts.csv", [name, phone])
        
        elif category == "Journal":
            mood = simpledialog.askstring("Journal", "How are you feeling?")
            if mood:
                self.save_item("journal.csv", [datetime.now(), mood])
    
    def save_item(self, filename, data):
        with open(filename, 'a', newline='') as f:
            csv.writer(f).writerow(data)
        messagebox.showinfo("Success", "Entry saved!")

    def save_item_form(self, category, entries):
        """Collect values from the form widgets and save to the appropriate CSV."""
        try:
            if category == 'Reminders':
                title = entries['title'].get().strip()
                time = entries['time'].get().strip()
                if not title or not time:
                    messagebox.showwarning('Missing', 'Please enter title and time')
                    return
                self.save_item('reminders.csv', [datetime.now().strftime('%Y-%m-%d'), time, title])

            elif category == 'Notes':
                title = entries['title'].get().strip()
                content = entries['content'].get('1.0', 'end').strip()
                if not title or not content:
                    messagebox.showwarning('Missing', 'Please enter title and content')
                    return
                self.save_item('notes.csv', [datetime.now().strftime('%Y-%m-%d %H:%M'), title, content])

            elif category == 'Contacts':
                name = entries['name'].get().strip()
                phone = entries['phone'].get().strip()
                if not name or not phone:
                    messagebox.showwarning('Missing', 'Please enter name and phone')
                    return
                self.save_item('contacts.csv', [name, phone])

            elif category == 'Journal':
                mood = entries['mood'].get().strip()
                notes = entries['notes'].get('1.0', 'end').strip()
                if not mood:
                    messagebox.showwarning('Missing', 'Please enter your mood')
                    return
                self.save_item('journal.csv', [datetime.now().strftime('%Y-%m-%d %H:%M'), mood, notes])

            # Provide subtle voice feedback if available
            try:
                self.voice.say('Entry saved')
                self.voice.runAndWait()
            except Exception:
                pass

        except Exception as e:
            messagebox.showerror('Error', f'Could not save entry: {e}')
    
    def search_items(self, category):
        term = simpledialog.askstring("Search", "Enter search term:")
        if term:
            try:
                with open(f"{category.lower()}.csv", 'r') as f:
                    data = list(csv.reader(f))
                    matches = [row for row in data if any(term.lower() in str(cell).lower() for cell in row)]
                    text = "\n".join([" | ".join(row) for row in matches])
                    messagebox.showinfo("Search Results", text if matches else "No matches found")
            except FileNotFoundError:
                messagebox.showinfo("Search", "No entries to search")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MemoraLite()
    app.run()
