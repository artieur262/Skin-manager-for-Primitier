# VRM Skin Manager

This project provides a small graphical interface to choose a skin in `.vrm` format, display a preview and apply it to the character.

## What the program does

- It reads all `.vrm` files present in the `skins/` folder.
- It displays a preview of the selected skin with its name and file size.
- It automatically generates a preview image in `apercus/` if it doesn't exist yet.
- When you apply a skin, the chosen `.vrm` file is copied to the root of the project.
- Before copying, any other `.vrm` files present at the root are deleted.

## What the programs do

- `skins_core.py` contains the common logic (reading skins, favorites, tags, options, applying a skin) used by both interfaces.
- `configure.py` is the "list" interface: a text list of skins with a detailed configuration panel (preview rotation, tags, forced regeneration).
- `main.py` is the "grid" interface: a visual grid of thumbnails like a game skin-selection menu, with All/Favorites tabs and search, without the advanced settings.
- `genreator.py` generates the preview images used by both interfaces. It reads the `.vrm` file and creates an image stored in `apercus/`.
- `options_menu.py` provides the "Options" window, shared by both interfaces.
- The scripts work together: the interfaces call `genreator.py` whenever a preview needs to be created or updated, and rely on `skins_core.py` for all skin-related operations.
- A button at the top of each interface ("Grid view" / "List view") lets you switch from one to the other at any time, without losing the currently applied skin.
- An "⚙ Options" button, present in both interfaces, opens the options window.

## Prerequisites

- Python 3
- The Pillow library

Installing Pillow if needed:

```bash
pip install pillow
```

## Running the application

From the project folder, run either of the two interfaces (the toggle button lets you switch to the other one afterwards):

```bash
python configure.py  # list + configuration interface
python main.py        # visual grid interface
```

## Usage

### List interface (`configure.py`)

1. Open the application.
2. Click on a skin in the list on the left.
3. Check the preview on the right.
4. Click "Apply skin" to copy the chosen file to the root of the project.
5. Use "Refresh" if you add or remove files in `skins/` while the application is open.

### Grid interface (`main.py`)

1. Open the application.
2. Choose the "ALL" or "FAVORITES" tab, and filter with the search bar if needed.
3. Click a thumbnail to select it (double-click to apply it directly).
4. Click a thumbnail's star to add/remove it from favorites.
5. Click "Apply selected skin" to copy the chosen file to the root of the project.

### Options menu ("⚙ Options")

Accessible from both interfaces:

1. **Interface on `main.py` startup**: choose whether launching `main.py` should open the grid view or the list view by default.
2. **Hiding tags**: check the tags that should hide the skins that carry them (or add a new one via the text field). A skin carrying a hiding tag disappears from the list and the grid, including from tag search — this menu is the only place where you can see/manage which tags are hiding tags and bring the affected skins back.

## Project structure

- `skins_core.py`: common logic (skins, favorites, tags, options, applying a skin) shared by both interfaces.
- `configure.py`: "list" graphical interface.
- `main.py`: "visual grid" graphical interface.
- `options_menu.py`: options window (startup interface, hiding tags).
- `genreator.py`: generation of skin previews.
- `skins/`: folder containing the available `.vrm` files.
- `apercus/`: folder containing the generated preview images.

## Notes

- The applied skin is simply the `.vrm` file copied to the root of the project.
- If no `.vrm` file is present in `skins/`, the list stays empty.
- A skin carrying a tag marked as hiding in the options menu no longer appears in the usual lists/grids.
