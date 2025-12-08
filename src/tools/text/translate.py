from tools.decorator import tool
from translate import Translator

@tool(
    name="translate_text",
    description="Translate text from one language to another.",
    category="text"
)
def translate_text(text: str, source_lang: str, target_lang: str) -> dict:
    try:
        translator = Translator(from_lang=source_lang, to_lang=target_lang)
        translated_text = translator.translate(text)
        return {
            "original_text": text,
            "translated_text": translated_text,
            "source_language": source_lang,
            "target_language": target_lang
        }
    except Exception as e:
        return {"error": str(e)}