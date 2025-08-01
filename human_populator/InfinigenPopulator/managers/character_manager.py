import re

import bpy
# noinspection PyUnresolvedReferences
from mathutils import Vector
from InfinigenPopulator.managers.item_manager import ItemManager
from InfinigenPopulator.extras.utils import Utils
# noinspection PyUnresolvedReferences
from numpy import radians
import os



class CharacterManager:
    def __init__(self, character_path):
        self.character_path = character_path
        self.character = None
        self.pose = character_path.split('/')[-1].split('.')[0]
        self.character_name = character_path.split('/')[-1].split('.')[0]
        self.relations = {}
        self.mesh = None
        self.camera = None
        self.interacted_obj = None


    def import_character(self):
        try:
            existing_objects = set(bpy.data.objects)
            bpy.ops.import_scene.fbx(filepath=self.character_path)
            new_objects = set(bpy.data.objects) - existing_objects
            armatures = [obj for obj in new_objects if obj.type == 'ARMATURE']
            self.character = armatures[0]
            mesh_children = [obj for obj in self.character.children if obj.type == "MESH"]
            self.mesh = mesh_children[0].name
            print("Imported: ", self.character.name)
        except Exception as e:
            raise RuntimeError(f"Error during character import: {e}")

    def import_smpl_character(self):
        try:
            existing_objects = set(bpy.data.objects)
            bpy.ops.import_scene.fbx(filepath=os.path.join(self.character_path))
            new_objects = set(bpy.data.objects) - existing_objects
            new_obj = [obj for obj in new_objects]
            for obj in new_obj:
                if obj.type == "ARMATURE" and "smpl" in obj.name.lower():
                    self.character = obj
            mesh_children = [obj for obj in self.character.children if obj.type == "MESH"]
            self.mesh = mesh_children[0].name
            print("Self character: ", self.character)
            print("Mesh Children: ", self.mesh)
        except:
            raise RuntimeError("Error during character import")




    def import_posed_fbx_character(self):
        try:
            existing_objects = set(bpy.data.objects)
            bpy.ops.import_scene.fbx(filepath=self.character_path)
            new_objects = set(bpy.data.objects) - existing_objects
            new_obj = [obj for obj in new_objects]
            for obj in new_obj:
                if obj.type == "ARMATURE" and "smpl" in obj.name.lower():
                    self.character = obj
                if obj.type == "MESH" and "smpl" not in obj.name.lower():
                    self.interacted_obj = obj
            print("Self character: ", self.character)
            print("Interacting with: ", self.interacted_obj)
        except:
            raise RuntimeError("Error during character import")


    def stop_animation(self, frame, scene):
        if not self.character:
            raise RuntimeError("Character not imported. Call import_character() first.")
        if frame < 0:
            raise ValueError("Frame number must be positive")
        scene.frame_end = frame
        scene.frame_current = frame
        bpy.context.view_layer.update()

    def prepare_for_segmentation(self):
        self._merge_children_into_one()
        self._unparent_surface()

    def _merge_children_into_one(self):
        if not self.character or self.character.type != 'ARMATURE':
            raise RuntimeError("Character armature is not set or invalid.")

        for mod in self.character.modifiers:
            if mod.type == 'ARMATURE':
                bpy.ops.object.modifier_apply(modifier=mod.name)

        child_objects = [obj for obj in self.character.children if obj.type == 'MESH']
        bpy.ops.object.select_all(action='DESELECT')
        for obj in child_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = child_objects[0]
        bpy.ops.object.join()

    def _unparent_surface(self):
        """Has to be executed AFTER get_information since self.character.name might not still work after!"""
        armature_name = self.character.name
        if not self.character or self.character.type != 'ARMATURE':
            raise RuntimeError("Character armature is not set or invalid.")
        child_objects = [obj for obj in self.character.children if obj.type == 'MESH']
        assert len(child_objects) == 1
        child = child_objects[0]
        bpy.ops.object.select_all(action='DESELECT')
        child.select_set(True)
        bpy.context.view_layer.objects.active = child
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        child.select_set(False)
        self.character.select_set(True)
        #bpy.ops.object.delete()
        self.character.name = armature_name + "_old"
        child.name = armature_name


    def find_valid_positions(self, floor_name=None, grid_spacing=0.35):
        valid_positions = Utils.get_valid_ground_positions(self.character, floor_name,  grid_spacing)
        if not valid_positions:
            print("Found no valid positions! Kept at origin coordinates!")
            valid_positions = [self.character.location]
        return valid_positions




    def place_character(self, position):
        print("Trying to place character: ", self.character_name)
        if self.character:
            self.character.location = position
            if "situps" in self.character_name.lower():
                self.character.location[2] += 0.48
            if "yoga" in self.character_name.lower() or "sitting" in self.character_name.lower():
                self.character.location[2] += 0.56
            if "gnome" in self.character_name.lower():
                self.character.location[2] += 1.28
            if "time" in self.character_name.lower() or "playing-guitar" in self.character_name.lower():
                self.character.location[2] += 1.4
            if "shoe" in self.character_name.lower():
                self.character.location[2] += 1.05

            print(f"Character placed at: {self.character.location}")
        else:
            raise RuntimeError("No character imported yet.")


    def rotate_character(self, degrees):
        """Rotates character counter-clockwise in degrees."""
        angle_radians = radians(degrees)
        bpy.context.view_layer.objects.active = self.character
        self.character.rotation_mode = 'XYZ'
        self.character.rotation_euler[2] += angle_radians


    def add_camera(self):
        camera_rigs_collection = bpy.data.collections["camera_rigs"]
        non_camera_objects = [obj for obj in camera_rigs_collection.objects if obj.type != 'CAMERA']
        camrigs_count = len(non_camera_objects)
        camera_rig = bpy.data.objects.new(f"camrig.{camrigs_count}", None)

        camera_rig.empty_display_size = 0.1
        camera_rigs_collection.objects.link(camera_rig)

        cameras_collection = bpy.data.collections["cameras"]
        cam_data = bpy.data.cameras.new(name=f"camera_{camrigs_count}_0")
        camera = bpy.data.objects.new(f"camera_{camrigs_count}_0", cam_data)
        camera.parent = camera_rig
        cameras_collection.objects.link(camera)

        loc_constraint = camera_rig.constraints.new(type='COPY_LOCATION')
        loc_constraint.target = self.character
        loc_constraint.subtarget = "head"

        rot_constraint = camera_rig.constraints.new(type='COPY_ROTATION')
        rot_constraint.target = self.character
        rot_constraint.subtarget = "head"

        camera.rotation_mode = 'XYZ'
        camera.rotation_euler[1] += radians(180)
        camera.rotation_euler[2] += radians(0)
        if "time" in self.character_name.lower():
            camera.rotation_euler[0] += radians(-10)
        camera.location = camera.location + Vector((0.0, -0.03, 0.15))

        camera.data.lens = 20.0
        self.camera = camera.name
        return camera

    def get_information(self):
        if not self.character:
            raise RuntimeError("No character!")
        character_data = {
            "id": None,
            "name": self.character.name,
            "pose": self.pose
        }
        return character_data


    def get_relations(self):
        if not self.character:
            raise RuntimeError("No character!")
        character_relations = []
        for key, value in self.relations.items():
            relation = {
                "character": self.mesh.name,
                "type": key,
                "object": value
            }
            character_relations.append(relation)
        return character_relations


def replace_map_kd(mtl_file,  new_tex_path):
    # Read the entire file
    with open(mtl_file, 'r') as f:
        text = f.read()

    # Replace any line starting with "map_Kd" (plus whitespace) up to end-of-line
    new_text = re.sub(
        r'^(map_Kd\s+).*$',
        rf'\1{new_tex_path}',
        text,
        flags=re.MULTILINE
    )

    # Write out
    with open(mtl_file, 'w') as f:
        f.write(new_text)
