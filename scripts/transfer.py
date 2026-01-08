import os
import shutil

# Root directory to start the search
root_dir = "."

for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
    # Move README.md from .chern folders
    if ".chern" in dirnames:
        chern_path = os.path.join(dirpath, ".chern")
        readme_path = os.path.join(chern_path, "README.md")
        if os.path.exists(readme_path):
            shutil.move(readme_path, os.path.join(dirpath, "README.md"))
            print(f"Moved {readme_path} -> {os.path.join(dirpath, 'README.md')}")

        # Rename .chern to .celebi
        celebi_path = os.path.join(dirpath, ".celebi")
        shutil.move(chern_path, celebi_path)
        print(f"Renamed {chern_path} -> {celebi_path}")

    # Rename chern.yaml to celebi.yaml
    for filename in filenames:
        if filename == "chern.yaml":
            old_yaml = os.path.join(dirpath, filename)
            new_yaml = os.path.join(dirpath, "celebi.yaml")
            os.rename(old_yaml, new_yaml)
            print(f"Renamed {old_yaml} -> {new_yaml}")

