#Menu.py
import string 

class Menu: 
    def __init__(self):
        # --- New Input Section ---
        self.publisher = input("What Publisher? ").strip()
        self.level = input("What Level? ").strip()
        self.subject = input("What Subject? ").strip()
        self.year = input("What Year? ").strip()
        
        # 1. The filename prefix (includes Level)
        self.file_prefix = f"{self.publisher}_{self.level}_{self.subject}_{self.year}"

        # 2. The folder name (Publisher_Subject_Year)
        self.folder_name = f"{self.publisher}_{self.subject}_{self.year}"

    def display_prefix(self):
        print(f"\nGenerated File Prefix: {self.file_prefix}")
        print(f"Target Folder: {self.folder_name}")

if __name__ == "__main__":
    my_menu = Menu()
    my_menu.display_prefix()
