# HOIverse : A Synthetic Scene Graph Dataset With Human Object Interactions

When humans and robotic agents coexist in an environment, scene understanding becomes crucial for the agents to carry out various downstream tasks like navigation and planning. Hence, an agent must be capable of localizing and identifying actions performed by the human. Current research lacks reliable datasets for performing scene understanding within indoor environments where humans are also a part of the scene.
Scene Graphs enable us to generate a structured representation of a scene or an image to perform visual scene understanding. To tackle this, we present HOIverse a synthetic dataset at the intersection of scene graph and human-object interaction, consisting of accurate and dense relationship ground truths between humans and surrounding objects along with corresponding RGB images, segmentation masks, depth images and human keypoints. We compute parametric relations between various pairs of objects and human-object pairs, resulting in an accurate and unambiguous relation definitions. In addition, we benchmark our dataset on state-of-the-art scene graph generation models to predict parametric relations and human-object interactions. Through this dataset, we aim to accelerate research in the field of scene understanding involving people.


- 📄 [Paper (arXiv)](https://www.arxiv.org/abs/2506.19639)
- 💻 [Code (GitHub)](https://github.com/mrunmaivp/hoiverse/)
- ⬇️ [Download HOIverse dataset](https://myweb.rz.uni-augsburg.de/~phatakmr/hoiverse/v1/)


# HumanPopulator
## Installation
* Install infinigen following the instructions on: https://github.com/princeton-vl/infinigen/blob/main/docs/Installation.md as a **Python Module**.
* When installing infinigen use the option **Full install** by using ```pip install -e .```.
* After successfully installing infinigen, you can use the InfinigenPopulator:
```
git clone https://github.com/mrunmaivp/hoiverse.git
cd human_populator
conda activate infinigen
python populate.py input_folder output_root characters_path

```
## Input Folder
* Should be a folder named after the seed with which the original scene was generated.
* Should contain a folder /fine which conatins the scene and a MaskTag.json.
## Output Root
* New folder where a new folder named again after the seed will be with the populated scene and rendered frames. 
## Characters
* Three default characters are provided at assets/smpl_charaters
