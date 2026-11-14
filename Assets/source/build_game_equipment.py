import bpy,json
from pathlib import Path
source=Path(__file__).with_name('build_game_assets.py')
text=source.read_text(encoding='utf-8-sig');ns={'__file__':str(source)}
exec(compile(text[:text.index('# Derive five')],str(source),'exec'),ns)
exec(text[text.index('white=material'):text.index("box('Shielded")],ns)
exec(compile(text[text.index('# Battery cabinets'):text.index('# Save an editable assembly catalogue')],str(source),'exec'),ns)
report=ns['OUT']/'asset-report.json';rows=json.loads(report.read_text())
new={r['asset'] for r in ns['reports']};report.write_text(json.dumps([r for r in rows if r['asset'] not in new]+ns['reports'],indent=2))
exec(compile(text[text.index('# Save an editable assembly catalogue'):text.index("(OUT/'asset-report.json')")],str(source),'exec'),ns)
