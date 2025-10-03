"""
ollama_client.py
- Simple helper to call a local Ollama instance for text generation.
- Ollama default HTTP endpoint is: http://localhost:11434
- Requires Ollama to be installed & a model pulled (e.g., "llama3", "mistral-7b", etc.)
"""
import requests, json, os, time

OLLAMA_URL = os.environ.get("OLLAMA_URL","http://localhost:11434")

def is_ollama_available(timeout: float=1.0) -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/v1/models", timeout=timeout)
        return r.status_code==200
    except Exception:
        return False

def ollama_model_client(prompt: str, model: str="llama3", max_tokens:int=512, temperature:float=0.2) -> str:
    """
    Calls Ollama text generation API and returns text. Raises exceptions on errors.
    """
    url = f"{OLLAMA_URL}/v1/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    headers = {"Content-Type":"application/json"}
    r = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
    if r.status_code!=200:
        raise RuntimeError(f"Ollama API error {r.status_code}: {r.text}")
    data = r.json()
    # Ollama returns generations list
    gen = data.get("content") or data.get("generations") or data
    # best-effort to extract text
    if isinstance(gen, str):
        return gen
    if isinstance(gen, dict) and "text" in gen:
        return gen["text"]
    if isinstance(gen, list) and len(gen)>0:
        # join pieces
        return " ".join([g.get("text", str(g)) for g in gen])
    return str(data)
