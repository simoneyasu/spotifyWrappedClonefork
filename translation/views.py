from django.http import JsonResponse
from deep_translator import GoogleTranslator
import json
'''
Uses Google Translate API to translate entire web application

param: HTTPRequest

return: JSONResponse including the translated text
'''
def translate_text(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        texts = data.get('text', [])
        target_language = data.get('target', 'en')

        try:
            translated_texts = [
                GoogleTranslator(source='auto', target=target_language).translate(text)
                for text in texts
            ]
            return JsonResponse({"translatedTexts": translated_texts})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)