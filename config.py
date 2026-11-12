"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY HINDI"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "HINDI"
HANDLE = "@velocityhindi"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'hi',
 'name': 'Hindi',
 'native_name': 'हिन्दी',
 'history_key': 'hindi',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'hi-IN-SwaraNeural',
 'native_fallback_voice': 'hi-IN-MadhurNeural',
 'native_engine': 'edge',
 'native_lang_code': 'hi',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'हिन्दी',
 'translit_label': 'ROMANIZED',
 'flag': 'in',
 'greeting': 'नमस्ते!',
 'encouragement': 'शानदार!',
 'rtl': False,
 'char_tiles': False,
 'script_font': 'Script.ttf',
 'glyphs': 'अआइईउऊएऐओऔकखगघचछजझटठडढतथदधनपफबभमयरलवशषसह'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'प्रेरणा',
 'Love': 'प्यार',
 'Success': 'सफलता',
 'Wisdom': 'ज्ञान',
 'Happiness': 'खुशी',
 'Self Improvement': 'आत्मसुधार',
 'Gratitude': 'कृतज्ञता',
 'Friendship': 'दोस्ती',
 'Hope': 'आशा',
 'Creativity': 'रचनात्मकता',
 'Inner Peace': 'आंतरिक शांति',
 'Confidence': 'आत्मविश्वास',
 'Perseverance': 'दृढ़ता',
 'Inspiration': 'प्रेरणा',
 'Positive Life': 'सकारात्मक जीवन',
 'Courage': 'साहस',
 'Kindness': 'दया',
 'Patience': 'धैर्य',
 'Forgiveness': 'क्षमा',
 'Strength': 'ताकत',
 'Joy': 'आनंद',
 'Balance': 'संतुलन',
 'Growth': 'विकास',
 'Purpose': 'उद्देश्य',
 'Mindfulness': 'सावधानता',
 'Travel & Airport': 'यात्रा और हवाई अड्डा',
 'Ordering Food & Dining': 'खाना ऑर्डर करना और भोजन',
 'Shopping & Prices': 'खरीदारी और कीमतें',
 'Asking for Directions': 'रास्ता पूछना',
 'Hotel & Accommodation': 'होटल और आवास',
 'Daily Routine': 'दैनिक दिनचर्या',
 'Meeting People & Greetings': 'लोगों से मिलना और अभिवादन',
 'Emergency & Health': 'आपातकाल और स्वास्थ्य',
 'Public Transportation': 'सार्वजनिक परिवहन',
 'Work & Office': 'काम और कार्यालय',
 'Weather & Small Talk': 'मौसम और सामान्य बातचीत',
 'Coffee Shop & Bakery': 'कॉफी शॉप और बेकरी',
 'Family & Home': 'परिवार और घर',
 'Hobbies & Free Time': 'शौक और खाली समय',
 'Dating & Romance': 'डेटिंग और रोमांस',
 'Phone Calls & Messages': 'फोन कॉल और संदेश',
 'Banking & Money': 'बैंकिंग और पैसा',
 'Doctor & Pharmacy': 'डॉक्टर और फार्मेसी',
 'Sports & Fitness': 'खेल और फिटनेस',
 'Celebrations & Parties': 'उत्सव और पार्टियाँ',
 'Feelings & Emotions': 'भावनाएँ और अहसास',
 'Agreeing & Disagreeing': 'सहमत होना और असहमत होना',
 'Making Plans': 'योजनाएँ बनाना',
 'Common Native Slang': 'आम स्थानीय बोलचाल',
 'Cultural Traditions': 'सांस्कृतिक परंपराएँ'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnhindi',
 '#hindilessons',
 '#hindiforbeginners',
 '#languagelearning',
 '#hindivocabulary',
 '#velocityhindi',
 '#dailyhindi',
 '#hindi',
 '#learnlanguages',
 '#speakhindi']
# ==== HASHTAGS END ====
