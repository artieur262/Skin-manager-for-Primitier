"""
Fenêtre des options, commune aux deux interfaces (configure.py et main.py).

Elle permet :
- de choisir l'interface affichée au démarrage de main.py (vue grille ou liste) ;
- de gérer des préréglages de tags, pour les ajouter rapidement à un skin
  depuis la vue liste (bouton d'ajout rapide par préréglage) ;
- de choisir quels tags masquent les skins qui les portent. Un skin portant
  un tag masquant disparaît des listes/grilles habituelles ; c'est ici, et
  uniquement ici, que l'on peut savoir quels tags sont masquants et changer
  ça.
"""
import tkinter as tk
from typing import Dict

from skins_core import (
    lister_tous_les_tags,
    recuperer_interface_demarrage,
    recuperer_tags_masques,
    recuperer_tags_presets,
    sauvegarder_interface_demarrage,
    sauvegarder_tags_masques,
    sauvegarder_tags_presets,
)


class FenetreOptions(tk.Toplevel):
    def __init__(self, parent: tk.Tk, on_close=None) -> None:
        super().__init__(parent)
        self.title("Options")
        self.geometry("420x680")
        self.minsize(360, 520)
        self.transient(parent)
        self.grab_set()

        self._on_close = on_close
        self.variables_tags: Dict[str, tk.BooleanVar] = {}

        self._construire_interface_demarrage()
        self._construire_tags_presets()
        self._construire_tags_masquants()
        self._construire_bas()

        self.protocol("WM_DELETE_WINDOW", self._fermer)

    # ------------------------------------------------------------------
    def _construire_interface_demarrage(self) -> None:
        cadre = tk.LabelFrame(self, text="Interface au démarrage de main.py", padx=10, pady=10)
        cadre.pack(fill="x", padx=12, pady=(12, 6))

        self.interface_var = tk.StringVar(value=recuperer_interface_demarrage())
        tk.Radiobutton(
            cadre,
            text="Vue grille (visuelle)",
            variable=self.interface_var,
            value="grille",
            command=self._changer_interface_demarrage,
        ).pack(anchor="w")
        tk.Radiobutton(
            cadre,
            text="Vue liste (configuration)",
            variable=self.interface_var,
            value="liste",
            command=self._changer_interface_demarrage,
        ).pack(anchor="w")

    def _changer_interface_demarrage(self) -> None:
        sauvegarder_interface_demarrage(self.interface_var.get())

    # ------------------------------------------------------------------
    def _construire_tags_presets(self) -> None:
        cadre = tk.LabelFrame(
            self, text="Préréglages de tags (ajout rapide dans la vue liste)", padx=10, pady=10
        )
        cadre.pack(fill="x", padx=12, pady=6)

        self.presets_liste_frame = tk.Frame(cadre)
        self.presets_liste_frame.pack(fill="x")

        self._rendre_liste_presets()

        ajout_frame = tk.Frame(cadre)
        ajout_frame.pack(fill="x", pady=(8, 0))
        self.nouveau_preset_entry = tk.Entry(ajout_frame)
        self.nouveau_preset_entry.pack(side="left", fill="x", expand=True)
        self.nouveau_preset_entry.bind("<Return>", lambda e: self._ajouter_preset())
        tk.Button(
            ajout_frame, text="Ajouter un préréglage", command=self._ajouter_preset
        ).pack(side="left", padx=(6, 0))

    def _rendre_liste_presets(self) -> None:
        for widget in self.presets_liste_frame.winfo_children():
            widget.destroy()

        presets = recuperer_tags_presets()
        if not presets:
            tk.Label(
                self.presets_liste_frame, text="Aucun préréglage pour l'instant.", fg="gray"
            ).pack(anchor="w")
            return

        for preset in presets:
            ligne = tk.Frame(self.presets_liste_frame)
            ligne.pack(fill="x", anchor="w")
            tk.Label(ligne, text=preset, anchor="w").pack(side="left", fill="x", expand=True)
            tk.Button(
                ligne, text="✕", padx=4, command=lambda p=preset: self._supprimer_preset(p)
            ).pack(side="right")

    def _ajouter_preset(self) -> None:
        tag = self.nouveau_preset_entry.get().strip().lower()
        self.nouveau_preset_entry.delete(0, tk.END)
        if not tag:
            return
        presets = recuperer_tags_presets()
        if tag not in presets:
            presets.append(tag)
            sauvegarder_tags_presets(presets)
            self._rendre_liste_presets()
            self._rendre_liste_tags()

    def _supprimer_preset(self, tag: str) -> None:
        presets = [p for p in recuperer_tags_presets() if p != tag]
        sauvegarder_tags_presets(presets)
        self._rendre_liste_presets()
        self._rendre_liste_tags()

    # ------------------------------------------------------------------
    def _construire_tags_masquants(self) -> None:
        cadre = tk.LabelFrame(
            self, text="Tags masquants (cachent les skins qui les portent)", padx=10, pady=10
        )
        cadre.pack(fill="both", expand=True, padx=12, pady=6)

        tk.Label(
            cadre,
            text="Coche un tag pour masquer partout les skins qui le portent.",
            justify="left",
            fg="gray",
            wraplength=320,
        ).pack(anchor="w", pady=(0, 8))

        zone = tk.Frame(cadre)
        zone.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(zone, highlightthickness=0)
        scrollbar = tk.Scrollbar(zone, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.liste_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.liste_frame, anchor="nw")
        self.liste_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self._rendre_liste_tags()

        ajout_frame = tk.Frame(cadre)
        ajout_frame.pack(fill="x", pady=(8, 0))
        self.nouveau_tag_entry = tk.Entry(ajout_frame)
        self.nouveau_tag_entry.pack(side="left", fill="x", expand=True)
        self.nouveau_tag_entry.bind("<Return>", lambda e: self._ajouter_tag_masquant())
        tk.Button(
            ajout_frame, text="Ajouter comme masquant", command=self._ajouter_tag_masquant
        ).pack(side="left", padx=(6, 0))

    def _rendre_liste_tags(self) -> None:
        for widget in self.liste_frame.winfo_children():
            widget.destroy()
        self.variables_tags.clear()

        tags_masques = set(recuperer_tags_masques())
        tous_les_tags = sorted(
            set(lister_tous_les_tags()) | tags_masques | set(recuperer_tags_presets())
        )

        if not tous_les_tags:
            tk.Label(self.liste_frame, text="Aucun tag n'a encore été créé.", fg="gray").pack(anchor="w")
            return

        for tag in tous_les_tags:
            var = tk.BooleanVar(value=tag in tags_masques)
            self.variables_tags[tag] = var
            tk.Checkbutton(
                self.liste_frame,
                text=tag,
                variable=var,
                command=lambda t=tag: self._basculer_tag_masquant(t),
            ).pack(anchor="w")

    def _basculer_tag_masquant(self, tag: str) -> None:
        tags_masques = set(recuperer_tags_masques())
        if self.variables_tags[tag].get():
            tags_masques.add(tag)
        else:
            tags_masques.discard(tag)
        sauvegarder_tags_masques(sorted(tags_masques))

    def _ajouter_tag_masquant(self) -> None:
        tag = self.nouveau_tag_entry.get().strip().lower()
        self.nouveau_tag_entry.delete(0, tk.END)
        if not tag:
            return
        tags_masques = set(recuperer_tags_masques())
        tags_masques.add(tag)
        sauvegarder_tags_masques(sorted(tags_masques))
        self._rendre_liste_tags()

    # ------------------------------------------------------------------
    def _construire_bas(self) -> None:
        tk.Button(self, text="Fermer", command=self._fermer).pack(pady=(0, 12))

    def _fermer(self) -> None:
        self.grab_release()
        self.destroy()
        if self._on_close:
            self._on_close()
