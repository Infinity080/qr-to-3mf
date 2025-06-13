from PIL import Image
import numpy as np
import lib3mf
import qrcode

def link_to_png(link, output_path):
    qr = qrcode.QRCode()
    qr.add_data(link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    return output_path

def qr_to_3mf(link, output_path, scale = 90): # 90 mm
    image_path = "error"
    image_path = link_to_png(link, image_path)

    image = Image.open(image_path).convert('L')  # Convert to grayscale
    image = (np.array(image) < 128)  # Convert to binary (black and white)
    
    elevation = 1.0 # difference of height between black and white
    height_map = image.astype(float) * elevation

    black_vertices = []
    black_faces = []

    base_z = 4.0

    rows, cols = height_map.shape

    local_scale = scale / max(rows,cols) # adjust to be 90 mm

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

    color_group = model.AddColorGroup()
    white_color = color_group.AddColor(lib3mf.Color(255, 255, 255, 255))
    black_color = color_group.AddColor(lib3mf.Color(0, 0, 0, 255))

    # white base mesh
    base_mesh = model.AddMeshObject()
    base_mesh.SetName("Base")

    for vert in base_vertices:
        position = lib3mf.Position((
            float(vert[0]) * local_scale,
            float(vert[1]) * local_scale,
            float(vert[2])
        ))

        base_mesh.AddVertex(position)

    # Add triangles
    for face in base_faces:
        triangle = lib3mf.Triangle(Indices=(face[0], face[1], face[2]))
        base_mesh.AddTriangle(triangle)

    resource_id = color_group.GetResourceID()
    base_mesh.SetObjectLevelProperty(resource_id, white_color)

    model.AddBuildItem(base_mesh, wrapper.GetIdentityTransform())

    # black part
    black_mesh = model.AddMeshObject()
    black_mesh.SetName("Black")

    for vert in black_vertices:
        position = lib3mf.Position((
            float(vert[0]) * local_scale,
            float(vert[1]) * local_scale,
            float(vert[2])
        ))

        black_mesh.AddVertex(position)

    for face in black_faces:
        triangle = lib3mf.Triangle(Indices=(face[0], face[1], face[2]))
        black_mesh.AddTriangle(triangle)

    black_mesh.SetObjectLevelProperty(resource_id, black_color)

    model.AddBuildItem(black_mesh, wrapper.GetIdentityTransform())

    writer = model.QueryWriter("3mf")
    writer.WriteToFile(output_path)

qr_to_3mf("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "rickroll.3mf")