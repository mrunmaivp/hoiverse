import os
from random import random

import bpy
import numpy as np
from numpy import radians
import re

from InfinigenPopulator.extras.utils import Utils
from InfinigenPopulator.managers.character_manager import CharacterManager
from InfinigenPopulator.managers.item_manager import ItemManager
from InfinigenPopulator.extras.bone_mapping import bone_name_mapping, BONE_LOOKUPS
from InfinigenPopulator.managers.scene_manager import SceneManager
# noinspection PyUnresolvedReferences
from mathutils import Vector
import math

IMPLEMENTED_POSES = ["waving", "fixing desk", "holding glass", "watering plant", "holding apple", "touching chair",
                     "arms down", "smpl", "smpl_sitting_on_object", "smpl working on computer", "smpl sitting chair",
                     "smpl sleeping on bed", "smpl eating"]


class PoseManager:
    def __init__(self, character_manager: CharacterManager):
        self.character_manager = character_manager
        self.character = character_manager.character
        self.rig_type = re.split(r"[_|-]", character_manager.character_name)[0].lower()
        print(self.rig_type)
        self.bone_lookup = BONE_LOOKUPS[self.rig_type]
        self.prev_obj = None

    def set_pose(self, pose: str):
        print("set pose", pose)
        if pose.lower() not in IMPLEMENTED_POSES:
            raise ValueError("Pose not implemented! Must be one of {}".format(IMPLEMENTED_POSES))
        self.character_manager.pose = pose
        match pose:
            case "waving": self._set_waving_pose()
            case "fixing desk": self._set_fixing_desk()
            case "holding glass": self._set_holding_glass()
            case "watering plant": self._set_smpl_watering_plant()
            case "holding apple": self._set_holding_apple()
            case "touching chair": self._set_touching_chair()
            case "arms down": self._set_arms_down_pose()
            case "smpl": self._integrate_smpl_pose()
            case "smpl_sitting_on_object": self._integrate_smpl_sitting_on_object()
            case "smpl working on computer": self._set_working_on_computer()
            case "smpl sitting chair": self._set_sitting_on_chair_pose()
            case "smpl sleeping on bed": self._set_sleeping_on_bed()
            case "smpl eating": self._set_eating_pose()

    def check_human_exists(self, objects):
        all_objects = [obj.name for obj in bpy.context.scene.objects if obj.type != "CAMERA"]
        humans = [name for name in all_objects if "SMPLX-lh" in name]
        # chosen_object = np.random.choice(objects)

        for human in humans:
            human_pos = bpy.data.objects.get(human)
            for obj in objects:
                sitting_object = bpy.data.objects.get(obj)
                world_corners = [sitting_object.matrix_world @ Vector(corner) for corner in sitting_object.bound_box]
                centroid = sum(world_corners, Vector()) / 8
                if human_pos.location.x == centroid.x and human_pos.location.y == centroid.y:
                    objects.remove(obj)

        chosen_object = np.random.choice(objects)

        return chosen_object

    def _set_smpl_watering_plant(self):
        temp_scene_manager = SceneManager()
        temp_scene_manager.connect_loaded_scene()

        objects = [obj.name for obj in bpy.context.scene.objects if obj.type != "CAMERA"]
        all_plants = [name for name in objects if "LargePlantContainer" in name]
        plant = all_plants[0]

        plant_container = bpy.data.objects.get(plant)

        margin = 0.6

        half_x = plant_container.dimensions.x / 4
        half_y = plant_container.dimensions.y / 4

        candidate_offsets = [
            Vector((half_x + margin, 0, 0)),  # Right
            Vector((-half_x - margin, 0, 0)),  # Left
            Vector((0, half_y + margin, 0)),  # Front
            Vector((0, -half_y - margin, 0))  # Back
        ]

        available_position = None
        for i, offset in enumerate(candidate_offsets):
            candidate_position = plant_container.location + offset
            free, colliding_obj = Utils.is_space_free(candidate_position, self.character, temp_scene_manager.floor)
            if free:
                available_position = candidate_position
                print(f"Found free space next to plant at {candidate_position}")
                break

        if available_position is not None:
            self.character.location = available_position
            direction = plant_container.location - available_position
            angle = math.atan2(direction.y, direction.x) + math.pi / 2
            self.character.rotation_euler.z = angle - math.pi / 4
            self.character.location.z = plant_container.location.z + 1.1
            self.character.scale = (0.9, 0.9, 0.9)
        else:
            print("Couldn't find space next to plant, so fell back to default poses!")
            #self._set_holding_apple()

        #item_manager = ItemManager()
        #item_manager.import_watering_can()
        self.character_manager.relations["watering"] = plant_container.name

    def _set_eating_pose(self):
        objects = [obj.name for obj in bpy.context.scene.objects if obj.type != "CAMERA"]
        obj_names = ["ChairFactory"]
        dining_object = bpy.data.objects.get([name for name in objects if "TableDiningFactory" in name and "spawn" in name][0])
        sittable_objects = [obj for name in obj_names for obj in objects if name in obj]
        sittable_objects = [name for name in sittable_objects if "spawn_asset" in name]
        scene_manager = SceneManager()
        scene_manager.connect_loaded_scene()
        floor = bpy.data.objects.get(scene_manager.floor)
        saved_height = floor.location[2]
        chosen_object = self.check_human_exists(sittable_objects)
        sitting_object = bpy.data.objects.get(chosen_object)
        print("Monitor location", sitting_object.location)

        world_corners = [sitting_object.matrix_world @ Vector(corner) for corner in sitting_object.bound_box]
        centroid = sum(world_corners, Vector()) / 8

        self.character_manager.relations["sitting-on-chair"] = sitting_object.name
        if "cake" in self.character_manager.character_path:
            self.character_manager.relations["eating"] = "carrot_cake"
            self.character_manager.relations["holding"] = "wooden_spoon"
        else:
            self.character_manager.relations["eating"] = "Croissant_croissant_10M_textured.002"
            self.character_manager.relations["holding"] = "Croissant_croissant_10M_textured.002"


        sitting_object_z = round(sitting_object.rotation_euler.z, 3)
        self.character.location = centroid
        self.character.rotation_mode = 'XYZ'
        self.character.rotation_euler.z = sitting_object_z + math.pi / 2
        self.character.scale = (0.8, 0.8, 0.8)
        self.character.location[2] = sitting_object.location.z + 0.45 if "ChairFactory" in chosen_object else sitting_object.location.z + 0.4
        children = self.character.children
        child_object = [obj for obj in children if "carved_wooden_plate" in obj.name][0]
        table_wm = dining_object.matrix_world
        world_bbox = [table_wm @ Vector(corner) for corner in dining_object.bound_box]
        max_z = max(v.z for v in world_bbox)
        child_object.location = Vector(
            (child_object.location.x, child_object.location.y, max_z - self.character.location.z))
        print("Set eating pose!")


    def _set_sleeping_on_bed(self):
        objects = [obj.name for obj in bpy.context.scene.objects if obj.type != "CAMERA"]
        sittable_objects = [name for name in objects if "BedFactory" in name]
        sittable_objects = [name for name in sittable_objects if "spawn_asset" in name]
        scene_manager = SceneManager()
        scene_manager.connect_loaded_scene()
        floor = bpy.data.objects.get(scene_manager.floor)
        saved_height = floor.location[2]
        chosen_object = self.check_human_exists(sittable_objects)
        sitting_object = bpy.data.objects.get(chosen_object)
        print("Monitor location", sitting_object.location)

        world_corners = [sitting_object.matrix_world @ Vector(corner) for corner in sitting_object.bound_box]
        centroid = sum(world_corners, Vector()) / 8

        sitting_object_z = round(sitting_object.rotation_euler.z, 3)
        self.character.location = centroid
        self.character.rotation_mode = 'XYZ'
        self.character.rotation_euler.z = sitting_object_z + 3 * math.pi / 4 + math.pi / 2
        self.character.scale = (0.8, 0.8, 0.8)
        self.character.location[2] = sitting_object.location.z + 0.7
        self.character_manager.relations["sleeping-on-bed"] = sitting_object.name
        print("Set sleeping on bed pose!")

    def _set_sitting_on_chair_pose(self):
        objects = [obj.name for obj in bpy.context.scene.objects if obj.type != "CAMERA"]
        obj_names = ["ChairFactory", "SofaFactory", "BedFactory"]
        sittable_objects = [obj for name in obj_names for obj in objects if name in obj]
        sittable_objects = [name for name in sittable_objects if "spawn_asset" in name]
        scene_manager = SceneManager()
        scene_manager.connect_loaded_scene()
        floor = bpy.data.objects.get(scene_manager.floor)
        saved_height = floor.location[2]
        chosen_object = self.check_human_exists(sittable_objects)
        sitting_object = bpy.data.objects.get(chosen_object)
        print("Monitor location", sitting_object.location)

        world_corners = [sitting_object.matrix_world @ Vector(corner) for corner in sitting_object.bound_box]
        centroid = sum(world_corners, Vector()) / 8

        self.character_manager.relations["sitting-on-chair"] = sitting_object.name

        sitting_object_z = round(sitting_object.rotation_euler.z, 3)
        #if "ChairFactory" not in chosen_object:
        #    if sitting_object_z == round(math.pi, 3) or sitting_object_z == round(-math.pi, 3):
        #        new_position = centroid + Vector((-1.0, -1.0, 0))
        #    elif sitting_object_z == round(math.pi / 2, 3):
        #        new_position = centroid + Vector((-1.0, 1.0, 0))
        #    elif sitting_object_z == round(-math.pi / 2, 3):
        #        new_position = centroid + Vector((1.0, -1.0, 0))
        #    else:
        #        new_position = centroid + Vector((1.0, 1.0, 0))
        #else:
        #    new_position = centroid

        self.character.location = centroid
        self.character.rotation_mode = 'XYZ'
        self.character.rotation_euler.z = sitting_object_z + 3 * math.pi / 4
        self.character.scale = (0.8, 0.8, 0.8)
        self.character.location[2] = sitting_object.location.z + 0.45 if "ChairFactory" in chosen_object else sitting_object.location.z + 0.45
        print("Set working on computer pose!")

    def _set_working_on_computer(self):
        objects = [obj.name for obj in bpy.context.scene.objects if obj.type != "CAMERA"]
        monitor_objects = [name for name in objects if "MonitorFactory" in name]
        monitor_table = bpy.data.objects.get([name for name in objects if "SimpleDeskFactory" in name and "spawn" in name][0])
        scene_manager = SceneManager()
        scene_manager.connect_loaded_scene()
        floor = bpy.data.objects.get(scene_manager.floor)
        saved_height = floor.location[2]

        chosen_monitor = np.random.choice(monitor_objects)
        monitor = bpy.data.objects.get(chosen_monitor)
        print("Monitor location", monitor.location)

        self.character_manager.relations["working-on-computer"] = monitor.name
        self.character_manager.relations["sitting-on-chair"] = "painted_wooden_chair_01"
        self.character_manager.relations["touching"] = "White G915 keyboard"

        local_front = Vector((1, 0, 0))
        world_front = local_front @ monitor.matrix_world.to_3x3()
        print("World_location", world_front)
        print("monitor rotation", round(monitor.rotation_euler.z, 3), round(-math.pi, 3))
        monitor_z = round(monitor.rotation_euler.z, 3)
        if monitor_z == round(math.pi, 3) or monitor_z == 0:
            new_position = monitor.location + Vector((0.7, 0, 0))
        elif monitor_z == round(-math.pi, 3):
            new_position = monitor.location + Vector((-0.7, 0, 0))
        elif monitor_z == round(math.pi / 2, 3):
            new_position = monitor.location + Vector((0, 0.7, 0))
        else:
            new_position = monitor.location + Vector((0, -0.7, 0))
        self.character.location = new_position
        print("character location", self.character.location)
        direction = monitor.location - new_position
        # raise ValueError(math.atan2(direction.y, direction.x))

        self.character.rotation_mode = 'XYZ'
        self.character.rotation_euler.z = monitor_z - math.pi / 2

        self.character.location[2] = saved_height + 0.9
        children = self.character.children
        child_object = [obj for obj in children if "White G915" in obj.name][0]
        table_wm = monitor_table.matrix_world
        world_bbox = [table_wm @ Vector(corner) for corner in monitor_table.bound_box]
        max_z = max(v.z for v in world_bbox)
        child_object.location = Vector((child_object.location.x, child_object.location.y, max_z - self.character.location.z))
        print("Set working on computer pose!")

    def get_bone(self, description: str):
        normalized_desc = description.strip().lower()
        bone_name = self.bone_lookup.get(normalized_desc)
        if bone_name is None:
            raise ValueError(f"Bone description '{description}' not found for rig type '{self.rig_type}'.")
        bone_obj = self.character.pose.bones.get(bone_name)
        if bone_obj is None:
            raise ValueError(f"Bone '{bone_name}' not found in the character's armature.")
        return bone_obj

    def _integrate_smpl_sitting_on_object(self):
        pose_name = self.character_manager.character_name.split("_")[-1].lower()
        print("Has SMPL pose: ", pose_name)
        self.character_manager.pose = pose_name
        sitting_poses = ["playing-guitar-sitting"]
        sitting_predicates = ["playing the "]
        scene_manager = SceneManager()
        scene_manager.connect_loaded_scene()
        _, sittable_objs = scene_manager.check_for_object_to_sit_on()
        obj_to_sit_on_name = np.random.choice(sittable_objs)
        obj_to_sit_on = bpy.data.objects.get(obj_to_sit_on_name)
        print("Object to sit on: ", obj_to_sit_on)
        print("Has location: ", obj_to_sit_on.location)
        self.character_manager.character.location = obj_to_sit_on.location

    def _integrate_smpl_pose(self):
        pose_name = self.character_manager.character_name.split("_")[-1].lower()
        print("Has SMPL pose: ", pose_name)
        self.character_manager.pose = pose_name
        floor_poses = ["doing-situps", "doing-yoga", "sitting-on-floor"]
        floor_predicates = ["doing situps on ", "doing yoga on", "sitting on "]
        scene_manager = SceneManager()
        scene_manager.connect_loaded_scene()
        floor = scene_manager.get_floor_with_most_objects_above()

        obj_interaction_poses = ["checking-time-on-pocket-watch", "presenting-garden-gnome", "playing-guitar"]
        obj_interaction_predicates = ["checking time on ", "presenting ", "playing the "]

        if pose_name in floor_poses:
            self.character_manager.relations[floor_predicates[floor_poses.index(pose_name)]] = floor

        if pose_name in obj_interaction_poses:
            self.character_manager.relations[obj_interaction_predicates[
                obj_interaction_poses.index(pose_name)]] = self.character_manager.interacted_obj.name

    def _set_arms_down_pose(self):
        self._set_arms_down()

    def _set_waving_pose(self):
        if not self.character or self.character.type != 'ARMATURE':
            raise RuntimeError("Character armature is not set or invalid.")
        self._set_arms_down()
        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        waving_bones = {
            "right upper arm": (0.0, 0.0, 0.0),
            "right forearm": (-1.5, -1.5, 0.0),
            "right hand": (0.0, 0.0, 0.0),

        }
        finger_bones = {
            "right thumb 1": (-0.2, 0.0, 0.0),
            "right index 1": (-0.2, 0.0, 0.0),
            "right middle 1": (0.0, -0.1, 0.0),
            "right ring 1": (-0.2, -0.3, 0.0),
            "right pinky 1": (-0.3, -0.3, 0.0),
        }
        for desc, rotation in waving_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        for desc, rotation in finger_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')

    def _set_holding_apple(self):
        item_manager = ItemManager()
        item_manager.import_apple()
        self._put_item_in_hand(item_manager, "Left")
        self._set_arms_down()
        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        rotation_y = radians(25)
        arms_bones = {
            "head": (radians(25), 0.0, -radians(20)),

            "spine 1": (0.0, 0.0, -radians(10)),

            "left shoulder": (-radians(45), 0.0, 0.0),
            "left upper arm": (0.0, radians(35), 0.0),
            "left forearm": (radians(25), 0.0, -radians(45)),

            "left hand": (-radians(90), 0.0, 0.0),
            "left thumb 1": (0.0, 0.0, 0.0),
            "left thumb 2": (0.0, 0.0, 0.0),
            "left thumb 3": (0.0, 0.0, 0.0),
            "left index 1": (0.0, 0.0, rotation_y),
            "left index 2": (0.0, 0.0, rotation_y),
            "left index 3": (0.0, 0.0, rotation_y),
            "left middle 1": (0.0, 0.0, rotation_y),
            "left middle 2": (0.0, 0.0, rotation_y),
            "left middle 3": (0.0, 0.0, rotation_y),
            "left ring 1": (0.0, 0.0, rotation_y),
            "left ring 2": (0.0, 0.0, rotation_y),
            "left ring 3": (0.0, 0.0, rotation_y),
            "left pinky 1": (0.0, 0.0, rotation_y),
            "left pinky 2": (0.0, 0.0, rotation_y),
            "left pinky 3": (0.0, 0.0, rotation_y),
        }
        for desc, rotation in arms_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')
        item_manager.move_item((0.05, -0.02, -0.02))
        item_manager.rotate_item((0.0, -80.0, 0.0))
        if "eric" in self.character_manager.character_path:
            item_manager.move_item((0.03, 0.0, -0.02))

    def _set_touching_chair(self):
        objects = [obj.name for obj in bpy.context.scene.objects if obj.type != "CAMERA"]
        chair_objects = [name for name in objects if "ChairFactory" in name]
        scene_manager = SceneManager()
        scene_manager.connect_loaded_scene()
        floor = bpy.data.objects.get(scene_manager.floor)
        saved_height = floor.location[2]

        print(chair_objects)
        chosen_chair = np.random.choice(chair_objects)
        chair = bpy.data.objects.get(chosen_chair)

        self.character_manager.relations["touches"] = chair.name

        local_behind = Vector((-0.25, 0, 0))
        world_behind = chair.matrix_world.to_3x3() @ local_behind

        new_position = chair.location + world_behind

        self.character.location = new_position
        direction = chair.location - new_position
        if direction.length > 0:
            angle = math.atan2(direction.y, direction.x)
            self.character.rotation_mode = 'XYZ'
            self.character.rotation_euler.z = angle + math.pi / 2

        self.character.location[2] = saved_height

        self._set_arms_down()
        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        rotation_y = radians(25)
        extra_rot = radians(10)
        eric_rot = 0

        if "eric" in self.character_manager.character_path:
            eric_rot = 8
        arms_bones = {
            "left shoulder": (0.0, 0.0, 0.0),
            "left upper arm": (0.0, radians(35), -radians(15)),
            "left forearm": (radians(25), 0.0, -radians(27 - eric_rot)),

            "head": (0.0, 0.0, -radians(15)),
            "spine 1": (0.0, 0.0, -radians(10)),

            "left hand": (radians(20), 0.0, 0.0),
            "left thumb 1": (0.0, 0.0, 0.0),
            "left thumb 2": (0.0, 0.0, 0.0),
            "left thumb 3": (0.0, 0.0, 0.0),
            "left index 1": (0.0, 0.0, rotation_y),
            "left index 2": (0.0, 0.0, rotation_y),
            "left index 3": (0.0, 0.0, rotation_y + extra_rot),
            "left middle 1": (0.0, 0.0, rotation_y),
            "left middle 2": (0.0, 0.0, rotation_y),
            "left middle 3": (0.0, 0.0, rotation_y + extra_rot),
            "left ring 1": (0.0, 0.0, rotation_y),
            "left ring 2": (0.0, 0.0, rotation_y),
            "left ring 3": (0.0, 0.0, rotation_y + extra_rot),
            "left pinky 1": (0.0, 0.0, rotation_y),
            "left pinky 2": (0.0, 0.0, rotation_y),
            "left pinky 3": (0.0, 0.0, rotation_y + extra_rot),

        }
        for desc, rotation in arms_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')
        print("Set touching chair pose!")

    def _set_fixing_desk(self):
        objects = [obj.name for obj in bpy.context.scene.objects if obj.type != "CAMERA"]
        simple_desk_objects = [name for name in objects if "SimpleDeskFactory" in name]
        valid_desks = []
        if simple_desk_objects:
            for desk in simple_desk_objects:
                factory_obj = bpy.data.objects.get(desk)
                if Utils.check_available_space_y(factory_obj):
                    valid_desks.append(desk)
        chosen_desk = bpy.data.objects.get(np.random.choice(valid_desks))
        print(chosen_desk)
        print("Set fixing desk pose.")
        self.pose = "fixing desk"
        self._set_lean_forward()
        self._set_arms_bending()
        self._set_knees_bending()
        self._set_fist("Right")
        self.character.location = chosen_desk.location + Vector((0.0, -1.7, -0.50))
        self.character_manager.rotate_character(180)
        item_manager = ItemManager()
        item_manager.import_item(
            "/home/nico/dev/hiwi/scenes/InfinigenPopulator/assets/items/screwdriver/screwdriver.fbx")
        self._put_item_in_hand(item_manager, "Right")
        self.character_manager.relations["fixes"] = chosen_desk.name
        item_manager.rotate_item((0, 90, 0))
        item_manager.move_item((0.06, 0.02, -0.075))
        hand_bone_name = self.bone_lookup["right hand"]
        thumb_bone_name = self.bone_lookup["right thumb 1"]
        # ---- Inverse Kinematics Setup for the Right Thumb ----

        ik_target_name = "IK_Target_RightHand"
        ik_target = bpy.data.objects.get(ik_target_name)
        if ik_target is None:
            ik_target = bpy.data.objects.new(ik_target_name, None)
            bpy.context.collection.objects.link(ik_target)

        ik_target.location = chosen_desk.location + Vector((0.4, -0.8, 0.73))

        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        pose_bone = self.character.pose.bones.get(thumb_bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone named '{thumb_bone_name}' not found in the armature.")
        ik_constraint = None
        if ik_constraint is None:
            ik_constraint = pose_bone.constraints.new('IK')
            ik_constraint.name = "IK_Constraint_RightHand"
        ik_constraint.target = ik_target
        ik_constraint.chain_count = 4

        ik_constraint.influence = 0.8
        ik_constraint.keyframe_insert(data_path='influence', frame=bpy.context.scene.frame_current)
        bpy.ops.object.mode_set(mode='OBJECT')

    def _set_holding_glass(self):
        item_manager = ItemManager()
        item_manager.import_glass()
        self._put_item_in_hand(item_manager, "Right")
        self._set_fist("Right")
        self._set_arms_relaxed_holding()
        item_manager.rotate_item((0.0, -92.0, 0.0))
        item_manager.move_item((-0.05, 0.10, -0.07))
        if "eric" in self.character_manager.character_path:
            item_manager.move_item((0.0, 0.01, -0.05))

    def _set_watering_plant(self):
        self._set_arms_down()
        temp_scene_manager = SceneManager()
        temp_scene_manager.connect_loaded_scene()

        objects = [obj.name for obj in bpy.context.scene.objects if obj.type != "CAMERA"]
        all_plants = [name for name in objects if "PlantContainer" in name]
        plant = all_plants[0]

        plant_container = bpy.data.objects.get(plant)

        margin = 0.6

        half_x = plant_container.dimensions.x / 4
        half_y = plant_container.dimensions.y / 4

        candidate_offsets = [
            Vector((half_x + margin, 0, 0)),  # Right
            Vector((-half_x - margin, 0, 0)),  # Left
            Vector((0, half_y + margin, 0)),  # Front
            Vector((0, -half_y - margin, 0))  # Back
        ]

        available_position = None
        offset_i = None
        for i, offset in enumerate(candidate_offsets):
            candidate_position = plant_container.location + offset
            free, colliding_obj = Utils.is_space_free(candidate_position, self.character, temp_scene_manager.floor)
            if free:
                available_position = candidate_position
                offset_i = i
                print(f"Found free space next to plant at {candidate_position}")
                break

        if available_position is not None:
            self.character.location = available_position
            direction = plant_container.location - available_position
            angle = math.atan2(direction.y, direction.x) + math.pi / 2
            self.character.rotation_euler.z = angle
        else:
            print("Couldn't find space next to plant, so fell back to default poses!")
            self._set_holding_apple()

        item_manager = ItemManager()
        item_manager.import_watering_can()
        self.character_manager.relations["watering"] = plant_container.name
        print("Offset_i: ", offset_i)
        if offset_i == 0 or offset_i == 2:
            side = "Left"
        else:
            side = "Right"
        self._put_item_in_hand(item_manager, side)
        side_rotation = 1.0 if side == "Right" else -1.0
        item_manager.rotate_item((-90.0, 90.0, 0.0))
        item_manager.move_item((-0.06, -0.2, -0.04))
        if side == "Right" and offset_i == 1:
            item_manager.rotate_item((0.0, 0.0, -180.0))

        if side == "Right" and offset_i == 3:
            item_manager.rotate_item((0.0, 0.0, -90.0))
            item_manager.move_item((0.257, 0.17, -0.04))

        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        arms_bones = {
            f"{side} shoulder": (0.0, 0.0, 0.0),
            f"{side} upper arm": (0.0, radians(35), -radians(15) * side_rotation),
            f"{side} forearm": (radians(25), 0.0, -radians(45)),

            "head": (0.0, 0.0, -radians(20)),

            "spine 1": (0.0, 0.0, -radians(10)),

        }
        for desc, rotation in arms_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')
        self._set_fist(side)

    def _set_arms_down(self):
        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        arms_bones = {
            "right shoulder": (0.0, 0.0, 0.0),
            "right upper arm": (0.0, radians(25), radians(20)),
            "right forearm": (radians(15), radians(35), -radians(20)),

            "left shoulder": (0.0, 0.0, 0.0),
            "left upper arm": (0.0, radians(25), radians(20)),
            "left forearm": (radians(15), radians(35), -radians(20)),
        }
        for desc, rotation in arms_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')

    def _set_arms_relaxed_holding(self):
        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        arms_bones = {
            "right shoulder": (0.0, 0.0, 0.0),
            "right upper arm": (0.0, radians(35), -radians(35)),
            "right forearm": (0.0, 0.0, -radians(45)),

            "left shoulder": (0.0, 0.0, 0.0),
            "left upper arm": (0.0, radians(25), radians(20)),
            "left forearm": (radians(15), radians(35), -radians(20)),
        }
        for desc, rotation in arms_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')

    def _set_lean_forward(self):
        if not self.character or self.character.type != 'ARMATURE':
            raise RuntimeError("Character armature is not set or invalid.")
        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        torso_bones = {
            "head": (-radians(35), 0.0, radians(20)),
            "hip": (0.0, 0.0, -radians(36)),
            "spine 1": (-radians(5), 0.0, -radians(10)),
            "spine 2": (0.0, 0.0, -radians(3)),
        }
        for desc, rotation in torso_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')

    def _set_torso_upright(self):
        if not self.character or self.character.type != 'ARMATURE':
            raise RuntimeError("Character armature is not set or invalid.")
        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        torso_bones = {
            "hip": (0.0, 0.0, 0.0),
            "spine 1": (0.0, 0.0, 0.0),
            "spine 2": (0.0, 0.0, 0.0),
            "spine 3": (0.0, 0.0, 0.0),
            "neck": (0.0, 0.0, 0.0),
            "head": (0.0, 0.0, 0.0),
            "head top": (0.0, 0.0, 0.0),
            "right shoulder": (0.0, 0.0, 0.0),
            "left shoulder": (0.0, 0.0, 0.0),
        }
        for desc, rotation in torso_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')

    def _set_fist(self, side: str):
        if not self.character or self.character.type != 'ARMATURE':
            raise RuntimeError("Character armature is not set or invalid.")
        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        if side not in ["Left", "Right"]:
            raise ValueError("Invalid side. Please specify 'Left' or 'Right'.")
        thumb_rotation = radians(25)
        hand_rotation = -radians(25)
        if side == "Left":
            thumb_rotation *= -1
            hand_rotation *= -1
            fist_bones = {
                "left hand": (hand_rotation, 0.0, 0.0),
                "left thumb 1": (0.0, 0.0, thumb_rotation),
                "left thumb 2": (0.0, 0.0, 0.0),
                "left thumb 3": (0.0, 0.0, 0.0),
                "left index 1": (0.0, 0.0, radians(70)),
                "left index 2": (0.0, 0.0, radians(70)),
                "left index 3": (0.0, 0.0, radians(70)),
                "left middle 1": (0.0, 0.0, radians(70)),
                "left middle 2": (0.0, 0.0, radians(70)),
                "left middle 3": (0.0, 0.0, radians(70)),
                "left ring 1": (0.0, 0.0, radians(70)),
                "left ring 2": (0.0, 0.0, radians(70)),
                "left ring 3": (0.0, 0.0, radians(70)),
                "left pinky 1": (0.0, 0.0, radians(70)),
                "left pinky 2": (0.0, 0.0, radians(70)),
                "left pinky 3": (0.0, 0.0, radians(70)),
            }
        else:
            fist_bones = {
                "right hand": (hand_rotation, 0.0, 0.0),
                "right thumb 1": (0.0, 0.0, thumb_rotation),
                "right thumb 2": (0.0, 0.0, 0.0),
                "right thumb 3": (0.0, 0.0, 0.0),
                "right index 1": (0.0, 0.0, radians(60)),
                "right index 2": (0.0, 0.0, radians(60)),
                "right index 3": (0.0, 0.0, radians(60)),
                "right middle 1": (0.0, 0.0, radians(60)),
                "right middle 2": (0.0, 0.0, radians(60)),
                "right middle 3": (0.0, 0.0, radians(60)),
                "right ring 1": (0.0, 0.0, radians(60)),
                "right ring 2": (0.0, 0.0, radians(60)),
                "right ring 3": (0.0, 0.0, radians(60)),
                "right pinky 1": (0.0, 0.0, radians(60)),
                "right pinky 2": (0.0, 0.0, radians(60)),
                "right pinky 3": (0.0, 0.0, radians(60)),
            }
        for desc, rotation in fist_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')

    def _set_knees_bending(self):
        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        leg_bones = {
            "right upper leg": (0.0, 0.0, radians(120)),
            "right leg": (0.0, 0.0, -radians(120)),
            "left upper leg": (0.0, 0.0, radians(120)),
            "left leg": (0.0, 0.0, -radians(120)),
            "right foot": (0.0, 0.0, radians(40)),
            "left foot": (0.0, 0.0, radians(40)),
        }
        for desc, rotation in leg_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                # XYZ, XZY, YXZ
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')

    def _set_arms_bending(self):
        bpy.context.view_layer.objects.active = self.character
        bpy.ops.object.mode_set(mode='POSE')
        arms_bones = {
            "right shoulder": (0.0, 0.0, 0.0),
            "right upper arm": (0.0, 0.0, 0.0),
            "right forearm": (0.0, 0.0, 0.0),
            "left shoulder": (0.0, radians(25), 0.0),
            "left upper arm": (0.0, 0.0, 0.0),
            "left forearm": (0.0, radians(25), 0.0),
        }
        for desc, rotation in arms_bones.items():
            try:
                pose_bone = self.get_bone(desc)
                pose_bone.rotation_mode = 'XYZ'
                pose_bone.rotation_euler = rotation
            except ValueError as e:
                print(e)
        bpy.ops.object.mode_set(mode='OBJECT')

    def _set_sitting_pose(self):
        if not self.character or self.character.type != 'ARMATURE':
            raise RuntimeError("Character armature is not set or invalid.")
        self._set_torso_upright()
        self._set_knees_bending()
        self._set_arms_bending()
        self._set_fist(side="Left")
        self._set_fist(side="Right")
        self.pose = "sitting"

    def _put_item_in_hand(self, item_manager: ItemManager, side: str):
        if side not in ["Left", "Right"]:
            raise ValueError("Invalid side. Please specify 'Left' or 'Right'.")

        if item_manager.item_origin == "import":
            self._put_imported_in_hand(item_manager, side)
            return
        if item_manager.item_origin == "copy":
            self._put_copied_in_hand(item_manager, side)
            return
        else:
            raise ValueError("No item exists yet in ItemManager!")

    def _put_imported_in_hand(self, item_manager: ItemManager, side: str):
        item = item_manager.item
        bone_name = f"{side.lower()} hand"
        hand_bone_name = self.bone_lookup.get(bone_name)
        hand_bone = self.get_bone(bone_name)
        item.parent = self.character
        item.parent_type = 'BONE'
        item.parent_bone = hand_bone_name
        item.matrix_parent_inverse = self.character.matrix_world.inverted()
        item.location = self.character.location + Vector((0, -0.02, -0.01))
        side_dependent_rotation = -radians(90)
        if side == "Right":
            side_dependent_rotation = radians(90)
        item.rotation_mode = 'XYZ'
        item.rotation_euler = (0, 0, side_dependent_rotation)
        self.character_manager.relations["holds"] = item.name

    def _put_copied_in_hand(self, item_manager: ItemManager, side: str):
        item = item_manager.item
        bone_name = f"{side.lower()} hand"
        hand_bone_name = self.bone_lookup.get(bone_name)
        hand_bone = self.get_bone(bone_name)
        if not hand_bone:
            raise ValueError(f"Hand bone '{hand_bone_name}' not found in the character armature.")
        item.parent = self.character
        item.parent_type = 'BONE'
        item.parent_bone = hand_bone_name
        item.matrix_parent_inverse = self.character.matrix_world.inverted()
        item.location = (0, -0.02, -0.01)
        side_dependent_rotation = -radians(90)
        if side == "Right":
            side_dependent_rotation = radians(90)
        item.rotation_euler = (0, 0, side_dependent_rotation)

        self.character_manager.relations["is holding"] = item.name
