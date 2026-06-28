"""
Ce programme génère des aperçus visuels pour les skins .vrm.
La liste des skins disponibles est stockée dans un dossier "skins".
Le programme lit ce dossier pour afficher les skins disponibles.
Quand on sélectionne un skin, on doit avoir un aperçu du skin avant de l'appliquer.
L'aperçu doit utiliser la vraie texture du VRM quand elle est embarquée dans le fichier,
et être stocké dans le dossier "apercus".
"""

import base64
import io
import json
import os
import struct
from pathlib import Path

from PIL import Image


class AvatarPreviewGenerator:
    def __init__(self, skins_dir="skins", preview_dir="apercus"):
        self.skins_dir = Path(skins_dir)
        self.preview_dir = Path(preview_dir)
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        
    def get_available_skins(self):
        """Retourne la liste des skins disponibles"""
        if not self.skins_dir.exists():
            return []
        return [f.name for f in self.skins_dir.iterdir() if f.suffix.lower() == '.vrm']
    
    def get_file_size(self, filepath):
        """Retourne la taille du fichier en MB"""
        return os.path.getsize(filepath) / (1024 * 1024)
    
    def _extract_image_bytes_from_vrm(self, skin_path):
        """Extrait la première image embarquée dans un fichier VRM/GLB."""
        data = skin_path.read_bytes()
        if len(data) < 20 or data[:4] != b"glTF":
            return None

        _, version, _ = struct.unpack_from("<4sII", data, 0)
        if version != 2:
            return None

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
            return None

        try:
            gltf = json.loads(json_chunk)
        except json.JSONDecodeError:
            return None

        images = gltf.get("images", [])
        buffer_views = gltf.get("bufferViews", [])

        for image_info in images:
            image_bytes = None

            uri = image_info.get("uri")
            if uri:
                if uri.startswith("data:") and "," in uri:
                    _, encoded = uri.split(",", 1)
                    image_bytes = base64.b64decode(encoded)
                else:
                    external_path = (skin_path.parent / uri).resolve()
                    if external_path.exists():
                        image_bytes = external_path.read_bytes()

            if image_bytes is None and bin_chunk is not None:
                buffer_view_index = image_info.get("bufferView")
                if buffer_view_index is not None and 0 <= buffer_view_index < len(buffer_views):
                    buffer_view = buffer_views[buffer_view_index]
                    start = buffer_view.get("byteOffset", 0)
                    length = buffer_view.get("byteLength", 0)
                    image_bytes = bin_chunk[start : start + length]

            if image_bytes:
                return image_bytes

        return None

    def create_preview_image(self, skin_path, output_path):
        """Crée une image d'aperçu à partir de la vraie texture du VRM."""
        image_bytes = self._extract_image_bytes_from_vrm(skin_path)
        if image_bytes is None:
            img = Image.new("RGB", (400, 600), color="white")
            img.save(output_path)
            return

        try:
            preview = Image.open(io.BytesIO(image_bytes))
            preview = preview.convert("RGBA")
        except Exception:
            img = Image.new("RGB", (400, 600), color="white")
            img.save(output_path)
            return

        canvas = Image.new("RGBA", (900, 1200), (255, 255, 255, 255))
        max_size = (840, 1140)
        preview.thumbnail(max_size, Image.LANCZOS)
        x = (canvas.width - preview.width) // 2
        y = (canvas.height - preview.height) // 2
        canvas.paste(preview, (x, y), preview)
        canvas.convert("RGB").save(output_path)
    
    def generate_preview(self, skin_name):
        """Génère une preview pour un skin spécifique"""
        skin_path = self.skins_dir / skin_name
        
        if not skin_path.exists():
            print(f"Erreur: Le skin '{skin_name}' n'existe pas")
            return False
        
        file_size = self.get_file_size(skin_path)
        preview_name = skin_name.replace('.vrm', '.png')
        preview_path = self.preview_dir / preview_name
        
        # Créer une image de preview à partir de la texture embarquée dans le VRM
        self.create_preview_image(skin_path, preview_path)
        
        # Sauvegarder les métadonnées
        metadata = {
            'name': skin_name,
            'file_size_mb': round(file_size, 2),
            'preview_path': str(preview_path)
        }
        
        metadata_path = self.preview_dir / f"{preview_name}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Preview générée: {preview_path}")
        return True
    
    def generate_all_previews(self):
        """Génère les previews pour tous les skins"""
        skins = self.get_available_skins()
        if not skins:
            print("Aucun skin trouvé dans le dossier 'skins'")
            return
        
        for skin in skins:
            self.generate_preview(skin)
        
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
