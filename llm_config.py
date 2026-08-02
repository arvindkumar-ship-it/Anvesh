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

def get_llm_response(prompt, model=M1, **kwargs):
    """
    Core function to call the LLM. 
    Handles extraction safely and automatically falls back through 5 models on 429 Quota errors.
    """
    if isinstance(prompt, str):
        msgs = [{"role": "user", "content": prompt}]
    else:
        # Agar prompt pehle se list hai (LangChain objects ya dicts), 
        # toh use safely dict mein convert karo
        msgs = []
        for m in prompt:
            if hasattr(m, 'content'): # LangChain object check
                role = "system" if "System" in str(type(m)) else "user"
                if "AI" in str(type(m)): role = "assistant"
                msgs.append({"role": role, "content": m.content})
            else:
                msgs.append(m)
    try:
        # Using litellm's completion (Wahi purana logic)
        response = completion(
            model=model,
            messages=msgs,
            **kwargs
        )

        # Safely extract content
        choices = getattr(response, 'choices', None)
        
        if choices is not None and len(choices) > 0:
            return choices[0].message.content
            
        return str(response)

    except Exception as e:
        err = str(e).lower()
        
        # 2. DETECT QUOTA LIMITS (429)
        if any(x in err for x in ["rate_limit", "429", "quota", "limit exceeded", "503", "unavailable", "demand"]):
            
            # Extract wait time if provider gives it, else default to 60.0s
            match = re.search(r'try again in ([0-9.]+)\s*s', err)
            wait_time = float(match.group(1)) if match else 60.0
            
            print(f"\n[!] Quota Exceeded on {model}.")
            
            # THE HIERARCHY SWITCH (Recursive Fallback)
            # Yahan se hum agle model par jump karenge
            if model == M1:
                print(f"[*] Switching to fallback 1: {M2}...")
                return get_llm_response(prompt, model=M2, **kwargs)
            
            elif model == M2:
                print(f"[*] Switching to fallback 2: {M3}...")
                return get_llm_response(prompt, model=M3, **kwargs)
                
            elif model == M3:
                print(f"[*] Switching to fallback 3: {M4}...")
                return get_llm_response(prompt, model=M4, **kwargs)

            # elif model == M4:
            #     print(f"[*] Switching to fallback 4: {M5}...")
            #     return get_llm_response(prompt, model=M5, **kwargs)
            
            else:
                # Agar saare (M5 tak) fail ho gaye, tabhi sleep karega
                print(f"[!] ALL models hit limits. Sleeping for {wait_time} seconds before reset...")
                time.sleep(wait_time)
                return get_llm_response(prompt, model=M1, **kwargs) # Restart from M1
        
        # If it's a different kind of error, raise it normally
        raise e
    