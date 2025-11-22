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
app = FastAPI(title="Gemini + MCP Headless App")

MCP_URL = os.getenv("RENDER_MCP_URL", "https://realestatemcp.onrender.com/mcp")
API_KEY = os.getenv("GOOGLE_API_KEY")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# MCP helpers (JSON-RPC)
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
		return types.Schema(type=types.Type.OBJECT)
	json_type = (schema_dict.get("type") or "object").lower()
	desc = schema_dict.get("description")
	if json_type == "object":
		props_in = schema_dict.get("properties", {}) or {}
		props: Dict[str, types.Schema] = {}
		for key, val in props_in.items():
			props[key] = _to_gemini_schema(val)
		required = schema_dict.get("required", []) or []
		return types.Schema(type=types.Type.OBJECT, description=desc, properties=props, required=required)
	if json_type == "array":
		items = _to_gemini_schema(schema_dict.get("items", {"type": "string"}))
		return types.Schema(type=types.Type.ARRAY, description=desc, items=items)
	if json_type == "string":
		return types.Schema(type=types.Type.STRING, description=desc)
	if json_type == "integer":
		return types.Schema(type=types.Type.INTEGER, description=desc)
	if json_type == "number":
		return types.Schema(type=types.Type.NUMBER, description=desc)
	if json_type == "boolean":
		return types.Schema(type=types.Type.BOOLEAN, description=desc)
	return types.Schema(type=types.Type.STRING, description=desc)


def get_tools_for_gemini() -> List[types.Tool]:
	res = mcp_rpc("tools/list")
	raw_tools = res.get("tools", []) if isinstance(res, dict) else []
	fn_decls: List[types.FunctionDeclaration] = []
	for t in raw_tools:
		name = t.get("name")
		if not name:
			continue
		desc = t.get("description", "")
		params = t.get("inputSchema", {"type": "object", "properties": {}})
		try:
			schema = _to_gemini_schema(params)
		except Exception:
			schema = types.Schema(type=types.Type.OBJECT)
		fn_decls.append(types.FunctionDeclaration(name=name, description=desc, parameters=schema))
	return [types.Tool(function_declarations=fn_decls)] if fn_decls else []


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

	# Convert frontend history to Gemini Content
	gem_hist: List[types.Content] = []
	for m in req.history:
		role = "user" if m.get("role") == "user" else "model"
		gem_hist.append(types.Content(role=role, parts=[types.Part.from_text(text=str(m.get("content", "")))]))

	gem_hist.append(types.Content(role="user", parts=[types.Part.from_text(text=req.message)]))

	try:
		cfg = types.GenerateContentConfig(tools=tools_conf) if tools_conf else None
		resp = client.models.generate_content(
			model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
			contents=gem_hist,
			config=cfg
		)
		cand = resp.candidates[0]
		first_part = cand.content.parts[0] if cand.content.parts else None

		# Function call?
		if first_part and getattr(first_part, "function_call", None):
			fc = first_part.function_call
			result = mcp_rpc("tools/call", {"name": fc.name, "arguments": fc.args})

			# Feed function response back
			gem_hist.append(cand.content)
			gem_hist.append(types.Content(
				role="user",
				parts=[types.Part.from_function_response(name=fc.name, response={"result": result})]
			))

			resp2 = client.models.generate_content(
				model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
				contents=gem_hist,
				config=cfg
			)
			cand2 = resp2.candidates[0]
			final_text = cand2.content.parts[0].text if cand2.content.parts else ""
			return {"response": final_text, "tool_used": fc.name}

		return {"response": first_part.text if first_part else ""}
	except Exception as e:
		return {"response": f"Erreur interne: {str(e)}"}


# Serve static frontend (bundled by Docker build)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


