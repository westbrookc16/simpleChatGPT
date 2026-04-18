# NVDA settings panel for the ChatGPT add-on.

import config
import gui
from gui import guiHelper
from gui.settingsDialogs import SettingsPanel
import wx

from . import api


CONFIG_SECTION = "chatgpt"
CONFIG_SPEC = {
	"apiKey": "string(default='')",
	"model": "string(default='gpt-4o-mini')",
	"systemPrompt": "string(default='')",
}

# Fallback list shown before the user refreshes from the API.
DEFAULT_CHAT_MODELS = [
	"gpt-4o-mini",
	"gpt-4o",
	"gpt-4.1-mini",
	"gpt-4.1",
	"gpt-4-turbo",
	"o1-mini",
	"o3-mini",
]

_REFRESH_LABEL = _("&Refresh models from OpenAI")


class ChatGPTSettingsPanel(SettingsPanel):
	# Translators: Title of the ChatGPT settings panel.
	title = _("ChatGPT")

	def makeSettings(self, settingsSizer):
		helper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		cfg = config.conf[CONFIG_SECTION]
		# Translators: Label for the OpenAI API key field.
		self.apiKeyEdit = helper.addLabeledControl(
			_("OpenAI &API key:"), wx.TextCtrl, style=wx.TE_PASSWORD,
		)
		self.apiKeyEdit.SetValue(cfg["apiKey"])
		savedModel = cfg["model"] or "gpt-4o-mini"
		items = list(DEFAULT_CHAT_MODELS)
		if savedModel and savedModel not in items:
			items.insert(0, savedModel)
		# Translators: Label for the model selection combo box.
		self.modelCombo = helper.addLabeledControl(
			_("&Model:"), wx.ComboBox, choices=items, style=wx.CB_DROPDOWN,
		)
		self.modelCombo.SetValue(savedModel)
		self.refreshBtn = helper.addItem(wx.Button(self, label=_REFRESH_LABEL))
		self.refreshBtn.Bind(wx.EVT_BUTTON, self.onRefreshModels)
		# Translators: Label for the system prompt field.
		self.systemPromptEdit = helper.addLabeledControl(
			_("&System prompt (optional):"), wx.TextCtrl,
			style=wx.TE_MULTILINE, size=(400, 80),
		)
		self.systemPromptEdit.SetValue(cfg["systemPrompt"])

	def onRefreshModels(self, event):
		apiKey = self.apiKeyEdit.GetValue().strip()
		if not apiKey:
			gui.messageBox(
				_("Enter your OpenAI API key first, then click Refresh."),
				_("ChatGPT"), wx.OK | wx.ICON_WARNING, self,
			)
			return
		self.refreshBtn.Disable()
		self.refreshBtn.SetLabel(_("Fetching models..."))
		api.listChatModelsAsync(
			apiKey,
			onSuccess=lambda r: wx.CallAfter(self._onModelsSuccess, r),
			onError=lambda e: wx.CallAfter(self._onModelsError, e),
		)

	def _onModelsSuccess(self, models):
		self.refreshBtn.Enable()
		self.refreshBtn.SetLabel(_REFRESH_LABEL)
		if not models:
			gui.messageBox(
				_("OpenAI returned no chat-capable models for this key."),
				_("ChatGPT"), wx.OK | wx.ICON_WARNING, self,
			)
			return
		current = self.modelCombo.GetValue().strip()
		if current and current not in models:
			models = [current] + models
		self.modelCombo.Set(models)
		self.modelCombo.SetValue(current or models[0])

	def _onModelsError(self, msg):
		self.refreshBtn.Enable()
		self.refreshBtn.SetLabel(_REFRESH_LABEL)
		gui.messageBox(
			_("Failed to fetch models: ") + msg,
			_("ChatGPT"), wx.OK | wx.ICON_ERROR, self,
		)

	def onSave(self):
		cfg = config.conf[CONFIG_SECTION]
		cfg["apiKey"] = self.apiKeyEdit.GetValue().strip()
		cfg["model"] = self.modelCombo.GetValue().strip() or "gpt-4o-mini"
		cfg["systemPrompt"] = self.systemPromptEdit.GetValue()
