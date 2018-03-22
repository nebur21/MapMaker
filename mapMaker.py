import argparse
import terrainGen

parser = argparse.ArgumentParser(description='A pirate island map generator written by Ruben Rodrigues.')

parser.add_argument('--out', dest='out', action='store', default='map.png',
                    help='file path for the generated map image (default: "map.png")')

parser.add_argument('--size', dest='size', action='store', default=1000,
                    help='size of the map side to generate, in pixels (default: 1000)')

parser.add_argument('--bw', dest='noise', action='store', default='false',
                    help='if the script should save a black and white copy of the terrain to better see the noise. saves it to the directory of the script (default: "false")')

args = parser.parse_args()

terrainGen.main(args.out, args.size, args.noise)