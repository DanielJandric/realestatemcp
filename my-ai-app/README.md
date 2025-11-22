# Gemini + MCP Headless App (Render-ready)

## Structure
```
my-ai-app/
├── backend/
│   ├── main.py            # FastAPI + Gemini + MCP loop
│   ├── requirements.txt
├── frontend/              # React + Vite + Tailwind
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       └── index.css
├── Dockerfile
```

## Environment
- `GOOGLE_API_KEY`: Your Gemini key
- `RENDER_MCP_URL`: Your MCP HTTP endpoint (e.g. https://realestatemcp.onrender.com/mcp)
- Optional: `GEMINI_MODEL` (default: `gemini-2.0-flash`)

## Local build (optional)
```
cd my-ai-app
docker build -t gemini-mcp-app .
docker run -p 8000:8000 -e GOOGLE_API_KEY=XXX -e RENDER_MCP_URL=https://.../mcp gemini-mcp-app
```
Open http://localhost:8000

## Render
- New Web Service → Runtime: Docker
- Set env vars: `GOOGLE_API_KEY`, `RENDER_MCP_URL`


