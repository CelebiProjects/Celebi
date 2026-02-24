'''
    Generate or remove the data for the project.
'''
import os
import shutil

def create_chern_project(src):
    '''
    Create the project directory.
    '''
    base_dir = os.path.dirname(__file__)
    data_root = os.path.join(base_dir, "data")
    source_path = os.path.join(data_root, src)
    # Check whether the directory already exists.
    if shutil.os.path.exists(src):
        print(f"Directory {src} already exists. Remove it first.")
        shutil.rmtree(src)
    # Copy the folder from data to the directory.
    shutil.copytree(source_path, src)

def remove_chern_project(src):
    '''
    Remove the project directory.
    '''
    # Remove the folder.
    shutil.rmtree(src)
