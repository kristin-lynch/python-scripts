import os

def rename_files(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in dirs + files:
            if name != name.lower():
                old_path = os.path.join(root, name)
                new_path = os.path.join(root, name.lower())
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: {old_path} -> {new_path}")
                except Exception as e:
                    print(f"Error renaming {old_path}: {e}")

# Change this to your target directory or use '.' for current directory
# target_directory = '/path/to/your/folder'
target_directory = '/Users/kristin/Downloads/new folder'
rename_files(target_directory)