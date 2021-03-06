# MapMaker
A pirate island map generator written by Ruben Rodrigues.


# Install (Windows)

You need Python 3 and virtualenv to run MapMaker.

Create a virtualenv and cd into it.
```
virtualenv map

cd map
```

Copy the files from github to this folder, and obtain the dependencies:

```
pip install -r requirements.txt

Scripts\activate

python mapMaker.py
```

# Usage

```
usage: mapMaker.py [-h] [--out OUT] [--size SIZE] [--bw NOISE]

A pirate island map generator written by Ruben Rodrigues.

optional arguments:
  -h, --help   show this help message and exit
  --out OUT    file path for the generated map image (default: "map.png")
  --size SIZE  size of the map side to generate, in pixels (default: 1000)
  --bw NOISE   if the script should save a black and white copy of the terrain
               to better see the noise. saves it to the directory of the
               script (default: "false")
```
