import os

import bpy
# noinspection PyUnresolvedReferences
import bmesh
# noinspection PyUnresolvedReferences
import numpy as np
# noinspection PyUnresolvedReferences
from mathutils import Vector
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt
from matplotlib.path import Path
from shapely.geometry import Polygon, Point

class Utils:
    @staticmethod
    def get_valid_ground_positions(character, floor_name, grid_spacing):
        #TOOD statt floor mit ceiling ausprobieren und dann schauen
        floor = bpy.data.objects.get(floor_name)
        if not floor:
            raise ValueError(f"Floor '{floor_name}' not found!")

        floor_verts = [floor.matrix_world @ v.co for v in floor.data.vertices]
        points_2d_verts = np.array([[v.x, v.y] for v in floor_verts])
        z = min(v.z for v in floor_verts)
        floor_polygon = Polygon(points_2d_verts)

        x_min, x_max = np.min(points_2d_verts[:, 0]), np.max(points_2d_verts[:, 0])
        y_min, y_max = np.min(points_2d_verts[:, 1]), np.max(points_2d_verts[:, 1])

        x_vals = np.arange(x_min, x_max, grid_spacing)
        y_vals = np.arange(y_min, y_max, grid_spacing)
        grid_x, grid_y = np.meshgrid(x_vals, y_vals)
        grid_points = np.vstack([grid_x.ravel(), grid_y.ravel()]).T

        filtered_points = np.array([
            [x, y] for x, y in grid_points if floor_polygon.contains(Point(x, y))
        ])

        candidate_positions = [(x, y, z) for x, y in filtered_points]

        floor_objects = Utils.get_objects_on_floor(floor_verts, floor_name, 0.6)
        valid_positions = []
        for position in candidate_positions:
            if Utils.can_place_character(character, floor_objects, position, floor_name):
                valid_positions.append(position)

        return valid_positions

    @staticmethod
    def can_place_character(character, floor_objects, position, floor_name):
        character_bbox_min, character_bbox_max = Utils.get_bounding_box_in_world(character, position)
        for obj in floor_objects:
            obj_min, obj_max = Utils.get_bounding_box_in_world(obj)
            is_within = Utils.check_object_within_floor_at_position(character, floor_name, position)
            is_overlapping = Utils.is_overlapping(character_bbox_min, character_bbox_max, obj_min, obj_max)
            if is_overlapping:
                return False
            if not is_within:
                return False
        return True

    @staticmethod
    def get_bounding_box_in_world(obj, location=None):
        bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        if location:
            offset = Vector(location) - obj.location
            bbox = [corner + offset for corner in bbox]
        min_coords = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
        max_coords = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))
        return min_coords, max_coords

    @staticmethod
    def is_overlapping(min1, max1, min2, max2):
        return (min1.x <= max2.x and max1.x >= min2.x and
                min1.y <= max2.y and max1.y >= min2.y and
                min1.z <= max2.z and max1.z >= min2.z)

    @staticmethod
    def get_objects_on_floor(floor_corners, floor_name, floor_height_wiggle_room):
        x_min = min(corner.x for corner in floor_corners)
        x_max = max(corner.x for corner in floor_corners)
        y_min = min(corner.y for corner in floor_corners)
        y_max = max(corner.y for corner in floor_corners)
        z = min(corner.z for corner in floor_corners)
        z_min = z - floor_height_wiggle_room
        z_max = z + floor_height_wiggle_room
        floor_objects = []
        for obj in bpy.context.scene.objects:
            if obj.name == floor_name:
                continue
            if (x_min <= obj.location.x <= x_max) and (y_min <= obj.location.y <= y_max) and (
                    z_min <= obj.location.z <= z_max):
                floor_objects.append(obj)
        return floor_objects

    @staticmethod
    def check_object_within_floor_at_position(character, floor_name, position):
        floor = bpy.data.objects.get(floor_name)

        floor_corners = [floor.matrix_world @ Vector(corner) for corner in floor.bound_box]
        floor_x_min = min(corner.x for corner in floor_corners)
        floor_x_max = max(corner.x for corner in floor_corners)
        floor_y_min = min(corner.y for corner in floor_corners)
        floor_y_max = max(corner.y for corner in floor_corners)

        character_corners = [character.matrix_world @ Vector(corner) for corner in character.bound_box]
        obj_min_x = min(corner.x for corner in character_corners)
        obj_max_x = max(corner.x for corner in character_corners)
        obj_min_y = min(corner.y for corner in character_corners)
        obj_max_y = max(corner.y for corner in character_corners)

        obj_min_y = position[1] + obj_min_y
        obj_max_y = position[1] + obj_max_y
        obj_min_x = position[0] + obj_min_x
        obj_max_x = position[0] + obj_max_x
        is_within = (
                obj_min_x >= floor_x_min and
                obj_max_x <= floor_x_max and
                obj_min_y >= floor_y_min and
                obj_max_y <= floor_y_max
        )
        return is_within

    @staticmethod
    def check_available_space_y(factory_obj, threshold = 0.3):
        if not factory_obj:
            print("Object not found.")
        else:
            left_objects = []
            right_objects = []

            inv_matrix = factory_obj.matrix_world.inverted()

            for obj in bpy.data.objects:

                if obj == factory_obj:
                    continue
                if obj.type == "CAMERA":
                    continue

                local_coord = inv_matrix @ obj.location

                if local_coord.x < 0 and abs(local_coord.x) <= threshold:
                    left_objects.append(obj.name)
                elif local_coord.x > 0 and abs(local_coord.x) <= threshold:
                    right_objects.append(obj.name)

            if left_objects:
                print("Objects to the left of 'SimpleDeskFactory' within threshold:", left_objects)

            if right_objects:
                print("Objects to the right of 'SimpleDeskFactory' within threshold:", right_objects)

            if not left_objects and not right_objects:
                return True
            else:
                return False

    @staticmethod
    def is_space_free(candidate_position, character, floor_name, clearance=0.4):
        """
        Checks if the candidate position is free by comparing the distance to all examined objects. Returns a tuple (bool, colliding_obj_name).
        """
        if not Utils.check_object_within_floor_at_position(character, floor_name, candidate_position):
            return False, "outside floor"
        examined_objects = [obj for obj in bpy.data.objects if obj.type != "CAMERA" or obj.type != "ARMATURE"]
        for obj in examined_objects:

            distance = (candidate_position - obj.location).length
            if distance < clearance:
                return False, obj.name
        return True, None


def get_file_paths(directory):
    return [
        os.path.join(directory, file)
        for file in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, file))
    ]
