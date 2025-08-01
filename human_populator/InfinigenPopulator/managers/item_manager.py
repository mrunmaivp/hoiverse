import os
import bpy
from numpy import radians
# noinspection PyUnresolvedReferences
from mathutils import Vector

class ItemManager:

    def __init__(self):
        self.item = None
        self.item_origin = None

    def import_item(self, item_path: str):
        try:
            existing_objects = set(bpy.data.objects)
            bpy.ops.import_scene.fbx(filepath=item_path)
            new_objects = set(bpy.data.objects) - existing_objects
            list_new_objects = [obj for obj in new_objects]
            item = list_new_objects[0]
            self.item = item
            self.item_origin = "import"
        except Exception as e:
            raise RuntimeError(f"Error during item import: {e}")

    def copy_item_from_scene(self, object_name: str):
        original = bpy.data.objects.get(object_name)
        if not original:
            raise ValueError(f"Object '{object_name}' not found in the scene.")
        copy = original.copy()
        copy.data = original.data.copy()
        bpy.context.collection.objects.link(copy)
        copy.location.x += 1.0
        self.item = copy
        self.item.name = self.item.name
        self.item_origin = "copy"
        return copy

    def import_screwdriver(self, item_path: str):
        existing_objects = set(bpy.data.objects)
        collection_name = "flathead_screwdriver"
        section = "Collection"
        directory = os.path.join(item_path, section)
        bpy.ops.wm.append(filepath=os.path.join(directory, collection_name),directory=directory, filename=collection_name)
        new_objects = set(bpy.data.objects) - existing_objects
        list_new_objects = [obj for obj in new_objects]
        item = list_new_objects[0]
        self.item = item
        self.item_origin = "import"
        print(self.item.name)


    def import_watering_can(self):
        existing_objects = set(bpy.data.objects)
        script_dir = os.getcwd()
        watering_plant_path = os.path.join(script_dir, "assets", "items", "watering_can", "watering_can.fbx")
        bpy.ops.import_scene.fbx(filepath=watering_plant_path)
        new_objects = set(bpy.data.objects) - existing_objects
        list_new_objects = [obj for obj in new_objects]
        item = list_new_objects[0]
        self.item = item
        self.item_origin = "import"


    def import_glass(self):
        existing_objects = set(bpy.data.objects)
        script_dir = os.getcwd()
        glass_path = os.path.join(script_dir, "assets", "items", "glass", "glass.fbx")
        bpy.ops.import_scene.fbx(filepath=glass_path)
        new_objects = set(bpy.data.objects) - existing_objects
        list_new_objects = [obj for obj in new_objects]
        item = list_new_objects[0]
        self.item = item
        self.item_origin = "import"


    def import_apple(self):
        existing_objects = set(bpy.data.objects)
        script_dir = os.getcwd()
        wapple_path = os.path.join(script_dir, "assets", "items", "apple", "apple.fbx")
        bpy.ops.import_scene.fbx(filepath=wapple_path)
        new_objects = set(bpy.data.objects) - existing_objects
        list_new_objects = [obj for obj in new_objects]
        item = list_new_objects[0]
        self.item = item
        self.item_origin = "import"



    def rotate_item(self, delta_rotation):
        delta_x = radians(delta_rotation[0])
        delta_y = radians(delta_rotation[1])
        delta_z = radians(delta_rotation[2])
        self.item.rotation_mode = "XYZ"
        self.item.rotation_euler[0] += delta_x
        self.item.rotation_euler[1] += delta_y
        self.item.rotation_euler[2] += delta_z


    def move_item(self, delta_movement):
        self.item.location = self.item.location + Vector(delta_movement)