from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Chat
import requests
import json
import os

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-r1:1.5b")

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
        if not user_message:
            return JsonResponse({"error": "No message provided"}, status=400)

        try:
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
            return JsonResponse({"error": f"Ollama Error: {str(e)}"}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)
