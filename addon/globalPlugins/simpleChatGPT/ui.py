# Chat dialog for the ChatGPT add-on.
# Presents a question field, a response field and a Send button.

import config
import speech
import ui as nvdaUi
import wx

from . import api
from .settings import CONFIG_SECTION


# Punctuation that marks a natural spoken break. When a chunked reply
# contains one of these followed by whitespace, flush the buffered text
# to speech so NVDA reads the response incrementally.
_SENTENCE_ENDERS = (". ", "! ", "? ", ".\n", "!\n", "?\n", "\n")


def _splitAtLastSentence(buf):
	best = -1
	for p in _SENTENCE_ENDERS:
		i = buf.rfind(p)
		if i >= 0:
			end = i + len(p)
			if end > best:
				best = end
	if best > 0:
		return buf[:best], buf[best:]
	return "", buf


class ChatDialog(wx.Dialog):

	def __init__(self, parent):
		# Translators: Title of the ChatGPT chat window.
		super().__init__(parent, title=_("ChatGPT"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self._history = []  # list of {"role","content"}
		self._pending = False
		self._currentUser = ""
		self._replyBuffer = ""
		self._speechBuffer = ""
		self._buildUi()
		self.SetSize((600, 500))
		self.CentreOnScreen()

	def _buildUi(self):
		panel = wx.Panel(self)
		vs = wx.BoxSizer(wx.VERTICAL)
		# Translators: Label for the question input.
		vs.Add(wx.StaticText(panel, label=_("&Your message:")), 0, wx.ALL, 4)
		self.input = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 100))
		vs.Add(self.input, 0, wx.EXPAND | wx.ALL, 4)
		btns = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Send button.
		self.sendBtn = wx.Button(panel, label=_("&Send"))
		# Translators: Clear conversation button.
		self.clearBtn = wx.Button(panel, label=_("C&lear conversation"))
		# Translators: Close button.
		self.closeBtn = wx.Button(panel, wx.ID_CLOSE, _("&Close"))
		btns.Add(self.sendBtn, 0, wx.RIGHT, 4)
		btns.Add(self.clearBtn, 0, wx.RIGHT, 4)
		btns.Add(self.closeBtn, 0)
		vs.Add(btns, 0, wx.ALL, 4)
		# Translators: Label for the response output.
		vs.Add(wx.StaticText(panel, label=_("&Response:")), 0, wx.ALL, 4)
		self.output = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 250))
		vs.Add(self.output, 1, wx.EXPAND | wx.ALL, 4)
		panel.SetSizer(vs)
		outer = wx.BoxSizer(wx.VERTICAL)
		outer.Add(panel, 1, wx.EXPAND)
		self.SetSizer(outer)
		self.sendBtn.Bind(wx.EVT_BUTTON, self.onSend)
		self.clearBtn.Bind(wx.EVT_BUTTON, self.onClear)
		self.closeBtn.Bind(wx.EVT_BUTTON, self.onClose)
		self.input.Bind(wx.EVT_CHAR_HOOK, self._onInputKey)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.SetEscapeId(wx.ID_CLOSE)

	def _onInputKey(self, event):
		# Ctrl+Enter in the message field triggers Send.
		if (
			event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER)
			and event.ControlDown()
		):
			self.onSend(event)
			return
		event.Skip()

	def focusInput(self):
		self.input.SetFocus()

	def onClose(self, event):
		self.Hide()

	def onClear(self, event):
		self._history = []
		self.output.SetValue("")
		nvdaUi.message(_("Conversation cleared"))
		self.input.SetFocus()

	def onSend(self, event):
		if self._pending:
			return
		text = self.input.GetValue().strip()
		if not text:
			return
		cfg = config.conf[CONFIG_SECTION]
		apiKey = cfg["apiKey"]
		model = cfg["model"] or "gpt-4o-mini"
		sysPrompt = cfg["systemPrompt"]
		if not apiKey:
			self._append(_("Error: no API key set. Open NVDA menu > Preferences > Settings > ChatGPT."))
			return
		messages = []
		if sysPrompt.strip():
			messages.append({"role": "system", "content": sysPrompt})
		messages.extend(self._history)
		messages.append({"role": "user", "content": text})
		self._currentUser = text
		self._replyBuffer = ""
		self._speechBuffer = ""
		self._append(_("You: ") + text)
		self._append(_("ChatGPT: "))
		self.input.SetValue("")
		self._pending = True
		self.sendBtn.Disable()
		nvdaUi.message(_("Sending to ChatGPT..."))
		api.streamChatAsync(
			apiKey, model, messages,
			onChunk=lambda c: wx.CallAfter(self._onStreamChunk, c),
			onDone=lambda: wx.CallAfter(self._onStreamDone),
			onError=lambda e: wx.CallAfter(self._onError, e),
		)

	def _onStreamChunk(self, chunk):
		self._replyBuffer += chunk
		self._speechBuffer += chunk
		self.output.AppendText(chunk)
		head, tail = _splitAtLastSentence(self._speechBuffer)
		if head:
			self._speechBuffer = tail
			speech.speakMessage(head)

	def _onStreamDone(self):
		self._pending = False
		self.sendBtn.Enable()
		tail = self._speechBuffer.strip()
		if tail:
			speech.speakMessage(tail)
		self._speechBuffer = ""
		if self._replyBuffer:
			self._history.append({"role": "user", "content": self._currentUser})
			self._history.append({"role": "assistant", "content": self._replyBuffer})
		self._replyBuffer = ""
		self._currentUser = ""
		self.input.SetFocus()

	def _onError(self, errMsg):
		self._pending = False
		self.sendBtn.Enable()
		self._speechBuffer = ""
		self._replyBuffer = ""
		self._currentUser = ""
		self._append(_("Error: ") + errMsg)
		nvdaUi.message(_("ChatGPT error: ") + errMsg)
		self.input.SetFocus()

	def _append(self, line):
		cur = self.output.GetValue()
		if cur:
			cur += "\n\n"
		self.output.SetValue(cur + line)
		self.output.SetInsertionPointEnd()
