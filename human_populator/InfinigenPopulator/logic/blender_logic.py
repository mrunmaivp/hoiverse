import os
import numpy as np

from InfinigenPopulator.managers.pose_manager import PoseManager
from InfinigenPopulator.managers.scene_manager import SceneManager
from InfinigenPopulator.managers.character_manager import CharacterManager
from InfinigenPopulator.managers.annotation_manager import AnnotationManager
import infinigen.core.placement.camera as cam_util


def find_character_by_keyword(characters, keyword):
    """Returns character and updated list after removal based on keyword."""
    for i, char in enumerate(characters):
        if keyword in char:
            return characters.pop(i)
    return None


def process_scene(scene_path: str, save_path: str, characters: list[str]):
    """
    Adds characters to a scene based on valid poses and saves the scene.
    Returns list of camera_ids to render.
    """
    scene_manager = SceneManager()
    scene = scene_manager.load_scene(scene_path)

    floor_area = scene_manager.get_floor_area()
    floor_name = scene_manager.floor
    valid_poses = scene_manager.get_valid_poses()
    annotation_path = os.path.join(os.path.dirname(save_path), "annotations.json")

    print("Valid poses for this scene:", valid_poses)

    num_chars = np.random.randint(2, 3) if floor_area < 25.0 else np.random.randint(4, 6)
    print("Characters required for this scene:", characters)

    # Poses that need extra positioning
    positioning_required_poses = {
        "waving", "holding glass", "holding apple", "arms down", "smpl"
    }

    prioritized_poses = {
        "smpl sitting chair": "chair",
        "watering plant": "watering",
        "smpl eating": "eating",
        "smpl sleeping on bed": "sleeping",
        "smpl working on computer": "working-computer"
    }

    for i in range(num_chars):
        print(f"Adding character {i + 1} / {num_chars}")
        chosen_pose, chosen_character = None, None

        for pose, keyword in prioritized_poses.items():
            if pose in valid_poses:
                character = find_character_by_keyword(characters, keyword)
                if character:
                    chosen_pose = pose
                    chosen_character = character
                    valid_poses.remove(pose)
                    break

        if not chosen_character:
            if not valid_poses or not characters:
                print("No valid poses or characters left.")
                continue

            if "bathroom" in floor_name or "kitchen" in floor_name:
                filtered = [char for char in characters if "doing" not in char and "smpli" in char]
            else:
                filtered = [char for char in characters if "smpli" in char]

            if not filtered:
                print("No suitable characters for fallback.")
                continue

            chosen_pose = np.random.choice(valid_poses)
            chosen_character = filtered[np.random.randint(len(filtered))]
            characters.remove(chosen_character)

        print(f"Chosen character: {chosen_character}")
        print(f"Pose: {chosen_pose}")

        # Import character
        character_manager = CharacterManager(chosen_character)
        character_manager.import_posed_fbx_character()

        # Set pose
        pose_manager = PoseManager(character_manager)
        pose_manager.set_pose(chosen_pose)

        if chosen_pose in positioning_required_poses:
            positions = character_manager.find_valid_positions(scene_manager.floor)
            if positions:
                pos = positions[np.random.randint(len(positions))]
                rot = np.random.randint(0, 360)
                print(f"Placing at position {pos}, rotation {rot}")
                character_manager.place_character(pos)
                character_manager.rotate_character(rot)

        # Add camera and annotate
        new_camera = character_manager.add_camera()
        cam_util.adjust_camera_sensor(new_camera)

        annotation_manager = AnnotationManager(annotation_path)
        annotation_manager.add_annotation(character_manager)
        annotation_manager.write_json()

    # Save scene and return camera IDs
    camera_rigs = cam_util.get_camera_rigs()
    camera_id_list = [[i, 0] for i in range(len(camera_rigs))]

    scene_manager.save_scene(save_path)
    return camera_id_list
