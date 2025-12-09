# Automatic Project Folder Generation in QGIS Plugin

This guide explains how users can generate project folders automatically by using a template folder, what can be defined, and how the process works.
---

## How to Generate a Project Folder Automatically

1. **Initiate Project Creation**
   - Use the Project Setup UI to enter project details (name, type, code, etc.).
   - Click the “Create Project” button.

2. **Define Folder Structure**
    - user can select a folder template from popup window can select the sample folder.
3. **Folder Creation Logic**
   - The plugin checks if the base directory exists; if not, it creates it.
   - It creates all subfolders as defined in the template.
   ---

## What Can Be Defined

- **Base Path**: Where all projects are stored (defined by setting).
- **Naming Rules**: How folders are named (e.g., by project code, name, or date).
- **Custom Fields**: Add custome naming for created folder naming.
  ---

## How Users Define These

- **Plugin Settings UI**: Set base path, customize structure, select template files.
- **Config File**: Advanced users can edit a JSON/YAML file for templates and rules.
- **During Project Creation**: UI may allow adding extra folders or choosing presets.
  ---

## Example Workflow

1. User clicks “Create Project.” on Projects cards action buttons.
2. Plugin reads the folder structure and base path.
3. Plugin creates the main project folder and all subfolders into predefined location.
4. Plugin copies template files from Template folders.
5. Plugin updates project folder_path.

---
