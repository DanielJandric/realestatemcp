#!/usr/bin/env python3
import os
import json
import requests
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
app = FastAPI(title="Gemini 2.5 + MCP Streaming Agent")

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
		return {"error": str(e)}


def get_tools_for_gemini() -> List[types.Tool]:
	"""Tous les outils MCP essentiels, bien formés"""
	fn_decls = [
		types.FunctionDeclaration(
			name="execute_sql",
			description="Exécute une requête SQL sur la base immobilière (SELECT only)",
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
			description="Liste toutes les propriétés du portefeuille",
			parameters=types.Schema(type="OBJECT", properties={}, required=[])
		),
		types.FunctionDeclaration(
			name="get_property_dashboard",
			description="Dashboard complet: unités, baux, revenus, occupation",
			parameters=types.Schema(
				type="OBJECT",
				properties={
					"property_name": types.Schema(type="STRING", description="Nom (ex: Gare 28, Pratifori)")
				},
				required=["property_name"]
			)
		),
		types.FunctionDeclaration(
			name="search_servitudes",
			description="Recherche de servitudes dans le registre foncier par mot-clé et/ou commune",
			parameters=types.Schema(
				type="OBJECT",
				properties={
					"query": types.Schema(type="STRING", description="Mot-clé (ex: passage, vue, servitude)"),
					"commune": types.Schema(type="STRING", description="Nom de la commune (optionnel)")
				},
				required=["query"]
			)
		),
		types.FunctionDeclaration(
			name="get_etat_locatif_complet",
			description="État locatif détaillé avec KPI par propriété",
			parameters=types.Schema(
				type="OBJECT",
				properties={
					"property_name": types.Schema(type="STRING", description="Nom de la propriété (optionnel pour toutes)")
				},
				required=[]
			)
		),
		types.FunctionDeclaration(
			name="calculate_rendements",
			description="Calcule les rendements (brut, net estimé) pour une propriété",
			parameters=types.Schema(
				type="OBJECT",
				properties={
					"property_name": types.Schema(type="STRING", description="Nom de la propriété"),
					"purchase_price": types.Schema(type="NUMBER", description="Prix d'achat en CHF (optionnel)")
				},
				required=["property_name"]
			)
		),
		types.FunctionDeclaration(
			name="detect_anomalies_locatives",
			description="Détecte les loyers anormaux (z-score) pour une propriété",
			parameters=types.Schema(
				type="OBJECT",
				properties={
					"property_name": types.Schema(type="STRING", description="Nom de la propriété"),
					"z_threshold": types.Schema(type="NUMBER", description="Seuil z-score (défaut: 2.0)")
				},
				required=["property_name"]
			)
		),
		types.FunctionDeclaration(
			name="get_echeancier_baux",
			description="Échéancier des fins de bail dans les N prochains mois",
			parameters=types.Schema(
				type="OBJECT",
				properties={
					"property_name": types.Schema(type="STRING", description="Nom de la propriété"),
					"months_ahead": types.Schema(type="INTEGER", description="Nombre de mois (défaut: 12)")
				},
				required=["property_name"]
			)
		),
		types.FunctionDeclaration(
			name="get_database_stats",
			description="Statistiques globales de la base (comptages)",
			parameters=types.Schema(type="OBJECT", properties={}, required=[])
		)
	]
	return [types.Tool(function_declarations=fn_decls)]


# -----------------------------------------------------------------------------
# System Instruction (Ton expertise Swiss RE)
# -----------------------------------------------------------------------------
SYSTEM_INSTRUCTION = """# IDENTITÉ & CONTEXTE

Tu es un assistant spécialisé en analyse immobilière pour le marché suisse, avec expertise en:
- Due diligence immobilière (résidentiel & commercial)
- Analyse financière de portefeuilles (rendements, NOI, TRI)
- Réglementation suisse (cantonale et fédérale)

Portfolio: propriétés en Suisse Romande (Valais, Vaud, Fribourg)

# OUTILS DISPONIBLES
1. **execute_sql** : Requêtes SQL (PRIORITAIRE pour données chiffrées)
2. **list_properties** : Liste des propriétés
3. **get_property_dashboard** : Vue 360° d'une propriété

# REQUÊTES SQL ESSENTIELLES

**État locatif net (une propriété) :**
```sql
SELECT u.unit_number, u.type, t.name as tenant, l.rent_net, l.charges
FROM leases l
JOIN units u ON l.unit_id = u.id
JOIN properties p ON u.property_id = p.id
LEFT JOIN tenants t ON l.tenant_id = t.id
WHERE (l.end_date IS NULL OR l.end_date > NOW())
  AND p.name ILIKE '%NOM%'
  AND t.name != 'Vacant'
```

**Total parc (hors vacants) :**
```sql
SELECT 
  SUM(CASE WHEN t.name != 'Vacant' THEN l.rent_net + COALESCE(l.charges,0) ELSE 0 END) as mensuel,
  SUM(CASE WHEN t.name != 'Vacant' THEN (l.rent_net + COALESCE(l.charges,0)) * 12 ELSE 0 END) as annuel,
  COUNT(DISTINCT CASE WHEN t.name != 'Vacant' THEN u.id END) as occupees
FROM leases l
JOIN units u ON l.unit_id = u.id
LEFT JOIN tenants t ON l.tenant_id = t.id
WHERE (l.end_date IS NULL OR l.end_date > NOW())
```

**Par propriété (agrégé) :**
```sql
SELECT 
  p.name,
  COUNT(DISTINCT u.id) as unites,
  SUM(CASE WHEN t.name != 'Vacant' THEN l.rent_net ELSE 0 END) as loyers_mensuels
FROM properties p
LEFT JOIN units u ON u.property_id = p.id
LEFT JOIN leases l ON l.unit_id = u.id AND (l.end_date IS NULL OR l.end_date > NOW())
LEFT JOIN tenants t ON l.tenant_id = t.id
GROUP BY p.id, p.name
ORDER BY loyers_mensuels DESC
```

# RÈGLES
1. TOUJOURS execute_sql pour chiffres
2. Exclure "Vacant" par défaut (sauf demande explicite)
3. Présenter en CHF formaté (ex: "1'234'567 CHF")
4. Être concis, data-driven et actionnable
5. Signaler limitations/données manquantes"""


# -----------------------------------------------------------------------------
# API Models
# -----------------------------------------------------------------------------
class MessagePart(BaseModel):
	text: str | None = None


class ChatMessage(BaseModel):
	role: str
	content: List[MessagePart]


class ChatRequest(BaseModel):
	messages: List[ChatMessage]


# -----------------------------------------------------------------------------
# Streaming Generator (Avec transparence)
# -----------------------------------------------------------------------------
async def agent_stream_generator(request_data: ChatRequest):
	"""Générateur SSE avec boucle agentique et transparence"""
	client = genai.Client(api_key=API_KEY)
	tools_conf = get_tools_for_gemini()

	# Conversion de l'historique
	gem_hist: List[types.Content] = []
	for msg in request_data.messages:
		text_parts = [p.text for p in msg.content if p.text]
		if text_parts:
			role = "user" if msg.role == "user" else "model"
			gem_hist.append(types.Content(
				role=role,
				parts=[types.Part.from_text(text="\n".join(text_parts))]
			))

	# Configuration
	config = types.GenerateContentConfig(
		tools=tools_conf,
		system_instruction=SYSTEM_INSTRUCTION,
		temperature=0.2  # Précis pour données financières
	)

	# BOUCLE AGENTIQUE (max 10 itérations)
	for iteration in range(10):
		try:
			# Event: Début itération
			yield {"data": json.dumps({"type": "iteration_start", "iteration": iteration + 1})}

			# Stream de Gemini
			response_stream = client.models.generate_content_stream(
				model="gemini-2.5-flash",
				contents=gem_hist,
				config=config
			)

			full_text = ""
			function_calls = []

			# Lecture du stream
			for chunk in response_stream:
				# Texte: envoi immédiat
				if chunk.text:
					full_text += chunk.text
					yield {"data": json.dumps({"type": "text_delta", "content": chunk.text})}

				# Accumulation des function_calls
				if chunk.candidates:
					for part in chunk.candidates[0].content.parts:
						if hasattr(part, 'function_call') and part.function_call:
							fc = part.function_call
							if fc not in function_calls:
								function_calls.append(fc)

			# Pas d'appels d'outils → Fin
			if not function_calls:
				yield {"data": json.dumps({"type": "done"})}
				break

			# Il y a des appels d'outils
			yield {"data": json.dumps({"type": "tools_start", "count": len(function_calls)})}

			# Reconstruction du Content
			fc_parts = []
			if full_text:
				fc_parts.append(types.Part.from_text(text=full_text))
			for fc in function_calls:
				fc_parts.append(types.Part.from_function_call(name=fc.name, args=fc.args))
			
			gem_hist.append(types.Content(role="model", parts=fc_parts))

			# Exécution des outils
			for fc in function_calls:
				tool_name = fc.name
				args = fc.args

				# Event: Début exécution outil
				yield {"data": json.dumps({
					"type": "tool_call",
					"name": tool_name,
					"args": args
				})}

				# Exécution MCP
				result = mcp_rpc("tools/call", {"name": tool_name, "arguments": args})

				# Event: Résultat outil (preview)
				result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
				yield {"data": json.dumps({
					"type": "tool_result",
					"name": tool_name,
					"preview": result_preview
				})}

				# Ajout à l'historique
				gem_hist.append(types.Content(
					role="user",
					parts=[types.Part.from_function_response(name=tool_name, response={"result": result})]
				))

			yield {"data": json.dumps({"type": "tools_end"})}
			# Continue la boucle

		except Exception as e:
			yield {"data": json.dumps({"type": "error", "message": str(e)})}
			break

	yield {"data": json.dumps({"type": "complete"})}


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
	return {"status": "ok", "mcp_url": MCP_URL, "streaming": True}


@app.post("/api/chat")
async def chat_stream(request: Request):
	"""Endpoint streaming SSE"""
	body = await request.json()
	req_obj = ChatRequest(**body)
	return EventSourceResponse(agent_stream_generator(req_obj))


# Serve static frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")
