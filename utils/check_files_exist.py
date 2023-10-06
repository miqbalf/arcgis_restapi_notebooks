import arcpy
import os

def create_folder(workspace, folder_name):
    # check if exist
    folder_path = os.path.join(workspace, folder_name)
    if not arcpy.Exists(folder_path):
        os.mkdir(folder_path)
        print(f"Folder '{folder_name}' created in workspace: {workspace}")
    else:
        print(f"Folder '{folder_name}' already exists in workspace: {workspace}")
    
    return folder_path

    
