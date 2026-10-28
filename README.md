# RandomColor
#### Cinema 4D Python Plugin
#### Version 1.3
#### Compatibility: Cinema 4D R20+

![randomcolor](https://4.bp.blogspot.com/-kTlwzVkd8wI/Wd1alCMQ3CI/AAAAAAAAB24/CeAjj5Y7gWgt5GrglCwIaGggVgeh7sdrACKgBGAs/s1600/menu.png "RandomColor")

- Assign random color to all or selected objects
- Convert display colors to materials


#### Installation: 

Clone the project or download the zip file and extract it into the Maxon plugins directory.

- Windows: `C:\Program Files\MAXON\CINEMA 4D R<version>\plugins\`
- MacOS: `/Applications/MAXON/CINEMA 4D R<version>/plugins/`


#### Tests:

Run outside Cinema 4D (Python 3): `python -m unittest discover tests`


#### Changelog:
- V1.3:
    - [Feature] Visually distinct colors (golden ratio hue distribution)
    - [Feature] One shared material per color on conversion
    - [Feature] Layer colors are converted to materials
    - [Feature] Material channels settings are saved between sessions
    - [Fix] Undo removes created materials and tags
    - [Fix] Lighter undo memory usage on heavy scenes
    - [Fix] "Apply color" checkbox could stay disabled in settings
    - [Fix] Safer reflection layer handling


- V1.2:
    - [Feature] Apply random color to children
    - [Fix] R23 Support added

- V1.1:
	- [Feature] Material channels selection

- V1.0:
    - Plugin version created (based on the random color script)
    - Source code cleaned


#### More informations:
- Please visit : [Safina3D Homepage](https://safina3d.blogspot.com "Visit Safina3D")
