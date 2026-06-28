"""
Ce programme a pour but de générer les images de preview pour les skins .vrm.
La liste des skins disponibles est stockée dans un dossier "skins".
Le programme lit ce dossier pour afficher les skins disponibles.
Quand on sélectionne un skin, on doit avoir un aperçu du skin avant de l'appliquer.
L'aperçu contient le nom du skin, une imag
e du skin et la taille du fichier.
Les images de preview sont stockées dans un dossier "apercus" et le programme crée une image du skin ressemblant à une photo.
pour une photo il doit faire un rendu du skin avec un fond blanc et une lumière douce, le skin doit être centré et bien visible.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw
import json


class AvatarPreviewGenerator:
    def __init__(self, skins_dir="skins", preview_dir="apercus"):
        self.skins_dir = Path(skins_dir)
        self.preview_dir = Path(preview_dir)
        self.preview_dir.mkdir(exist_ok=True)
        
    def get_available_skins(self):
        """Retourne la liste des skins disponibles"""
        if not self.skins_dir.exists():
            return []
        return [f.name for f in self.skins_dir.iterdir() if f.suffix.lower() == '.vrm']
    
    def get_file_size(self, filepath):
        """Retourne la taille du fichier en MB"""
        return os.path.getsize(filepath) / (1024 * 1024)
    
    def create_placeholder_preview(self, skin_name, output_path):
        """Crée une image de preview avec fond blanc et texte"""
        img = Image.new('RGB', (400, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Ajouter le nom du skin
        draw.text((20, 250), f"Preview: {skin_name}", fill='black')
        img.save(output_path)
    
    def generate_preview(self, skin_name):
        """Génère une preview pour un skin spécifique"""
        skin_path = self.skins_dir / skin_name
        
        if not skin_path.exists():
            print(f"Erreur: Le skin '{skin_name}' n'existe pas")
            return False
        
        file_size = self.get_file_size(skin_path)
        preview_name = skin_name.replace('.vrm', '.png')
        preview_path = self.preview_dir / preview_name
        
        # Créer une image de preview
        self.create_placeholder_preview(skin_name, preview_path)
        
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
