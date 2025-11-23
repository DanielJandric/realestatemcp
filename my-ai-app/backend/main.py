#!/usr/bin/env python3
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any

from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
app = FastAPI(title="Gemini + MCP Chat")

MCP_URL = os.getenv("RENDER_MCP_URL", "https://realestatemcp.onrender.com/mcp")
API_KEY = os.getenv("GOOGLE_API_KEY")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# MCP helpers
# -----------------------------------------------------------------------------
def mcp_rpc(method: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
	payload = {"jsonrpc": "2.0", "id": "1", "method": method}
	if params:
		payload["params"] = params
	try:
		r = requests.post(MCP_URL, json=payload, timeout=60)
		r.raise_for_status()
		data = r.json()
		return data.get("result", {}) if isinstance(data, dict) else {}
	except Exception as e:
		return {"error": str(e)}


def get_tools() -> List[Dict[str, Any]]:
	"""Simple dict format pour Gemini"""
	res = mcp_rpc("tools/list")
	tools = res.get("tools", []) if isinstance(res, dict) else []
	return [{
		"name": t["name"],
		"description": t.get("description", ""),
		"parameters": t.get("inputSchema", {"type": "object", "properties": {}})
	} for t in tools if isinstance(t, dict) and t.get("name")]


# -----------------------------------------------------------------------------
# API models
# -----------------------------------------------------------------------------
class MessagePart(BaseModel):
	text: str | None = None


class ChatMessage(BaseModel):
	role: str
	content: List[MessagePart]


class ChatRequest(BaseModel):
	messages: List[ChatMessage]


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
	return {"status": "ok", "mcp_url": MCP_URL}


@app.post("/api/chat_stream")
async def chat_endpoint(req: ChatRequest):
	if not API_KEY:
		raise HTTPException(500, "GOOGLE_API_KEY missing")

	client = genai.Client(api_key=API_KEY)
	
	# Outils (Google Search uniquement pour l'instant - MCP cause des problèmes)
	tools_conf = [
		types.Tool(google_search=types.GoogleSearch())
	]

	# System instruction
	system_instruction = """Tu es un assistant immobilier expert.
Tu as accès à Google Search pour trouver des informations.
Sois synthétique, professionnel et conversationnel."""

	# Conversion de l'historique
	gem_hist: List[types.Content] = []
	for msg in req.messages:
		text_parts = [p.text for p in msg.content if p.text]
		if text_parts:
			role = "user" if msg.role == "user" else "model"
			gem_hist.append(types.Content(
				role=role,
				parts=[types.Part.from_text(text="\n".join(text_parts))]
			))

	# Génération
	try:
		response = client.models.generate_content(
			model="gemini-2.0-flash",
			contents=gem_hist,
			config=types.GenerateContentConfig(
				tools=tools_conf,
				system_instruction=system_instruction,
				temperature=0.4
			)
		)
		
		cand = response.candidates[0]
		text = ""
		for part in cand.content.parts:
			if hasattr(part, 'text') and part.text:
				text += part.text
		
		return {"response": text or "Aucune réponse générée."}
	except Exception as e:
		return {"response": f"Erreur: {str(e)}"}


# Servir le Frontend React
if os.path.exists("static"):
	app.mount("/", StaticFiles(directory="static", html=True), name="static")
