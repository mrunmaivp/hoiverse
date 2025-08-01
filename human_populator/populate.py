#!/usr/bin/env python3
import os
import argparse
import shutil

import numpy as np

from InfinigenPopulator.logic.blender_logic import process_scene
from InfinigenPopulator.logic.render_logic import render_images_gt
from InfinigenPopulator.extras.verification import verify_characters, verify_scene, verify_infinigen, verify_output_root

from infinigen_examples.generate_nature import main as infinigen_render



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_folder")
    parser.add_argument("output_root")
    parser.add_argument("characters")

    args = parser.parse_args()
    infinigen_path = os.path.dirname(os.path.dirname(infinigen_render.__code__.co_filename))

    infinigen_path = verify_infinigen(infinigen_path)
    input_path = args.input_folder
    input_scene = verify_scene(input_path)
    output_root = verify_output_root(args.output_root)
    available_characters = verify_characters(args.characters)

    seed = os.path.basename(input_path)
    if not seed:
        input_path_new = input_path[:-1]
        seed = os.path.basename(input_path_new)
    print("Scene Seed: ", seed)

    output_scene_dir = os.path.join(output_root, str(seed))
    os.makedirs(output_scene_dir, exist_ok=True)

    scene_dir = os.path.join(output_scene_dir, "fine")
    os.makedirs(scene_dir, exist_ok=True)

    input_path = os.path.dirname(input_scene)
    masktag_path = os.path.join(input_path, "MaskTag.json")
    shutil.copy(masktag_path, scene_dir)

    output_scene = os.path.join(scene_dir, "scene.blend")

    print("\n=== Processing scene in Blender ===")
    camera_id_list = process_scene(input_scene, output_scene, available_characters)
    print("Cameras to render: ", len(camera_id_list))

    render_dir = os.path.join(output_scene_dir, "frames")
    os.makedirs(render_dir, exist_ok=True)

    os.chdir(infinigen_path)


    print("\n=== Running infinigen ===")
    render_images_gt(scene_dir, render_dir, seed, camera_id_list)
    print("All steps completed successfully.")

if __name__ == "__main__":
    main()
