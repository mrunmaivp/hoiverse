import os

def verify_characters(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")

    if not os.path.isdir(path):
        raise NotADirectoryError(f"Path is not a directory: {path}")

    characters = []
    for item in os.listdir(path):
        sub_path = os.path.join(path, item)
        # Check if the item is a directory
        if os.path.isdir(sub_path):
            # Look for .fbx files in this subdirectory
            for file in os.listdir(sub_path):
                file_path = os.path.join(sub_path, file)
                if file.lower().endswith('.fbx') and os.path.isfile(file_path) and "smpl" in file.lower():
                    characters.append(file_path)



    """characters = [
        os.path.join(path, file)
        for file in os.listdir(path)
        if file.lower().endswith('.fbx') and os.path.isfile(os.path.join(path, file))
    ]"""
    return characters


def verify_output_root(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")
    return path


def verify_scene(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")

    fine_path = os.path.join(path, "fine")
    if not os.path.exists(fine_path):
        raise FileNotFoundError(f"Folder 'fine' does not exist: {fine_path}")

    blend_path = os.path.join(fine_path, "scene.blend")
    if not os.path.isfile(blend_path):
        raise ValueError(f"'Scene.blend' is missing: {blend_path}")

    if not blend_path.lower().endswith(".blend"):
        raise ValueError(f"File is not a .blend file: {blend_path}")

    mask_tag_path = os.path.join(os.path.dirname(blend_path), 'MaskTag.json')
    if not os.path.exists(mask_tag_path) or not os.path.isfile(mask_tag_path):
        raise ValueError(f"The required file 'MaskTag.json' does not exist in the directory of the input scene.")

    return blend_path


def verify_infinigen(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File does not exist: {path}")
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Path is not a directory: {path}")
    #Checking whether some random samples of infinigen code exist in the directory.
    if not os.path.isdir(os.path.join(path, "infinigen_examples")) and os.path.isfile(os.path.join(path, "setup.py")):
        raise ValueError(f"The directory {path} does not seem like an infinigen directory.")
    return path
