#!/usr/bin/env python3
import os
import json
import requests
import sys
from typing import Any, Dict, List

try:
	# pip install google-genai
	from google import genai
	from google.genai import types
except ImportError:
	print("\033[91mErreur: Installez le SDK : pip install google-genai\033[0m")
	sys.exit(1)

# --- CONFIGURATION ---
MCP_URL = os.getenv("RENDER_MCP_URL", "https://realestatemcp.onrender.com/mcp")
REST_TOOLS_BASE = os.getenv("RENDER_MCP_REST_BASE", "https://realestatemcp.onrender.com/tools")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # ex: "gemini-3.0-pro"


# --- COULEURS POUR LE TERMINAL ---
class Colors:
	HEADER = '\033[95m'
	BLUE = '\033[94m'
	GREEN = '\033[92m'
	YELLOW = '\033[93m'
	RED = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'


# --- FONCTIONS MCP ---
def mcp_rpc(method: str, params: Dict[str, Any] | None = None, id_value: Any = "1") -> Dict[str, Any]:
	payload = {"jsonrpc": "2.0", "id": id_value, "method": method}
	if params:
		payload["params"] = params
	try:
		r = requests.post(MCP_URL, json=payload, timeout=60)
		r.raise_for_status()
		data = r.json()
		if "error" in data:
			return {"error": data["error"]}
		return data["result"]
	except Exception as e:
		return {"error": str(e)}


def mcp_list_tools() -> List[Dict[str, Any]]:
	res = mcp_rpc("tools/list")
	return res.get("tools", [])


def mcp_call_tool(name: str, arguments: Dict[str, Any]) -> Any:
	print(f"{Colors.YELLOW}   [Outil] Exécution de '{name}' avec {json.dumps(arguments, ensure_ascii=False)}...{Colors.ENDC}")
	# Essai via RPC
	res = mcp_rpc("tools/call", {"name": name, "arguments": arguments}, id_value="2")

	# Extraction du contenu textuel standard MCP
	if isinstance(res, dict) and "content" in res:
		contents = res.get("content", [])
		text_results = []
		for c in contents:
			if c.get("type") == "text":
				text_results.append(c.get("text", ""))
		final_text = "\n".join(text_results)
		try:
			return json.loads(final_text)
		except Exception:
			return final_text

	# Fallback REST wrapper si jamais
	try:
		rr = requests.post(f"{REST_TOOLS_BASE}/{name}", json=arguments, timeout=60)
		rr.raise_for_status()
		return rr.json()
	except Exception:
		return res


def mcp_tools_to_gemini(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	fns = []
	for t in tools:
		fns.append({
			"name": t.get("name"),
			"description": t.get("description", ""),
			"parameters": t.get("inputSchema", {"type": "object", "properties": {}})
		})
	return fns  # Le SDK gère l'encapsulation


# --- COEUR DU CHATBOT ---
def main():
	api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")
	if not api_key:
		print(f"{Colors.RED}Erreur: La variable d'environnement GOOGLE_API_KEY est manquante.{Colors.ENDC}")
		return

	client = genai.Client(api_key=api_key)

	print(f"{Colors.HEADER}--- Démarrage du Client Gemini + MCP (HTTP Render) ---{Colors.ENDC}")
	print(f"Connexion au serveur MCP : {MCP_URL}")

	# 1. Découverte des outils au démarrage
	try:
		mcp_tools = mcp_list_tools()
		print(f"{Colors.GREEN}✓ {len(mcp_tools)} outils chargés depuis le serveur MCP.{Colors.ENDC}")
	except Exception as e:
		print(f"{Colors.RED}Erreur de connexion MCP: {e}{Colors.ENDC}")
		return

	# Conversion pour Gemini
	gemini_tools_conf = [{"function_declarations": mcp_tools_to_gemini(mcp_tools)}]

	# Historique
	chat_history = []

	print(f"{Colors.BLUE}Prêt ! Tapez 'quit' ou 'exit' pour quitter.{Colors.ENDC}\n")

	while True:
		try:
			user_input = input(f"{Colors.BOLD}Vous: {Colors.ENDC}")
			if user_input.lower() in ["quit", "exit", "q"]:
				print("Au revoir !")
				break
			if not user_input.strip():
				continue
		except KeyboardInterrupt:
			print("\nAu revoir !")
			break

		# Ajout message utilisateur
		chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_input)]))

		# --- BOUCLE DE RÉSOLUTION (Agent Loop) ---
		while True:
			try:
				response = client.models.generate_content(
					model=MODEL_NAME,
					contents=chat_history,
					config=types.GenerateContentConfig(tools=gemini_tools_conf)
				)
			except Exception as e:
				print(f"{Colors.RED}Erreur API Gemini: {e}{Colors.ENDC}")
				break

			candidate = response.candidates[0]
			# Toujours ajouter à l'historique
			chat_history.append(candidate.content)

			# Collecter les appels d'outils éventuels
			function_calls = []
			for part in candidate.content.parts:
				if getattr(part, "function_call", None):
					function_calls.append(part.function_call)

			if function_calls:
				for fc in function_calls:
					tool_name = fc.name
					tool_args = fc.args or {}
					tool_result = mcp_call_tool(tool_name, tool_args)

					# Retour à Gemini comme function_response
					chat_history.append(types.Content(
						role="user",
						parts=[types.Part.from_function_response(
							name=tool_name,
							response={"result": tool_result}
						)]
					))
				# Continue la boucle interne pour laisser Gemini enchaîner
			else:
				# Réponse finale (texte)
				first_part = next((p for p in candidate.content.parts if getattr(p, "text", None)), None)
				text = first_part.text if first_part else ""
				print(f"{Colors.GREEN}Gemini:{Colors.ENDC} {text}")
				print("-" * 50)
				break


if __name__ == "__main__":
	main()


