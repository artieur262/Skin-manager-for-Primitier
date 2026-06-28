# VRM Skin Manager

This project provides a small graphical interface to choose a skin in `.vrm` format, display a preview and apply it to the character.

## What the program does

- It reads all `.vrm` files present in the `skins/` folder.
- It displays a preview of the selected skin with its name and file size.
- It automatically generates a preview image in `apercus/` if it doesn't exist yet.
- When you apply a skin, the chosen `.vrm` file is copied to the root of the project.
- Before copying, any other `.vrm` files present at the root are deleted.

## What the programs do

- `selection.py` is the main program. It displays the graphical interface, lists available skins, shows the preview of the selected skin and applies the chosen skin.
- `genreator.py` generates the preview images used by the interface. It reads the `.vrm` file and creates an image stored in `apercus/`.
- The two scripts work together: `selection.py` calls `genreator.py` when a preview needs to be created or updated.

## Prerequisites

- Python 3
- The Pillow library

Installing Pillow if needed:

```bash
pip install pillow
```

## Running the application

From the project folder, run:

```bash
python selection.py
```

## Usage

1. Open the application.
2. Click on a skin in the list on the left.
3. Check the preview on the right.
4. Click on "Apply skin" to copy the chosen file to the root of the project.
5. Use "Refresh" if you add or remove files in `skins/` while the application is open.

## Project structure

- `selection.py`: main graphical interface.
- `genreator.py`: generation of skin previews.
- `skins/`: folder containing available `.vrm` files.
- `apercus/`: folder containing generated preview images.

## Notes

- The applied skin is simply the `.vrm` file copied to the root of the project.
- If no `.vrm` file is present in `skins/`, the list remains empty.
