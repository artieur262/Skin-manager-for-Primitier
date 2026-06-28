"""
ce programe est un gestionaire de skin sous le format .vrm
il a pour but d'avoir une interface graphique ou l'utilisateur peut choisir un skin et le mettre sur son personnage
un skin est un fichier .vrm qui contient les informations de texture et de modèle 3D pour un personnage
quand un skin est choisi, le programme va le déplacer dans le dossier courant et il supprimera l'ancien skin si il existe dans le dossier courant
la liste des skins disponibles est stockée dans un dossier "skins" et le programme va lire ce dossier pour afficher les skins disponibles
quand on clique sur un skin on doit avoir un aperçu du skin à coté de la liste des skins,
l'apperçu doit avoir le nom du skin, une image du skin et la taille du fichier

"""

import shutil
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import List, Optional

from PIL import Image, ImageTk

from genreator import AvatarPreviewGenerator

BASE_DIR = Path(__file__).resolve().parent
SKINS_DIR = BASE_DIR / "skins"
APERCU_DIR = BASE_DIR / "apercus"
PREVIEW_GENERATOR = AvatarPreviewGenerator(SKINS_DIR, APERCU_DIR)


def lister_skins() -> List[Path]:
    """Retourne la liste des fichiers .vrm disponibles."""
    if not SKINS_DIR.exists():
        return []
    return sorted(
        [f for f in SKINS_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".vrm"],
        key=lambda p: p.name.lower(),
    )


def appliquer_skin(skin_path: Path) -> Path:
    """Copie le skin choisi dans le dossier courant du script."""
    # Supprime les anciens fichiers .vrm présents dans le dossier courant
    for f in BASE_DIR.iterdir():
        if f.is_file() and f.suffix.lower() == ".vrm":
            try:
                # n'efface pas le fichier source dans le dossier skins
                if f.resolve() == skin_path.resolve():
                    continue
            except Exception:
                pass
            try:
                f.unlink()
            except Exception:
                # en cas d'erreur, on continue pour tenter les autres fichiers
                pass

    destination = BASE_DIR / skin_path.name
    shutil.copy2(skin_path, destination)
    return destination


def afficher_apercu_skin(skin_path: Path) -> bool:
    """Affiche un aperçu simple du skin et demande confirmation."""
    taille = skin_path.stat().st_size
    taille_ko = taille / 1024 if taille else 0
    preview_path = APERCU_DIR / skin_path.with_suffix(".png").name
    if not preview_path.exists():
        PREVIEW_GENERATOR.generate_preview(skin_path.name)

    apercu = tk.Toplevel()
    apercu.title(f"Aperçu - {skin_path.name}")
    apercu.geometry("420x320")
    apercu.resizable(False, False)
    apercu.transient()
    apercu.grab_set()

    tk.Label(
        apercu,
        text="Aperçu du skin sélectionné",
        font=("TkDefaultFont", 11, "bold"),
    ).pack(pady=(14, 8))

    cadre = tk.Frame(apercu, relief="groove", borderwidth=2)
    cadre.pack(fill="both", expand=True, padx=14, pady=8)

    zone_image = tk.Frame(cadre)
    zone_image.pack(fill="x", padx=12, pady=(12, 8))

    if preview_path.exists():
        try:
            with Image.open(preview_path) as source:
                preview_image = source.copy()
            preview_image.thumbnail((360, 180), Image.LANCZOS)
            image = ImageTk.PhotoImage(preview_image)
            label_image = tk.Label(zone_image, image=image)
            label_image.image = image
            label_image.pack()
        except Exception:
            tk.Label(
                zone_image,
                text="Image du skin indisponible",
                fg="gray",
            ).pack()
    else:
        tk.Label(
            zone_image,
            text="Aucune image d'aperçu n'a pu être générée",
            fg="gray",
        ).pack()

    infos = [
        f"Nom : {skin_path.name}",
        f"Taille : {taille_ko:.1f} Ko",
    ]

    for texte in infos:
        tk.Label(cadre, text=texte, anchor="w", justify="left").pack(
            fill="x", padx=12, pady=4
        )

    resultat = {"ok": False}

    def confirmer() -> None:
        resultat["ok"] = True
        apercu.destroy()

    def annuler() -> None:
        apercu.destroy()

    boutons = tk.Frame(apercu)
    boutons.pack(fill="x", padx=14, pady=(0, 14))
    tk.Button(boutons, text="Annuler", command=annuler).pack(side="right")
    tk.Button(boutons, text="Appliquer", command=confirmer).pack(side="right", padx=8)

    apercu.wait_window()
    return resultat["ok"]


class Application(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Gestionnaire de skins VRM")
        self.geometry("960x540")
        self.minsize(860, 480)
        self.preview_image = None

        self.label_info = tk.Label(
            self,
            text=f"Dossier des skins : {SKINS_DIR}",
            anchor="w",
            justify="left",
        )
        self.label_info.pack(fill="x", padx=10, pady=(10, 4))

        contenu = tk.Frame(self)
        contenu.pack(fill="both", expand=True, padx=10, pady=6)

        liste_frame = tk.Frame(contenu)
        liste_frame.pack(side="left", fill="both", expand=True)

        self.current_applied_label = tk.Label(
            liste_frame,
            text="Skin actuellement appliqué : aucun",
            anchor="w",
            justify="left",
            fg="#1b5e20",
        )
        self.current_applied_label.pack(fill="x", pady=(0, 6))

        self.listbox = tk.Listbox(liste_frame, activestyle="dotbox")
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_skin_selected)

        preview_frame = tk.LabelFrame(contenu, text="Prévisualisation", padx=12, pady=12)
        preview_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self.preview_nom = tk.Label(
            preview_frame,
            text="Clique sur un skin pour voir l'aperçu.",
            anchor="w",
            justify="left",
        )
        self.preview_nom.pack(fill="x", pady=(0, 8))

        self.preview_image_label = tk.Label(
            preview_frame,
            text="Aucune image",
            fg="gray",
        )
        self.preview_image_label.pack(fill="both", expand=True)

        self.preview_taille = tk.Label(
            preview_frame,
            text="",
            anchor="w",
            justify="left",
        )
        self.preview_taille.pack(fill="x", pady=(8, 0))

        boutons = tk.Frame(self)
        boutons.pack(fill="x", padx=10, pady=(0, 10))

        self.btn_rafraichir = tk.Button(
            boutons, text="Rafraîchir", command=self.rafraichir
        )
        self.btn_rafraichir.pack(side="left")

        self.btn_appliquer = tk.Button(
            boutons, text="Appliquer le skin", command=self.on_appliquer
        )
        self.btn_appliquer.pack(side="right")

        self.status_message = tk.StringVar(value="")
        self.status_label = tk.Label(
            self,
            textvariable=self.status_message,
            anchor="w",
            justify="left",
            fg="#1b5e20",
        )
        self.status_label.pack(fill="x", padx=10, pady=(0, 10))

        self.rafraichir()
        self.afficher_etat_vide()

    def afficher_etat_vide(self) -> None:
        self.preview_image = None
        self.preview_nom.config(text="Clique sur un skin pour voir l'aperçu.")
        self.preview_image_label.config(image="", text="Aucune image", fg="gray")
        self.preview_taille.config(text="")

    def skin_applique_actuel(self) -> Optional[Path]:
        for skin in lister_skins():
            if (BASE_DIR / skin.name).exists():
                return skin
        return None

    def nom_skin_affiche(self, skin: Path, skin_applique: Optional[Path]) -> str:
        if skin_applique is not None and skin.name == skin_applique.name:
            return f"✓ {skin.name}"
        return f"  {skin.name}"

    def nom_skin_reel(self, nom_affiche: str) -> str:
        return nom_affiche.lstrip(" ✓")

    def mettre_en_evidence_skin_applique(self) -> None:
        skin_applique = self.skin_applique_actuel()
        if skin_applique is None:
            self.current_applied_label.config(text="Skin actuellement appliqué : aucun")
        else:
            self.current_applied_label.config(
                text=f"Skin actuellement appliqué : {skin_applique.name}"
            )

    def afficher_preview(self, skin_path: Path) -> None:
        taille = skin_path.stat().st_size
        taille_ko = taille / 1024 if taille else 0
        preview_path = APERCU_DIR / skin_path.with_suffix(".png").name
        if not preview_path.exists():
            PREVIEW_GENERATOR.generate_preview(skin_path.name)

        self.preview_nom.config(text=f"Nom : {skin_path.name}")
        self.preview_taille.config(text=f"Taille : {taille_ko:.1f} Ko")

        if preview_path.exists():
            try:
                with Image.open(preview_path) as source:
                    preview_image = source.copy()
                preview_image.thumbnail((320, 220), Image.LANCZOS)
                self.preview_image = ImageTk.PhotoImage(preview_image)
                self.preview_image_label.config(image=self.preview_image, text="")
                return
            except Exception:
                pass

        self.preview_image = None
        self.preview_image_label.config(
            image="",
            text="Image du skin indisponible",
            fg="gray",
        )

    def rafraichir(self) -> None:
        self.listbox.delete(0, tk.END)
        skins = lister_skins()
        skin_applique = self.skin_applique_actuel()

        if not skins:
            self.listbox.insert(
                tk.END, "Aucun fichier .vrm trouvé dans le dossier skins."
            )
            self.listbox.config(state="disabled")
            self.btn_appliquer.config(state="disabled")
            self.mettre_en_evidence_skin_applique()
            self.afficher_etat_vide()
            return

        self.listbox.config(state="normal")
        self.btn_appliquer.config(state="normal")
        for skin in skins:
            self.listbox.insert(tk.END, self.nom_skin_affiche(skin, skin_applique))

        self.mettre_en_evidence_skin_applique()

        self.listbox.selection_clear(0, tk.END)
        if skin_applique is not None:
            for index, skin in enumerate(skins):
                if skin.name == skin_applique.name:
                    self.listbox.selection_set(index)
                    self.listbox.see(index)
                    self.afficher_preview(skin)
                    break
        else:
            self.afficher_etat_vide()

    def on_skin_selected(self, event: tk.Event) -> None:
        selection = self.listbox.curselection()
        if not selection:
            self.afficher_etat_vide()
            return

        nom = self.nom_skin_reel(self.listbox.get(selection[0]))
        skin_path = SKINS_DIR / nom
        if not skin_path.exists():
            self.afficher_etat_vide()
            return

        self.afficher_preview(skin_path)

    def on_appliquer(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning(
                "Sélection manquante", "Choisis un skin dans la liste."
            )
            return

        nom = self.nom_skin_reel(self.listbox.get(selection[0]))
        skin_path = SKINS_DIR / nom
        if not skin_path.exists():
            messagebox.showerror("Erreur", "Le fichier sélectionné n'existe plus.")
            self.rafraichir()
            return

        try:
            destination = appliquer_skin(skin_path)
            self.status_message.set(
                f"Skin appliqué : {skin_path.name} a été copié dans {destination}"
            )
            self.rafraichir()
        except Exception as exc:  # pragma: no cover - interface utilisateur
            messagebox.showerror("Erreur", f"Impossible d'appliquer le skin :\n{exc}")


def main() -> None:
    SKINS_DIR.mkdir(exist_ok=True)
    app = Application()
    app.mainloop()


if __name__ == "__main__":
    main()
