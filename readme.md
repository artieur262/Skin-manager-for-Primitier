# Gestionnaire de skins VRM

Ce projet fournit une petite interface graphique pour choisir un skin au format `.vrm`, afficher un aperçu et l’appliquer au personnage.

## Ce que fait le programme

- Il lit tous les fichiers `.vrm` présents dans le dossier `skins/`.
- Il affiche un aperçu du skin sélectionné avec son nom et la taille du fichier.
- Il génère automatiquement une image d’aperçu dans `apercus/` si elle n’existe pas encore.
- Quand tu appliques un skin, le fichier `.vrm` choisi est copié à la racine du projet.
- Avant la copie, les autres fichiers `.vrm` présents à la racine sont supprimés.

## Ce que font les programmes

- `selection.py` est le programme principal. Il affiche l’interface graphique, liste les skins disponibles, montre l’aperçu du skin sélectionné et applique le skin choisi.
- `genreator.py` génère les images d’aperçu utilisées par l’interface. Il lit le fichier `.vrm` et crée une image stockée dans `apercus/`.
- Les deux scripts travaillent ensemble : `selection.py` appelle `genreator.py` quand un aperçu doit être créé ou mis à jour.

## Prérequis

- Python 3
- La bibliothèque Pillow

Installation de Pillow si besoin :

```bash
pip install pillow
```

## Lancer l’application

Depuis le dossier du projet, exécute :

```bash
python selection.py
```

## Utilisation

1. Ouvre l’application.
2. Clique sur un skin dans la liste de gauche.
3. Vérifie l’aperçu à droite.
4. Clique sur « Appliquer le skin » pour copier le fichier choisi à la racine du projet.
5. Utilise « Rafraîchir » si tu ajoutes ou supprimes des fichiers dans `skins/` pendant que l’application est ouverte.

## Structure du projet

- `selection.py` : interface graphique principale.
- `genreator.py` : génération des aperçus des skins.
- `skins/` : dossier qui contient les fichiers `.vrm` disponibles.
- `apercus/` : dossier qui contient les images d’aperçu générées.

## Notes

- Le skin appliqué est simplement le fichier `.vrm` copié à la racine du projet.
- Si aucun fichier `.vrm` n’est présent dans `skins/`, la liste reste vide.
