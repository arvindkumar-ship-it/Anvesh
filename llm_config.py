# import re
# import time
# from litellm import completion

# # Define your default models
# PRIMARY_MODEL = "gemini/gemini-2.5-flash" # Or whichever Gemini you are using
# FALLBACK_MODEL = "groq/llama-3.3-70b-versatile"       # Your Groq fallback

# def get_llm_response(prompt, model=PRIMARY_MODEL, **kwargs):
#     """
#     Core function to call the LLM. 
#     Handles extraction safely and automatically falls back to Groq on 429 Quota errors.
#     """
#     try:
#         # Using litellm's completion
#         response = completion(
#             model=model,
#             messages=[{"role": "user", "content": prompt}],
#             **kwargs
#         )

#         # Safely extract content (Fixes the Pylance 'choices' attribute error)
#         choices = getattr(response, 'choices', None)
        
#         if choices is not None and len(choices) > 0:
#             return choices[0].message.content
            
#         return str(response)

#     except Exception as e:
#         err = str(e).lower()
        
#         # 2. DETECT QUOTA LIMITS (429)
#         if any(x in err for x in ["rate_limit", "429", "quota", "limit exceeded"]):
            
#             # Extract wait time if provider gives it, else default to 60.0s
#             match = re.search(r'try again in ([0-9.]+)\s*s', err)
#             wait_time = float(match.group(1)) if match else 60.0
            
#             print(f"\n[!] Quota Exceeded on {model}.")
            
#             # THE SILENT SWITCH: If Gemini fails, immediately try Groq
#             if model != FALLBACK_MODEL:
#                 print(f"[*] Silently switching to fallback: {FALLBACK_MODEL}...")
#                 return get_llm_response(prompt, model=FALLBACK_MODEL, **kwargs)
#             else:
#                 # If even the fallback fails (rare), then we wait
#                 print(f"[!] Fallback also hit limits. Sleeping for {wait_time} seconds...")
#                 time.sleep(wait_time)
#                 return get_llm_response(prompt, model=FALLBACK_MODEL, **kwargs)
        
#         # If it's a different kind of error (not a quota issue), raise it normally
#         raise e



import logging
logging.getLogger('LiteLLM').setLevel(logging.CRITICAL)



import re
import time
from litellm import completion

# Models Define kar rahe hain (Tu yahan apne hisaab se add kar sakta hai)
M1 = "gemini/gemini-2.5-flash"
M2 = "groq/llama-3.3-70b-versatile"
M3 = "groq/llama-3.1-8b-instant"
M4 = "groq/openai/gpt-oss-120b"

def get_llm_response(prompt, model=M1, max_attempts=4, **kwargs):
    """Try each configured fallback once. Exhaustion is an explicit failure."""
    if not 1 <= max_attempts <= 4:
        raise ValueError("max_attempts must be between 1 and 4")
    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = []
        for message in prompt:
            if hasattr(message, "content"):
                kind = getattr(message, "type", "")
                role = "system" if kind == "system" or "System" in type(message).__name__ else "assistant" if kind == "ai" or "AI" in type(message).__name__ else "user"
                messages.append({"role": role, "content": message.content})
            else:
                messages.append(message)
    models = [M1, M2, M3, M4]
    attempts = models[models.index(model):] if model in models else [model]
    options = dict(kwargs)
    options.setdefault("timeout", 30)
    last_error = None
    for candidate in attempts[:max_attempts]:
        try:
            response = completion(model=candidate, messages=messages, **options)
            choices = getattr(response, "choices", None)
            if not choices or not isinstance(choices[0].message.content, str) or not choices[0].message.content.strip():
                raise ValueError("Provider returned no usable text")
            return choices[0].message.content
        except Exception as error:
            last_error = error
            status = getattr(error, "status_code", None)
            text = str(error).lower()
            retryable = status in {429, 500, 502, 503, 504} or any(marker in text for marker in ("rate_limit", "429", "quota", "503", "unavailable"))
            if not retryable:
                raise
    raise RuntimeError("All configured model attempts failed") from last_error
