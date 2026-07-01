"""
ce programe est un gestionaire de skin sous le format .vrm
il a pour but d'avoir une interface graphique ou l'utilisateur peut choisir un skin et le mettre sur son personnage
un skin est un fichier .vrm qui contient les informations de texture et de modèle 3D pour un personnage
quand un skin est choisi, le programme va le déplacer dans le dossier courant et il supprimera l'ancien skin si il existe dans le dossier courant
la liste des skins disponibles est stockée dans un dossier "skins" et le programme va lire ce dossier pour afficher les skins disponibles
quand on clique sur un skin on doit avoir un aperçu du skin à coté de la liste des skins,
l'apperçu doit avoir le nom du skin, une image du skin et la taille du fichier

"""
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog
from typing import Optional


from PIL import Image, ImageTk

from skins_core import (
    SKINS_DIR,
    APERCU_DIR,
    OPTIONS_DIR,
    TAGS_DIR,
    PREVIEW_GENERATOR,
    recuperer_options,
    sauvegarder_options,
    recuperer_liste_favoris,
    sauvegarder_liste_favoris,
    lister_tags,
    sauvegarder_tags,
    lister_skins_visibles,
    recuperer_tags_presets,
    skin_applique_actuel,
    appliquer_skin,
    renommer_skin,
    correspondre_recherche,
)
from options_menu import FenetreOptions


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
        #ajout le dossier options s'il n'existe pas
        OPTIONS_DIR.mkdir(exist_ok=True)

        self.__options: dict = recuperer_options()
        self.__favoris: set[str] = set(recuperer_liste_favoris())
        self.__recherche: str = ""
        self.__force_preview_generation: bool = False
        self.next_mode: Optional[str] = None
        self.title("Gestionnaire de skins VRM")
        self.geometry("960x650")
        self.minsize(860, 650)
        self.preview_image = None

        self.up_panel = tk.Frame(self)
        self.up_panel.pack(fill="x", pady=(2, 0))

       
        self.label_info = tk.Label(
            self.up_panel,
            text=f"Dossier des skins : {SKINS_DIR}",
            anchor="w",
            justify="left",
        )
        self.label_info.pack(side="left", pady=10)

        self.btn_vue_grille = tk.Button(
            self.up_panel, text="Vue grille ▦", command=self.passer_en_vue_grille
        )
        self.btn_vue_grille.pack(side="right", padx=(10, 0), pady=10)

        self.btn_options = tk.Button(
            self.up_panel, text="⚙ Options", command=self.ouvrir_options
        )
        self.btn_options.pack(side="right", padx=(10, 0), pady=10)

        self.current_applied_label = tk.Label(
            self.up_panel,
            text="Skin actuellement appliqué : aucun",
            anchor="w",
            justify="right",
            fg="#1b5e20",
        )
        self.current_applied_label.pack(side="right", padx=(10, 20), pady=10)

        contenu = tk.Frame(self)
        contenu.pack(fill="both", expand=True, padx=10, pady=6)

        liste_frame = tk.Frame(contenu)
        liste_frame.pack(side="left", fill="both", expand=True)

        self.recherche_bar = tk.Entry(liste_frame)
        self.recherche_bar.pack(fill="x", pady=(0, 8))

        self.recherche_bouton = tk.Button(
            liste_frame, text="Rechercher", command=lambda: self.set_recherche(self.recherche_bar.get().strip())
        )
        self.recherche_bouton.pack(fill="x", pady=(0, 8))

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
        
        self.boutons_degre = tk.Frame(preview_frame)
        self.boutons_degre.pack(fill="x", pady=(2, 0))

        self.label_degre = tk.Label(
            self.boutons_degre, text="Rotation de l'aperçu :"
        )
        self.label_degre.pack(side="left", padx=(0, 8))

        self.btn_degre_0 = tk.Button(
            self.boutons_degre, text="0°", command=lambda: self.changer_degre(0)
        )
        self.btn_degre_0.pack(side="left")

        self.btn_degre_180 = tk.Button(
            self.boutons_degre, text="180°", command=lambda: self.changer_degre(180)
        )
        self.btn_degre_180.pack(side="left")

        self.btn_force_preview = tk.Button(
            self.boutons_degre,
            text="activer la régénération forcée",
            command=self.toggle_force_preview_generation
        )
        self.btn_force_preview.pack(side="right", padx=(8, 0))

        self.panel_get_tags = tk.Frame(preview_frame)
        self.panel_get_tags.pack(fill="x", pady=(8, 0))

        self.panel_add_tags = tk.Frame(preview_frame)
        self.panel_add_tags.pack(fill="x", pady=(8, 0))

        self.ajouter_tags_entry = tk.Entry(self.panel_add_tags)
        self.ajouter_tags_entry.pack(side="left", fill="x", expand=True, pady=(8, 0))

        self.btn_ajouter_tags = tk.Button(
            self.panel_add_tags,
            text="Ajouter un tag",
            command=lambda: self.ajouter_tags(self.ajouter_tags_entry.get().strip())
        )
        self.btn_ajouter_tags.pack(side="left", padx=(6, 0), pady=(8, 0))

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

        self.btn_favori = tk.Button(
            preview_frame, text="Ajouter/Retirer des favoris", command=self.changer_le_favori
        )
        self.btn_favori.pack(fill="x", pady=(8, 0))

        self.btn_renommer = tk.Button(
            preview_frame, text="Renommer le skin", command=self.renommer_skin_selectionne
        )
        self.btn_renommer.pack(fill="x", pady=(8, 0))

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
        self.rafraichir()



    def get_options(self) -> dict:
        return self.__options
    
    def update_options(self, key: str, value) -> None:
        self.__options[key] = value
        sauvegarder_options(self.__options)
    
    def get_favoris(self) -> set:
        return self.__favoris
    
    def add_favori(self, skin_name: str) -> None:
        self.__favoris.add(skin_name)
        sauvegarder_liste_favoris(list(self.__favoris))
    
    def remove_favori(self, skin_name: str) -> None:
        self.__favoris.discard(skin_name)
        sauvegarder_liste_favoris(list(self.__favoris))

    def is_skin_favori(self, skin_name: str) -> bool:
        return skin_name in self.__favoris
    
    def get_force_preview_generation(self) -> bool:
        return self.__force_preview_generation
    
    def get_recherche(self) -> str:
        return self.__recherche
    
    def set_recherche(self, value: str) -> None:
        self.__recherche = value.lower()
        self.rafraichir()
    
    def set_force_preview_generation(self, value: bool) -> None:
        self.__force_preview_generation = value
        self.update_options("force_preview_generation", value)
        self.actualiser_force_preview_button()
    
    def toggle_force_preview_generation(self) -> None:
        self.__force_preview_generation = not self.__force_preview_generation
        self.update_options("force_preview_generation", self.__force_preview_generation)
        self.actualiser_force_preview_button()

    def actualiser_force_preview_button(self) -> None:
        if self.__force_preview_generation:
            self.btn_force_preview.config(relief="sunken", text="désactiver la régénération forcée")
        else:
            self.btn_force_preview.config(relief="raised", text="activer la régénération forcée")

    def afficher_etat_vide(self) -> None:
        self.preview_image = None
        self.preview_nom.config(text="Clique sur un skin pour voir l'aperçu.")
        self.preview_image_label.config(image="", text="Aucune image", fg="gray")
        self.preview_taille.config(text="")

    def passer_en_vue_grille(self) -> None:
        self.next_mode = "grille"
        self.destroy()

    def ouvrir_options(self) -> None:
        FenetreOptions(self, on_close=self.rafraichir)

    def nom_skin_affiche(self, skin: Path, skin_applique: Optional[Path]) -> str:
        name = ("♥ " if self.is_skin_favori(skin.name) else "") + skin.name
        if skin_applique is not None and skin.name == skin_applique.name:
            return f"✓ {name}"
        return f"  {name}"

    def nom_skin_reel(self, nom_affiche: str) -> str:
        return nom_affiche.lstrip(" ✓").lstrip("♥ ")

    
        

    def mettre_en_evidence_skin_applique(self) -> None:
        skin_applique = skin_applique_actuel()
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
        self.fabriquer_bouton_tags(skin_path.name)

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
                
    def rafraichir(self, skin_selected:str=None) -> None:
        
        self.listbox.delete(0, tk.END)
        skins = lister_skins_visibles()
        skin_applique = skin_applique_actuel()

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
            if correspondre_recherche(skin.name, self.get_recherche()):
                self.listbox.insert(tk.END, self.nom_skin_affiche(skin, skin_applique))

        self.mettre_en_evidence_skin_applique()
        if skin_selected is None:
            skin_selected : Path | None = skin_applique

        self.listbox.selection_clear(0, tk.END) 
        if skin_selected is not None:
            for index, skin in enumerate(skins):
                if skin.name == skin_selected.name:
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
    
    def changer_le_favori(self) -> None:
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
            if self.is_skin_favori(skin_path.name):
                self.remove_favori(skin_path.name)
                self.status_message.set(f"Skin retiré des favoris : {skin_path.name}")
            else:
                self.add_favori(skin_path.name)
                self.status_message.set(f"Skin ajouté aux favoris : {skin_path.name}")
            self.rafraichir(skin_path)
        except Exception as exc:  # pragma: no cover - interface utilisateur
            messagebox.showerror("Erreur", f"Impossible de changer le favori :\n{exc}")

    def renommer_skin_selectionne(self) -> None:
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

        nouveau_nom = simpledialog.askstring(
            "Renommer le skin",
            "Nouveau nom du skin :",
            initialvalue=skin_path.stem,
            parent=self,
        )
        if nouveau_nom is None:
            return

        try:
            destination = renommer_skin(skin_path, nouveau_nom)
            self.__favoris = set(recuperer_liste_favoris())
            self.status_message.set(f"Skin renommé : {nom} → {destination.name}")
            self.rafraichir(destination)
        except (ValueError, FileExistsError) as exc:
            messagebox.showerror("Erreur", str(exc))
        except Exception as exc:  # pragma: no cover - interface utilisateur
            messagebox.showerror("Erreur", f"Impossible de renommer le skin :\n{exc}")

    def changer_degre(self, degre: int) -> None:
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
            PREVIEW_GENERATOR.generate_preview(skin_path.name, rotation=degre, force=self.__force_preview_generation)
            self.afficher_preview(skin_path)
            self.status_message.set(f"Aperçu du skin {skin_path.name} mis à jour à {degre}°")
        except Exception as exc:  # pragma: no cover - interface utilisateur
            messagebox.showerror("Erreur", f"Impossible de changer l'apercu :\n{exc}")



    def ajouter_tags(self, tag:str) -> None:
        """Ajoute un tag au skin sélectionné."""
        tag = tag.lower().strip()
        if not tag:
            messagebox.showwarning("Tag vide", "Le tag ne peut pas être vide.")
            return
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
            tags = lister_tags(skin_path.name)
            if tag not in tags:
                tags.append(tag)
                sauvegarder_tags(skin_path.name, tags)
                self.status_message.set(f"Tag '{tag}' ajouté au skin {skin_path.name}")
                self.afficher_preview(skin_path)
            else:
                messagebox.showinfo("Info", f"Le tag '{tag}' existe déjà pour ce skin.")
        except Exception as exc:  # pragma: no cover - interface utilisateur
            messagebox.showerror("Erreur", f"Impossible de supprimer le tag :\n{exc}")

    def suprimer_tags(self, tag:str) -> None:
        """Supprime un tag du skin sélectionné."""
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
            tags = lister_tags(skin_path.name)
            if tag in tags:
                tags.remove(tag)
                sauvegarder_tags(skin_path.name, tags)
                self.status_message.set(f"Tag '{tag}' supprimé du skin {skin_path.name}")
                self.rafraichir(skin_path)
            else:
                messagebox.showinfo("Info", f"Le tag '{tag}' n'existe pas pour ce skin.")
        except Exception as exc:  # pragma: no cover - interface utilisateur
            messagebox.showerror("Erreur", f"Impossible de supprimer le tag :\n{exc}")


    def fabriquer_bouton_tags(self, skin_name: str) -> None:
        """Fabrique un bouton pour supprimer un tag du skin sélectionné."""
        for widget in self.panel_get_tags.winfo_children():
            widget.destroy()
        if not skin_name:
            return
        label_tags = tk.Label(self.panel_get_tags, text="Tags :")
        label_tags.pack(side="left", pady=10, padx=(0, 4))
        for tag in lister_tags(skin_name):
            btn = tk.Button(
                self.panel_get_tags,
                text=f"'{tag}'",
                command=lambda t=tag: self.suprimer_tags(t)
            )
            btn.pack(side="left", pady=10, padx=4)
        bouton_ajouter_tag_preset = tk.Button(
            self.panel_get_tags,
            text="+ Tag préréglé",
            command=self.ouvrir_menu_presets_tags,
        )
        bouton_ajouter_tag_preset.pack(side="left", pady=10, padx=4)

    def ouvrir_menu_presets_tags(self) -> None:
        """Propose les préréglages de tags (définis dans Options) pour ajout rapide."""
        presets = recuperer_tags_presets()
        if not presets:
            messagebox.showinfo(
                "Aucun préréglage",
                "Ajoute des préréglages de tags depuis le menu ⚙ Options pour les retrouver ici.",
            )
            return

        menu = tk.Menu(self, tearoff=0)
        for preset in presets:
            menu.add_command(label=preset, command=lambda p=preset: self.ajouter_tags(p))

        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()


def main() -> None:
    SKINS_DIR.mkdir(exist_ok=True)
    mode = "liste"
    while mode:
        if mode == "liste":
            app = Application()
        else:
            from main import ApplicationGrille

            app = ApplicationGrille()
        app.mainloop()
        mode = getattr(app, "next_mode", None)

if __name__ == "__main__":
    main()
