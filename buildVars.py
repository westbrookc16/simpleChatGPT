# Build configuration for the simpleChatGPT NVDA add-on.
# This file is the single source of truth for manifest metadata and build inputs.
# It follows the NVDA add-on template convention so the values map 1-to-1 onto
# manifest.ini via manifest.ini.tpl.


addon_info = {
	# Internal add-on name; must be unique in the NVDA Add-on Store.
	"addon_name": "simpleChatGPT",
	# User-visible name shown in the Add-on Store and Manage add-ons dialog.
	"addon_summary": "A simple add on that lets users chat with chat gpt with streaming responses read automatically.",
	# Long description shown in the store.
	"addon_description": (
		"Chat with OpenAI's ChatGPT from within NVDA using your own API key.\n"
		"Features:\n"
		"- Dedicated chat dialog bound to NVDA+Alt+C.\n"
		"- Responses stream in and are spoken sentence by sentence.\n"
		"- Ctrl+Enter sends the current message.\n"
		"- Model picker populated live from your OpenAI account.\n"
		"- System prompt and API key managed via NVDA Settings."
	),
	
	"addon_author": "Chris Westbrook <westbchris@gmail.com>",
	# Semantic version: major.minor.patch (integers), required by the store validator.
	"addon_version": "1.0.1",
	# Short user-facing changelog. Appears in the store.
	"addon_changelog": (
		"1.0.1: Streaming responses, Ctrl+Enter to send, auto-speak, live model list.\n"
		"1.0.0: Initial release."
	),

	"addon_url": "https://github.com/westbrookc16/simpleChatGPT",
	
	"addon_sourceURL": "https://github.com/westbrookc16/simpleChatGPT",
	# Documentation file delivered inside doc/<lang>/ in the archive.
	"addon_docFileName": "readme.html",
	# NVDA version range this add-on is compatible with.
	"addon_minimumNVDAVersion": "2023.1",
	"addon_lastTestedNVDAVersion": "2026.1",
	# Update channel; None means the stable channel.
	"addon_updateChannel": "beta",
	# License metadata (not enforced by the store but included for transparency).
	"addon_license": "GPL v2",
	"addon_licenseURL": "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html",
}

# Python sources inside the add-on. Used by gettext extraction and by build.py
# to confirm the package layout. Glob expressions use forward slashes.
pythonSources = [
	"addon/globalPlugins/simpleChatGPT/*.py",
]

# Source files to scan for translatable strings.
i18nSources = pythonSources + ["buildVars.py"]

# Files that should be excluded from the built .nvda-addon archive.
excludedFiles = []

# Base documentation language (directory under addon/doc/).
baseLanguage = "en"

# Markdown extensions used when converting readme.md to readme.html.
markdownExtensions = []
