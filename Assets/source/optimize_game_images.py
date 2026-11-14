"""Optimize credited globe map and UI portraits, retaining the source images."""
import bpy
from pathlib import Path
root=Path(__file__).resolve().parents[2]
for source,dest,width in [('Assets/world/mars-global-color-4k.jpg','public/assets/mars-color.jpg',2048),('Assets/previews/nova-reference-robot-bust.png','public/assets/nova.png',192),('Assets/previews/explorer-reference-bust.png','public/assets/alex.png',192)]:
    image=bpy.data.images.load(str(root/source),check_existing=False)
    image.scale(width,round(image.size[1]*width/image.size[0]))
    image.filepath_raw=str(root/dest);image.save()
    print(dest,tuple(image.size))
