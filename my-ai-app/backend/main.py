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
app = FastAPI(title="Gemini + MCP Agentic Chat")

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
	payload = {"jsonrpc": "2.0", "id": "1", "method": method}
	if params:
		payload["params"] = params
	try:
		r = requests.post(MCP_URL, json=payload, timeout=60)
		r.raise_for_status()
		result = r.json().get("result", {})
		
		# Si c'est un appel d'outil, extraire le texte du format MCP standard
		if method == "tools/call" and isinstance(result, dict) and "content" in result:
			text_parts = []
			for content_item in result["content"]:
				if isinstance(content_item, dict) and content_item.get("type") == "text":
					text_parts.append(content_item.get("text", ""))
			return "\n".join(text_parts) if text_parts else result
		
		return result
	except Exception as e:
		print(f"❌ MCP Error: {e}")
		return {"error": str(e)}


def get_tools_config() -> List[Dict[str, Any]]:
	"""Récupère les outils MCP et les formate pour Gemini"""
	try:
		res = mcp_rpc("tools/list")
		tools_list = res.get("tools", []) if isinstance(res, dict) else []
		
		gemini_funcs = []
		for t in tools_list:
			if not isinstance(t, dict):
				continue
			gemini_funcs.append({
				"name": t.get("name", ""),
				"description": t.get("description", ""),
				"parameters": t.get("inputSchema", {"type": "object", "properties": {}})
			})
		return gemini_funcs
	except Exception as e:
		print(f"❌ Error loading tools: {e}")
		return []


# -----------------------------------------------------------------------------
# API Models
# -----------------------------------------------------------------------------
class ChatRequest(BaseModel):
	message: str
	history: List[Dict[str, Any]] = []


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
	return {"status": "ok", "mcp_url": MCP_URL}


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
	if not API_KEY:
		raise HTTPException(500, "GOOGLE_API_KEY missing")

	client = genai.Client(api_key=API_KEY)

	# 1. Préparation des outils (Web + MCP)
	mcp_tools = get_tools_config()
	tools_conf = [
		types.Tool(google_search=types.GoogleSearch()),
		types.Tool(function_declarations=mcp_tools)
	] if mcp_tools else [types.Tool(google_search=types.GoogleSearch())]

	# 2. System instruction (personnalité et règles)
	system_instruction = """Tu es un assistant immobilier expert piloté par Gemini.
Tu as accès à un serveur MCP qui contient des données immobilières précises (baux, locataires, états financiers, propriétés, servitudes).

RÈGLES :
1. Si tu as besoin d'informations, utilise tes outils. N'invente JAMAIS de chiffres.
2. Tu peux enchaîner plusieurs outils (ex: lister les propriétés → consulter les baux → calculer le total).
3. Quand l'utilisateur demande un montant, calcule le total et présente-le en CHF avec formatage (ex: "1'234'567 CHF").
4. Comprends le langage naturel : "état locatif" = consulter les baux actifs, "loyers" = revenus locatifs, etc.
5. Sois synthétique, professionnel et conversationnel.
6. Si tu utilises Google Search, cite tes sources."""

	# 3. Reconstruction de l'historique pour Gemini
	gemini_history = []
	for msg in req.history:
		if not isinstance(msg, dict) or not msg.get("content"):
			continue
		role = "user" if msg.get("role") == "user" else "model"
		gemini_history.append(types.Content(
			role=role,
			parts=[types.Part.from_text(text=str(msg["content"]))]
		))

	# Ajout de la nouvelle question utilisateur
	gemini_history.append(types.Content(
		role="user",
		parts=[types.Part.from_text(text=req.message)]
	))

	# 4. BOUCLE AGENTIQUE (max 5 itérations)
	final_response_text = ""
	tools_used = []

	# Configuration de la génération
	config = types.GenerateContentConfig(
		tools=tools_conf,
		system_instruction=system_instruction,
		temperature=0.4  # Rigoureux avec les données
	)

	current_turn_content = gemini_history

	for iteration in range(5):
		try:
			# Appel à Gemini
			response = client.models.generate_content(
				model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
				contents=current_turn_content,
				config=config
			)

			candidate = response.candidates[0]

			# Chercher les appels de fonction
			function_calls = []
			for part in candidate.content.parts:
				if hasattr(part, 'function_call') and part.function_call:
					function_calls.append(part.function_call)

			if function_calls:
				# Gemini veut utiliser des outils
				current_turn_content.append(candidate.content)

				for fc in function_calls:
					tools_used.append(fc.name)
					print(f"🤖 Iteration {iteration+1}/5: Appel {fc.name}")
					print(f"   Args: {fc.args}")

					# Exécution de l'outil
					result = mcp_rpc("tools/call", {"name": fc.name, "arguments": fc.args})

					# Format pour Gemini
					result_str = str(result) if not isinstance(result, str) else result

					# Ajout du résultat à l'historique
					current_turn_content.append(types.Content(
						role="user",
						parts=[types.Part.from_function_response(
							name=fc.name,
							response={"result": result_str}
						)]
					))
				# Continue la boucle pour laisser Gemini analyser
			else:
				# Pas d'appel d'outil → Réponse finale
				for part in candidate.content.parts:
					if hasattr(part, 'text') and part.text:
						final_response_text += part.text
				break  # Sortie de la boucle

		except Exception as e:
			print(f"❌ Error in iteration {iteration+1}: {e}")
			return {
				"response": f"Erreur durant le raisonnement : {str(e)}",
				"tools_used": tools_used
			}

	if not final_response_text:
		final_response_text = "Désolé, je n'ai pas pu générer de réponse complète. Essayez de reformuler votre question."

	return {
		"response": final_response_text,
		"tools_used": tools_used
	}


# Servir le Frontend React (build statique)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
