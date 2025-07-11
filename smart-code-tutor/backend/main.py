from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
from dotenv import load_dotenv
import os
from e2b_code_interpreter import Sandbox
from rag_engine import retrieve_relevant_docs, generate_explanation
from langchain_groq import ChatGroq
from pydantic.types import SecretStr

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

def execute_code(code, language):
    output = ""
    error = ""
    try:
        if language == "python":
            sbx = Sandbox(api_key=os.getenv("E2B_API_KEY"))
            execution = sbx.run_code(code)
        elif language == "javascript":
            sbx = Sandbox(api_key=os.getenv("E2B_API_KEY"))
            execution = sbx.run_code(code, language="js")
        elif language == "typescript":
            sbx = Sandbox(api_key=os.getenv("E2B_API_KEY"))
            execution = sbx.run_code(code, language="ts")
        else:
            return "", f"Unsupported language: {language}"
        if hasattr(execution, 'logs'):
            logs = execution.logs
            if isinstance(logs, dict):
                output = ''.join(logs.get('stdout', [])) if isinstance(logs.get('stdout', []), list) else str(logs.get('stdout', ''))
                error = ''.join(logs.get('stderr', [])) if isinstance(logs.get('stderr', []), list) else str(logs.get('stderr', ''))
            elif hasattr(logs, 'stdout') or hasattr(logs, 'stderr'):
                output = getattr(logs, 'stdout', '')
                error = getattr(logs, 'stderr', '')
            elif isinstance(logs, str):
                output = logs
    except Exception as e:
        error = str(e)
    return output, error

# --- Intent Detection and Routing ---

def detect_intent(user_message: str, groq_api_key: str) -> str:
    """Use LLM to classify the user message intent."""
    llm = ChatGroq(api_key=SecretStr(groq_api_key), model="meta-llama/llama-4-scout-17b-16e-instruct")
    prompt = f"""
Classify the following user message as one of: 'generate', 'explain', 'modify', 'debug', or 'other'.
Respond with only the label.
Message: {user_message}
"""
    result = llm.invoke(prompt)
    label = str(getattr(result, 'content', result)).strip().lower()
    return label

def route_llm_response(intent: str, code: str, output: str, error: str, user_message: str, groq_api_key: str):
    # Retrieve relevant docs for all intents
    query = user_message or error or code
    retrieved_docs = retrieve_relevant_docs(query, top_k=3)
    docs_text = '\n'.join(retrieved_docs) if retrieved_docs else ''
    llm = ChatGroq(api_key=SecretStr(groq_api_key), model="meta-llama/llama-4-scout-17b-16e-instruct")
    if intent == 'generate':
        prompt = f"""
You are a helpful coding assistant. Write code as per the following request:
Request: {user_message}
Relevant Documentation:
{docs_text}
Provide only the code, with a brief explanation in markdown if needed.
"""
    elif intent == 'explain':
        prompt = f"""
Code breakdown:
You are a code tutor. Explain the following code in detail:
Code:
{code}
Relevant Documentation:
{docs_text}
"""
    elif intent == 'modify':
        prompt = f"""
You are a helpful coding assistant. Update the following code as per the user's request.
Request: {user_message}
Code:
{code}
Relevant Documentation:
{docs_text}
Provide only the updated code, with a brief explanation in markdown if needed.
"""
    elif intent == 'debug':
        prompt = f"""
You are a code assistant. Given the code and error below, suggest a fix and explain the issue.
Code:
{code}
Error:
{error}
Output:
{output}
Relevant Documentation:
{docs_text}
"""
    else:
        prompt = f"""
You are a helpful coding assistant. Answer the following user question:
{user_message}
Relevant Documentation:
{docs_text}
"""
    result = llm.invoke(prompt)
    return str(getattr(result, 'content', result))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        try:
            payload = json.loads(data)
            action = payload.get("action", "run")  # default to 'run' for backward compatibility
            code = payload.get("code", "")
            language = payload.get("language", "")
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                response = json.dumps({"error": "GROQ_API_KEY is not set in the backend environment."})
                await websocket.send_text(response)
                continue
            if action == "run":
                output, error = execute_code(code, language)
                response_obj = {"output": output, "error": error}
            elif action == "explain":
                output = payload.get("output", "")
                error = payload.get("error", "")
                user_message = payload.get("user_message", "")
                # 1. Detect intent
                intent = detect_intent(user_message, groq_api_key)
                # 2. Route to correct LLM prompt
                explanation = route_llm_response(intent, code, output, error, user_message, groq_api_key)
                response_obj = {"explanation": explanation, "intent": intent}
            else:
                response_obj = {"error": f"Unknown action: {action}"}
            response = json.dumps(response_obj)
        except Exception as e:
            response = json.dumps({"output": "", "error": str(e)})
        await websocket.send_text(response)