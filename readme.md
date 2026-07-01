# Gestionnaire de skins VRM

Ce projet fournit une petite interface graphique pour choisir un skin au format `.vrm`, afficher un aperçu et l’appliquer au personnage.

## Ce que fait le programme

- Il lit tous les fichiers `.vrm` présents dans le dossier `skins/`.
- Il affiche un aperçu du skin sélectionné avec son nom et la taille du fichier.
- Il génère automatiquement une image d’aperçu dans `apercus/` si elle n’existe pas encore.
- Quand tu appliques un skin, le fichier `.vrm` choisi est copié à la racine du projet.
- Avant la copie, les autres fichiers `.vrm` présents à la racine sont supprimés.

## Ce que font les programmes

- `skins_core.py` contient la logique commune (lecture des skins, favoris, tags, options, application du skin) utilisée par les deux interfaces.
- `configure.py` est l’interface « liste » : une liste texte des skins avec un panneau de configuration détaillé (rotation de l’aperçu, tags, régénération forcée).
- `main.py` est l’interface « grille » : une grille visuelle de vignettes façon menu de sélection de skins, avec onglets Tous/Favoris et recherche, sans les réglages avancés.
- `genreator.py` génère les images d’aperçu utilisées par les deux interfaces. Il lit le fichier `.vrm` et crée une image stockée dans `apercus/`.
- Les trois scripts travaillent ensemble : les interfaces appellent `genreator.py` quand un aperçu doit être créé ou mis à jour, et s’appuient sur `skins_core.py` pour toutes les opérations sur les skins.
- Un bouton en haut de chaque interface (« Vue grille » / « Vue liste ») permet de passer de l’une à l’autre à tout moment, sans perdre le skin actuellement appliqué.

## Prérequis

- Python 3
- La bibliothèque Pillow

Installation de Pillow si besoin :

```bash
pip install pillow
```

## Lancer l’application

Depuis le dossier du projet, exécute l’une des deux interfaces (le bouton de bascule permet de rejoindre l’autre ensuite) :

```bash
python configure.py  # interface liste + configuration
python main.py        # interface grille visuelle
```

## Utilisation

### Interface liste (`configure.py`)

1. Ouvre l’application.
2. Clique sur un skin dans la liste de gauche.
3. Vérifie l’aperçu à droite.
4. Clique sur « Appliquer le skin » pour copier le fichier choisi à la racine du projet.
5. Utilise « Rafraîchir » si tu ajoutes ou supprimes des fichiers dans `skins/` pendant que l’application est ouverte.

### Interface grille (`main.py`)

1. Ouvre l’application.
2. Choisis l’onglet « Tous » ou « Favoris », et filtre avec la barre de recherche si besoin.
3. Clique sur une vignette pour la sélectionner (double-clic pour l’appliquer directement).
4. Clique sur l’étoile d’une vignette pour l’ajouter/retirer des favoris.
5. Clique sur « Appliquer le skin sélectionné » pour copier le fichier choisi à la racine du projet.

## Structure du projet

- `skins_core.py` : logique commune (skins, favoris, tags, options, application du skin) partagée par les deux interfaces.
- `configure.py` : interface graphique « liste ».
- `main.py` : interface graphique « grille visuelle ».
- `genreator.py` : génération des aperçus des skins.
- `skins/` : dossier qui contient les fichiers `.vrm` disponibles.
- `apercus/` : dossier qui contient les images d’aperçu générées.

## Notes

- Le skin appliqué est simplement le fichier `.vrm` copié à la racine du projet.
- Si aucun fichier `.vrm` n’est présent dans `skins/`, la liste reste vide.
