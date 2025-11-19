#!/usr/bin/env python3
"""
HTTP Wrapper for MCP Server
Allows remote access via REST API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import json
from server_final import app as mcp_app, call_tool

http_app = Flask(__name__)
CORS(http_app)  # Allow CORS for web access


@http_app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "real-estate-mcp"})


@http_app.route('/tools', methods=['GET'])
async def list_tools():
    """List available tools"""
    tools = await mcp_app.list_tools()
    return jsonify({
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.inputSchema
            } for t in tools
        ]
    })


@http_app.route('/call', methods=['POST'])
async def call():
    """Call a tool"""
    data = request.json
    tool_name = data.get('tool')
    arguments = data.get('arguments', {})
    
    if not tool_name:
        return jsonify({"error": "tool name required"}), 400
    
    try:
        result = await call_tool(tool_name, arguments)
        return jsonify({
            "success": True,
            "result": json.loads(result[0].text)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("\n🚀 MCP HTTP Server démarré sur http://localhost:5000")
    print("📋 Endpoints:")
    print("   GET  /health  - Health check")
    print("   GET  /tools   - List tools")
    print("   POST /call    - Call tool\n")
    
    http_app.run(host='0.0.0.0', port=5000, debug=True)

