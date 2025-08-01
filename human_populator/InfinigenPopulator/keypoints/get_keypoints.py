import bpy
import bpy_extras
from mathutils import Vector
import os
import json
from argparse import ArgumentParser
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import re

def plot_keypoint(camera_keypoints, scenedir, scene_name):
    for cam_name, humans in camera_keypoints.items():
        if cam_name not in ['Camera', 'Camera.001']:
            i = cam_name.split("_")[1]
            image_name = f"Image_{i}_0_0048_0.png"
            image_path = os.path.join(scenedir, scene_name, "frames/Image/camera_0", image_name)
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            for armature_name, keypoints in humans.items():
                for center in keypoints.values():
                    if center is not None:
                        bbox = [
                            (center[0] - 3, center[1] - 3),
                            (center[0] + 3, center[1] + 3)
                        ]
                        draw.ellipse(bbox, fill="white")
            plt.imshow(img)
            plt.axis("off")
            plt.title("Image with Point")
            plt.show()


def get_keypoints(scenedir):
    for scene_name in os.listdir(scenedir):
        scene_path = os.path.join(scenedir, scene_name, "fine/scene.blend")
        bpy.ops.wm.open_mainfile(filepath=scene_path)

        scene = bpy.context.scene
        render = scene.render
        resolution_x = render.resolution_x
        resolution_y = render.resolution_y

        camera_keypoints = {}

        for cam_obj in bpy.data.objects:
            if cam_obj.type != 'CAMERA':
                continue
            cam_name = cam_obj.name
            if cam_name not in ['Camera', 'Camera.001'] and re.search("^camera.*0$", cam_name):
                i = cam_name.split("_")[1]
                image_name = f"Image_{i}_0_0048_0.png"

                camera_keypoints[image_name] = {}

                for obj in bpy.data.objects:
                    if "SMPLX-lh" in obj.name and obj.type == 'ARMATURE':
                        armature = obj

                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.object.select_all(action='DESELECT')
                        armature.select_set(True)
                        bpy.context.view_layer.objects.active = armature
                        bpy.ops.object.mode_set(mode='POSE')

                        keypoints_3d = {}
                        for bone in armature.pose.bones:
                            if bone.name.endswith("_end"):
                                continue
                            pos = armature.matrix_world @ bone.head
                            keypoints_3d[bone.name] = pos

                        keypoints_2d = {}
                        for bone_name, pos in keypoints_3d.items():
                            co_ndc = bpy_extras.object_utils.world_to_camera_view(scene, cam_obj, pos)
                            if 0.0 <= co_ndc.x <= 1.0 and 0.0 <= co_ndc.y <= 1.0 and co_ndc.z >= 0:
                                x = int(co_ndc.x * resolution_x)
                                y = int((1.0 - co_ndc.y) * resolution_y)
                                keypoints_2d[bone_name] = (x, y)
                            else:
                                keypoints_2d[bone_name] = None

                        camera_keypoints[image_name][armature.name] = keypoints_2d

        #plot_keypoint(camera_keypoints, scenedir, scene_name)

        output_path = os.path.join(scenedir, scene_name, "fine/keypoints.json")
        with open(output_path, "w") as f:
            json.dump(camera_keypoints, f, indent=2)

        print(f"Saved 2D keypoints to {output_path}")

def cli():
    parser = ArgumentParser()
    parser.add_argument("scenedir")
    args = parser.parse_args()
    get_keypoints(args.scenedir)

if __name__ == "__main__":
    cli()
