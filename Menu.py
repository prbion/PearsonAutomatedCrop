# Menu.py
import string

class Menu:
    def __init__(self):
        self.publisher = input("What Publisher? ").strip()
        self.level     = input("What Level? ").strip()
        self.subject   = input("What Subject? ").strip()
        self.year      = input("What Year? ").strip()
        self.paper     = input("What Paper number? ").strip()   # <-- NEW

        self.file_prefix = f"{self.publisher}_{self.level}_{self.subject}_{self.year}"
        self.folder_name = f"{self.publisher}_{self.subject}_{self.year}"

    def display_prefix(self):
        print(f"\nGenerated File Prefix: {self.file_prefix}")
        print(f"Target Folder: {self.folder_name}")
