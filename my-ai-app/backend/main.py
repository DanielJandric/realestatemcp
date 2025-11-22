#!/usr/bin/env python3
import os
import json
import base64
import requests
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
app = FastAPI(title="Gemini 3.0 Agentic Streaming Chat")

MCP_URL = os.getenv("RENDER_MCP_URL", "https://realestatemcp.onrender.com/mcp")
API_KEY = os.getenv("GOOGLE_API_KEY")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# MCP Client
# -----------------------------------------------------------------------------
def mcp_rpc(method: str, params: Dict[str, Any] | None = None) -> Any:
	"""Appel JSON-RPC vers le serveur MCP"""
	try:
		payload = {"jsonrpc": "2.0", "id": "1", "method": method}
		if params:
			payload["params"] = params
		r = requests.post(MCP_URL, json=payload, timeout=30)
		r.raise_for_status()
		return r.json().get("result", {})
	except Exception as e:
		return {"error": str(e)}


def get_tools_config() -> List[Dict[str, Any]]:
	"""Récupère les outils MCP et les formate pour Gemini"""
	try:
		res = mcp_rpc("tools/list")
		tools = res.get("tools", []) if isinstance(res, dict) else []
		return [{
			"name": t["name"],
			"description": t.get("description", ""),
			"parameters": t.get("inputSchema", {"type": "object", "properties": {}})
		} for t in tools if isinstance(t, dict)]
	except:
		return []


# -----------------------------------------------------------------------------
# API Models
# -----------------------------------------------------------------------------
class MessagePart(BaseModel):
	text: str | None = None
	image_url: str | None = None  # Base64 data URL


class ChatMessage(BaseModel):
	role: str
	content: List[MessagePart]


class ChatRequest(BaseModel):
	messages: List[ChatMessage]


# -----------------------------------------------------------------------------
# Streaming Generator (Le Cœur)
# -----------------------------------------------------------------------------
async def agent_stream_generator(request_data: ChatRequest):
	"""Générateur SSE pour streaming avec boucle agentique"""
	client = genai.Client(api_key=API_KEY)

	# 1. Préparation des outils (Web + MCP)
	mcp_funcs = get_tools_config()
	tools_conf = [
		types.Tool(google_search=types.GoogleSearch()),
		types.Tool(function_declarations=mcp_funcs)
	] if mcp_funcs else [types.Tool(google_search=types.GoogleSearch())]

	# 2. Conversion de l'historique (Texte + Images)
	gemini_history = []
	for msg in request_data.messages:
		parts = []
		for p in msg.content:
			if p.text:
				parts.append(types.Part.from_text(text=p.text))
			if p.image_url:
				# Extraction base64: "data:image/png;base64,AAAA..."
				try:
					header, encoded = p.image_url.split(",", 1)
					mime_type = header.split(":")[1].split(";")[0]
					image_bytes = base64.b64decode(encoded)
					parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
				except:
					pass  # Skip invalid images

		role = "user" if msg.role == "user" else "model"
		if parts:
			gemini_history.append(types.Content(role=role, parts=parts))

	# 3. System instruction
	system_instruction = """Tu es un assistant immobilier expert piloté par Gemini.
Tu as accès à un serveur MCP avec des données immobilières (baux, locataires, états financiers).
Tu peux aussi utiliser Google Search pour des infos externes.

RÈGLES :
1. Si tu as besoin d'infos, utilise tes outils. N'invente JAMAIS de chiffres.
2. Enchaîne plusieurs outils si nécessaire (ex: lister → filtrer → calculer).
3. Présente les montants en CHF avec formatage (ex: "1'234'567 CHF").
4. Comprends le langage naturel : "état locatif" = consulter les baux actifs.
5. Sois synthétique, professionnel et conversationnel.
6. Cite tes sources si tu utilises Google Search."""

	# 4. Boucle Agentique (Max 5 tours)
	current_contents = gemini_history

	for turn in range(5):
		try:
			# Stream de la réponse Gemini
			response_stream = client.models.generate_content_stream(
				model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
				contents=current_contents,
				config=types.GenerateContentConfig(
					tools=tools_conf,
					system_instruction=system_instruction,
					temperature=0.3
				)
			)

			full_response_text = ""
			function_calls = []

			# Lecture du stream chunk par chunk
			for chunk in response_stream:
				# Texte : envoi immédiat au frontend
				if chunk.text:
					full_response_text += chunk.text
					yield {"data": json.dumps({"type": "text_delta", "content": chunk.text})}

				# Accumulation des appels de fonction
				for part in chunk.candidates[0].content.parts:
					if hasattr(part, 'function_call') and part.function_call:
						function_calls.append(part.function_call)

			# Pas d'appels de fonction → Fin de la conversation
			if not function_calls:
				break

			# 5. Exécution des outils
			yield {"data": json.dumps({"type": "tool_start", "count": len(function_calls)})}

			# Reconstruction du Content pour l'historique
			fc_parts = []
			if full_response_text:
				fc_parts.append(types.Part.from_text(text=full_response_text))
			
			for fc in function_calls:
				fc_parts.append(types.Part.from_function_call(name=fc.name, args=fc.args))
			
			current_contents.append(types.Content(role="model", parts=fc_parts))

			# Exécution réelle des outils
			for fc in function_calls:
				yield {"data": json.dumps({"type": "tool_log", "name": fc.name, "args": fc.args})}

				# Appel MCP
				result = mcp_rpc("tools/call", {"name": fc.name, "arguments": fc.args})

				# Feedback UI (preview)
				result_preview = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
				yield {"data": json.dumps({"type": "tool_result", "name": fc.name, "result": result_preview})}

				# Ajout du résultat à l'historique
				current_contents.append(types.Content(
					role="user",
					parts=[types.Part.from_function_response(name=fc.name, response={"result": result})]
				))

			yield {"data": json.dumps({"type": "tool_end"})}

			# Continue la boucle pour laisser Gemini analyser les résultats

		except Exception as e:
			yield {"data": json.dumps({"type": "error", "message": str(e)})}
			break

	yield {"data": json.dumps({"type": "done"})}


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
	return {"status": "ok", "mcp_url": MCP_URL, "streaming": True}


@app.post("/api/chat_stream")
async def chat_stream(request: Request):
	"""Endpoint de streaming SSE"""
	body = await request.json()
	req_obj = ChatRequest(**body)
	return EventSourceResponse(agent_stream_generator(req_obj))


# Servir le Frontend React (build statique)
if os.path.exists("static"):
	app.mount("/", StaticFiles(directory="static", html=True), name="static")
