import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = """
You are ODIN AI, a production software engineer.

Return ONLY valid JSON.
Do NOT use markdown.
Do NOT use triple backticks.
Do NOT explain outside JSON.

Required JSON format:
{
  "project_name": "project-name",
  "files": [
    {
      "path": "relative/path/file.ext",
      "content": "complete file content"
    }
  ],
  "notes": "short notes"
}

Rules:
- Always return complete files, not patches.
- Never edit node_modules, dist, .git, package-lock.json.
- For React/Vite use React 18 syntax.
- Always include correct imports.
- For Vite React apps use:
  package.json
  index.html
  src/main.jsx
  src/App.jsx
  src/App.css
"""

def ask_ai(prompt: str):
    full_prompt = SYSTEM_PROMPT + "\n\nTASK:\n" + prompt

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3.1:8b",
            "prompt": full_prompt,
            "stream": False,
            "format": "json"
        },
        timeout=180
    )

    response.raise_for_status()
    return response.json()["response"]