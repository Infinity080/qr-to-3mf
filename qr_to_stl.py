from PIL import Image
import numpy as np
import trimesh
import lib3mf

def qr_to_3mf(image_path, output_path):
    image = Image.open(image_path).convert('L')  # Convert to grayscale
    image = (np.array(image) < 128)  # Convert to binary (black and white)
    
    elevation = 3.0 # difference of height between black and white
    height_map = image.astype(float) * elevation

    black_vertices = []
    black_faces = []

    base_z = 1.0

    rows, cols = height_map.shape

    box_vertices = [
        (0,     0,     0),
        (cols,  0,     0),
        (cols,  rows,  0),
        (0,     rows,  0),
        (0,     0,     base_z),
        (cols,  0,     base_z),
        (cols,  rows,  base_z),
        (0,     rows,  base_z),
    ]

    box_faces = [
        (0, 1, 2), (0, 2, 3),  # bottom
        (4, 5, 6), (4, 6, 7),  # top
        (0, 1, 5), (0, 5, 4),  # front
        (1, 2, 6), (1, 6, 5),  # right
        (2, 3, 7), (2, 7, 6),  # back
        (3, 0, 4), (3, 4, 7),  # left
    ]
    # vertices and faces form a cube of size (cols x rows x base_z)
    base_vertices = box_vertices
    base_faces = box_faces

    for i in range(rows - 1):
        for j in range(cols - 1): # divide each 2x2 block into triangles
            # identify heights of corners of 2x2 blocks
            z00 = base_z + height_map[i][j]
            z10 = base_z + height_map[i+1][j]
            z01 = base_z + height_map[i][j+1]
            z11 = base_z + height_map[i+1][j+1]

            if image[i][j] or image[i+1][j] or image[i][j+1] or image[i+1][j+1]: # add elevated vertices and faces
                black_idx = len(black_vertices)
                black_vertices.extend([
                    (j, i, z00),
                    (j+1, i, z10),
                    (j, i+1, z01),
                    (j+1, i+1, z11)
                ])
                black_faces.append([black_idx, black_idx + 1, black_idx + 2])
                black_faces.append([black_idx, black_idx + 2, black_idx + 3])

    # convert to 3mf
    wrapper = lib3mf.get_wrapper()
    model = wrapper.CreateModel()
    # white base mesh
    base_mesh = model.AddMeshObject()
    base_mesh.SetName("Base")

    for vert in base_vertices:
        position = lib3mf.Position((float(vert[0]), float(vert[1]), float(vert[2])))
        base_mesh.AddVertex(position)

    # Add triangles
    for face in base_faces:
        triangle = lib3mf.Triangle(Indices=(face[0], face[1], face[2]))
        base_mesh.AddTriangle(triangle)

    model.AddBuildItem(base_mesh, wrapper.GetIdentityTransform())

    # black part
    black_mesh = model.AddMeshObject()
    black_mesh.SetName("Black")

    for vert in black_vertices:
        position = lib3mf.Position((float(vert[0]), float(vert[1]), float(vert[2])))
        black_mesh.AddVertex(position)

    for face in black_faces:
        triangle = lib3mf.Triangle(Indices=(face[0], face[1], face[2]))
        black_mesh.AddTriangle(triangle)

    model.AddBuildItem(black_mesh, wrapper.GetIdentityTransform())

    writer = model.QueryWriter("3mf")
    writer.WriteToFile(output_path)



qr_to_3mf("image1.png", "test_mesh3mf.3mf")