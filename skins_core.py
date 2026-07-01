"""
Logique commune (non graphique) partagée par les différentes interfaces
de sélection de skins (vue liste et vue grille).
"""
import json
import shutil
from pathlib import Path
from tkinter import messagebox
from typing import List, Optional

from genreator import AvatarPreviewGenerator

BASE_DIR = Path(__file__).resolve().parent
SKINS_DIR = BASE_DIR / "skins"
APERCU_DIR = BASE_DIR / "apercus"
OPTIONS_DIR = BASE_DIR / "options"
TAGS_DIR = BASE_DIR / "tags"

PREVIEW_GENERATOR = AvatarPreviewGenerator(SKINS_DIR, APERCU_DIR)


def recuperer_options() -> dict:
    """Récupère les options depuis le fichier options.json."""
    OPTIONS_DIR.mkdir(exist_ok=True)
    options_file = OPTIONS_DIR / "options.json"
    if not options_file.exists():
        with open(options_file, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}
    try:
        with open(options_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def sauvegarder_options(options: dict) -> None:
    """Sauvegarde les options dans le fichier options.json."""
    OPTIONS_DIR.mkdir(exist_ok=True)
    options_file = OPTIONS_DIR / "options.json"
    try:
        with open(options_file, "w", encoding="utf-8") as f:
            json.dump(options, f, indent=4)
    except Exception:
        pass


def recuperer_liste_favoris() -> List[str]:
    """Récupère la liste des skins favoris depuis le fichier favoris.json."""
    OPTIONS_DIR.mkdir(exist_ok=True)
    favoris_file = OPTIONS_DIR / "favoris.json"
    if not favoris_file.exists():
        with open(favoris_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
        return []
    try:
        with open(favoris_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def sauvegarder_liste_favoris(favoris: List[str]) -> None:
    """Sauvegarde la liste des skins favoris dans le fichier favoris.json."""
    OPTIONS_DIR.mkdir(exist_ok=True)
    favoris_file = OPTIONS_DIR / "favoris.json"
    try:
        with open(favoris_file, "w", encoding="utf-8") as f:
            json.dump(favoris, f, indent=4)
    except Exception:
        pass


def lister_tags(skin_name: str) -> List[str]:
    """Retourne la liste des tags associés à un skin."""
    TAGS_DIR.mkdir(exist_ok=True)
    tag_file = TAGS_DIR / f"{skin_name}.json"
    if not tag_file.exists():
        return []
    try:
        with open(tag_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def sauvegarder_tags(skin_name: str, tags: List[str]) -> None:
    """Sauvegarde la liste des tags associés à un skin."""
    TAGS_DIR.mkdir(exist_ok=True)
    tag_file = TAGS_DIR / f"{skin_name}.json"
    if not tags:
        try:
            if tag_file.exists():
                tag_file.unlink()
        except Exception:
            pass
        return
    try:
        with open(tag_file, "w", encoding="utf-8") as f:
            json.dump(tags, f, indent=4)
    except Exception:
        pass


def lister_skins() -> List[Path]:
    """Retourne la liste des fichiers .vrm disponibles."""
    if not SKINS_DIR.exists():
        return []
    return sorted(
        [f for f in SKINS_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".vrm"],
        key=lambda p: p.name.lower(),
    )


def skin_applique_actuel() -> Optional[Path]:
    """Retourne le skin actuellement copié à la racine du projet, s'il y en a un."""
    for skin in lister_skins():
        if (BASE_DIR / skin.name).exists():
            return skin
    return None


def appliquer_skin(skin_path: Path) -> Path:
    """Copie le skin choisi dans le dossier courant du script."""
    SKINS_DIR.mkdir(exist_ok=True)

    # Supprime/range les anciens fichiers .vrm présents dans le dossier courant
    for f in BASE_DIR.iterdir():
        if f.is_file() and f.suffix.lower() == ".vrm":
            try:
                if f.resolve() == skin_path.resolve():
                    continue
            except Exception:
                pass

            try:
                destination = SKINS_DIR / f.name
                if not destination.exists():
                    shutil.move(f, destination)
                else:
                    try:
                        f.unlink()
                    except Exception:
                        messagebox.showwarning(
                            "Erreur",
                            f"Impossible de supprimer le fichier {f.name} dans le dossier courant.",
                        )
            except Exception:
                messagebox.showwarning(
                    "Erreur",
                    f"Impossible de déplacer le fichier {f.name} dans le dossier skins.",
                )

    destination = BASE_DIR / skin_path.name
    shutil.copy2(skin_path, destination)
    return destination


def correspondre_recherche(skin_name: str, recherche: str) -> bool:
    """Vérifie si le skin correspond à la recherche (texte libre ou '#tag')."""
    if not recherche:
        return True
    if recherche[0] == "#":
        tag_recherche = recherche[1:]
        tags = lister_tags(skin_name)
        return tag_recherche in tags
    return recherche in skin_name.lower()
