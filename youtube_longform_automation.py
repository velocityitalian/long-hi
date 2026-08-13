"""
YouTube Long-Form Video Automation - Bilingual English/Hindi Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 15  # Target ~15-minute videos (~170 phrases)
TARGET_PHRASES = 170  # Number of phrases to generate

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Hindi translations (Devanagari script)
CATEGORIES_HINDI = {
    "Motivation": "प्रेरणा",
    "Love": "प्यार",
    "Success": "सफलता",
    "Wisdom": "ज्ञान",
    "Happiness": "खुशी",
    "Self Improvement": "आत्मसुधार",
    "Gratitude": "कृतज्ञता",
    "Friendship": "दोस्ती",
    "Hope": "आशा",
    "Creativity": "रचनात्मकता",
    "Inner Peace": "आंतरिक शांति",
    "Confidence": "आत्मविश्वास",
    "Perseverance": "दृढ़ता",
    "Inspiration": "प्रेरणा",
    "Positive Life": "सकारात्मक जीवन",
    "Courage": "साहस",
    "Kindness": "दया",
    "Patience": "धैर्य",
    "Forgiveness": "क्षमा",
    "Strength": "ताकत",
    "Joy": "आनंद",
    "Balance": "संतुलन",
    "Growth": "विकास",
    "Purpose": "उद्देश्य",
    "Mindfulness": "सावधानता",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "hi-IN-SwaraNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    """Add new phrases to history (deduplicated)"""
    history = load_phrase_history()
    existing = {p.get("english", "").lower().strip() for p in history.get("phrases", [])}
    added = 0
    for phrase in phrases:
        key = phrase.get("english", "").lower().strip()
        if not key or key in existing:
            continue
        existing.add(key)
        history["phrases"].append({
            "english": phrase["english"],
            "hindi": phrase["hindi"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
        added += 1
    save_phrase_history(history)
    print(f"[history] Added {added} unique phrases to history (total: {len(history['phrases'])})")

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_hindi = CATEGORIES_HINDI[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Hindi.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - STRICTLY ENFORCE:
The "english" field must contain PURE ENGLISH words only. ZERO Hindi/Devanagari.
The "hindi" field contains the Hindi translation in Devanagari script.
The "pronunciation" field is phonetic English spelling.

WRONG (mixed language): {{"english": "Apna sapna sach karo, believe in yourself", ...}}
WRONG (Hindi in english): {{"english": "Follow your sapne and success will come", ...}}
CORRECT: {{"english": "Make your dreams come true, believe in yourself.", "hindi": "अपने सपने सच करो, खुद पर विश्वास करो।", "pronunciation": "ap-ne sap-ne sach ka-ro, khud par vi-shwas ka-ro."}}
CORRECT: {{"english": "Follow your dreams and success will come.", "hindi": "अपने सपनों का पालन करो और सफलता आएगी।", "pronunciation": "ap-ne sap-non ka paa-lan ka-ro aur saf-al-taa aa-e-gi."}}

The english field MUST be 100% English words only. NO Hindi words allowed.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Hindi) with commas for natural pauses
2. Hindi translation (Devanagari script only)
3. Pronunciation guide (phonetic English spelling)
CRITICAL: Every translation MUST be in Hindi. NEVER use German, Spanish, or any other language. Only Hindi.

Return as JSON array:
[{{"english": "...", "hindi": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a viral Hindi teacher. CRITICAL: The 'english' field must contain PURE ENGLISH words ONLY. NO Hindi/Devanagari in english field. Hindi goes in the 'hindi' field. This is strictly enforced."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)
                # Filter by similarity against history AND phrases already
                # collected in THIS run (prevents same-run duplicates)
                filtered_phrases = filter_similar_phrases(phrases, history)
                filtered_phrases = filter_similar_phrases(
                    filtered_phrases, {"phrases": [{"english": p["english"]} for p in all_phrases]},
                    similarity_threshold=0.7)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "hindi": "अपने आप पर विश्वास करो।", "pronunciation": "ap-ne aap par vish-waas ka-ro."},
            {"english": "You are capable of amazing things.", "hindi": "आप अद्भुत चीज़ों में सक्षम हैं।", "pronunciation": "aap ad-bhut chee-zon mein sak-sham hain."},
            {"english": "Dream big, start small.", "hindi": "बड़े सपने देखो, छोटे से शुरू करो।", "pronunciation": "ba-de sap-ne de-kho, chho-te se shu-ru ka-ro."},
            {"english": "Your future is created by your actions.", "hindi": "आपका भविष्य आपके कर्मों से बनता है।", "pronunciation": "aap-ka bha-vish-y aap-ke kar-mon se ban-ta hai."},
            {"english": "Never give up on your dreams.", "hindi": "अपने सपनों का पीछा कभी मत छोड़ो।", "pronunciation": "ap-ne sap-non ka pee-chha ka-bhi mat chho-ro."},
            {"english": "Small steps lead to big changes.", "hindi": "छोटे कदम बड़े बदलाव लाते हैं।", "pronunciation": "chho-te ka-dam ba-de bad-laa-va laa-te hain."},
            {"english": "You are stronger than you think.", "hindi": "आप जितना सोचते हैं उससे ज़्यादा मज़बूत हैं।", "pronunciation": "aap jit-na soch-te hain us-se zya-da maz-boot hain."},
        ],
        "Love": [
            {"english": "Love yourself first.", "hindi": "पहले खुद से प्यार करो।", "pronunciation": "pah-le khud se pyaar ka-ro."},
            {"english": "Love makes everything possible.", "hindi": "प्यार सब कुछ संभव बनाता है।", "pronunciation": "pyaar sab kuch samb-hav ba-na-ta hai."},
            {"english": "My heart beats for you.", "hindi": "मेरा दिल तुम्हारे लिए धड़कता है।", "pronunciation": "me-ra dil tum-ha-re li-ye dha-dak-ta hai."},
            {"english": "You are my everything.", "hindi": "तुम मेरे सब कुछ हो।", "pronunciation": "tum me-re sab kuch ho."},
            {"english": "Together forever, hand in hand.", "hindi": "हमेशा साथ, हाथ में हाथ।", "pronunciation": "ha-me-sha saath, haath mein haath."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "hindi": "सफलता कड़ी मेहनत से आती है।", "pronunciation": "saf-al-ta ka-ri meh-nat se aa-ti hai."},
            {"english": "Keep going, you're getting there.", "hindi": "लगे रहो, तुम वहाँ पहुँच रहे हो।", "pronunciation": "la-ge ra-ho, tum vahan pahunch ra-he ho."},
            {"english": "Winners never quit.", "hindi": "विजेता कभी हार नहीं मानते।", "pronunciation": "vi-je-ta ka-bhi haar na-hi maan-te."},
            {"english": "Your effort will pay off.", "hindi": "तुम्हारी मेहनत रंग लाएगी।", "pronunciation": "tum-ha-ri meh-nat rang laa-e-gi."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "hindi": "ज्ञान शक्ति है।", "pronunciation": "gyaan shak-ti hai."},
            {"english": "Learn from yesterday, live for today.", "hindi": "कल से सीखो, आज के लिए जियो।", "pronunciation": "kal se see-kho, aaj ke li-ye ji-yo."},
            {"english": "Think before you act.", "hindi": "करने से पहले सोचो।", "pronunciation": "kar-ne se pah-le so-cho."},
            {"english": "Experience is the best teacher.", "hindi": "अनुभव सबसे अच्छा शिक्षक है।", "pronunciation": "a-nu-bhav sab-se ach-chha shik-shak hai."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "hindi": "खुशी एक विकल्प है।", "pronunciation": "khu-shi ek vi-kalp hai."},
            {"english": "Find joy in the little things.", "hindi": "छोटी चीज़ों में खुशी ढूँढो।", "pronunciation": "chho-ti chee-zon mein khu-shi dhoondho."},
            {"english": "Smile, it makes others happy.", "hindi": "मुस्कुराओ, इससे दूसरे खुश होते हैं।", "pronunciation": "mus-ku-ra-o, is-se doo-sre khush ho-te hain."},
            {"english": "Today is a gift.", "hindi": "आज एक उपहार है।", "pronunciation": "aaj ek up-haar hai."},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "hindi": "कल से बेहतर बनो।", "pronunciation": "kal se be-hat ban-no."},
            {"english": "Grow through what you go through.", "hindi": "जो तुम गुज़रते हो, उससे बढ़ो।", "pronunciation": "jo tum gu-zar-te ho, us-se badho."},
            {"english": "Invest in yourself daily.", "hindi": "रोज़ अपने आप में निवेश करो।", "pronunciation": "roj ap-ne aap mein ni-vesh ka-ro."},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "hindi": "हर चीज़ के लिए धन्यवाद।", "pronunciation": "har cheez ke li-ye dha-nya-vaad."},
            {"english": "I appreciate your help.", "hindi": "मैं आपकी मदद की सराहना करता हूँ।", "pronunciation": "main aap-ki ma-dad ki sa-ráh-na kar-ta hoon."},
            {"english": "Grateful for this moment.", "hindi": "इस पल के लिए आभारी हूँ।", "pronunciation": "is pal ke li-ye aab-ha-ri hoon."},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "hindi": "हमेशा दोस्त, चाहे कुछ भी हो।", "pronunciation": "ha-me-sha dost, cha-he kuch bhi ho."},
            {"english": "You are my best friend.", "hindi": "तुम मेरे सबसे अच्छे दोस्त हो।", "pronunciation": "tum me-re sab-se ach-che dost ho."},
            {"english": "True friends stick together.", "hindi": "सच्चे दोस्त हमेशा साथ रहते हैं।", "pronunciation": "sach-che dost ha-me-sha saath rah-te hain."},
        ],
        "Hope": [
            {"english": "There is always hope.", "hindi": "हमेशा उम्मीद होती है।", "pronunciation": "ha-me-sha um-meed ho-ti hai."},
            {"english": "Better days are coming.", "hindi": "बेहतर दिन आ रहे हैं।", "pronunciation": "be-hat din aa ra-he hain."},
            {"english": "Keep faith, keep going.", "hindi": "विश्वास रखो, लगे रहो।", "pronunciation": "va-shwas rak-kho, la-ge ra-ho."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "hindi": "आज कुछ सुंदर बनाओ।", "pronunciation": "aaj kuch sun-dar ba-nao."},
            {"english": "Your imagination is unlimited.", "hindi": "तुम्हारी कल्पना असीमित है।", "pronunciation": "tum-ha-ri kalp-na a-si-mit hai."},
            {"english": "Art comes from the heart.", "hindi": "कला दिल से आती है।", "pronunciation": "kala dil se aa-ti hai."},
            {"english": "Express yourself freely.", "hindi": "खुद को स्वतंत्र रूप से अभिव्यक्त करो।", "pronunciation": "khud ko sva-tantr roop se a-bhi-vyakt karo."},
            {"english": "Innovation starts with curiosity.", "hindi": "नवाचार जिज्ञासा से शुरू होता है।", "pronunciation": "na-va-char jig-ya-sa se shu-ru ho-ta hai."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "hindi": "अपने अंदर शांति ढूँढो।", "pronunciation": "ap-ne an-dar shan-ti dhoondho."},
            {"english": "Breathe, relax, let go.", "hindi": "साँस लो, आराम करो, छोड़ दो।", "pronunciation": "saans lo, a-raam karo, chhod do."},
            {"english": "Calm mind, happy heart.", "hindi": "शांत मन, खुश दिल।", "pronunciation": "shant man, khush dil."},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "hindi": "तुम काफ़ी हो, जैसे भी हो।", "pronunciation": "tum ka-fi ho, jai-se bhi ho."},
            {"english": "Stand tall, speak up.", "hindi": "सीधे खड़े रहो, बोलो।", "pronunciation": "see-dhe kha-de ra-ho, bo-lo."},
            {"english": "Believe in your abilities.", "hindi": "अपनी क्षमताओं पर विश्वास करो।", "pronunciation": "ap-ni ksha-ma-ta-o par va-shwas karo."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "hindi": "कभी हार मत मानो, धक्का देते रहो।", "pronunciation": "ka-bhi haar mat ma-no, dhak-kaa de-te ra-ho."},
            {"english": "Storms make trees take deeper roots.", "hindi": "तूफ़ान पेड़ों की जड़ें गहरी करते हैं।", "pronunciation": "too-faan pe-don ki ja-den ge-hi kar-te hain."},
            {"english": "Patience and persistence win.", "hindi": "धैर्य और दृढ़ता जीतते हैं।", "pronunciation": "dhairy aur dreedh-ta jeet-te hain."},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "hindi": "अपनी रोशनी को चमकने दो।", "pronunciation": "ap-ni rosh-ni ko cha-mak-ne do."},
            {"english": "Inspire others by your actions.", "hindi": "अपने कामों से दूसरों को प्रेरित करो।", "pronunciation": "ap-ne ka-mon se doo-sron ko pre-rit karo."},
            {"english": "Be the change you want to see.", "hindi": "वह बदलाव बनो जो तुम देखना चाहते हो।", "pronunciation": "vah bad-laa-v bano jo tum dekh-na chah-te ho."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "hindi": "हर दिन सकारात्मकता चुनो।", "pronunciation": "har din sa-ka-raat-ma-ta chuno."},
            {"english": "Good vibes only.", "hindi": "केवल अच्छी ऊर्जा।", "pronunciation": "ke-val ach-chhi oor-ja."},
            {"english": "Life is what you make it.", "hindi": "जीवन वही है जो तुम बनाते हो।", "pronunciation": "jee-van va-hi hai jo tum ba-na-te ho."},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "hindi": "बहादुर बनो, पहला कदम उठाओ।", "pronunciation": "ba-haa-dur bano, pah-la ka-dam utha-o."},
            {"english": "Courage is not the absence of fear.", "hindi": "साहस का मतलब डर का न होना नहीं है।", "pronunciation": "saa-has ka mat-lab dar ka na ho-na nahi hai."},
            {"english": "Face your fears head on.", "hindi": "अपने डर का सामना करो।", "pronunciation": "ap-ne dar ka saa-mna karo."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "hindi": "हर किसी के प्रति दयालु बनो।", "pronunciation": "har ki-si ke prati da-yaa-lu bano."},
            {"english": "Kindness costs nothing, means everything.", "hindi": "दयालुता की कोई कीमत नहीं, लेकिन यह सब कुछ है।", "pronunciation": "da-yaa-lu-ta ki koi kim-mat nahi, le-kin yah sab kuch hai."},
            {"english": "Spread kindness wherever you go.", "hindi": "जहाँ भी जाओ, दयालुता फैलाओ।", "pronunciation": "jahan bhi jao, da-yaa-lu-ta phai-lao."},
        ],
        "Patience": [
            {"english": "Good things take time.", "hindi": "अच्छी चीज़ों में समय लगता है।", "pronunciation": "ach-chhi chee-zon mein sa-may lag-ta hai."},
            {"english": "Wait patiently, trust the process.", "hindi": "धैर्य से प्रतीक्षा करो, प्रक्रिया पर भरोसा रखो।", "pronunciation": "dhairy se pratee-ksha karo, prak-riya par bha-ro-sa rakho."},
            {"english": "Rome wasn't built in a day.", "hindi": "रोम एक दिन में नहीं बना था।", "pronunciation": "rom ek din mein nahi ba-na tha."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "hindi": "क्षमा करो और खुद को आज़ाद करो।", "pronunciation": "ksha-ma karo aur khud ko a-zaad karo."},
            {"english": "Let go of grudges, find peace.", "hindi": "शिकायतें छोड़ो, शांति पाओ।", "pronunciation": "shi-kaa-ye-ten chhodo, shan-ti pao."},
            {"english": "Forgiveness is a gift to yourself.", "hindi": "क्षमा अपने आप को एक उपहार है।", "pronunciation": "ksha-ma ap-ne aap ko ek up-haar hai."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "hindi": "तुम जितना जानते हो उससे ज़्यादा मज़बूत हो।", "pronunciation": "tum jit-na jan-te ho us-se zya-da maz-boot ho."},
            {"english": "Inner strength comes from within.", "hindi": "आंतरिक शक्ति अंदर से आती है।", "pronunciation": "aan-tarik shak-ti an-dar se aa-ti hai."},
            {"english": "Challenges make you stronger.", "hindi": "चुनौतियाँ तुम्हें मज़बूत बनाती हैं।", "pronunciation": "chu-nau-ti-yan tum-he maz-boot ba-na-ti hain."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "hindi": "हर पल में आनंद ढूँढो।", "pronunciation": "har pal mein aa-nand dhoondho."},
            {"english": "Joy is contagious, spread it.", "hindi": "आनंद संक्रामक है, इसे फैलाओ।", "pronunciation": "aa-nand san-kraa-mak hai, i-se phai-lao."},
            {"english": "Dance like nobody's watching.", "hindi": "ऐसे नाचो जैसे कोई देख नहीं रहा।", "pronunciation": "ai-se naa-cho jai-se koi dekh nahi ra-ha."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "hindi": "अपने जीवन में संतुलन पाओ।", "pronunciation": "ap-ne jee-van mein san-tu-lan pao."},
            {"english": "Work hard, rest well.", "hindi": "मेहनत करो, अच्छी तरह आराम करो।", "pronunciation": "meh-nat karo, ach-chhi tarah aa-raam karo."},
            {"english": "Too much of anything is not good.", "hindi": "किसी भी चीज़ की अति अच्छी नहीं।", "pronunciation": "ki-si bhi cheez ki ati ach-chhi nahi."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "hindi": "विकास आपके आराम क्षेत्र के बाहर होता है।", "pronunciation": "vi-kaas aap-ke aa-raam kshe-tra ke ba-har ho-ta hai."},
            {"english": "Embrace change, grow stronger.", "hindi": "बदलाव को अपनाओ, मज़बूत बनो।", "pronunciation": "bad-laa-v ko ap-nao, maz-boot bano."},
            {"english": "Every challenge is a chance to grow.", "hindi": "हर चुनौती बढ़ने का एक मौक़ा है।", "pronunciation": "har chu-nau-ti badh-ne ka ek mau-ka hai."},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "hindi": "अपना उद्देश्य खोजो, उसका पालन करो।", "pronunciation": "ap-na ud-desh-y khojo, us-ka paa-lan karo."},
            {"english": "Your life has meaning.", "hindi": "तुम्हारे जीवन का अर्थ है।", "pronunciation": "tum-ha-re jee-van ka arth hai."},
            {"english": "Live with intention, not accident.", "hindi": "इरादे से जियो, संयोग से नहीं।", "pronunciation": "i-raa-de se ji-yo, san-yog se nahi."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "hindi": "इस पल में मौजूद रहो।", "pronunciation": "is pal mein mau-jood raho."},
            {"english": "Breathe deeply, stay grounded.", "hindi": "गहरी साँस लो, ज़मीन से जुड़े रहो।", "pronunciation": "ga-hi saans lo, za-meen se ju-de raho."},
            {"english": "Notice the little things around you.", "hindi": "अपने आस-पास की छोटी चीज़ों पर ध्यान दो।", "pronunciation": "ap-ne aas-paas ki chho-ti chee-zon par dhyaan do."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["hindi"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        str(BASE_DIR / "fonts" / "NotoSansDevanagari-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansDevanagari-Bold.ttf"),
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    hindi = phrase_data.get("hindi", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(hindi, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Hindi Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY HINDI"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_hindi: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansDevanagari-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER HINDI", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_hindi, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 ESSENTIAL PHRASES"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY HINDI", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_hindi: str, phrases: list, duration_minutes: float, output_dir: str):
    duration_label = f"{int(round(duration_minutes))}" if duration_minutes >= 10 else f"{duration_minutes:.0f}"
    titles = [
        f"Learn Hindi in {duration_label} Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_hindi})",
        f"60 Hindi Phrases for {category_english} | Speak Hindi Like a Native! ({category_hindi})",
        f"Master Hindi {category_english} | 60 Essential Hindi Phrases with Pronunciation | Velocity Hindi",
        f"Hindi Learning Made Easy | {category_english} Vocabulary | {duration_label} Minute Lesson",
        f"Speak Hindi Fluently | {category_english} Phrases | English + Hindi + Pronunciation",
    ]

    # YouTube title limit is 100 chars - truncate any overlong title safely
    titles = [t if len(t) <= 100 else (t[:97] + "...") for t in titles]

    description = f"""🇮🇳 Learn Hindi with Velocity Hindi! 🇮🇳

In this video, you'll learn 60 essential Hindi phrases about {category_english} ({category_hindi}).
Perfect for beginners and intermediate learners!

📚 WHAT YOU'LL LEARN:
• 60 practical {category_english} phrases in Hindi
• Correct pronunciation guide
• Natural pauses for speaking practice
• Common expressions used by native speakers

⏱️ VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        seconds = int(i * avg_phrase_duration)
        minute = seconds // 60
        second = seconds % 60
        end_phrase = min(i + 10, len(phrases))
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
📝 ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Hindi: {phrase['hindi']}
   Pronunciation: {phrase['pronunciation']}
"""

    description += """
🎯 PERFECT FOR:
• Hindi beginners wanting to expand vocabulary
• Intermediate learners practicing pronunciation
• Anyone interested in Hindi language and culture
• Language enthusiasts and polyglots
• Students preparing for exams

💡 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

🔔 SUBSCRIBE for more Hindi learning content!
👍 LIKE this video if you found it helpful!
💬 COMMENT which phrases you want to learn next!

📱 FOLLOW VELOCITY HINDI:
[Add your social media links here]

🎵 MUSIC:
[Add music credits if applicable]

📖 RELATED VIDEOS:
• Hindi Motivation Phrases
• Hindi Love Expressions
• Basic Hindi Greetings

#LearnHindi #HindiPhrases #HindiLanguage #{category_english.replace(' ', '')} #VelocityHindi #HindiForBeginners #SpeakHindi #HindiVocabulary #Pronunciation #LanguageLearning #Hindi101 #HindiLesson

---
© Velocity Hindi - Making Hindi learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Hindi",
            "Hindi Phrases",
            "Hindi Language",
            category_english,
            "Velocity Hindi",
            "Hindi for Beginners",
            "Speak Hindi",
            "Hindi Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Hindi 101",
            "Hindi Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_hindi": category_hindi,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_HINDI[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['hindi']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_HINDI[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_HINDI[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"
    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_HINDI[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Hindi: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Hindi", "Hindi Phrases", "Hindi", category_english, "Velocity Hindi"],
        "category_english": category_english,
        "category_hindi": CATEGORIES_HINDI[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Hindi")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Hindi YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY HINDI - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_HINDI[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)