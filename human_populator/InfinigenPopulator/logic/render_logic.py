import os
import subprocess
import gin

def render_images_gt(scene_folder, frames_folder, seed, camera_ids):
    input_folder = os.path.expanduser(scene_folder)
    output_folder = os.path.expanduser(frames_folder)
    for camera_id in camera_ids:
        camrig_id, subcam_id = camera_id
        print("Camera: ", camrig_id, subcam_id)
        gin.clear_config(clear_constants=True)
        print("Rendering images: ")
        render_full_cmd = [
            "python",
            "-m", "infinigen_examples.generate_indoors",
            "--",
            "--input_folder", input_folder,
            "--output_folder", output_folder,
            "--seed", seed,
            "--task", "render",
            "--task_uniqname", "rendershort_{}".format(camrig_id),
            "-g", "singleroom.gin",
            "-p", "render.render_image_func=@full/render_image",
            "execute_tasks.frame_range=[48,48]",
            f"execute_tasks.camera_id={camera_id}"
        ]
        print("Running command:", " ".join(render_full_cmd))
        subprocess.run(render_full_cmd, check=True)
        gin.clear_config(clear_constants=True)
        print("Rendering ground truth: ")
        render_flat_cmd = [
            "python",
            "-m", "infinigen_examples.generate_indoors",
            "--",
            "--input_folder", input_folder,
            "--output_folder", output_folder,
            "--seed", seed,
            "--task", "render",
            "--task_uniqname", "rendershort_{}".format(camrig_id),
            "-g", "singleroom.gin",
            "-p", "render.render_image_func=@flat/render_image",
            "execute_tasks.frame_range=[48,48]",
            f"execute_tasks.camera_id={camera_id}"
        ]
        print("Running command:", " ".join(render_flat_cmd))
        subprocess.run(render_flat_cmd, check=True)


