"""
Ce programme a pour but de générer les images de preview pour les skins .vrm. 
La liste des skins disponibles est stockée dans un dossier "skins" 
et le programme va lire ce dossier pour afficher les skins disponibles. 
Quand on sélectionne un skin, on doit avoir un aperçu du skin avant de l'appliquer. 
L'aperçu doit avoir le nom du skin, une image du skin et la taille du fichier.
les images de preview sont stockées dans un dossier "apercus" et le programme va lire ce dossier pour afficher les aperçus disponibles.
"""

import os
import json
from pathlib import Path
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Erreur: installez Pillow avec 'pip install Pillow' (le module à importer est PIL).")

# Chemins des dossiers
SKINS_FOLDER = "skins"
APERCUS_FOLDER = "apercus"

def get_file_size(filepath):
    """Retourne la taille du fichier en MB."""
    size_bytes = os.path.getsize(filepath)
    size_mb = size_bytes / (1024 * 1024)
    return f"{size_mb:.2f} MB"

def list_available_skins():
    """Liste tous les fichiers .vrm disponibles dans le dossier 'skins'."""
    if not os.path.exists(SKINS_FOLDER):
        os.makedirs(SKINS_FOLDER)
        print(f"Dossier '{SKINS_FOLDER}' créé.")
        return []
    
    skins = [f for f in os.listdir(SKINS_FOLDER) if f.endswith('.vrm')]
    return skins

def generate_preview(skin_name, skin_path):
    """Génère une image de preview pour un skin."""
    if not os.path.exists(APERCUS_FOLDER):
        os.makedirs(APERCUS_FOLDER)
    
    # Créer une image de preview
    img = Image.new('RGB', (400, 300), color='lightgray')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Ajouter les informations
    file_size = get_file_size(skin_path)
    
    draw.text((20, 50), f"Skin: {skin_name}", fill="black", font=font)
    draw.text((20, 120), f"Fichier: {skin_name}", fill="black", font=font_small)
    draw.text((20, 150), f"Taille: {file_size}", fill="black", font=font_small)
    
    # Sauvegarder l'aperçu
    preview_name = skin_name.replace('.vrm', '.png')
    preview_path = os.path.join(APERCUS_FOLDER, preview_name)
    img.save(preview_path)
    print(f"Aperçu généré: {preview_path}")

def generate_all_previews():
    """Génère les aperçus pour tous les skins disponibles."""
    skins = list_available_skins()
    
    if not skins:
        print("Aucun skin trouvé dans le dossier 'skins'.")
        return
    
    print(f"Nombre de skins trouvés: {len(skins)}")
    
    for skin in skins:
        skin_path = os.path.join(SKINS_FOLDER, skin)
        generate_preview(skin, skin_path)

def display_previews():
    """Affiche les aperçus disponibles."""
    if not os.path.exists(APERCUS_FOLDER):
        print("Aucun aperçu disponible.")
        return
    
    previews = [f for f in os.listdir(APERCUS_FOLDER) if f.endswith('.png')]
    
    print("\nAperçus disponibles:")
    for preview in previews:
        preview_path = os.path.join(APERCUS_FOLDER, preview)
        print(f"  - {preview}")

if __name__ == "__main__":
    print("=== Générateur d'aperçus pour skins VRM ===\n")
    generate_all_previews()
    display_previews()

