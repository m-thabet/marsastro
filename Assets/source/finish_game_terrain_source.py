import bpy
from pathlib import Path
source=Path(__file__).with_name('build_game_assets.py')
text=source.read_text(encoding='utf-8-sig');ns={'__file__':str(source)}
exec(compile(text[:text.index('# Derive five')],str(source),'exec'),ns)
bpy.ops.wm.open_mainfile(filepath=str(ns['ROOT']/'Assets/source/game-terrain.blend'))
ns['finish_terrain_source']()
