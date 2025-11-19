import subprocess
import json
import sys
import time

def verify_stdio():
    print("Starting MCP server process...")
    process = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="c:/OneDriveExport"
    )

    # JSON-RPC Initialize Request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }

    print("Sending initialize request...")
    try:
        # Send request
        json_str = json.dumps(init_request)
        process.stdin.write(json_str + "\n")
        process.stdin.flush()

        # Read response
        print("Waiting for response...")
        output = process.stdout.readline()
        print(f"Received: {output}")
        
        if output:
            resp = json.loads(output)
            print("Server initialized successfully!")
            print(json.dumps(resp, indent=2))
        else:
            print("No output received.")
            print("Stderr:", process.stderr.read())

    except Exception as e:
        print(f"Error: {e}")
        print("Stderr:", process.stderr.read())
    finally:
        process.terminate()

if __name__ == "__main__":
    verify_stdio()
