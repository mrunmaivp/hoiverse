import json
import os


class AnnotationManager:
    def __init__(self, annotation_path):
        self.annotation_path = annotation_path
        self.scene_data = None
        self.character_data = []
        self.relations_data = []
        self.annotation = {}

    def set_scene_data(self, scene_data):
        self.scene_data = scene_data

    def add_annotation(self, character_manager):
        self.annotation = {
            "id": character_manager.character.name,
            "pose": character_manager.pose,
            "relations": character_manager.relations,
            "camera": character_manager.camera,
        }


    def add_relation_data(self, relation_data):
        self.relations_data.append(relation_data)


    def write_json(self):
        if not self.annotation:
            raise RuntimeError("No character data.")
        try:
            existing_data = []
            if os.path.isfile(self.annotation_path):
                with open(self.annotation_path, 'r') as json_file:
                    try:
                        existing_data = json.load(json_file)
                    except json.JSONDecodeError:
                        existing_data = []

            if not isinstance(existing_data, list):
                # If the existing data isn't a list, wrap it in one.
                existing_data = [existing_data]

            existing_data.append(self.annotation)
            with open( self.annotation_path, 'w') as json_file:
                json.dump(existing_data, json_file, indent=4)
            print(f"Json saved to { self.annotation_path}")
        except Exception as e:
            raise RuntimeError(f"Error writing JSON file: {e}")