"""
Interface graphique alternative pour choisir un skin .vrm.

Contrairement à `selection.py` (liste + panneau de configuration), cette
interface met en avant une grille visuelle de vignettes, façon menu de
sélection de skins des jeux vidéo (voir test.png) : on parcourt les skins
sous forme d'images plutôt que sous forme de texte, et on retrouve le
minimum de réglages (recherche, favoris, application du skin).

On peut basculer à tout moment vers l'autre interface via le bouton
"Vue liste" en haut de la fenêtre.
"""
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Dict, List, Optional

from PIL import Image, ImageTk

from skins_core import (
    APERCU_DIR,
    OPTIONS_DIR,
    PREVIEW_GENERATOR,
    SKINS_DIR,
    appliquer_skin,
    correspondre_recherche,
    lister_skins_visibles,
    recuperer_interface_demarrage,
    recuperer_liste_favoris,
    recuperer_plein_ecran_demarrage,
    recuperer_verrouillage_configuration_main,
    recuperer_verrouillage_options_main,
    sauvegarder_liste_favoris,
    skin_applique_actuel,
)
from options_menu import FenetreOptions

CARD_WIDTH = 156
CARD_HEIGHT = 214
THUMB_MAX_SIZE = (132, 150)
GRID_PADDING = 10

COULEUR_FOND_CARTE = "#f4f4f4"
COULEUR_BORDURE = "#d0d0d0"
COULEUR_SELECTION = "#2e7d32"
COULEUR_APPLIQUE = "#1565c0"


class CarteSkin:
    """Regroupe les widgets d'une vignette de skin dans la grille."""

    def __init__(self, cadre: tk.Frame, image_label: tk.Label, etoile: tk.Label, badge: tk.Label):
        self.cadre = cadre
        self.image_label = image_label
        self.etoile = etoile
        self.badge = badge


class ApplicationGrille(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        OPTIONS_DIR.mkdir(exist_ok=True)

        self.__favoris: set[str] = set(recuperer_liste_favoris())
        self.__recherche: str = ""
        self.__onglet: str = "tous"
        self.next_mode: Optional[str] = None

        self.selected_skin: Optional[Path] = None
        self.images_cache: Dict[str, ImageTk.PhotoImage] = {}
        self.cartes: Dict[str, CarteSkin] = {}
        self._derniere_largeur_colonnes: int = -1
        self._file_generation_apercus: List[Path] = []
        self._generation_apercus_en_cours: bool = False
        self._redimensionnement_apres_id: Optional[str] = None

        self.title("Gestionnaire de skins VRM — Vue grille")
        self.geometry("1065x700")
        self.minsize(785, 560)
        if recuperer_plein_ecran_demarrage():
            self.state("zoomed")

        self._construire_entete()
        self._construire_onglets()
        self._construire_grille()
        self._construire_bas()

        self.rafraichir()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------
    def _construire_entete(self) -> None:
        entete = tk.Frame(self, bg="#37474f")
        entete.pack(fill="x")

        configuration_verrouillee = recuperer_verrouillage_configuration_main()
        self.btn_vue_liste = tk.Button(
            entete,
            text="☰ Vue liste (verrouillé)" if configuration_verrouillee else "☰ Vue liste",
            command=self.passer_en_vue_liste,
            state="disabled" if configuration_verrouillee else "normal",
            bg="#455a64",
            fg="white",
            activebackground="#546e7a",
            activeforeground="white",
            disabledforeground="#90a4ae",
            relief="flat",
            padx=12,
        )
        self.btn_vue_liste.pack(side="left", padx=12, pady=10)

        tk.Label(
            entete,
            text="COLLECTION DE SKINS",
            bg="#37474f",
            fg="white",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side="left", expand=True)

        self.current_applied_label = tk.Label(
            entete,
            text="Skin appliqué : aucun",
            bg="#37474f",
            fg="#c8e6c9",
        )
        self.current_applied_label.pack(side="right", padx=16, pady=10)

        options_verrouillees = recuperer_verrouillage_options_main()
        self.btn_options = tk.Button(
            entete,
            text="⚙ Options (verrouillé)" if options_verrouillees else "⚙ Options",
            command=self.ouvrir_options,
            state="disabled" if options_verrouillees else "normal",
            bg="#455a64",
            fg="white",
            activebackground="#546e7a",
            activeforeground="white",
            disabledforeground="#90a4ae",
            relief="flat",
            padx=12,
        )
        self.btn_options.pack(side="right", padx=(0, 12), pady=10)

    def _construire_onglets(self) -> None:
        barre = tk.Frame(self)
        barre.pack(fill="x", padx=12, pady=(10, 4))

        self.btn_onglet_tous = tk.Button(
            barre, text="TOUS", relief="flat", command=lambda: self.set_onglet("tous")
        )
        self.btn_onglet_tous.pack(side="left")

        self.btn_onglet_favoris = tk.Button(
            barre, text="FAVORIS", relief="flat", command=lambda: self.set_onglet("favoris")
        )
        self.btn_onglet_favoris.pack(side="left", padx=(6, 0))

        self.recherche_bar = tk.Entry(barre, width=28)
        self.recherche_bar.pack(side="right")
        self.recherche_bar.bind("<Return>", lambda e: self.set_recherche(self.recherche_bar.get().strip()))

        tk.Button(
            barre, text="Rechercher", command=lambda: self.set_recherche(self.recherche_bar.get().strip())
        ).pack(side="right", padx=(0, 6))

        self._actualiser_style_onglets()

    def _construire_grille(self) -> None:
        conteneur = tk.Frame(self, bg="#e0e0e0")
        conteneur.pack(fill="both", expand=True, padx=12, pady=8)

        self.canvas = tk.Canvas(conteneur, bg="#e0e0e0", highlightthickness=0)
        scrollbar = tk.Scrollbar(conteneur, orient="vertical", width=28, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(self.canvas, bg="#e0e0e0")
        self.grid_window = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.grid_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self._on_molette)

    def _construire_bas(self) -> None:
        selection_bar = tk.Frame(self)
        selection_bar.pack(fill="x", padx=12, pady=(0, 4))

        self.label_selection = tk.Label(
            selection_bar, text="Clique sur un skin pour le sélectionner.", anchor="w"
        )
        self.label_selection.pack(side="left")

        self.btn_appliquer = tk.Button(
            selection_bar, text="Appliquer le skin sélectionné", state="disabled", command=self.on_appliquer
        )
        self.btn_appliquer.pack(side="right")

        self.btn_rafraichir = tk.Button(selection_bar, text="Rafraîchir", command=self.rafraichir)
        self.btn_rafraichir.pack(side="right", padx=(0, 8))

        self.status_message = tk.StringVar(value="")
        tk.Label(self, textvariable=self.status_message, anchor="w", fg="#1b5e20").pack(
            fill="x", padx=12, pady=(0, 10)
        )

    # ------------------------------------------------------------------
    # État (recherche / onglet / favoris)
    # ------------------------------------------------------------------
    def get_recherche(self) -> str:
        return self.__recherche

    def set_recherche(self, value: str) -> None:
        self.__recherche = value.lower()
        self.rafraichir()

    def set_onglet(self, onglet: str) -> None:
        self.__onglet = onglet
        self._actualiser_style_onglets()
        self.rafraichir()

    def _actualiser_style_onglets(self) -> None:
        actif = {"bg": "#2e7d32", "fg": "white", "activebackground": "#2e7d32", "activeforeground": "white"}
        inactif = {"bg": "#eeeeee", "fg": "black", "activebackground": "#dddddd", "activeforeground": "black"}
        self.btn_onglet_tous.configure(**(actif if self.__onglet == "tous" else inactif))
        self.btn_onglet_favoris.configure(**(actif if self.__onglet == "favoris" else inactif))

    def is_skin_favori(self, skin_name: str) -> bool:
        return skin_name in self.__favoris

    def toggle_favori(self, skin_name: str) -> None:
        if skin_name in self.__favoris:
            self.__favoris.discard(skin_name)
            self.status_message.set(f"Skin retiré des favoris : {skin_name}")
        else:
            self.__favoris.add(skin_name)
            self.status_message.set(f"Skin ajouté aux favoris : {skin_name}")
        sauvegarder_liste_favoris(list(self.__favoris))
        if self.__onglet == "favoris":
            self.rafraichir()
        else:
            self._actualiser_etoile(skin_name)

    # ------------------------------------------------------------------
    # Navigation entre interfaces
    # ------------------------------------------------------------------
    def passer_en_vue_liste(self) -> None:
        self.next_mode = "liste"
        self.destroy()

    def ouvrir_options(self) -> None:
        FenetreOptions(self, on_close=self.rafraichir)

    # ------------------------------------------------------------------
    # Rendu de la grille
    # ------------------------------------------------------------------
    def _skins_filtres(self) -> List[Path]:
        skins = lister_skins_visibles()
        skins = [s for s in skins if correspondre_recherche(s.name, self.__recherche)]
        if self.__onglet == "favoris":
            skins = [s for s in skins if self.is_skin_favori(s.name)]
        return skins

    def _on_canvas_resize(self, event: tk.Event) -> None:
        self.canvas.itemconfig(self.grid_window, width=event.width)
        colonnes = max(1, event.width // (CARD_WIDTH + GRID_PADDING))
        if colonnes == self._derniere_largeur_colonnes:
            return

        # Glisser un bord de fenêtre déclenche une rafale d'événements <Configure>
        # (plusieurs par seconde). Reconstruire toute la grille à chacun d'eux
        # (destruction/recréation de toutes les cartes) rendait le
        # redimensionnement très saccadé : on attend une accalmie avant de
        # reconstruire, une seule fois par geste de redimensionnement.
        if self._redimensionnement_apres_id is not None:
            self.after_cancel(self._redimensionnement_apres_id)
        self._redimensionnement_apres_id = self.after(
            120, lambda c=colonnes: self._appliquer_redimensionnement(c)
        )

    def _appliquer_redimensionnement(self, colonnes: int) -> None:
        self._redimensionnement_apres_id = None
        self._derniere_largeur_colonnes = colonnes
        self._regriller_cartes(colonnes)

    def _regriller_cartes(self, colonnes: int) -> None:
        """Repositionne les cartes déjà construites sur la nouvelle grille de
        colonnes, sans les détruire/recréer.

        Un redimensionnement ne change ni la recherche ni le contenu affiché,
        donc un rafraichir() complet (destruction/recréation de toutes les
        cartes) est un travail inutilement lourd qui peut encore bloquer assez
        longtemps la boucle d'événements pour perturber le redimensionnement
        interactif de la fenêtre (Windows peut alors la faire revenir à sa
        taille précédente). Un simple repositionnement est quasi instantané.
        """
        skins = self._skins_filtres()
        if not skins or not self.cartes:
            self.rafraichir(conserver_selection=True)
            return

        for index, skin in enumerate(skins):
            carte = self.cartes.get(skin.name)
            if carte is None:
                # Le contenu affiché a changé entre-temps (cas improbable pour
                # un simple redimensionnement) : on retombe sur le rebuild complet.
                self.rafraichir(conserver_selection=True)
                return
            ligne, colonne = divmod(index, colonnes)
            carte.cadre.grid(row=ligne, column=colonne, padx=GRID_PADDING // 2, pady=GRID_PADDING // 2)

        self.canvas.after(1, lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def _on_molette(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def rafraichir(self, conserver_selection: bool = True) -> None:
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.cartes.clear()
        # Le cache de vignettes (self.images_cache) n'est volontairement pas vidé
        # ici : il persiste entre deux reconstructions de la grille (recherche,
        # redimensionnement...) pour éviter de redécoder chaque PNG depuis le
        # disque à chaque fois, ce qui était la principale source de lenteur.

        skins = self._skins_filtres()
        skin_applique = skin_applique_actuel()

        colonnes = max(1, self.canvas.winfo_width() // (CARD_WIDTH + GRID_PADDING))
        self._derniere_largeur_colonnes = colonnes

        if not conserver_selection or (
            self.selected_skin is not None and self.selected_skin.name not in {s.name for s in skins}
        ):
            self.selected_skin = None

        if not skins:
            tk.Label(
                self.grid_frame,
                text="Aucun skin ne correspond à la recherche / à cet onglet.",
                bg="#e0e0e0",
                fg="gray",
                pady=30,
            ).grid(row=0, column=0, sticky="w")
        else:
            for index, skin in enumerate(skins):
                ligne, colonne = divmod(index, colonnes)
                self._creer_carte(skin, ligne, colonne, skin_applique)

        self.mettre_en_evidence_skin_applique(skin_applique)
        self._actualiser_selection_bar()
        self.canvas.after(1, lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def _creer_carte(self, skin: Path, ligne: int, colonne: int, skin_applique: Optional[Path]) -> None:
        cadre = tk.Frame(
            self.grid_frame,
            width=CARD_WIDTH,
            height=CARD_HEIGHT,
            bg=COULEUR_FOND_CARTE,
            highlightthickness=2,
            highlightbackground=COULEUR_BORDURE,
        )
        cadre.grid(row=ligne, column=colonne, padx=GRID_PADDING // 2, pady=GRID_PADDING // 2)
        cadre.grid_propagate(False)

        zone_image = tk.Frame(cadre, bg=COULEUR_FOND_CARTE, height=THUMB_MAX_SIZE[1] + 6)
        zone_image.pack(fill="x", pady=(6, 2))
        zone_image.pack_propagate(False)

        image_label = tk.Label(zone_image, bg=COULEUR_FOND_CARTE)
        image_label.pack(expand=True)
        self._charger_vignette(skin, image_label)

        badge = tk.Label(
            zone_image, text="✓ appliqué", bg=COULEUR_APPLIQUE, fg="white", font=("TkDefaultFont", 8, "bold")
        )
        if skin_applique is not None and skin.name == skin_applique.name:
            badge.place(relx=0.0, rely=0.0, x=2, y=2, anchor="nw")

        etoile = tk.Label(
            zone_image,
            text="★" if self.is_skin_favori(skin.name) else "☆",
            bg=COULEUR_FOND_CARTE,
            fg="#f9a825" if self.is_skin_favori(skin.name) else "#9e9e9e",
            font=("TkDefaultFont", 13, "bold"),
            cursor="hand2",
        )
        etoile.place(relx=1.0, rely=0.0, x=-4, y=2, anchor="ne")
        etoile.bind("<Button-1>", lambda e, n=skin.name: self.toggle_favori(n))

        nom_affiche = skin.name if len(skin.name) <= 20 else skin.name[:17] + "..."
        nom_label = tk.Label(
            cadre, text=nom_affiche, bg=COULEUR_FOND_CARTE, font=("TkDefaultFont", 9), wraplength=CARD_WIDTH - 10
        )
        nom_label.pack(fill="x", padx=6)

        carte = CarteSkin(cadre, image_label, etoile, badge)
        self.cartes[skin.name] = carte

        for widget in (cadre, zone_image, image_label, nom_label):
            widget.bind("<Button-1>", lambda e, s=skin: self.selectionner_skin(s))
            widget.bind("<Double-Button-1>", lambda e, s=skin: self.selectionner_et_appliquer(s))

        if self.selected_skin is not None and self.selected_skin.name == skin.name:
            self._mettre_en_valeur_carte(skin.name, True)

    def _charger_vignette(self, skin: Path, image_label: tk.Label) -> None:
        photo_en_cache = self.images_cache.get(skin.name)
        if photo_en_cache is not None:
            image_label.config(image=photo_en_cache, text="")
            return

        preview_path = APERCU_DIR / skin.with_suffix(".png").name
        if not preview_path.exists():
            # On ne génère surtout pas l'aperçu manquant ici : cette méthode est
            # appelée pendant la construction de la grille, donc génération
            # synchrone = fenêtre invisible/figée tant que tous les aperçus
            # manquants n'ont pas fini de se générer (long au premier lancement).
            # On affiche un espace réservé et on reporte la génération après
            # l'affichage, une vignette à la fois.
            image_label.config(image="", text="Génération...", fg="gray")
            self._mettre_en_file_generation(skin)
            return

        self._afficher_vignette_depuis_fichier(skin, preview_path, image_label)

    def _afficher_vignette_depuis_fichier(self, skin: Path, preview_path: Path, image_label: tk.Label) -> None:
        try:
            with Image.open(preview_path) as source:
                vignette = source.copy()
            vignette.thumbnail(THUMB_MAX_SIZE, Image.LANCZOS)
            photo = ImageTk.PhotoImage(vignette)
            self.images_cache[skin.name] = photo
            image_label.config(image=photo, text="")
        except Exception:
            image_label.config(text="Pas d'aperçu", fg="gray")

    def _mettre_en_file_generation(self, skin: Path) -> None:
        if any(s.name == skin.name for s in self._file_generation_apercus):
            return
        self._file_generation_apercus.append(skin)
        if not self._generation_apercus_en_cours:
            self._generation_apercus_en_cours = True
            self.after(50, self._generer_prochain_apercu)

    def _generer_prochain_apercu(self) -> None:
        if not self.winfo_exists():
            return
        if not self._file_generation_apercus:
            self._generation_apercus_en_cours = False
            return

        skin = self._file_generation_apercus.pop(0)
        preview_path = APERCU_DIR / skin.with_suffix(".png").name
        if not preview_path.exists():
            PREVIEW_GENERATOR.generate_preview(skin.name)

        # La grille a pu être reconstruite (recherche, onglet, redimensionnement)
        # depuis la mise en file : on ne met à jour que si la carte est toujours là.
        carte = self.cartes.get(skin.name)
        if carte is not None and preview_path.exists():
            self._afficher_vignette_depuis_fichier(skin, preview_path, carte.image_label)

        self.after(10, self._generer_prochain_apercu)

    # ------------------------------------------------------------------
    # Sélection / application
    # ------------------------------------------------------------------
    def _mettre_en_valeur_carte(self, skin_name: str, selectionnee: bool) -> None:
        carte = self.cartes.get(skin_name)
        if carte is None:
            return
        if selectionnee:
            carte.cadre.configure(highlightbackground=COULEUR_SELECTION, highlightthickness=3)
        else:
            carte.cadre.configure(highlightbackground=COULEUR_BORDURE, highlightthickness=2)

    def _actualiser_etoile(self, skin_name: str) -> None:
        carte = self.cartes.get(skin_name)
        if carte is None:
            return
        favori = self.is_skin_favori(skin_name)
        carte.etoile.configure(text="★" if favori else "☆", fg="#f9a825" if favori else "#9e9e9e")

    def selectionner_skin(self, skin: Path) -> None:
        ancien = self.selected_skin
        if ancien is not None:
            self._mettre_en_valeur_carte(ancien.name, False)
        self.selected_skin = skin
        self._mettre_en_valeur_carte(skin.name, True)
        self._actualiser_selection_bar()

    def selectionner_et_appliquer(self, skin: Path) -> None:
        self.selectionner_skin(skin)
        self.on_appliquer()

    def _actualiser_selection_bar(self) -> None:
        if self.selected_skin is None:
            self.label_selection.config(text="Clique sur un skin pour le sélectionner.")
            self.btn_appliquer.config(state="disabled")
            return

        taille_ko = self.selected_skin.stat().st_size / 1024
        self.label_selection.config(text=f"Sélectionné : {self.selected_skin.name} ({taille_ko:.1f} Ko)")
        self.btn_appliquer.config(state="normal")

    def mettre_en_evidence_skin_applique(self, skin_applique: Optional[Path]) -> None:
        if skin_applique is None:
            self.current_applied_label.config(text="Skin appliqué : aucun")
        else:
            self.current_applied_label.config(text=f"Skin appliqué : {skin_applique.name}")

    def on_appliquer(self) -> None:
        if self.selected_skin is None:
            messagebox.showwarning("Sélection manquante", "Choisis un skin dans la grille.")
            return

        skin_path = self.selected_skin
        if not skin_path.exists():
            messagebox.showerror("Erreur", "Le fichier sélectionné n'existe plus.")
            self.rafraichir()
            return

        try:
            destination = appliquer_skin(skin_path)
            self.status_message.set(f"Skin appliqué : {skin_path.name} a été copié dans {destination}")
            self.rafraichir()
        except Exception as exc:  # pragma: no cover - interface utilisateur
            messagebox.showerror("Erreur", f"Impossible d'appliquer le skin :\n{exc}")


def main() -> None:
    SKINS_DIR.mkdir(exist_ok=True)
    mode = recuperer_interface_demarrage()
    while mode:
        if mode == "grille":
            app = ApplicationGrille()
        else:
            from configure import Application

            app = Application()
        app.mainloop()
        mode = getattr(app, "next_mode", None)


if __name__ == "__main__":
    main()
