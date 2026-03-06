from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Chat
from django.conf import settings
import google.generativeai as genai
import requests
import json
import os

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-r1:1.5b")

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or getattr(settings, 'GEMINI_API_KEY', None)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash')
else:
    gemini_model = None

SYSTEM_PROMPT = "You are a neurology medical assistant. Only answer questions related to neurology such as brain disorders, nervous system diseases, symptoms, and treatments. If the question is unrelated politely refuse. Keep your answers concise and professional."

def get_medical_image(response_text):
    keywords = {
        "stroke": "stroke.png",
        "epilepsy": "epilepsy.png",
        "parkinson": "parkinson.png",
        "tumor": "brain_tumor.png",
        "alzheimer": "alzheimer.png"
    }
    for key, img in keywords.items():
        if key in response_text.lower():
            return f"/static/images/{img}"
    return None

@login_required
def home(request):
    chats = Chat.objects.filter(user=request.user).order_by('timestamp')
    return render(request, "chatbot/index.html", {"chats": chats})

@login_required
def chat_view(request):
    if request.method == "POST":
        user_message = request.POST.get("message")
        provider = request.POST.get("provider", "ollama") # Default to ollama
        
        if not user_message:
            return JsonResponse({"error": "No message provided"}, status=400)

        try:
            if provider == "gemini":
                if not gemini_model:
                    return JsonResponse({"error": "Gemini API key not configured."}, status=500)
                full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_message}"
                response = gemini_model.generate_content(full_prompt)
                bot_response = response.text
            else:
                # Use Ollama
                payload = {
                    "model": OLLAMA_MODEL,
                    "prompt": f"{SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:",
                    "stream": False
                }
                response = requests.post(OLLAMA_URL, json=payload, timeout=30)
                response.raise_for_status()
                response_data = response.json()
                bot_response = response_data.get("response", "Sorry, I encountered an error.")

            # Save to database
            Chat.objects.create(user=request.user, message=user_message, response=bot_response)

            image_url = get_medical_image(bot_response)

            return JsonResponse({
                "response": bot_response,
                "image_url": image_url
            })
        except Exception as e:
            return JsonResponse({"error": f"{provider.capitalize()} Error: {str(e)}"}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)
