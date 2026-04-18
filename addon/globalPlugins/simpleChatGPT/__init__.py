# ChatGPT global plugin for NVDA.
# Registers a settings panel and a script to open the chat dialog.

import config
import globalPluginHandler
import gui
import wx
from scriptHandler import script

from .settings import ChatGPTSettingsPanel, CONFIG_SECTION, CONFIG_SPEC
from .ui import ChatDialog


config.conf.spec[CONFIG_SECTION] = CONFIG_SPEC


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	scriptCategory = _("ChatGPT")

	def __init__(self):
		super().__init__()
		self._dialog = None
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(ChatGPTSettingsPanel)

	def terminate(self):
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(ChatGPTSettingsPanel)
		except ValueError:
			pass
		if self._dialog is not None:
			try:
				self._dialog.Destroy()
			except Exception:
				pass
			self._dialog = None

	@script(
		description=_("Open the ChatGPT chat window"),
		gesture="kb:NVDA+alt+c",
	)
	def script_openChatGPT(self, gesture):
		wx.CallAfter(self._showDialog)

	def _showDialog(self):
		if self._dialog is None:
			self._dialog = ChatDialog(gui.mainFrame)
		if not self._dialog.IsShown():
			self._dialog.Show()
		self._dialog.Raise()
		try:
			self._dialog.focusInput()
		except Exception:
			pass
