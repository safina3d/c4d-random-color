# RandomColor
#### Cinema 4D Python Plugin

![randomcolor](https://4.bp.blogspot.com/-kTlwzVkd8wI/Wd1alCMQ3CI/AAAAAAAAB24/CeAjj5Y7gWgt5GrglCwIaGggVgeh7sdrACKgBGAs/s1600/menu.png "RandomColor")

RandomColor helps you tell objects apart in the viewport and block out scenes fast.
In one click, every object gets its own distinct display color.
Then, if you want, those colors are turned into real materials, ready to render.

Typical uses:
- Read a complex scene or an imported CAD model at a glance
- Quick clay / color previews before texturing
- Turn a colored layout into materials in one step


## Features

The plugin adds 3 commands:

| Command | What it does |
|---|---|
| **Assign random color** | Gives each object a distinct, vivid display color |
| **Disable display color** | Turns display colors off |
| **Convert display color to material** | Creates materials from display colors and assigns them to the objects |

How the commands work:
- **Target objects**: the selected objects and their children. If nothing is selected, the whole scene.
- **Undo**: each command is a single undo step (Ctrl+Z / Cmd+Z).
- **Shared materials**: objects with the same color share one material.
- **Converted colors**: both object colors ("On" mode) and layer colors ("Layer" mode). "Automatic" mode is ignored.


## Installation

1. Download the project: **Code > Download ZIP** on GitHub, then extract it. Or clone it with git.
2. Install the `RandomColor` folder with one of the methods below.
3. Restart Cinema 4D.

#### Method A: plugin folder from the preferences (recommended, Cinema 4D S22 / R23 and later)
No copying or admin rights needed, and it survives Cinema 4D updates.

1. Open **Edit > Preferences** (macOS: **Cinema 4D > Preferences / Settings**).
2. Go to **Plugins**.
3. Click **Add Folder...** and select the extracted `RandomColor` folder (or the folder that contains it).

#### Method B: copy into a plugins folder (all versions, required for R20 / R21)
Copy the `RandomColor` folder into one of these `plugins` folders (create it if it doesn't exist):

- **User preferences folder (recommended):** open **Edit > Preferences** and click **Open Preferences Folder...** at the bottom left. Then copy into its `plugins` folder.
- **Installation folder:** this requires admin rights, and you must repeat it after each update.
    - Windows: `C:\Program Files\Maxon Cinema 4D <version>\plugins\`
    - macOS: `/Applications/Maxon Cinema 4D <version>/plugins/`

#### Check the installation
The commands appear in the **Extensions** menu (**Plugins** menu in R20 / R21).
You can also find them with the **Commander** (Shift+C) by typing "color".


## Usage

1. *(Optional)* Select the objects to color.
2. Run **Assign random color**. Run it again to get new colors.
3. Run **Convert display color to material** to create the materials.

#### Conversion settings
Click the **gear icon** next to **Convert display color to material** to choose the material channels:

- **Active?**: enables the channel in the created material.
- **Apply color?**: puts the object color in this channel.

By default, only the **Color** channel is active and colored.
Settings are saved between sessions.


## Development

Unit tests run outside Cinema 4D (Python 3):

```
python -m unittest discover tests
```


## Changelog
- V1.3:
    - [Feature] Visually distinct colors (golden ratio hue distribution)
    - [Feature] One shared material per color on conversion
    - [Feature] Layer colors are converted to materials
    - [Feature] Material channels settings are saved between sessions
    - [Fix] Undo removes created materials and tags
    - [Fix] Lighter undo memory usage on heavy scenes
    - [Fix] "Apply color" checkbox could stay disabled in settings
    - [Fix] Safer reflection layer handling
    - [Change] Cinema 4D R20 or later required

- V1.2:
    - [Feature] Apply random color to children
    - [Fix] R23 Support added

- V1.1:
    - [Feature] Material channels selection

- V1.0:
    - Plugin version created (based on the random color script)
    - Source code cleaned


## More information
- Please visit: [Safina3D Homepage](https://safina3d.blogspot.com "Visit Safina3D")
