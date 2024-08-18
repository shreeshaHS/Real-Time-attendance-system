import os

def open_folder(folder_path):
    try:
        os.startfile(folder_path)  # Opens the folder in the default file explorer
        print(f"Folder opened: {folder_path}")
    except FileNotFoundError:
        print("Folder not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    # Hardcoded folder paths
    
    folder_path = "Main\static\captured_images"  # Replace this with the path of the folder you want to open
    open_folder(folder_path)

if __name__ == "__main__":
    main()
