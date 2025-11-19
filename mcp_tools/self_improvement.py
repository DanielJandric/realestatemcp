"""
Self-Improvement System for MCP Server
Allows Claude to analyze and improve itself recursively
"""

import json
from pathlib import Path
from datetime import datetime

# Logs storage
LOGS_FILE = Path(__file__).parent.parent / "mcp_logs.json"
IMPROVEMENTS_FILE = Path(__file__).parent.parent / "improvements_history.json"


class ToolLogger:
    """Log tool calls for analysis"""
    
    @staticmethod
    def log_call(tool_name: str, success: bool, duration_ms: float, error: str = None):
        """Log a tool call"""
        logs = ToolLogger.get_logs()
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "success": success,
            "duration_ms": duration_ms,
            "error": error
        })
        
        # Keep only last 1000 logs
        logs = logs[-1000:]
        
        LOGS_FILE.write_text(json.dumps(logs, indent=2))
    
    @staticmethod
    def get_logs():
        """Get all logs"""
        if LOGS_FILE.exists():
            return json.loads(LOGS_FILE.read_text())
        return []


def analyze_system(focus: str = "all"):
    """Analyze the MCP system and suggest improvements"""
    logs = ToolLogger.get_logs()
    
    if not logs:
        return {
            "success": True,
            "message": "Aucun log disponible pour l'analyse",
            "suggestions": []
        }
    
    analysis = {
        "total_calls": len(logs),
        "success_rate": sum(1 for l in logs if l['success']) / len(logs) * 100,
        "avg_duration_ms": sum(l['duration_ms'] for l in logs) / len(logs),
        "errors": [l for l in logs if not l['success']],
        "slow_calls": [l for l in logs if l['duration_ms'] > 5000]  # > 5s
    }
    
    # Generate suggestions
    suggestions = []
    
    # Error analysis
    if analysis['errors']:
        error_types = {}
        for error in analysis['errors']:
            tool = error['tool']
            error_types[tool] = error_types.get(tool, 0) + 1
        
        for tool, count in error_types.items():
            if count > 5:
                suggestions.append({
                    "type": "error_handling",
                    "tool": tool,
                    "issue": f"{count} erreurs détectées",
                    "suggestion": "Ajouter retry logic et meilleure gestion d'erreurs",
                    "priority": "HIGH"
                })
    
    # Performance analysis
    if analysis['slow_calls']:
        slow_tools = {}
        for call in analysis['slow_calls']:
            tool = call['tool']
            slow_tools[tool] = slow_tools.get(tool, []) + [call['duration_ms']]
        
        for tool, durations in slow_tools.items():
            avg_duration = sum(durations) / len(durations)
            suggestions.append({
                "type": "performance",
                "tool": tool,
                "issue": f"Temps moyen: {avg_duration:.0f}ms",
                "suggestion": "Optimiser avec caching ou requêtes SQL plus efficaces",
                "priority": "MEDIUM"
            })
    
    # Data quality analysis (focus on tools that return empty results)
    empty_results = [l for l in logs if l.get('error') and 'non trouvée' in l.get('error', '')]
    if empty_results:
        suggestions.append({
            "type": "data_quality",
            "issue": f"{len(empty_results)} résultats vides",
            "suggestion": "Améliorer fuzzy matching ou ajouter synonymes",
            "priority": "LOW"
        })
    
    return {
        "success": True,
        "analysis": analysis,
        "suggestions": suggestions,
        "recommendation": "Commencer par les suggestions HIGH priority" if suggestions else "Système optimal"
    }


def improve_tool(tool_name: str, improvements: list):
    """Generate improved code for a tool"""
    
    # Read current server code
    server_file = Path(__file__).parent / "server_final.py"
    current_code = server_file.read_text()
    
    # Find tool function
    if f"def {tool_name}(" not in current_code:
        return {
            "success": False,
            "error": f"Outil '{tool_name}' non trouvé dans le code"
        }
    
    # Generate improvement suggestions based on requested improvements
    improvement_code = f"""
# AMÉLIORATION SUGGÉRÉE POUR: {tool_name}
# Date: {datetime.now().isoformat()}
# Améliorations demandées: {', '.join(improvements)}

def {tool_name}_improved(...):
    \"\"\"
    Version améliorée avec:
    {chr(10).join(f'    - {imp}' for imp in improvements)}
    \"\"\"
    
    try:
        # TODO: Implémenter les améliorations suivantes:
"""
    
    for imp in improvements:
        if "cache" in imp.lower():
            improvement_code += """
        # 1. Ajouter caching
        cache_key = f"{tool_name}_{arguments}"
        if cache_key in global_cache:
            return global_cache[cache_key]
"""
        
        if "retry" in imp.lower():
            improvement_code += """
        # 2. Ajouter retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = ... # code original
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # exponential backoff
"""
        
        if "log" in imp.lower():
            improvement_code += """
        # 3. Ajouter logging
        start_time = time.time()
        result = ... # code original
        duration = (time.time() - start_time) * 1000
        ToolLogger.log_call(tool_name, True, duration)
"""
    
    improvement_code += """
        
        return result
        
    except Exception as e:
        ToolLogger.log_call(tool_name, False, 0, str(e))
        return {"success": False, "error": str(e)}
"""
    
    # Save improvement
    improvements_history = []
    if IMPROVEMENTS_FILE.exists():
        improvements_history = json.loads(IMPROVEMENTS_FILE.read_text())
    
    improvements_history.append({
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "improvements": improvements,
        "code": improvement_code
    })
    
    IMPROVEMENTS_FILE.write_text(json.dumps(improvements_history, indent=2))
    
    return {
        "success": True,
        "tool": tool_name,
        "improved_code": improvement_code,
        "next_steps": [
            "1. Réviser le code généré",
            "2. L'intégrer dans server_final.py",
            "3. Tester avec des exemples",
            "4. Redémarrer le serveur MCP"
        ],
        "file_saved": str(IMPROVEMENTS_FILE)
    }


def get_system_logs(last_n_calls: int = 100):
    """Get recent system logs"""
    logs = ToolLogger.get_logs()
    return {
        "success": True,
        "total_logs": len(logs),
        "recent_logs": logs[-last_n_calls:],
        "summary": {
            "success_rate": sum(1 for l in logs[-last_n_calls:] if l['success']) / len(logs[-last_n_calls:]) * 100 if logs else 0,
            "most_used_tools": _get_most_used_tools(logs[-last_n_calls:]),
            "most_errors": _get_most_errors(logs[-last_n_calls:])
        }
    }


def _get_most_used_tools(logs):
    tools = {}
    for log in logs:
        tool = log['tool']
        tools[tool] = tools.get(tool, 0) + 1
    return sorted(tools.items(), key=lambda x: -x[1])[:5]


def _get_most_errors(logs):
    errors = {}
    for log in logs:
        if not log['success']:
            tool = log['tool']
            errors[tool] = errors.get(tool, 0) + 1
    return sorted(errors.items(), key=lambda x: -x[1])[:5]

