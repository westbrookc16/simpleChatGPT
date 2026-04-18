# Build a .nvda-addon archive from this directory.
# Layout:
#   buildVars.py         configuration (addon_info dict, source globs, baseLanguage)
#   manifest.ini.tpl     str.format template rendered with addon_info
#   readme.md            source of truth for the help document
#   addon/               tree copied to the root of the archive
# Output:
#   dist/<addon_name>-<addon_version>.nvda-addon
# The archive contains:
#   manifest.ini
#   doc/<baseLanguage>/<addon_docFileName>
#   <everything under addon/>

import os
import sys
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ADDON_DIR = HERE / "addon"
DIST_DIR = HERE / "dist"
MANIFEST_TPL = HERE / "manifest.ini.tpl"
README_MD = HERE / "readme.md"

sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import buildVars  # noqa: E402


def _renderManifest():
	tpl = MANIFEST_TPL.read_text(encoding="utf-8")
	# None is rendered as an empty string; NVDA treats missing values as unset.
	info = {k: ("" if v is None else v) for k, v in buildVars.addon_info.items()}
	return tpl.format(**info)


def _mdToHtml(mdText, title):
	try:
		import markdown as _md
		body = _md.markdown(mdText, extensions=getattr(buildVars, "markdownExtensions", []))
	except ImportError:
		escaped = mdText.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
		body = "<pre>" + escaped + "</pre>"
	safeTitle = (
		title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
	)
	return (
		"<!DOCTYPE html>\n"
		"<html lang=\"en\"><head>"
		"<meta charset=\"utf-8\">"
		f"<title>{safeTitle}</title>"
		"</head><body>\n"
		f"{body}\n"
		"</body></html>\n"
	)


def _collectAddonFiles():
	items = []
	for root, dirs, files in os.walk(ADDON_DIR):
		dirs[:] = [d for d in dirs if d != "__pycache__"]
		for fn in files:
			if fn.endswith((".pyc", ".pyo")):
				continue
			full = Path(root) / fn
			rel = full.relative_to(ADDON_DIR).as_posix()
			items.append((full, rel))
	return items


def main():
	if not ADDON_DIR.is_dir():
		raise SystemExit(f"addon/ directory not found at {ADDON_DIR}")
	if not MANIFEST_TPL.is_file():
		raise SystemExit(f"manifest.ini.tpl not found at {MANIFEST_TPL}")
	info = buildVars.addon_info
	name = info["addon_name"]
	version = info["addon_version"]
	DIST_DIR.mkdir(exist_ok=True)
	outPath = DIST_DIR / f"{name}-{version}.nvda-addon"
	if outPath.exists():
		outPath.unlink()
	manifestText = _renderManifest()
	readmeHtml = None
	if README_MD.is_file():
		readmeHtml = _mdToHtml(README_MD.read_text(encoding="utf-8"), info["addon_summary"])
	written = 0
	with zipfile.ZipFile(outPath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
		zf.writestr("manifest.ini", manifestText)
		written += 1
		if readmeHtml is not None:
			docPath = f"doc/{buildVars.baseLanguage}/{info['addon_docFileName']}"
			zf.writestr(docPath, readmeHtml)
			written += 1
		for full, rel in _collectAddonFiles():
			zf.write(full, arcname=rel)
			written += 1
	print(f"Wrote {outPath} ({written} files)")


if __name__ == "__main__":
	sys.exit(main() or 0)
