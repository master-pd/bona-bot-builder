# utils/language.py
import re
from typing import Dict, List, Optional

class LanguageManager:
    
    # Banglish to Bangla mapping
    BANGLISH_TO_BANGLA = {
        # Common words
        "ami": "আমি",
        "tumi": "তুমি",
        "apni": "আপনি",
        "valo": "ভালো",
        "kharap": "খারাপ",
        "achhi": "আছি",
        "acho": "আছো",
        "achen": "আছেন",
        "ki": "কী",
        "kemon": "কেমন",
        "kno": "কেন",
        "kothay": "কোথায়",
        "kokhon": "কখন",
        "ke": "কে",
        "ki kor": "কী কর",
        "ki korch": "কী করছ",
        "ki korchen": "কী করছেন",
        "jan": "জান",
        "jani": "জানি",
        "janno": "জানো",
        "janen": "জানেন",
        "chai": "চাই",
        "chaile": "চাইলে",
        "hoy": "হয়",
        "hoyeche": "হয়েছে",
        "hoyni": "হয়নি",
        "hobe": "হবে",
        "hoyto": "হতে",
        "ache": "আছে",
        "nai": "নাই",
        "nei": "নেই",
        "onek": "অনেক",
        "valo lage": "ভালো লাগে",
        "valo lagena": "ভালো লাগেনা",
        
        # Pronouns
        "amar": "আমার",
        "tomar": "তোমার",
        "apnar": "আপনার",
        "tar": "তার",
        "amader": "আমাদের",
        "tomader": "তোমাদের",
        "apnader": "আপনাদের",
        "tader": "তাদের",
        
        # Common phrases
        "ki obostha": "কী অবস্থা",
        "ki khobor": "কী খবর",
        "kothay achen": "কোথায় আছেন",
        "ki korchen": "কী করছেন",
        "ki jani na": "কী জানি না",
        "thik ache": "ঠিক আছে",
        "kono somossa nai": "কোন সমস্যা নেই",
        "somossa ache": "সমস্যা আছে",
        "valo thakben": "ভালো থাকবেন",
        "allahr rohomot": "আল্লাহর রহমত",
        "inshallah": "ইনশাআল্লাহ",
        "mashallah": "মাশাআল্লাহ",
        "alhamdulillah": "আলহামদুলিল্লাহ",
        
        # Emoticons to Emojis
        ":\)": "😊",
        ":D": "😃",
        ":\(": "😔",
        ";\)": "😉",
        ":P": "😛",
        ":O": "😮",
        ":\|": "😐",
        ":\/": "😕",
        "<3": "❤️",
        ":\*": "😘",
    }
    
    # English to Bangla mapping (simplified)
    ENGLISH_TO_BANGLA = {
        "hello": "হ্যালো",
        "hi": "হাই",
        "how": "কেমন",
        "are": "আছ",
        "you": "তুমি/আপনি",
        "i": "আমি",
        "am": "আছি",
        "good": "ভালো",
        "bad": "খারাপ",
        "what": "কী",
        "why": "কেন",
        "where": "কোথায়",
        "when": "কখন",
        "who": "কে",
        "help": "সাহায্য",
        "need": "দরকার",
        "want": "চাই",
        "thank": "ধন্যবাদ",
        "thanks": "থ্যাঙ্কস",
        "please": "দয়া করে",
        "sorry": "দুঃখিত",
        "yes": "হ্যাঁ",
        "no": "না",
        "ok": "ওকে",
        "okay": "ঠিক আছে",
        "problem": "সমস্যা",
        "solution": "সমাধান",
        "work": "কাজ",
        "not": "না",
        "working": "কাজ করছে",
        "broken": "ভাঙ্গা",
        "fix": "ঠিক করা",
    }
    
    @staticmethod
    def translate(text: str, target_lang: str = "bangla") -> str:
        """Translate text to target language"""
        if target_lang == "bangla":
            return LanguageManager._to_bangla(text)
        elif target_lang == "banglish":
            return LanguageManager._to_banglish(text)
        else:
            return text
    
    @staticmethod
    def _to_bangla(text: str) -> str:
        """Convert Banglish/English mixed text to Bangla"""
        if not text:
            return text
        
        result = text
        
        # Replace emoticons with emojis
        for emoticon, emoji in LanguageManager.BANGLISH_TO_BANGLA.items():
            if emoticon.startswith(":"):
                result = re.sub(re.escape(emoticon), emoji, result, flags=re.IGNORECASE)
        
        # Replace Banglish words
        for banglish, bangla in LanguageManager.BANGLISH_TO_BANGLA.items():
            if not banglish.startswith(":"):
                # Word boundary replacement
                pattern = r'\b' + re.escape(banglish) + r'\b'
                result = re.sub(pattern, bangla, result, flags=re.IGNORECASE)
        
        # Replace common English words
        for english, bangla in LanguageManager.ENGLISH_TO_BANGLA.items():
            pattern = r'\b' + re.escape(english) + r'\b'
            result = re.sub(pattern, bangla, result, flags=re.IGNORECASE)
        
        return result
    
    @staticmethod
    def _to_banglish(text: str) -> str:
        """Convert Bangla text to Banglish (simplified)"""
        # This is a simplified version
        # Full Bangla to Banglish conversion would need more complex logic
        return text
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Detect language of text"""
        if not text:
            return "unknown"
        
        # Check for Bangla Unicode range
        bangla_pattern = r'[\u0980-\u09FF]'
        if re.search(bangla_pattern, text):
            return "bangla"
        
        # Check for English
        english_pattern = r'[a-zA-Z]'
        if re.search(english_pattern, text):
            # Check if it's Banglish (mixed)
            banglish_words = list(LanguageManager.BANGLISH_TO_BANGLA.keys())
            for word in text.lower().split():
                if word in banglish_words:
                    return "banglish"
            return "english"
        
        return "unknown"
    
    @staticmethod
    def is_bangla(text: str) -> bool:
        """Check if text contains Bangla characters"""
        bangla_pattern = r'[\u0980-\u09FF]'
        return bool(re.search(bangla_pattern, text))
    
    @staticmethod
    def is_english(text: str) -> bool:
        """Check if text is English"""
        # Remove spaces and special chars
        clean_text = re.sub(r'[^a-zA-Z]', '', text)
        return len(clean_text) > 0 and not LanguageManager.is_bangla(text)
    
    @staticmethod
    def is_banglish(text: str) -> bool:
        """Check if text is Banglish"""
        if LanguageManager.is_bangla(text):
            return False
        
        # Check for common Banglish words
        words = text.lower().split()
        banglish_count = 0
        
        for word in words:
            if word in LanguageManager.BANGLISH_TO_BANGLA:
                banglish_count += 1
        
        # If more than 30% words are Banglish, consider it Banglish
        if len(words) > 0 and (banglish_count / len(words)) > 0.3:
            return True
        
        return False
    
    @staticmethod
    def get_supported_languages() -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return [
            {"code": "bangla", "name": "বাংলা", "emoji": "🇧🇩"},
            {"code": "banglish", "name": "বাংলিশ", "emoji": "🌐"},
            {"code": "english", "name": "English", "emoji": "🇺🇸"}
        ]
    
    @staticmethod
    def format_message(text: str, language: str = "banglish") -> str:
        """Format message for specific language"""
        translated = LanguageManager.translate(text, language)
        
        # Add appropriate emojis based on content
        if "ধন্যবাদ" in translated or "thank" in text.lower():
            translated += " 🙏"
        elif "সমস্যা" in translated or "problem" in text.lower():
            translated += " 🔧"
        elif "সাহায্য" in translated or "help" in text.lower():
            translated += " 🤝"
        elif "ভালো" in translated or "good" in text.lower():
            translated += " 😊"
        elif "খারাপ" in translated or "bad" in text.lower():
            translated += " 😔"
        
        return translated