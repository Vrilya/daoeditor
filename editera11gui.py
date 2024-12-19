import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from gff4 import read_header, read_gff4
import json
import os
from typing import Dict, Any

class SaveGameEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Save Game Editor")
        self.root.geometry("800x600")
        
        # Configure root grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Data storage
        self.current_save_file = None
        self.save_data = None
        self.header_data = None  # Store header data
        self.stat_names = self.load_stat_names()
        self.characters = {}  # Store character data
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File operations frame
        self.file_frame = ttk.LabelFrame(self.main_container, text="File Operations", padding="5")
        self.file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.load_button = ttk.Button(self.file_frame, text="Load Save File", command=self.load_save_file)
        self.load_button.grid(row=0, column=0, padx=5)
        
        self.save_button = ttk.Button(self.file_frame, text="Save Changes", command=self.save_changes, state=tk.DISABLED)
        self.save_button.grid(row=0, column=1, padx=5)
        
        # Character selection frame
        self.char_frame = ttk.LabelFrame(self.main_container, text="Characters", padding="5")
        self.char_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.char_listbox = tk.Listbox(self.char_frame, width=30, height=10)
        self.char_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.char_listbox.bind('<<ListboxSelect>>', self.on_character_select)
        
        # Scrollbar for character listbox
        char_scrollbar = ttk.Scrollbar(self.char_frame, orient=tk.VERTICAL, command=self.char_listbox.yview)
        char_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.char_listbox.configure(yscrollcommand=char_scrollbar.set)
        
        # Attributes frame
        self.attr_frame = ttk.LabelFrame(self.main_container, text="Attributes", padding="5")
        self.attr_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        # Create a canvas and scrollbar for attributes
        self.attr_canvas = tk.Canvas(self.attr_frame)
        self.attr_scrollbar = ttk.Scrollbar(self.attr_frame, orient=tk.VERTICAL, command=self.attr_canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.attr_canvas)
        self.scrollable_frame.bind("<Configure>", 
            lambda e: self.attr_canvas.configure(scrollregion=self.attr_canvas.bbox("all")))
        
        self.attr_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.attr_canvas.configure(yscrollcommand=self.attr_scrollbar.set)
        
        self.attr_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.attr_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights for proper scaling
        # Main container
        self.main_container.columnconfigure(0, weight=1)  # Character frame column
        self.main_container.columnconfigure(1, weight=3)  # Attributes frame column
        self.main_container.rowconfigure(1, weight=1)     # Main content row
        
        # File frame
        self.file_frame.columnconfigure(1, weight=1)
        
        # Character frame
        self.char_frame.columnconfigure(0, weight=1)
        self.char_frame.rowconfigure(0, weight=1)
        
        # Attributes frame
        self.attr_frame.columnconfigure(0, weight=1)
        self.attr_frame.rowconfigure(0, weight=1)
        
    def load_stat_names(self) -> Dict[int, str]:
        """Load the stat names from stats.json file."""
        try:
            with open('stats.json', 'r') as f:
                stats = json.load(f)
            return {int(v): k for k, v in stats.items()}
        except FileNotFoundError:
            messagebox.showerror("Error", "stats.json file not found!")
            return {}
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid stats.json file!")
            return {}

    def load_save_file(self):
        """Load a save file and populate the character list."""
        filepath = filedialog.askopenfilename(
            filetypes=[("DAS files", "*.das"), ("All files", "*.*")]
        )
        if not filepath:
            return
            
        try:
            with open(filepath, 'rb') as f:
                self.header_data = read_header(f)  # Store header data
                self.save_data = read_gff4(f, self.header_data)
                
            self.current_save_file = filepath
            self.save_button.configure(state=tk.NORMAL)
            self.load_characters()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load save file: {str(e)}")
    
    def load_characters(self):
        """Load characters from save data and populate the listbox."""
        self.char_listbox.delete(0, tk.END)
        self.characters.clear()
        
        # Load main character
        try:
            player = self.save_data[16002]  # Main character structure
            crp1 = player[16208]  # Main character's data
            
            # Get character's name - using the same logic as the original script
            character_name_obj = crp1[16255] if 16255 in crp1 else None
            if isinstance(character_name_obj, object) and hasattr(character_name_obj, 's'):
                character_name = character_name_obj.s.strip('\x00')
            else:
                character_name = "Unknown Name"
            
            self.characters["Main Character"] = {
                'name': character_name,
                'data': crp1[16209]  # CPS1 structure
            }
            self.char_listbox.insert(tk.END, f"Main Character: {character_name}")
            
        except Exception as e:
            messagebox.showwarning("Warning", f"Failed to load main character: {str(e)}")
        
        # Load party members
        try:
            party_struct = self.save_data._dict.get(16003)  # StructPRTY
            if party_struct:
                party_list = party_struct._dict.get(16204)  # ListStructCRL1
                if party_list and hasattr(party_list, "_list"):
                    for i, member in enumerate(party_list._list):
                        if hasattr(member, "_dict"):
                            # Get name exactly as in original script
                            name_key = member._dict.get(3)  # ECString with character name
                            if name_key:
                                name = getattr(name_key, 's', None) or str(name_key)
                                name = name.strip('\x00')
                                name = self.format_party_member_name(name)  # Format the name
                            else:
                                name = "Unknown (name_key missing)"
                            
                            member_data = member._dict.get(16209)  # CPS1 structure
                            if member_data:
                                self.characters[f"Party Member {i}"] = {
                                    'name': name,
                                    'data': member_data
                                }
                                self.char_listbox.insert(tk.END, f"Party Member {i}: {name}")
                            
        except Exception as e:
            print(f"Error while exploring party members: {e}")
            messagebox.showwarning("Warning", f"Failed to load party members: {str(e)}")
    
    def clear_attributes(self):
        """Clear all widgets in the attributes frame."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
    
    def on_character_select(self, event):
        """Handle character selection from the listbox."""
        selection = self.char_listbox.curselection()
        if not selection:
            return
            
        self.clear_attributes()
        char_key = self.char_listbox.get(selection[0]).split(":")[0].strip()
        char_data = self.characters.get(char_key)
        
        if char_data and char_data['data']:
            self.display_attributes(char_data['data'])
    
    def display_attributes(self, cps1_struct):
        """Display character attributes in the attributes frame."""
        if not hasattr(cps1_struct, "_dict") or 16350 not in cps1_struct._dict:
            return
            
        attributes = cps1_struct._dict[16350]
        if not hasattr(attributes, "_list"):
            return
            
        for i, attr in enumerate(attributes._list):
            if not hasattr(attr, "fields"):
                continue
                
            # Get attribute type and name
            attr_type = int(attr[16353])
            attr_name = self.stat_names.get(attr_type, f"Unknown({attr_type})")
            
            # Create frame for this attribute
            attr_frame = ttk.LabelFrame(self.scrollable_frame, text=f"{attr_name}", padding="5")
            attr_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=2, padx=5)
            
            # Add entry fields for each attribute value
            row = 0
            for field in attr.fields:
                if field.label == 16353:  # Skip type ID
                    continue
                    
                field_name = self.get_field_name(field.label)
                ttk.Label(attr_frame, text=field_name).grid(row=row, column=0, sticky=tk.W, padx=5)
                
                value = attr[field.label]
                entry = ttk.Entry(attr_frame)
                entry.insert(0, str(value))
                entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
                
                # Store reference to the attribute and field for saving
                entry.attr_ref = (attr, field.label)
                
                row += 1
    
    def format_party_member_name(self, name):
        """Format party member name by removing prefix and capitalizing."""
        if name.startswith("gen00fl_"):
            name = name[8:]  # Remove "gen00fl_" prefix
        return name.capitalize()

    def get_field_name(self, field_label):
        """Convert field label to human-readable name."""
        FIELD_NAMES = {
            16300: "Base",
            16301: "Modifier",
            16302: "Current",
            16303: "Combat regen",
            16304: "Regen"
        }
        return FIELD_NAMES.get(field_label, str(field_label))
        FIELD_NAMES = {
            16300: "Base",
            16301: "Modifier",
            16302: "Current",
            16303: "Combat regen",
            16304: "Regen"
        }
        return FIELD_NAMES.get(field_label, str(field_label))
    
    def save_changes(self):
        """Save changes to the save file."""
        if not self.current_save_file or not self.header_data:
            print("Missing save file or header data")
            return
            
        try:
            print("\nStarting save process...")
            
            # Uppdatera värden från entry-fälten
            for widget in self.scrollable_frame.winfo_children():
                if isinstance(widget, ttk.LabelFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            attr, field_label = child.attr_ref
                            try:
                                value = float(child.get())
                                attr[field_label] = value
                            except ValueError:
                                messagebox.showerror("Error", f"Invalid value in {widget['text']}")
                                return
    
            # Skapa backup om den inte finns
            backup_path = self.current_save_file + ".backup"
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(self.current_save_file, backup_path)
            
            # Skapa temporär fil
            temp_path = self.current_save_file + ".temp"
            
            try:
                # Skriv direkt till temp-filen med write_gff4
                with open(temp_path, 'wb') as f:
                    from gff4 import write_gff4
                    write_gff4(f, self.save_data, self.header_data)
                
                # Om skrivningen lyckades, ersätt originalfilen
                os.replace(temp_path, self.current_save_file)
                messagebox.showinfo("Success", "Changes saved successfully!")
                
            except Exception as e:
                print(f"Error during save: {str(e)}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")
            if os.path.exists(backup_path):
                import shutil
                shutil.copy2(backup_path, self.current_save_file)
                messagebox.showinfo("Recovery", "Restored from backup after save failure.")

def main():
    root = tk.Tk()
    app = SaveGameEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()