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
* Three default characters are provided at assets/smpl_charaters.
