# Minimal OpenAI Chat Completions client using urllib.
# Runs requests on a background thread so NVDA's UI is not blocked.

import json
import ssl
import threading
import urllib.error
import urllib.request


CHAT_URL = "https://api.openai.com/v1/chat/completions"
MODELS_URL = "https://api.openai.com/v1/models"
DEFAULT_TIMEOUT = 60

# Heuristic filter applied to /v1/models output to keep only chat-capable ids.
_CHAT_PREFIXES = ("gpt-", "chatgpt-", "o1", "o3", "o4")
_CHAT_EXCLUDE = ("audio", "realtime", "transcribe", "tts", "search", "image")


class OpenAIError(Exception):
	pass


def _doRequest(req, timeout):
	ctx = ssl.create_default_context()
	try:
		with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
			return resp.read()
	except urllib.error.HTTPError as e:
		body = b""
		try:
			body = e.read()
		except Exception:
			pass
		detail = body.decode("utf-8", errors="replace").strip()
		if detail:
			raise OpenAIError("HTTP %s: %s" % (e.code, detail))
		raise OpenAIError("HTTP %s: %s" % (e.code, e.reason))
	except urllib.error.URLError as e:
		raise OpenAIError("Network error: %s" % e.reason)
	except Exception as e:
		raise OpenAIError(str(e))


def _decodeJson(raw):
	try:
		data = json.loads(raw.decode("utf-8"))
	except Exception as e:
		raise OpenAIError("Invalid JSON from OpenAI: %s" % e)
	if isinstance(data, dict) and "error" in data:
		err = data["error"]
		msg = err.get("message") if isinstance(err, dict) else None
		raise OpenAIError(msg or str(err))
	return data


def sendChat(apiKey, model, messages, timeout=DEFAULT_TIMEOUT):
	"""Synchronous call. Raises OpenAIError on failure."""
	if not apiKey:
		raise OpenAIError("No OpenAI API key configured. Set one in NVDA Settings > ChatGPT.")
	payload = json.dumps({"model": model, "messages": messages}).encode("utf-8")
	req = urllib.request.Request(CHAT_URL, data=payload, method="POST")
	req.add_header("Content-Type", "application/json")
	req.add_header("Authorization", "Bearer " + apiKey)
	data = _decodeJson(_doRequest(req, timeout))
	try:
		return data["choices"][0]["message"]["content"]
	except (KeyError, IndexError, TypeError):
		raise OpenAIError("Unexpected response shape from OpenAI")


def listModels(apiKey, timeout=DEFAULT_TIMEOUT):
	"""Return all model ids visible to the given API key, sorted."""
	if not apiKey:
		raise OpenAIError("No OpenAI API key configured.")
	req = urllib.request.Request(MODELS_URL, method="GET")
	req.add_header("Authorization", "Bearer " + apiKey)
	data = _decodeJson(_doRequest(req, timeout))
	items = data.get("data", []) if isinstance(data, dict) else []
	ids = [m["id"] for m in items if isinstance(m, dict) and "id" in m]
	return sorted(ids)


def listChatModels(apiKey, timeout=DEFAULT_TIMEOUT):
	"""Return only the chat-capable model ids, using a name-based heuristic."""
	out = []
	for mid in listModels(apiKey, timeout):
		if not mid.startswith(_CHAT_PREFIXES):
			continue
		low = mid.lower()
		if any(s in low for s in _CHAT_EXCLUDE):
			continue
		out.append(mid)
	return out


def _openStream(apiKey, model, messages, timeout):
	payload = json.dumps({
		"model": model,
		"messages": messages,
		"stream": True,
	}).encode("utf-8")
	req = urllib.request.Request(CHAT_URL, data=payload, method="POST")
	req.add_header("Content-Type", "application/json")
	req.add_header("Authorization", "Bearer " + apiKey)
	req.add_header("Accept", "text/event-stream")
	ctx = ssl.create_default_context()
	try:
		return urllib.request.urlopen(req, timeout=timeout, context=ctx)
	except urllib.error.HTTPError as e:
		body = b""
		try:
			body = e.read()
		except Exception:
			pass
		detail = body.decode("utf-8", errors="replace").strip()
		if detail:
			raise OpenAIError("HTTP %s: %s" % (e.code, detail))
		raise OpenAIError("HTTP %s: %s" % (e.code, e.reason))
	except urllib.error.URLError as e:
		raise OpenAIError("Network error: %s" % e.reason)
	except Exception as e:
		raise OpenAIError(str(e))


def streamChat(apiKey, model, messages, timeout=DEFAULT_TIMEOUT):
	"""Generator yielding content chunks as they arrive. Raises OpenAIError."""
	if not apiKey:
		raise OpenAIError("No OpenAI API key configured. Set one in NVDA Settings > ChatGPT.")
	resp = _openStream(apiKey, model, messages, timeout)
	try:
		for rawLine in resp:
			line = rawLine.decode("utf-8", errors="replace").rstrip("\r\n")
			if not line or line.startswith(":"):
				continue
			if not line.startswith("data:"):
				continue
			data = line[5:].strip()
			if data == "[DONE]":
				return
			try:
				obj = json.loads(data)
			except Exception:
				continue
			if isinstance(obj, dict) and "error" in obj:
				err = obj["error"]
				msg = err.get("message") if isinstance(err, dict) else None
				raise OpenAIError(msg or str(err))
			try:
				delta = obj["choices"][0].get("delta") or {}
			except (KeyError, IndexError, TypeError):
				continue
			text = delta.get("content") if isinstance(delta, dict) else None
			if text:
				yield text
	finally:
		try:
			resp.close()
		except Exception:
			pass


def streamChatAsync(apiKey, model, messages, onChunk, onDone, onError, timeout=DEFAULT_TIMEOUT):
	"""Run streamChat on a background thread. Callbacks fire on that thread."""
	def _target():
		try:
			for chunk in streamChat(apiKey, model, messages, timeout=timeout):
				onChunk(chunk)
		except OpenAIError as e:
			onError(str(e))
		except Exception as e:
			onError(str(e))
		else:
			onDone()
	t = threading.Thread(target=_target, name="ChatGPTStream", daemon=True)
	t.start()
	return t


def _runAsync(threadName, work, onSuccess, onError):
	def _target():
		try:
			result = work()
		except OpenAIError as e:
			onError(str(e))
		except Exception as e:
			onError(str(e))
		else:
			onSuccess(result)
	t = threading.Thread(target=_target, name=threadName, daemon=True)
	t.start()
	return t


def sendChatAsync(apiKey, model, messages, onSuccess, onError, timeout=DEFAULT_TIMEOUT):
	"""Run sendChat on a background thread. Callbacks fire on that thread."""
	return _runAsync(
		"ChatGPTRequest",
		lambda: sendChat(apiKey, model, messages, timeout=timeout),
		onSuccess, onError,
	)


def listChatModelsAsync(apiKey, onSuccess, onError, timeout=DEFAULT_TIMEOUT):
	"""Run listChatModels on a background thread. Callbacks fire on that thread."""
	return _runAsync(
		"ChatGPTListModels",
		lambda: listChatModels(apiKey, timeout=timeout),
		onSuccess, onError,
	)
