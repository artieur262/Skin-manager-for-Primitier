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


CARACTERES_INVALIDES = set('\\/:*?"<>|')


def renommer_skin(skin_path: Path, nouveau_nom: str) -> Path:
    """Renomme un skin ainsi que son fichier de tags et son aperçu associés.

    Le nom de fichier de l'aperçu et celui du fichier de tags sont dérivés
    du nom du skin (même base), donc ils doivent être renommés en même
    temps pour ne pas se retrouver orphelins.
    """
    nouveau_nom = nouveau_nom.strip()
    if not nouveau_nom:
        raise ValueError("Le nouveau nom ne peut pas être vide.")
    if any(caractere in CARACTERES_INVALIDES for caractere in nouveau_nom):
        raise ValueError('Le nom ne peut pas contenir : \\ / : * ? " < > |')
    if not nouveau_nom.lower().endswith(".vrm"):
        nouveau_nom += ".vrm"

    ancien_nom = skin_path.name
    destination = SKINS_DIR / nouveau_nom
    if ancien_nom == nouveau_nom:
        return skin_path
    if destination.exists():
        raise FileExistsError(f"Un skin nommé '{nouveau_nom}' existe déjà.")

    skin_path.rename(destination)

    ancien_apercu = APERCU_DIR / Path(ancien_nom).with_suffix(".png").name
    nouvel_apercu = APERCU_DIR / destination.with_suffix(".png").name
    if ancien_apercu.exists():
        try:
            ancien_apercu.replace(nouvel_apercu)
        except Exception:
            pass

    ancien_tags = TAGS_DIR / f"{ancien_nom}.json"
    nouveau_tags = TAGS_DIR / f"{nouveau_nom}.json"
    if ancien_tags.exists():
        try:
            ancien_tags.replace(nouveau_tags)
        except Exception:
            pass

    favoris = recuperer_liste_favoris()
    if ancien_nom in favoris:
        sauvegarder_liste_favoris(
            [nouveau_nom if favori == ancien_nom else favori for favori in favoris]
        )

    # Si ce skin est actuellement appliqué à la racine du projet, on garde
    # le fichier appliqué cohérent avec le nouveau nom.
    applique = BASE_DIR / ancien_nom
    if applique.exists():
        try:
            applique.replace(BASE_DIR / nouveau_nom)
        except Exception:
            pass

    return destination


TRADUCTION_CARACTERES_INTERDITS = str.maketrans({c: "-" for c in CARACTERES_INVALIDES})


def _semble_venir_de_vroid_hub(skin_path: Path) -> bool:
    """Un fichier téléchargé tel quel depuis hub.vroid.com est nommé avec un
    identifiant numérique (ex. 6795810513740058493.vrm)."""
    return skin_path.stem.isdigit()


def renommer_avatars_vroid_hub() -> dict:
    """Renomme les skins encore nommés par leur identifiant hub.vroid.com en
    utilisant le titre présent dans les métadonnées VRM (extensions.VRM.meta.title).

    Ne touche pas aux skins déjà renommés manuellement (nom non numérique).
    Retourne un résumé : {"renommes": [(ancien, nouveau), ...], "ignores": [...], "erreurs": [...]}.
    """
    resultat = {"renommes": [], "ignores": [], "erreurs": []}

    for skin_path in lister_skins():
        if not _semble_venir_de_vroid_hub(skin_path):
            continue

        try:
            meta = PREVIEW_GENERATOR.read_vrm_meta(skin_path)
        except Exception as exc:
            resultat["erreurs"].append((skin_path.name, str(exc)))
            continue

        titre = (meta.get("title") or "").strip()
        nouveau_nom = titre.translate(TRADUCTION_CARACTERES_INTERDITS).strip(" .")
        if not nouveau_nom:
            resultat["ignores"].append(skin_path.name)
            continue

        candidat = nouveau_nom
        suffixe = 2
        while True:
            destination_visee = SKINS_DIR / f"{candidat}.vrm"
            if not destination_visee.exists() or destination_visee.resolve() == skin_path.resolve():
                break
            candidat = f"{nouveau_nom} ({suffixe})"
            suffixe += 1

        try:
            destination = renommer_skin(skin_path, candidat)
            resultat["renommes"].append((skin_path.name, destination.name))
        except Exception as exc:
            resultat["erreurs"].append((skin_path.name, str(exc)))

    return resultat


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
                            "Error",
                            f"Could not delete file {f.name} in the current folder.",
                        )
            except Exception:
                messagebox.showwarning(
                    "Error",
                    f"Could not move file {f.name} to the skins folder.",
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


def lister_tous_les_tags() -> List[str]:
    """Retourne la liste de tous les tags utilisés par au moins un skin."""
    TAGS_DIR.mkdir(exist_ok=True)
    tags = set()
    for fichier in TAGS_DIR.glob("*.json"):
        try:
            with open(fichier, "r", encoding="utf-8") as f:
                tags.update(json.load(f))
        except Exception:
            continue
    return sorted(tags)


def _recuperer_fichier_tags() -> dict:
    """Récupère les réglages de tags (préréglages et masquants) depuis options/tags.json.

    Ces deux réglages vivaient auparavant dans options.json : s'ils y sont
    encore présents (fichier créé avant cette séparation), on les rapatrie
    ici une bonne fois pour toutes puis on les retire d'options.json, pour
    ne pas perdre les réglages déjà faits par l'utilisateur.
    """
    OPTIONS_DIR.mkdir(exist_ok=True)
    tags_file = OPTIONS_DIR / "tags.json"
    if not tags_file.exists():
        options = recuperer_options()
        donnees = {}
        a_migrer = False
        for cle in ("tags_masques", "tags_presets"):
            if cle in options:
                donnees[cle] = options.pop(cle)
                a_migrer = True
        if a_migrer:
            sauvegarder_options(options)
        donnees.setdefault("tags_masques", [])
        donnees.setdefault("tags_presets", [])
        _sauvegarder_fichier_tags(donnees)
        return donnees
    try:
        with open(tags_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"tags_masques": [], "tags_presets": []}


def _sauvegarder_fichier_tags(donnees: dict) -> None:
    """Sauvegarde les réglages de tags (préréglages et masquants) dans options/tags.json."""
    OPTIONS_DIR.mkdir(exist_ok=True)
    tags_file = OPTIONS_DIR / "tags.json"
    try:
        with open(tags_file, "w", encoding="utf-8") as f:
            json.dump(donnees, f, indent=4)
    except Exception:
        pass


def recuperer_tags_presets() -> List[str]:
    """Retourne la liste des tags prédéfinis (ajout rapide depuis le menu de configuration)."""
    return _recuperer_fichier_tags().get("tags_presets", [])


def sauvegarder_tags_presets(presets: List[str]) -> None:
    """Sauvegarde la liste des tags prédéfinis."""
    donnees = _recuperer_fichier_tags()
    donnees["tags_presets"] = presets
    _sauvegarder_fichier_tags(donnees)


def recuperer_tags_masques() -> List[str]:
    """Retourne la liste des tags qui masquent les skins qui les portent."""
    return _recuperer_fichier_tags().get("tags_masques", [])


def sauvegarder_tags_masques(tags: List[str]) -> None:
    """Sauvegarde la liste des tags qui masquent les skins qui les portent."""
    donnees = _recuperer_fichier_tags()
    donnees["tags_masques"] = tags
    _sauvegarder_fichier_tags(donnees)


def skin_est_masque(skin_name: str, tags_masques: Optional[List[str]] = None) -> bool:
    """Vérifie si un skin doit être masqué car il porte un tag masquant."""
    if tags_masques is None:
        tags_masques = recuperer_tags_masques()
    if not tags_masques:
        return False
    return any(tag in tags_masques for tag in lister_tags(skin_name))


def lister_skins_visibles() -> List[Path]:
    """Retourne les skins disponibles, sans ceux masqués par un tag masquant.

    Les skins masqués restent utilisables (skin appliqué, renommage...) mais
    n'apparaissent plus dans les listes/grilles de navigation habituelles.
    Seul le menu des options permet de savoir quels tags masquent des skins.
    """
    tags_masques = recuperer_tags_masques()
    return [s for s in lister_skins() if not skin_est_masque(s.name, tags_masques)]


def recuperer_interface_demarrage() -> str:
    """Retourne l'interface à afficher au démarrage de main.py ('grille' ou 'liste')."""
    valeur = recuperer_options().get("interface_demarrage", "grille")
    return valeur if valeur in ("grille", "liste") else "grille"


def sauvegarder_interface_demarrage(interface: str) -> None:
    """Sauvegarde l'interface à afficher au démarrage de main.py."""
    options = recuperer_options()
    options["interface_demarrage"] = interface
    sauvegarder_options(options)


def recuperer_verrouillage_options_main() -> bool:
    """Indique si l'accès au menu des options est bloqué depuis main.py."""
    return bool(recuperer_options().get("verrouiller_options_main", False))


def sauvegarder_verrouillage_options_main(verrouille: bool) -> None:
    """Bloque/débloque l'accès au menu des options depuis main.py."""
    options = recuperer_options()
    options["verrouiller_options_main"] = verrouille
    sauvegarder_options(options)


def recuperer_plein_ecran_demarrage() -> bool:
    """Indique si main.py doit démarrer en fenêtre maximisée (plein écran)."""
    return bool(recuperer_options().get("plein_ecran_demarrage", False))


def sauvegarder_plein_ecran_demarrage(plein_ecran: bool) -> None:
    """Sauvegarde si main.py doit démarrer en fenêtre maximisée (plein écran)."""
    options = recuperer_options()
    options["plein_ecran_demarrage"] = plein_ecran
    sauvegarder_options(options)


def recuperer_verrouillage_configuration_main() -> bool:
    """Indique si l'accès à la vue liste (configuration) est bloqué depuis main.py."""
    return bool(recuperer_options().get("verrouiller_configuration_main", False))


def sauvegarder_verrouillage_configuration_main(verrouille: bool) -> None:
    """Bloque/débloque l'accès à la vue liste (configuration) depuis main.py."""
    options = recuperer_options()
    options["verrouiller_configuration_main"] = verrouille
    sauvegarder_options(options)
