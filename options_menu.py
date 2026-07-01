"""
Fenêtre des options, commune aux deux interfaces (configure.py et main.py).

Organisée en onglets pour rester compacte :
- Général : interface affichée au démarrage de main.py, verrouillage de main.py.
- Tags : préréglages de tags (ajout rapide) et tags masquants (cachent les
  skins qui les portent, uniquement gérable ici).
- Entretien : actions ponctuelles (renommage des avatars VRoid Hub).
"""
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict

from skins_core import (
    lister_tous_les_tags,
    recuperer_interface_demarrage,
    recuperer_plein_ecran_demarrage,
    recuperer_tags_masques,
    recuperer_tags_presets,
    recuperer_verrouillage_configuration_main,
    recuperer_verrouillage_options_main,
    renommer_avatars_vroid_hub,
    sauvegarder_interface_demarrage,
    sauvegarder_plein_ecran_demarrage,
    sauvegarder_tags_masques,
    sauvegarder_tags_presets,
    sauvegarder_verrouillage_configuration_main,
    sauvegarder_verrouillage_options_main,
)


class FenetreOptions(tk.Toplevel):
    def __init__(self, parent: tk.Tk, on_close=None) -> None:
        super().__init__(parent)
        self.title("設定")
        self.geometry("440x480")
        self.minsize(400, 420)
        self.transient(parent)
        self.grab_set()

        self._on_close = on_close
        self.variables_tags: Dict[str, tk.BooleanVar] = {}

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        onglet_general = tk.Frame(notebook)
        onglet_tags = tk.Frame(notebook)
        onglet_entretien = tk.Frame(notebook)
        notebook.add(onglet_general, text="一般")
        notebook.add(onglet_tags, text="タグ")
        notebook.add(onglet_entretien, text="メンテナンス")

        self._construire_interface_demarrage(onglet_general)
        self._construire_verrouillage_main(onglet_general)
        self._construire_tags_presets(onglet_tags)
        self._construire_tags_masquants(onglet_tags)
        self._construire_entretien(onglet_entretien)
        self._construire_bas()

        self.protocol("WM_DELETE_WINDOW", self._fermer)

    # ------------------------------------------------------------------
    def _construire_interface_demarrage(self, parent: tk.Widget) -> None:
        cadre = tk.LabelFrame(parent, text="main.py起動時のインターフェース", padx=10, pady=10)
        cadre.pack(fill="x", padx=10, pady=(10, 6))

        self.interface_var = tk.StringVar(value=recuperer_interface_demarrage())
        tk.Radiobutton(
            cadre,
            text="グリッド表示（ビジュアル）",
            variable=self.interface_var,
            value="grille",
            command=self._changer_interface_demarrage,
        ).pack(anchor="w")
        tk.Radiobutton(
            cadre,
            text="リスト表示（設定）",
            variable=self.interface_var,
            value="liste",
            command=self._changer_interface_demarrage,
        ).pack(anchor="w")

        self.plein_ecran_var = tk.BooleanVar(value=recuperer_plein_ecran_demarrage())
        tk.Checkbutton(
            cadre,
            text="フルスクリーンで起動する（ウィンドウを最大化）",
            variable=self.plein_ecran_var,
            command=lambda: sauvegarder_plein_ecran_demarrage(self.plein_ecran_var.get()),
        ).pack(anchor="w", pady=(6, 0))

    def _changer_interface_demarrage(self) -> None:
        sauvegarder_interface_demarrage(self.interface_var.get())

    # ------------------------------------------------------------------
    def _construire_verrouillage_main(self, parent: tk.Widget) -> None:
        cadre = tk.LabelFrame(parent, text="main.pyからのロック", padx=10, pady=10)
        cadre.pack(fill="x", padx=10, pady=6)

        tk.Label(
            cadre,
            text="一度ロックすると、configure.pyからのみ解除できます。",
            justify="left",
            fg="gray",
            wraplength=360,
        ).pack(anchor="w", pady=(0, 6))

        self.verrouiller_options_var = tk.BooleanVar(value=recuperer_verrouillage_options_main())
        tk.Checkbutton(
            cadre,
            text="設定メニューへのアクセスをロック",
            variable=self.verrouiller_options_var,
            command=lambda: sauvegarder_verrouillage_options_main(self.verrouiller_options_var.get()),
        ).pack(anchor="w")

        self.verrouiller_configuration_var = tk.BooleanVar(
            value=recuperer_verrouillage_configuration_main()
        )
        tk.Checkbutton(
            cadre,
            text="設定（リスト表示）へのアクセスをロック",
            variable=self.verrouiller_configuration_var,
            command=lambda: sauvegarder_verrouillage_configuration_main(
                self.verrouiller_configuration_var.get()
            ),
        ).pack(anchor="w")

    # ------------------------------------------------------------------
    def _construire_tags_presets(self, parent: tk.Widget) -> None:
        cadre = tk.LabelFrame(parent, text="タグのプリセット（クイック追加）", padx=10, pady=10)
        cadre.pack(fill="x", padx=10, pady=(10, 6))

        self.presets_liste_frame = tk.Frame(cadre)
        self.presets_liste_frame.pack(fill="x")

        self._rendre_liste_presets()

        ajout_frame = tk.Frame(cadre)
        ajout_frame.pack(fill="x", pady=(8, 0))
        self.nouveau_preset_entry = tk.Entry(ajout_frame)
        self.nouveau_preset_entry.pack(side="left", fill="x", expand=True)
        self.nouveau_preset_entry.bind("<Return>", lambda e: self._ajouter_preset())
        tk.Button(
            ajout_frame, text="追加", command=self._ajouter_preset
        ).pack(side="left", padx=(6, 0))

    def _rendre_liste_presets(self) -> None:
        for widget in self.presets_liste_frame.winfo_children():
            widget.destroy()

        presets = recuperer_tags_presets()
        if not presets:
            tk.Label(
                self.presets_liste_frame, text="プリセットはまだありません。", fg="gray"
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
    def _construire_tags_masquants(self, parent: tk.Widget) -> None:
        cadre = tk.LabelFrame(parent, text="非表示タグ", padx=10, pady=10)
        cadre.pack(fill="both", expand=True, padx=10, pady=6)

        tk.Label(
            cadre,
            text="タグにチェックを入れると、そのタグを持つスキンをどこでも非表示にします。",
            justify="left",
            fg="gray",
            wraplength=360,
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
            ajout_frame, text="非表示タグとして追加", command=self._ajouter_tag_masquant
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
            tk.Label(self.liste_frame, text="まだタグが作成されていません。", fg="gray").pack(anchor="w")
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
    def _construire_entretien(self, parent: tk.Widget) -> None:
        cadre = tk.LabelFrame(parent, text="VRoid Hub", padx=10, pady=10)
        cadre.pack(fill="x", padx=10, pady=(10, 6))

        tk.Label(
            cadre,
            text=(
                "hub.vroid.comの識別子で名前が付けられたままのスキン"
                "（例：6795810513740058493.vrm）を、.vrmファイルの"
                "メタデータに含まれるタイトルを使って名前変更します。"
            ),
            justify="left",
            fg="gray",
            wraplength=360,
        ).pack(anchor="w", pady=(0, 6))

        tk.Button(
            cadre,
            text="VRoid Hubのアバター名を変更",
            command=self._renommer_avatars_vroid_hub,
        ).pack(anchor="w")

    def _renommer_avatars_vroid_hub(self) -> None:
        resultat = renommer_avatars_vroid_hub()

        lignes = [f"名前を変更したアバター：{len(resultat['renommes'])}件。"]
        if resultat["ignores"]:
            lignes.append(f"スキップ：{len(resultat['ignores'])}件（メタデータにタイトルなし）。")
        if resultat["erreurs"]:
            lignes.append(f"エラー：{len(resultat['erreurs'])}件。")

        if resultat["renommes"]:
            lignes.append("")
            lignes.extend(f"{ancien} → {nouveau}" for ancien, nouveau in resultat["renommes"][:15])
            if len(resultat["renommes"]) > 15:
                lignes.append("...")

        messagebox.showinfo("VRoid Hubの名前変更", "\n".join(lignes), parent=self)

    # ------------------------------------------------------------------
    def _construire_bas(self) -> None:
        tk.Button(self, text="閉じる", command=self._fermer).pack(pady=(0, 10))

    def _fermer(self) -> None:
        self.grab_release()
        self.destroy()
        if self._on_close:
            self._on_close()
