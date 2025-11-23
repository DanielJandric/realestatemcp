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
		print(f"MCP Error: {e}")
		return {"error": str(e)}


def convert_to_gemini_schema(json_schema: Dict[str, Any]) -> types.Schema:
	"""Conversion récursive JSON Schema → types.Schema avec types en MAJUSCULES"""
	if not isinstance(json_schema, dict):
		return types.Schema(type="STRING")
	
	schema_type = (json_schema.get("type") or "string").upper()
	description = json_schema.get("description", "")
	
	# OBJECT
	if schema_type == "OBJECT":
		properties = {}
		for prop_name, prop_schema in (json_schema.get("properties") or {}).items():
			properties[prop_name] = convert_to_gemini_schema(prop_schema)
		required = json_schema.get("required", [])
		return types.Schema(
			type="OBJECT",
			description=description,
			properties=properties,
			required=required
		)
	
	# ARRAY
	elif schema_type == "ARRAY":
		items_schema = convert_to_gemini_schema(json_schema.get("items", {"type": "string"}))
		return types.Schema(type="ARRAY", description=description, items=items_schema)
	
	# Scalaires
	elif schema_type in ["STRING", "INTEGER", "NUMBER", "BOOLEAN"]:
		return types.Schema(type=schema_type, description=description)
	
	# Fallback
	return types.Schema(type="STRING", description=description)


def get_mcp_tools_for_gemini() -> List[types.Tool]:
	"""Récupère les outils MCP et les convertit pour Gemini"""
	try:
		res = mcp_rpc("tools/list")
		tools_list = res.get("tools", []) if isinstance(res, dict) else []
		
		function_declarations = []
		for tool in tools_list:
			if not isinstance(tool, dict):
				continue
			
			name = tool.get("name")
			if not name:
				continue
			
			description = tool.get("description", "")
			input_schema = tool.get("inputSchema", {"type": "object", "properties": {}})
			
			try:
				parameters_schema = convert_to_gemini_schema(input_schema)
				function_declarations.append(
					types.FunctionDeclaration(
						name=name,
						description=description,
						parameters=parameters_schema
					)
				)
			except Exception as e:
				print(f"⚠️ Skipping tool {name}: {e}")
				continue
		
		if function_declarations:
			return [types.Tool(function_declarations=function_declarations)]
		return []
	except Exception as e:
		print(f"❌ Error loading MCP tools: {e}")
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
	"""Chat endpoint avec boucle agentique (max 5 itérations)"""
	if not API_KEY:
		raise HTTPException(500, "GOOGLE_API_KEY missing")

	client = genai.Client(api_key=API_KEY)
	
	# Récupération des outils MCP
	mcp_tools = get_mcp_tools_for_gemini()
	
	# Configuration des outils (Web + MCP)
	tools_conf = [types.Tool(google_search=types.GoogleSearch())]
	if mcp_tools:
		tools_conf.extend(mcp_tools)

	# System instruction
	system_instruction = """Tu es un assistant immobilier expert connecté à une base de données Supabase via MCP.

Tu as accès à des outils pour :
- Consulter les états locatifs, propriétés, baux, locataires
- Calculer les rendements et performances financières
- Analyser les charges et les anomalies
- Rechercher dans les documents (contrats, servitudes, etc.)
- Accéder au web via Google Search si besoin

RÈGLES IMPORTANTES :
1. Utilise TOUJOURS tes outils MCP pour les données immobilières - N'invente JAMAIS de chiffres
2. Comprends le langage naturel : "état locatif" = liste des baux actifs avec revenus
3. Quand on demande des montants, calcule le total et présente en CHF avec formatage (ex: "1'234'567 CHF")
4. Enchaîne plusieurs outils si nécessaire pour répondre complètement
5. Sois professionnel, précis et conversationnel"""

	# Conversion de l'historique
	gem_hist: List[types.Content] = []
	for m in req.history:
		role = "user" if m.get("role") == "user" else "model"
		content = str(m.get("content", ""))
		if content:
			gem_hist.append(types.Content(role=role, parts=[types.Part.from_text(text=content)]))

	# Ajout du nouveau message
	gem_hist.append(types.Content(role="user", parts=[types.Part.from_text(text=req.message)]))

	# Configuration Gemini
	config = types.GenerateContentConfig(
		tools=tools_conf,
		system_instruction=system_instruction,
		temperature=0.3
	)

	# BOUCLE AGENTIQUE (max 5 itérations)
	tools_used = []
	
	for iteration in range(5):
		try:
			print(f"🔄 Iteration {iteration + 1}/5")
			
			response = client.models.generate_content(
				model="gemini-2.0-flash",
				contents=gem_hist,
				config=config
			)

			candidate = response.candidates[0]
			
			# Chercher les function_calls
			function_calls = []
			for part in candidate.content.parts:
				if hasattr(part, 'function_call') and part.function_call:
					function_calls.append(part.function_call)

			if not function_calls:
				# Pas d'appel d'outil → Réponse finale
				final_text = ""
				for part in candidate.content.parts:
					if hasattr(part, 'text') and part.text:
						final_text += part.text
				
				return {
					"response": final_text or "Aucune réponse générée.",
					"tools_used": tools_used
				}

			# Il y a des appels d'outils
			gem_hist.append(candidate.content)

			for fc in function_calls:
				tool_name = fc.name
				tools_used.append(tool_name)
				print(f"🛠️ Calling {tool_name} with args: {fc.args}")

				# Exécution de l'outil MCP
				result = mcp_rpc("tools/call", {"name": tool_name, "arguments": fc.args})
				print(f"✅ Result: {str(result)[:100]}...")

				# Ajout du résultat à l'historique
				gem_hist.append(types.Content(
					role="user",
					parts=[types.Part.from_function_response(
						name=tool_name,
						response={"result": result}
					)]
				))

			# Continue la boucle pour laisser Gemini analyser les résultats

		except Exception as e:
			print(f"❌ Error in iteration {iteration + 1}: {e}")
			return {
				"response": f"Erreur durant le traitement : {str(e)}",
				"tools_used": tools_used
			}

	# Max iterations atteintes
	return {
		"response": "La requête est trop complexe. Veuillez reformuler ou simplifier votre question.",
		"tools_used": tools_used
	}


# Servir le Frontend React
app.mount("/", StaticFiles(directory="static", html=True), name="static")
