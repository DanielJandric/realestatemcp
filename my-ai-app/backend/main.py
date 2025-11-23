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


def _to_gemini_schema(schema_dict: Dict[str, Any]) -> types.Schema:
	if not isinstance(schema_dict, dict):
		return types.Schema(type="OBJECT")
	json_type = (schema_dict.get("type") or "object").lower()
	desc = schema_dict.get("description")
	if json_type == "object":
		props_in = schema_dict.get("properties", {}) or {}
		props: Dict[str, types.Schema] = {}
		for key, val in props_in.items():
			props[key] = _to_gemini_schema(val)
		required = schema_dict.get("required", []) or []
		return types.Schema(type="OBJECT", description=desc, properties=props, required=required)
	if json_type == "array":
		items = _to_gemini_schema(schema_dict.get("items", {"type": "string"}))
		return types.Schema(type="ARRAY", description=desc, items=items)
	if json_type == "string":
		return types.Schema(type="STRING", description=desc)
	if json_type == "integer":
		return types.Schema(type="INTEGER", description=desc)
	if json_type == "number":
		return types.Schema(type="NUMBER", description=desc)
	if json_type == "boolean":
		return types.Schema(type="BOOLEAN", description=desc)
	return types.Schema(type="STRING", description=desc)


def get_tools_for_gemini() -> List[types.Tool]:
	"""Outils MCP simplifiés et bien formés pour Gemini"""
	# Au lieu de récupérer tous les outils MCP (qui causent des erreurs),
	# on définit manuellement les 3 principaux en format Gemini natif
	fn_decls = [
		types.FunctionDeclaration(
			name="execute_sql",
			description="Exécute une requête SQL sur la base de données immobilière (SELECT only)",
			parameters=types.Schema(
				type="OBJECT",
				properties={
					"query": types.Schema(type="STRING", description="Requête SQL SELECT")
				},
				required=["query"]
			)
		),
		types.FunctionDeclaration(
			name="list_properties",
			description="Liste toutes les propriétés du portefeuille immobilier",
			parameters=types.Schema(type="OBJECT", properties={}, required=[])
		),
		types.FunctionDeclaration(
			name="get_property_dashboard",
			description="Récupère le dashboard complet d'une propriété (unités, baux, revenus, occupation)",
			parameters=types.Schema(
				type="OBJECT",
				properties={
					"property_name": types.Schema(type="STRING", description="Nom de la propriété (ex: Gare 28, Pratifori)")
				},
				required=["property_name"]
			)
		)
	]
	return [types.Tool(function_declarations=fn_decls)]


# -----------------------------------------------------------------------------
# API models
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
def chat_endpoint(req: ChatRequest):
	if not API_KEY:
		raise HTTPException(500, "GOOGLE_API_KEY missing")

	client = genai.Client(api_key=API_KEY)
	tools_conf = get_tools_for_gemini()

	# System instruction pour guider Gemini
	system_instruction = """Tu es un assistant immobilier expert avec accès à une base de données PostgreSQL via 3 outils :
1. execute_sql : Pour requêtes SQL directes
2. list_properties : Pour lister les propriétés
3. get_property_dashboard : Pour dashboard d'une propriété

RÈGLES CRITIQUES :
1. Pour "état locatif", utilise execute_sql avec cette requête SQL :
   SELECT p.name, u.unit_number, u.type, t.name as tenant, l.rent_net, l.charges
   FROM leases l
   JOIN units u ON l.unit_id = u.id
   JOIN properties p ON u.property_id = p.id
   LEFT JOIN tenants t ON l.tenant_id = t.id
   WHERE (l.end_date IS NULL OR l.end_date > NOW())
   [ET WHERE p.name ILIKE '%nom_propriété%' si une propriété spécifique]
   [ET WHERE t.name != 'Vacant' pour exclure les vacants]

2. Pour "total du parc", utilise :
   SELECT SUM(rent_net + COALESCE(charges, 0)) as total_monthly
   FROM leases l JOIN units u ON l.unit_id = u.id
   LEFT JOIN tenants t ON l.tenant_id = t.id
   WHERE (l.end_date IS NULL OR l.end_date > NOW()) AND t.name != 'Vacant'

3. Présente les montants en CHF avec formatage (ex: "1'234'567 CHF")
4. N'invente JAMAIS de chiffres - utilise TOUJOURS execute_sql"""

	# Conversion de l'historique
	gem_hist: List[types.Content] = []
	for m in req.history:
		role = "user" if m.get("role") == "user" else "model"
		content = str(m.get("content", ""))
		if content:
			gem_hist.append(types.Content(role=role, parts=[types.Part.from_text(text=content)]))

	gem_hist.append(types.Content(role="user", parts=[types.Part.from_text(text=req.message)]))

	# Configuration
	config = types.GenerateContentConfig(
		tools=tools_conf,
		system_instruction=system_instruction,
		temperature=0.3
	)

	# BOUCLE AGENTIQUE (max 10 itérations pour requêtes complexes)
	tools_used = []

	for iteration in range(10):
		try:
			response = client.models.generate_content(
				model="gemini-2.5-flash",  # Gemini 2.5 Flash stable avec function calling
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

				# Exécution de l'outil MCP
				result = mcp_rpc("tools/call", {"name": tool_name, "arguments": fc.args})

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
			return {
				"response": f"Erreur durant le traitement : {str(e)}",
				"tools_used": tools_used
			}

	# Max iterations atteintes
	return {
		"response": "La requête est trop complexe. Veuillez reformuler.",
		"tools_used": tools_used
	}


# Serve static frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")
