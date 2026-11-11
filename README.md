# First 30 JK — modèle 3D

Voilier de course-croisière type **Bénéteau First 30 JK** (plan Juan Kouyoumdjian),
généré de façon paramétrique en Python (aucune dépendance externe hors numpy/matplotlib
pour la génération et les rendus).

## Caractéristiques du modèle

| Paramètre | Valeur |
|---|---|
| Longueur hors tout (coque) | 9,81 m |
| Longueur avec bout-dehors | ~11,1 m |
| Bau | 3,20 m |
| Tirant d'eau (bulbe) | 1,90 m |
| Hauteur de mât au-dessus du pont | 13,0 m |
| Déplacement visé | ~3,75 t |

## Contenu

- Coque à bouchain arrière, étrave droite (plumb bow), livet de couleur
- Pont avec cockpit ouvert, bancs, roof avec hublots, trappe de pont avant
- Quille à bulbe, **double saumon** (2 safrans)
- Gréement sloop fractionnaire : mât, bôme, bout-dehors, haubans, étai, pataras
- Grand-voile (avec chute rondie) et génois sur étai, avec creux
- Bastingages, chandeliers, filières, pulpits, 2 roues de barre

## Fichiers

- `First30_JK.obj` + `First30_JK.mtl` — modèle 3D avec matériaux (18 groupes nommés)
- `First30_JK.stl` — version maillée pour impression 3D / CAO
- `make_first30.py` — générateur (modifiez les cotes en haut du fichier et relancez)
- `viewer.py` — rendu rapide : `python3 viewer.py First30_JK.obj sortie.png`
- `viewer.html` — visionneuse interactive (ouvrir dans un navigateur, nécessite internet pour Three.js)
- `preview_*.png` — rendus de contrôle générés automatiquement

## Ouvrir le modèle

- **Blender / MeshLab / FreeCAD / Windows 3D Viewer** : ouvrir `First30_JK.obj`
- **Impression 3D** : utiliser `First30_JK.stl`
- **Navigateur** : ouvrir `viewer.html` dans le même dossier que le `.obj`/`.mtl`

## Régénérer / modifier

```bash
python3 make_first30.py
```

Les cotes principales (LOA, bau, tirant d'eau, hauteur de mât) sont des constantes
en tête du script ; les profils de coque (largeur, livet, quille) sont des listes
de points de contrôle interpolées en Catmull-Rom.
