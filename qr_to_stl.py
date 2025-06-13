from PIL import Image
import numpy as np
import trimesh

def qr_to_stl(image_path, output_path):
    image = Image.open(image_path).convert('L')  # Convert to grayscale
    image = (np.array(image) < 128)  # Convert to binary (black and white)
    
    elevation = 3.0 # difference of height between black and white
    height_map = image.astype(float) * elevation

    vertices = []
    faces = []
    rows, cols = height_map.shape
    for i in range(rows - 1):
        for j in range(cols - 1): # divide each 2x2 block into triangles
            # identify heights of corners of 2x2 blocks
            z00 = height_map[i][j]
            z10 = height_map[i+1][j]
            z01 = height_map[i][j+1]
            z11 = height_map[i+1][j+1]
            # create (x,y,z) vertices
            idx = len(vertices)
            vertices.extend([
                (j,i,z00),
                (j+1,i,z10),
                (j,i+1,z01),
                (j+1,i+1,z11)
                ])
            # save triangle positions [0,1,2] and [0,2,3]
            faces.append([idx,idx+1,idx+2])
            faces.append([idx,idx+2,idx+3])
    mesh = trimesh.Trimesh(vertices,faces)
    mesh.export(output_path)
