from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
from dotenv import load_dotenv
import os
from e2b_code_interpreter import Sandbox

load_dotenv()

app = FastAPI()

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        try:
            payload = json.loads(data)
            code = payload.get("code", "")
            language = payload.get("language", "")
            if language == "python":
                try:
                    sbx = Sandbox(api_key=os.getenv("E2B_API_KEY"))
                    execution = sbx.run_code(code)
                    stdout = ''
                    stderr = ''
                    if hasattr(execution, 'logs'):
                        logs = execution.logs
                        print("this is logs:", logs)
                        if isinstance(logs, dict):
                            # E2B returns dict with 'stdout' and 'stderr' as lists
                            stdout = ''.join(logs.get('stdout', [])) if isinstance(logs.get('stdout', []), list) else str(logs.get('stdout', ''))
                            stderr = ''.join(logs.get('stderr', [])) if isinstance(logs.get('stderr', []), list) else str(logs.get('stderr', ''))
                        elif hasattr(logs, 'stdout') or hasattr(logs, 'stderr'):
                            # E2B may return object with 'stdout'/'stderr' attributes
                            stdout = getattr(logs, 'stdout', '')
                            stderr = getattr(logs, 'stderr', '')
                        elif isinstance(logs, str):
                            stdout = logs
                    response_obj = {"output": stdout, "error": stderr}
                except Exception as e:
                    response_obj = {"output": "", "error": str(e)}
                response = json.dumps(response_obj)
            elif language == "javascript":
                response = "JavaScript execution not implemented yet."
            else:
                response = f"Unsupported language: {language}"
        except Exception as e:
            response = f"Error parsing message: {e}"
        await websocket.send_text(response)