import bpy,json
from pathlib import Path
source=Path(__file__).with_name('build_game_assets.py')
text=source.read_text()
ns={'__file__':str(source)}
exec(compile(text[:text.index('# Derive five')],str(source),'exec'),ns)
palette=text[text.index('white=material'):text.index("box('Shielded")]
exec(palette,ns)
start=text.index('# Editable full-body')
end=text.index("export('commander',merge=False)",start)+len("export('commander',merge=False)")
exec(compile(text[start:end],str(source),'exec'),ns)
report=ns['OUT']/'asset-report.json'
rows=json.loads(report.read_text())
rows=[r for r in rows if r['asset']!='commander']+ns['reports']
report.write_text(json.dumps(rows,indent=2))
exec(compile(text[text.index('# Save an editable assembly catalogue'):text.index("(OUT/'asset-report.json')")],str(source),'exec'),ns)
