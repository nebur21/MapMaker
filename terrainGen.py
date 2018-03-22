from opensimplex import OpenSimplex
from colour import Color
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import math
import sys
import os

# ------------------------ CONSTANTS ------------------------
output = None
mapSize = None
diagonal = None
mapCenter = None
mapArea = None

spectreBW = list(Color("white").range_to(Color("black"),100))
water1 = list(Color("#3eb5ff").range_to("#3eb5ff",15))
water2 = list(Color("#3eb5ff").range_to("#67d6ff",15))
water3 = list(Color("#67d6ff").range_to("#cfeefc",10))
beach = list(Color("#f2e9da").range_to("#70bf48",20))
forest = list(Color("#70bf48").range_to("#007517",20))
mountain = list(Color("#007517").range_to("#1a1100",10))
peak = list(Color("#292727").range_to("#292727",10))
spectre = water1 + water2 + water3 + beach + forest + mountain + peak

textSizes = None

textSpacing = None
textBorderSize = None

islandSizeThreshold = None

islandNames = None
with open('names.txt', 'r') as the_file:
    islandNames = the_file.readlines()
islandNames = [name.replace('$', '\n') for name in islandNames]
# -----------------------------------------------------------

def rgb(color): # translate Colour color into 255 rgb
	return tuple([int(val*255) for val in color.rgb])

def getColor(elevation, bw=False): # translate height into color
	e = int(elevation*100)
	if e>99:
		e=99
	elif(e<0):
		e=0
	if(bw):
		return rgb(spectreBW[e])
	else:
		return rgb(spectre[e])

def noise(generator, nx, ny):
    # Rescale from -1.0:+1.0 to 0.0:1.0
    return generator.noise2d(nx, ny) / 2.0 + 0.5

def generateTerrain():
	print("generating terrain...")
	gen = OpenSimplex(random.getrandbits(16))
	heightMap = [[0 for i in range(mapSize)] for j in range(mapSize)]
	a = 0.05
	b = 4.0
	c = 2.0
	for y in range(mapSize):
		sys.stdout.write("\ty: %d/%d   \r" % (y, mapSize))
		sys.stdout.flush()
		for x in range(mapSize):
			nx = x/mapSize - 0.5
			ny = y/mapSize - 0.5
			elevation = 0.85*noise(gen, 7.0*nx, 7.0*ny) + \
						0.1*noise(gen, 35.0*nx, 35.0*ny) + \
	        			0.05*noise(gen, 100.0*nx, 100.0*ny)
			d = math.sqrt((x-mapCenter)**2 + (y-mapCenter)**2)/diagonal
			e = elevation + a - b*d**c
			heightMap[y][x] = e
	print("\n\tdone")
	return heightMap

def colorizeImage(heightMap, bw=False):
	print("coloring image...")
	image = Image.new("RGBA", (mapSize, mapSize))
	for y in range(mapSize):
		sys.stdout.write("\ty: %d/%d   \r" % (y, mapSize))
		sys.stdout.flush()
		for x in range(mapSize):
			color = getColor(heightMap[y][x], bw)
			image.putpixel((x,y), color)
	print("\n\tdone")
	return image

def getCentroid(listPixels): # get centroid of a list of coords
	x = [p[0] for p in listPixels]
	y = [p[1] for p in listPixels]
	return (int(sum(x) / len(listPixels)), int(sum(y) / len(listPixels)))

def isValidCoord(point): # check if coord is inside map limits
	if(point[0]>0 and point[1]>0 and point[0]<mapSize and point[1]<mapSize):
		return True
	else:
		return False

def validateTextCoord(start, length):
	newX = start[0]
	newY = start[1]
	if(start[0]<0):
		newX=0
	elif(start[0]+length[0]>mapSize):
		newX = start[0] - (start[0]+length[0]-mapSize)
	if(start[1]<0):
		newY=0
	elif(start[1]+length[1]>mapSize):
		newY = start[1] - (start[1]+length[1]-mapSize)
	return (newX, newY)

def getNeighbours(point):
	n = []
	n.append((point[0]-1, point[1]))
	n.append((point[0]+1, point[1]))
	n.append((point[0],   point[1]-1))
	n.append((point[0],   point[1]+1))
	return n

def iterativeCC(binaryMx, visited, x, y): # connected components algorithm step
	cluster = []
	lookup = []
	lookup.append((x, y))
	while(lookup):
		point = lookup.pop(0)
		x = point[0]
		y = point[1]
		if(not visited[y][x]):
			visited[y][x] = True
			if(binaryMx[y][x]):
				cluster.append(point)
				neigh = getNeighbours(point)
				for n in neigh:
					if(isValidCoord(n) and n not in lookup):
						lookup.append(n)
	return cluster

def getCC(binaryMx, image): # get connected components
	print("calculating connected components... (this may take a long time)")
	visited = [[False for i in range(mapSize)] for j in range(mapSize)]
	components = []
	for y in range(mapSize):
		sys.stdout.write("\ty: %d/%d   \r" % (y, mapSize))
		sys.stdout.flush()
		for x in range(mapSize):
			if(not visited[y][x] and binaryMx[y][x]):
				cc = iterativeCC(binaryMx, visited, x, y)
				if(cc):
					components.append(cc)
	print("\n\tdone")
	return components

def annotate(heightMap): # generate names and label islands
	print("generating binary height map...")
	txt = Image.new('RGBA', (mapSize, mapSize), (255,255,255,0))
	# generate binary height map (0 if water, 1 if land)
	land = [[0 for i in range(mapSize)] for j in range(mapSize)]
	for y in range(mapSize):
		sys.stdout.write("\ty: %d/%d   \r" % (y, mapSize))
		sys.stdout.flush()
		for x in range(mapSize):
			if(heightMap[y][x]>0.4):
				land[y][x] = 1
			else:
				land[y][x] = 0
	print("\n\tdone")
	components = getCC(land, txt)
	draw = ImageDraw.Draw(txt)
	chosenNames = [] # to avoid repeated island names
	for island in components:
		if(len(island)>0.5*mapSize): # ignore very small islands
			centroid = getCentroid(island)
			# place island in island categories (S, M, L, XL)
			size = None
			spacing = None
			for i in range(len(islandSizeThreshold)):
				if(len(island)<islandSizeThreshold[i]):
					size = textSizes[i]
					spacing = textSpacing[i]
					border = textBorderSize[i]
					break
			if(not size):
				size = textSizes[-1]
				spacing = textSpacing[-1]
				border = textBorderSize[-1]
			# choose a unique island name
			while(True):
				name = random.choice(islandNames)
				if(name not in chosenNames):
					chosenNames.append(name)
					break
			# draw text label over island
			font = ImageFont.truetype("fonts/BlackPearl.ttf", size)
			labelSizePx = draw.multiline_textsize(name, font=font)
			anchor = (centroid[0]-labelSizePx[0]/2.0, centroid[1]-labelSizePx[1]/2.0)
			anchor = validateTextCoord(anchor, labelSizePx)
			# shadow 
			for i in range(1, border+1):
				draw.multiline_text((anchor[0]+i, anchor[1]), name, font=font, fill=(255,255,255, 180), align='center', spacing=spacing)
				draw.multiline_text((anchor[0]-i, anchor[1]), name, font=font, fill=(255,255,255, 180), align='center', spacing=spacing)
				draw.multiline_text((anchor[0], anchor[1]+i), name, font=font, fill=(255,255,255, 180), align='center', spacing=spacing)
				draw.multiline_text((anchor[0], anchor[1]-i), name, font=font, fill=(255,255,255, 180), align='center', spacing=spacing)
			# text itself
			draw.multiline_text(anchor, name, font=font, fill=(0,0,0, 255), align='center', spacing=spacing)
	return txt

# ----------------------- script flow -----------------------
def main(out, size, noise):
	global output, mapSize, diagonal, mapCenter, mapArea, textSizes, textSpacing, textBorderSize, islandSizeThreshold

	output = out
	mapSize = int(size)
	diagonal = math.sqrt(2*mapSize**2)
	mapCenter = mapSize/2.0
	mapArea = mapSize*mapSize

	textSizes = [int(0.02*mapSize), # small island
			 int(0.025*mapSize), # medium island
			 int(0.03*mapSize), # large island
			 int(0.06*mapSize) # x large island
			]

	textSpacing = [int(0.15*s) for s in textSizes]
	textBorderSize = [int(0.05*s) for s in textSizes]

	islandSizeThreshold = [int(0.005*mapArea),
						   int(0.01*mapArea),
						   int(0.05*mapArea),
						   int(0.1*mapArea)
						  ]

	heightMap = generateTerrain()
	if(noise=='true'):
		image = colorizeImage(heightMap, noise)
		image.save('bw.png')

	image = colorizeImage(heightMap)
	labels = annotate(heightMap)
	combined = Image.alpha_composite(image, labels)
	combined = combined.filter(ImageFilter.SHARPEN)
	combined.save(output)
	combined.show()