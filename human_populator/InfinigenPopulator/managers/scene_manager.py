import bpy
# noinspection PyUnresolvedReferences
from mathutils import Vector

class SceneManager:
    def __init__(self):
        self.scene = None
        self.floor = None

    def connect_loaded_scene(self):
        try:
            self.scene = bpy.data.scenes[0]
            self.floor = self.get_floor_with_most_objects_above()
        except Exception as e:
            raise RuntimeError(f"Error connecting scene to SceneManager: {e}")

    def get_floor_area(self):
        total_floor_area = 0.0
        for obj in self.scene.objects:
            if obj.name == self.floor:
                mesh = obj.data
                for face in mesh.polygons:
                    if abs(face.normal.dot((0, 0, 1))) > 0.999:
                        total_floor_area += face.area

        return total_floor_area


    def load_scene(self, scene_path):
        try:
            bpy.ops.wm.open_mainfile(filepath=scene_path)
            self.scene = bpy.data.scenes[0]
            self.floor = self.get_floor_with_most_objects_above()
            print("Floor OBJ", self.floor)
            for obj in bpy.data.objects:
                if obj.type == 'CAMERA':
                    old_name = obj.name
                    if old_name.startswith("CameraRigs/"):
                        # Strip off "CameraRigs/" and replace any remaining "/" with "_"
                        suffix = old_name[len("CameraRigs/"):]
                        new_name = "camera_" + suffix.replace("/", "_")
                        obj.name = new_name
            camera_rigs_collection = bpy.data.collections.get("CameraRigs")
            if camera_rigs_collection:
                camera_rigs_collection.name = "camera_rigs"
        except Exception as e:
            raise RuntimeError(f"Error during scene loading: {e}")

    def save_scene(self, save_path):
        try:
            bpy.ops.wm.save_mainfile(filepath=save_path)
        except Exception as e:
            raise RuntimeError(f"Error during scene saving: {e}")


    def check_for_object_to_sit_on(self):
        objects = [obj.name for obj in self.scene.objects if obj.type != "CAMERA"]
        sittable_names = ["Dishwasher", "Bed", "Fridge", "WashingMachine", "Sofa"]
        sittable_objects = []
        for name in sittable_names:
            found_sittable = [obj for obj in objects if name in obj]
            if found_sittable:
                sittable_objects.extend(found_sittable)
        if sittable_objects:
            return True, sittable_objects
        else:
            return False, None




    def get_floor_with_most_objects_above(self):
        floor_object_count = {}
        floors = [obj for obj in self.scene.objects if "floor" in obj.name.lower()]
        for floor in floors:
            bbox_world = [floor.matrix_world @ Vector(corner) for corner in floor.bound_box]
            min_coords = Vector(
                (min(v.x for v in bbox_world), min(v.y for v in bbox_world), min(v.z for v in bbox_world)))
            max_coords = Vector(
                (max(v.x for v in bbox_world), max(v.y for v in bbox_world), max(v.z for v in bbox_world)))
            floor_object_count[floor.name] = 0
            for obj in self.scene.objects:
                if obj == floor or "floor" in obj.name.lower() or obj.type != "MESH":  # Skip floor objects
                    continue
                obj_location = obj.location
                if (min_coords.x <= obj_location.x <= max_coords.x and
                        min_coords.y <= obj_location.y <= max_coords.y and
                        max_coords.z < obj_location.z <= max_coords.z + 1):
                    floor_object_count[floor.name] += 1
        floor_with_most_objects = max(floor_object_count, key=floor_object_count.get)
        return floor_with_most_objects

    def get_valid_poses(self):
        objects = [obj.name for obj in self.scene.objects if obj.type != "CAMERA"]

        # valid_poses = ["waving", "holding apple", "holding glass", "arms down"]
        valid_poses = ["smpl"]
        #for now disabled
        """simple_desk_objects = [name for name in objects if "SimpleDeskFactory" in name]
        valid_desks = []
        if simple_desk_objects:
            for desk in simple_desk_objects:
                factory_obj = bpy.data.objects.get(desk)
                if Utils.check_available_space_y(factory_obj):
                    valid_desks.append(desk)
            if valid_desks:
                valid_poses.append("fixing desk")"""

        plants = [name for name in objects if "LargePlantContainer" in name]
        if plants:
            valid_poses.append("watering plant")

        chairs = [name for name in objects if "ChairFactory" in name and "spawn_asset" in name]
        sofa = [name for name in objects if "SofaFactory" in name and "spawn_asset" in name]
        if chairs or sofa:
            # valid_poses.append("touching chair")
            num_char = 2 if len(chairs) > 4 else 1
            valid_poses.extend(["smpl sitting chair"] * num_char)
        if chairs:
            num_char = 2 if len(chairs) >= 4 else 1
            valid_poses.extend(["smpl eating"] * num_char)

        beds = [name for name in objects if "BedFactory" in name and "spawn_asset" in name]
        if beds:
            # valid_poses.append("touching chair")
            num_char = 2 if len(beds) > 1 else 1
            valid_poses.extend(["smpl sleeping on bed"] * num_char)

        monitor = [name for name in objects if "MonitorFactory" in name]
        if monitor:
            valid_poses.append("smpl working on computer")

        print("Valid poses: ", valid_poses)
        return valid_poses

