"""
Ce programme génère des aperçus visuels pour les skins .vrm.
La liste des skins disponibles est stockée dans un dossier "skins".
Le programme lit ce dossier pour afficher les skins disponibles.
Quand on sélectionne un skin, on doit avoir un aperçu du skin avant de l'appliquer.
L'aperçu doit montrer le skin assemblé, pas seulement ses textures brutes.
"""

import base64
import io
import json
import math
import os
import struct
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


class AvatarPreviewGenerator:
    def __init__(self, skins_dir="skins", preview_dir="apercus"):
        self.skins_dir = Path(skins_dir)
        self.preview_dir = Path(preview_dir)
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        self._texture_cache = {}
        
    def get_available_skins(self):
        """Retourne la liste des skins disponibles"""
        if not self.skins_dir.exists():
            return []
        return [f.name for f in self.skins_dir.iterdir() if f.suffix.lower() == '.vrm']
    
    def get_file_size(self, filepath):
        """Retourne la taille du fichier en MB"""
        return os.path.getsize(filepath) / (1024 * 1024)

    def _load_glb(self, skin_path):
        """Charge le JSON et le bloc binaire d'un fichier GLB/VRM."""
        data = skin_path.read_bytes()
        if len(data) < 20 or data[:4] != b"glTF":
            return None, None

        _, version, _ = struct.unpack_from("<4sII", data, 0)
        if version != 2:
            return None, None

        offset = 12
        json_chunk = None
        bin_chunk = None

        while offset + 8 <= len(data):
            chunk_length, chunk_type = struct.unpack_from("<I4s", data, offset)
            offset += 8
            chunk_data = data[offset : offset + chunk_length]
            offset += chunk_length

            if chunk_type == b"JSON":
                json_chunk = chunk_data.decode("utf-8").rstrip("\x00 ")
            elif chunk_type == b"BIN\x00":
                bin_chunk = chunk_data

        if not json_chunk:
            return None, None

        try:
            return json.loads(json_chunk), bin_chunk
        except json.JSONDecodeError:
            return None, None

    def _identity_matrix(self):
        return [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]

    def _matrix_multiply(self, left, right):
        result = [[0.0, 0.0, 0.0, 0.0] for _ in range(4)]
        for row in range(4):
            for column in range(4):
                result[row][column] = sum(
                    left[row][index] * right[index][column] for index in range(4)
                )
        return result

    def _matrix_vector(self, matrix, vector):
        x, y, z, w = vector
        return (
            matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z + matrix[0][3] * w,
            matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z + matrix[1][3] * w,
            matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z + matrix[2][3] * w,
            matrix[3][0] * x + matrix[3][1] * y + matrix[3][2] * z + matrix[3][3] * w,
        )

    def _translation_matrix(self, values):
        matrix = self._identity_matrix()
        matrix[0][3], matrix[1][3], matrix[2][3] = values
        return matrix

    def _scale_matrix(self, values):
        matrix = self._identity_matrix()
        matrix[0][0], matrix[1][1], matrix[2][2] = values
        return matrix

    def _quaternion_matrix(self, values):
        x, y, z, w = values
        xx = x * x
        yy = y * y
        zz = z * z
        xy = x * y
        xz = x * z
        yz = y * z
        wx = w * x
        wy = w * y
        wz = w * z

        return [
            [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy), 0.0],
            [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx), 0.0],
            [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy), 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]

    def _node_local_matrix(self, node):
        if "matrix" in node:
            raw = node["matrix"]
            return [
                [raw[0], raw[4], raw[8], raw[12]],
                [raw[1], raw[5], raw[9], raw[13]],
                [raw[2], raw[6], raw[10], raw[14]],
                [raw[3], raw[7], raw[11], raw[15]],
            ]

        matrix = self._identity_matrix()
        if "translation" in node:
            matrix = self._matrix_multiply(matrix, self._translation_matrix(node["translation"]))
        if "rotation" in node:
            matrix = self._matrix_multiply(matrix, self._quaternion_matrix(node["rotation"]))
        if "scale" in node:
            matrix = self._matrix_multiply(matrix, self._scale_matrix(node["scale"]))
        return matrix

    def _component_info(self, component_type):
        mapping = {
            5120: ("b", 1),
            5121: ("B", 1),
            5122: ("h", 2),
            5123: ("H", 2),
            5125: ("I", 4),
            5126: ("f", 4),
        }
        return mapping.get(component_type)

    def _type_size(self, type_name):
        return {
            "SCALAR": 1,
            "VEC2": 2,
            "VEC3": 3,
            "VEC4": 4,
            "MAT4": 16,
        }.get(type_name, 1)

    def _read_accessor(self, gltf, bin_chunk, accessor_index):
        accessors = gltf.get("accessors", [])
        buffer_views = gltf.get("bufferViews", [])
        if accessor_index is None or accessor_index >= len(accessors):
            return []

        accessor = accessors[accessor_index]
        buffer_view_index = accessor.get("bufferView")
        if buffer_view_index is None or buffer_view_index >= len(buffer_views):
            return []

        buffer_view = buffer_views[buffer_view_index]
        component = self._component_info(accessor.get("componentType"))
        if component is None:
            return []

        fmt_char, component_size = component
        type_count = self._type_size(accessor.get("type", "SCALAR"))
        count = accessor.get("count", 0)
        offset = buffer_view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        stride = buffer_view.get("byteStride", component_size * type_count)

        values = []
        if stride == component_size * type_count:
            fmt = "<" + (fmt_char * type_count)
            for index in range(count):
                values.append(struct.unpack_from(fmt, bin_chunk, offset + index * stride))
        else:
            for index in range(count):
                start = offset + index * stride
                values.append(
                    struct.unpack_from("<" + (fmt_char * type_count), bin_chunk, start)
                )

        if accessor.get("type", "SCALAR") == "SCALAR":
            return [item[0] for item in values]
        return values

    def _load_texture(self, gltf, bin_chunk, texture_index):
        if texture_index is None:
            return None

        textures = gltf.get("textures", [])
        images = gltf.get("images", [])
        if texture_index >= len(textures):
            return None

        image_index = textures[texture_index].get("source")
        if image_index is None or image_index >= len(images):
            return None

        cache_key = (id(bin_chunk), image_index)
        cached = self._texture_cache.get(cache_key)
        if cached is not None:
            return cached

        image_info = images[image_index]
        image_bytes = None
        uri = image_info.get("uri")
        if uri:
            if uri.startswith("data:") and "," in uri:
                _, encoded = uri.split(",", 1)
                image_bytes = base64.b64decode(encoded)
            else:
                image_bytes = None

        if image_bytes is None:
            buffer_view_index = image_info.get("bufferView")
            if buffer_view_index is not None and buffer_view_index < len(gltf.get("bufferViews", [])):
                buffer_view = gltf["bufferViews"][buffer_view_index]
                start = buffer_view.get("byteOffset", 0)
                length = buffer_view.get("byteLength", 0)
                image_bytes = bin_chunk[start : start + length]

        if image_bytes is None:
            return None

        try:
            texture = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        except Exception:
            return None

        self._texture_cache[cache_key] = texture
        return texture

    def _load_image_by_index(self, gltf, bin_chunk, image_index):
        images = gltf.get("images", [])
        if image_index is None or image_index >= len(images):
            return None

        cache_key = (id(bin_chunk), image_index, "image")
        cached = self._texture_cache.get(cache_key)
        if cached is not None:
            return cached

        image_info = images[image_index]
        image_bytes = None
        uri = image_info.get("uri")
        if uri:
            if uri.startswith("data:") and "," in uri:
                _, encoded = uri.split(",", 1)
                image_bytes = base64.b64decode(encoded)

        if image_bytes is None:
            buffer_view_index = image_info.get("bufferView")
            if buffer_view_index is not None and buffer_view_index < len(gltf.get("bufferViews", [])):
                buffer_view = gltf["bufferViews"][buffer_view_index]
                start = buffer_view.get("byteOffset", 0)
                length = buffer_view.get("byteLength", 0)
                image_bytes = bin_chunk[start : start + length]

        if image_bytes is None:
            return None

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        except Exception:
            return None

        self._texture_cache[cache_key] = image
        return image

    def _sample_texture(self, texture, u, v):
        if texture is None:
            return (208, 208, 208, 255)

        width, height = texture.size
        if width <= 0 or height <= 0:
            return (208, 208, 208, 255)

        u = u % 1.0
        v = v % 1.0
        x = min(width - 1, max(0, int(u * (width - 1) + 0.5)))
        y = min(height - 1, max(0, int((1.0 - v) * (height - 1) + 0.5)))
        return texture.getpixel((x, y))

    def _mix_color(self, color, factor):
        red, green, blue, alpha = color
        return (
            max(0, min(255, int(red * factor))),
            max(0, min(255, int(green * factor))),
            max(0, min(255, int(blue * factor))),
            alpha,
        )

    def _render_preview_image(self, skin_path, output_path, rotation_degrees=0.0, force=False):
        """Rend un aperçu du VRM avec une rotation autour de l'axe vertical."""
        gltf, bin_chunk = self._load_glb(skin_path)
        if not gltf or not bin_chunk:
            img = Image.new("RGB", (900, 1200), color="white")
            img.save(output_path)
            return

        vrm_extension = gltf.get("extensions", {}).get("VRM", {})
        meta = vrm_extension.get("meta", {}) if isinstance(vrm_extension, dict) else {}
        thumbnail_index = meta.get("texture") if isinstance(meta, dict) else None
        if not force and isinstance(thumbnail_index, int):
            thumbnail = self._load_image_by_index(gltf, bin_chunk, thumbnail_index)
            if thumbnail is not None:
                canvas = Image.new("RGBA", (900, 1200), (248, 248, 248, 255))
                max_size = (780, 1080)
                thumbnail = thumbnail.copy()
                thumbnail.thumbnail(max_size, Image.LANCZOS)
                x = (canvas.width - thumbnail.width) // 2
                y = (canvas.height - thumbnail.height) // 2
                canvas.paste(thumbnail, (x, y), thumbnail)
                canvas.convert("RGB").save(output_path)
                return

        nodes = gltf.get("nodes", [])
        if not nodes:
            img = Image.new("RGB", (900, 1200), color="white")
            img.save(output_path)
            return

        world_matrices = [None] * len(nodes)

        def walk(node_index, parent_matrix):
            node = nodes[node_index]
            local_matrix = self._node_local_matrix(node)
            world_matrix = self._matrix_multiply(parent_matrix, local_matrix)
            world_matrices[node_index] = world_matrix
            for child_index in node.get("children", []):
                walk(child_index, world_matrix)

        scene_index = gltf.get("scene", 0)
        scenes = gltf.get("scenes", [])
        root_nodes = scenes[scene_index].get("nodes", []) if scene_index < len(scenes) else []
        for root_index in root_nodes:
            walk(root_index, self._identity_matrix())

        # Les modèles VRM font face à -Z (convention VRM 0.x) alors que la caméra
        # de rendu regarde par défaut depuis +Z : sans ce décalage de 180°, la
        # rotation "0°" montrerait le dos du personnage au lieu de sa face.
        rotation_y = math.radians(rotation_degrees + 180.0)
        rotation_x = math.radians(8.0)
        cos_y = math.cos(rotation_y)
        sin_y = math.sin(rotation_y)
        cos_x = math.cos(rotation_x)
        sin_x = math.sin(rotation_x)

        def view_transform(point):
            x, y, z = point
            x2 = x * cos_y + z * sin_y
            z2 = -x * sin_y + z * cos_y
            y2 = y * cos_x - z2 * sin_x
            z3 = y * sin_x + z2 * cos_x
            return x2, y2, z3

        render_triangles = []
        all_points = []
        materials = gltf.get("materials", [])

        for node_index, node in enumerate(nodes):
            mesh_index = node.get("mesh")
            if mesh_index is None or mesh_index >= len(gltf.get("meshes", [])):
                continue

            world_matrix = world_matrices[node_index]
            if world_matrix is None:
                continue

            mesh = gltf["meshes"][mesh_index]
            for primitive in mesh.get("primitives", []):
                position_accessor = primitive.get("attributes", {}).get("POSITION")
                if position_accessor is None:
                    continue

                positions = self._read_accessor(gltf, bin_chunk, position_accessor)
                if not positions:
                    continue

                texcoord_accessor = primitive.get("attributes", {}).get("TEXCOORD_0")
                texcoords = self._read_accessor(gltf, bin_chunk, texcoord_accessor) if texcoord_accessor is not None else []

                indices_accessor = primitive.get("indices")
                if indices_accessor is not None:
                    indices = self._read_accessor(gltf, bin_chunk, indices_accessor)
                    if not indices:
                        continue
                else:
                    indices = list(range(len(positions)))

                material_index = primitive.get("material")
                texture = None
                base_color = (210, 210, 210, 255)
                double_sided = True
                if material_index is not None and material_index < len(materials):
                    material = materials[material_index]
                    double_sided = bool(material.get("doubleSided", False))
                    base_color_factor = material.get("pbrMetallicRoughness", {}).get("baseColorFactor")
                    if base_color_factor and len(base_color_factor) >= 3:
                        red = int(max(0.0, min(1.0, base_color_factor[0])) * 255)
                        green = int(max(0.0, min(1.0, base_color_factor[1])) * 255)
                        blue = int(max(0.0, min(1.0, base_color_factor[2])) * 255)
                        alpha = int(max(0.0, min(1.0, base_color_factor[3] if len(base_color_factor) > 3 else 1.0)) * 255)
                        base_color = (red, green, blue, alpha)

                    texture_info = material.get("pbrMetallicRoughness", {}).get("baseColorTexture", {})
                    texture = self._load_texture(gltf, bin_chunk, texture_info.get("index"))

                for tri_start in range(0, len(indices) - 2, 3):
                    vertex_indices = indices[tri_start : tri_start + 3]
                    if len(vertex_indices) < 3:
                        continue

                    transformed = []
                    projected = []
                    triangle_depths = []
                    uvs = []

                    for vertex_index in vertex_indices:
                        if vertex_index >= len(positions):
                            break

                        position = positions[vertex_index]
                        world_point = self._matrix_vector(
                            world_matrix, (position[0], position[1], position[2], 1.0)
                        )
                        view_point = view_transform((world_point[0], world_point[1], world_point[2]))
                        transformed.append(view_point)
                        projected.append((view_point[0], view_point[1]))
                        triangle_depths.append(view_point[2])
                        all_points.append((view_point[0], view_point[1]))

                        if texcoords and vertex_index < len(texcoords):
                            uv = texcoords[vertex_index]
                            if len(uv) >= 2:
                                uvs.append((uv[0], uv[1]))

                    if len(transformed) != 3:
                        continue

                    if len(uvs) != 3:
                        uvs = []

                    normal_x = (transformed[1][1] - transformed[0][1]) * (transformed[2][2] - transformed[0][2]) - (
                        transformed[1][2] - transformed[0][2]
                    ) * (transformed[2][1] - transformed[0][1])
                    normal_y = (transformed[1][2] - transformed[0][2]) * (transformed[2][0] - transformed[0][0]) - (
                        transformed[1][0] - transformed[0][0]
                    ) * (transformed[2][2] - transformed[0][2])
                    normal_z = (transformed[1][0] - transformed[0][0]) * (transformed[2][1] - transformed[0][1]) - (
                        transformed[1][1] - transformed[0][1]
                    ) * (transformed[2][0] - transformed[0][0])
                    normal_length = math.sqrt(normal_x * normal_x + normal_y * normal_y + normal_z * normal_z) or 1.0
                    normal_z /= normal_length

                    if not double_sided and normal_z < 0:
                        # Triangle tourné dos à la caméra : sans ça, les faces internes
                        # d'un mesh (ex. l'intérieur d'une aile fine) peuvent se dessiner
                        # par-dessus les faces visibles à cause du tri approximatif par
                        # profondeur, rendant l'aperçu illisible.
                        continue

                    light_factor = 0.58 + max(-0.18, min(0.35, normal_z * 0.28))
                    if uvs and texture is not None:
                        centroid_u = sum(uv[0] for uv in uvs) / len(uvs)
                        centroid_v = sum(uv[1] for uv in uvs) / len(uvs)
                        sampled = self._sample_texture(texture, centroid_u, centroid_v)
                        color = self._mix_color(sampled, light_factor)
                    else:
                        color = self._mix_color(base_color, light_factor)

                    depth = sum(triangle_depths) / 3.0
                    render_triangles.append((depth, projected, color))

        render_scale = 2
        canvas = Image.new("RGBA", (900 * render_scale, 1200 * render_scale), (248, 248, 248, 255))
        draw = ImageDraw.Draw(canvas, "RGBA")

        if not render_triangles or not all_points:
            canvas.convert("RGB").save(output_path)
            return

        min_x = min(point[0] for point in all_points)
        max_x = max(point[0] for point in all_points)
        min_y = min(point[1] for point in all_points)
        max_y = max(point[1] for point in all_points)

        span_x = max(max_x - min_x, 1e-6)
        span_y = max(max_y - min_y, 1e-6)
        scale = min((760.0 * render_scale) / span_x, (980.0 * render_scale) / span_y)
        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5
        offset_x = canvas.width * 0.5
        offset_y = canvas.height * 0.55

        shadow_box = [
            offset_x - (span_x * scale) * 0.34,
            offset_y + (span_y * scale) * 0.40,
            offset_x + (span_x * scale) * 0.34,
            offset_y + (span_y * scale) * 0.48,
        ]
        draw.ellipse(shadow_box, fill=(0, 0, 0, 26))

        render_triangles.sort(key=lambda item: item[0])
        for _, projected, color in render_triangles:
            points = [
                (
                    offset_x + (point[0] - center_x) * scale,
                    offset_y - (point[1] - center_y) * scale,
                )
                for point in projected
            ]
            draw.polygon(points, fill=color)

        final_image = canvas.resize((900, 1200), Image.LANCZOS)
        final_image.convert("RGB").save(output_path)

    def _solve_3x3(self, matrix, values):
        augmented = [row[:] + [value] for row, value in zip(matrix, values)]

        for column in range(3):
            pivot_row = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
            if abs(augmented[pivot_row][column]) < 1e-12:
                return None
            if pivot_row != column:
                augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]

            pivot = augmented[column][column]
            for index in range(column, 4):
                augmented[column][index] /= pivot

            for row in range(3):
                if row == column:
                    continue
                factor = augmented[row][column]
                for index in range(column, 4):
                    augmented[row][index] -= factor * augmented[column][index]

        return augmented[0][3], augmented[1][3], augmented[2][3]

    def _affine_coefficients(self, destination_points, source_points):
        matrix = [
            [destination_points[0][0], destination_points[0][1], 1.0],
            [destination_points[1][0], destination_points[1][1], 1.0],
            [destination_points[2][0], destination_points[2][1], 1.0],
        ]
        source_x = [source_points[0][0], source_points[1][0], source_points[2][0]]
        source_y = [source_points[0][1], source_points[1][1], source_points[2][1]]
        coeff_x = self._solve_3x3(matrix, source_x)
        coeff_y = self._solve_3x3(matrix, source_y)
        if coeff_x is None or coeff_y is None:
            return None
        return coeff_x[0], coeff_x[1], coeff_x[2], coeff_y[0], coeff_y[1], coeff_y[2]

    def _warp_texture_triangle(self, canvas, texture, destination_points, uv_points, mask_alpha=None):
        min_x = max(0, int(math.floor(min(point[0] for point in destination_points))))
        max_x = min(canvas.width, int(math.ceil(max(point[0] for point in destination_points))))
        min_y = max(0, int(math.floor(min(point[1] for point in destination_points))))
        max_y = min(canvas.height, int(math.ceil(max(point[1] for point in destination_points))))

        if max_x <= min_x or max_y <= min_y:
            return

        local_destination_points = [
            (point[0] - min_x, point[1] - min_y) for point in destination_points
        ]
        texture_width, texture_height = texture.size
        source_points = [
            (
                uv[0] * (texture_width - 1),
                (1.0 - uv[1]) * (texture_height - 1),
            )
            for uv in uv_points
        ]

        coefficients = self._affine_coefficients(local_destination_points, source_points)
        if coefficients is None:
            return

        patch_width = max_x - min_x
        patch_height = max_y - min_y
        warped = texture.transform(
            (patch_width, patch_height),
            Image.AFFINE,
            coefficients,
            resample=Image.BILINEAR,
        ).convert("RGBA")

        triangle_mask = Image.new("L", (patch_width, patch_height), 0)
        ImageDraw.Draw(triangle_mask).polygon(local_destination_points, fill=255)

        if mask_alpha is not None:
            triangle_mask = ImageChops.multiply(triangle_mask, mask_alpha)

        alpha = warped.getchannel("A")
        warped.putalpha(ImageChops.multiply(alpha, triangle_mask))
        canvas.alpha_composite(warped, (min_x, min_y))

    def create_preview_image(self, skin_path, output_path):
        self._render_preview_image(skin_path, output_path, rotation_degrees=0.0)

    def create_upright_preview_image(self, skin_path, output_path):
        """Crée une image d'aperçu du VRM à l'endroit."""
        self._render_preview_image(skin_path, output_path, rotation_degrees=0.0)

    def create_preview_image_180(self, skin_path, output_path):
        """Crée une image d'aperçu du VRM tournée à 180°."""
        self._render_preview_image(skin_path, output_path, rotation_degrees=180.0)
    
    def generate_preview(self, skin_name, rotation:int=0, rapide:bool=False, force:bool=False):
        """Génère une preview pour un skin spécifique"""
        skin_path = self.skins_dir / skin_name
        
        if not skin_path.exists():
            print(f"Erreur: Le skin '{skin_name}' n'existe pas")
            return False
        
        # file_size = self.get_file_size(skin_path)
        preview_name = skin_name.replace('.vrm', '.png')
        preview_path = self.preview_dir / preview_name
        
        if preview_path.exists():
            if rapide:
                print(f"L'aperçu pour '{skin_name}' existe déjà. Passage au suivant.")
                return True
            else:
                 # Supprimer l'aperçu existant pour le régénérer
                os.remove(preview_path)
                print(f"Régénération de l'aperçu pour {skin_name}")

        # Créer une image de preview à partir de la texture embarquée dans le VRM
        self._render_preview_image(skin_path, preview_path, rotation_degrees=rotation, force=force)
        
        # Sauvegarder les métadonnées
        # metadata = {
        #     'name': skin_name,
        #     'file_size_mb': round(file_size, 2),
        #     'preview_path': str(preview_path)
        # }
        
        # metadata_path = self.preview_dir / f"{preview_name}.json"
        # with open(metadata_path, 'w') as f:
        #     json.dump(metadata, f, indent=2)
        
        print(f"Preview générée: {preview_path}")
        return True
    
    def generate_all_previews(self, rapide:bool=True):
        """Génère les previews pour tous les skins"""
        skins = self.get_available_skins()
        if not skins:
            print("Aucun skin trouvé dans le dossier 'skins'")
            return
        
        for skin in skins:
            self.generate_preview(skin, rapide=rapide)
        
        print(f"Génération terminée: {len(skins)} preview(s) créée(s)")


if __name__ == "__main__":
    generator = AvatarPreviewGenerator()
    
    # Afficher les skins disponibles
    skins = generator.get_available_skins()
    print("Skins disponibles:")
    for i, skin in enumerate(skins, 1):
        print(f"{i}. {skin}")
    
    # Générer toutes les previews
    if skins:
        print("\nGénération des previews...")
        generator.generate_all_previews()
