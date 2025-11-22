#!/usr/bin/env python3
"""
Gemini 3.0 + MCP (HTTP) client pointing to Render
 - Discovers tools from your MCP server
 - Lets Gemini decide to call tools
 - Executes the tool via MCP HTTP, returns the result, and asks Gemini to synthesize

Usage (PowerShell):
  $env:GOOGLE_API_KEY="YOUR_KEY_HERE"
  python clients/gemini_mcp_http_client.py --prompt "Donne le dashboard complet de Pratifori."
"""

import os
import json
import argparse
import requests
from typing import Any, Dict, List

try:
    # pip install google-genai
    from google import genai
except Exception:
    raise SystemExit("Missing dependency: pip install google-genai")

MCP_URL = os.getenv("RENDER_MCP_URL", "https://realestatemcp.onrender.com/mcp")
MCP_TOOLS_URL = MCP_URL  # JSON-RPC endpoint
REST_TOOLS_BASE = os.getenv("RENDER_MCP_REST_BASE", "https://realestatemcp.onrender.com/tools")


def mcp_rpc(method: str, params: Dict[str, Any] | None = None, id_value: Any = "1") -> Dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": id_value, "method": method}
    if params is not None:
        payload["params"] = params
    r = requests.post(MCP_TOOLS_URL, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"MCP error: {data['error']}")
    return data["result"]


def mcp_list_tools() -> List[Dict[str, Any]]:
    res = mcp_rpc("tools/list")
    return res.get("tools", [])


def mcp_call_tool(name: str, arguments: Dict[str, Any]) -> Any:
    # First try RPC
    try:
        res = mcp_rpc("tools/call", {"name": name, "arguments": arguments}, id_value="2")
        # API returns {"content":[{"type":"text","text":"{...json...}"}]}
        contents = res.get("content", [])
        for c in contents:
            if c.get("type") == "text":
                text = c.get("text", "")
                try:
                    return json.loads(text)
                except Exception:
                    return {"raw": text}
        return res
    except Exception:
        # Fallback to REST wrapper
        rr = requests.post(f"{REST_TOOLS_BASE}/{name}", json=arguments, timeout=30)
        rr.raise_for_status()
        return rr.json()


def mcp_tools_to_gemini(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Convert MCP tool definitions to Gemini function_declarations
    fns = []
    for t in tools:
        fns.append({
            "name": t.get("name"),
            "description": t.get("description", ""),
            "parameters": t.get("inputSchema", {"type": "object", "properties": {}})
        })
    return [{"function_declarations": fns}]


def extract_function_call(resp) -> Dict[str, Any] | None:
    try:
        cand = resp.candidates[0]
        parts = cand.content.parts
        for p in parts:
            fc = getattr(p, "function_call", None)
            if fc and getattr(fc, "name", None):
                args_raw = getattr(fc, "args", "") or ""
                try:
                    args = json.loads(args_raw) if isinstance(args_raw, str) else dict(args_raw)
                except Exception:
                    args = {}
                return {"name": fc.name, "arguments": args}
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", "-p", default="Donne le dashboard complet de Pratifori.")
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set GOOGLE_API_KEY env var first.")

    client = genai.Client(api_key=api_key)

    # 1) Discover tools from MCP server (Render)
    tools = mcp_list_tools()
    gemini_tools = mcp_tools_to_gemini(tools)

    # 2) Ask Gemini; it may request a function call
    resp = client.models.generate_content(
        model="gemini-3.0-pro",
        contents=args.prompt,
        tools=gemini_tools
    )

    fc = extract_function_call(resp)
    if not fc:
        print(getattr(resp, "text", "") or str(resp))
        return

    # 3) Execute the requested tool via MCP HTTP
    tool_name = fc["name"]
    tool_args = fc.get("arguments", {}) or {}
    tool_result = mcp_call_tool(tool_name, tool_args)

    # 4) Provide the tool result back to Gemini for final synthesis
    resp2 = client.models.generate_content(
        model="gemini-3.0-pro",
        contents=[{
            "role": "user",
            "parts": [{
                "function_response": {
                    "name": tool_name,
                    "response": json.dumps(tool_result, ensure_ascii=False)
                }
            }]
        }]
    )
    print(getattr(resp2, "text", "") or json.dumps(tool_result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()


