"""
Offline comment analyzer for English and Arabic. It needs no network and no API key.

English sentiment comes from VADER, with extra words for customer service, because people
complain in ordinary words ("delayed", "still waiting") that a general lexicon scores as neutral.
Arabic sentiment comes from the word lists below, covering Modern Standard, Gulf and Egyptian
spelling, with negation handled so that "مش حلو" counts as negative.

Both give a score from -1 to 1 on the same scale, and everything else follows from that score.
The rules were written on the development half of tools/evaluate_analyzer.py.
"""
import math
import re

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Score limits for the emotions. Between NEGATIVE_BELOW and POSITIVE_ABOVE a comment is neutral.
# Arabic scores come from fewer known words, so its bar for positive is lower.
POSITIVE_ABOVE = {"en": 0.5, "ar": 0.2}
NEGATIVE_BELOW = -0.05
ANGER_BELOW = -0.5

RESPONSES = {
    "en": {
        "joy": "Thank you for the positive feedback! We appreciate your support.",
        "neutral": "Thanks for your input. We'll consider your feedback.",
        "sadness": "We're sorry you had this experience. We're working to improve.",
        "anger": "We sincerely apologize for this issue. Our team will investigate immediately.",
    },
    "ar": {
        "joy": "شكرا لك على هذا التقييم الجميل، ونقدر دعمك لنا.",
        "neutral": "شكرا على رسالتك، وسنأخذ رأيك بعين الاعتبار.",
        "sadness": "نأسف لما واجهته، ونعمل على تحسين الخدمة.",
        "anger": "نعتذر بشدة عن هذه المشكلة، وسيتابعها فريقنا فورا.",
    },
}

# --- English ---------------------------------------------------------------------------------

# Added to VADER's lexicon, on its scale of -4 to 4.
CUSTOMER_SERVICE_WORDS = {
    "delay": -1.5, "delayed": -1.8, "delays": -1.5, "late": -1.2, "cancelled": -1.8, "canceled": -1.8,
    "cancellation": -1.2, "lost": -1.8, "missing": -1.5, "stuck": -1.8, "stranded": -2.2,
    "waiting": -1.0, "refund": -1.2, "overcharged": -2.2, "charged": -0.8, "rebook": -0.8,
    "broken": -2.0, "crash": -2.0, "crashed": -2.0, "crashes": -2.0, "crashing": -2.0,
    "failed": -1.8, "fails": -1.8, "glitch": -1.5, "bug": -1.5, "error": -1.5, "unable": -1.5,
    "nobody": -1.2, "never": -0.8, "ignored": -1.8, "worst": -3.0, "rude": -2.5, "unacceptable": -2.8,
    "damaged": -2.0, "complaint": -1.5, "issue": -1.0, "issues": -1.0, "problem": -1.5, "problems": -1.5,
    "hours": -0.8, "hour": -0.8, "hrs": -0.8, "minutes": -0.6, "mins": -0.6, "days": -0.5, "hold": -1.0,
    "told": -0.8, "nothing": -1.0, "still": -0.6, "why": -0.8, "wait": -1.0, "sitting": -0.8, "without": -0.6,
    "ridiculous": -2.2, "disappointed": -2.2, "disappointing": -2.2, "terrible": -3.0,
}

# Complaints that only show up across several words. Each hit moves the score down.
PROBLEM_PHRASES = re.compile(
    r"\b("
    r"(no|never (got|had|received)( a| any)?) (reply|response|answer|call ?back|help|update|info)"
    r"|on hold|still (waiting|no|not|have not|haven'?t)|not (working|helpful|happy|impressed)"
    r"|(doesn'?t|does not|won'?t|didn'?t|did not|can'?t|cannot|couldn'?t) (work|load|open|log ?in|get through|find|get|help|respond|reply)"
    r"|keeps? (crashing|failing|freezing|breaking)|hours? late|been waiting|hung up"
    r")\b",
    re.IGNORECASE,
)
PHRASE_PENALTY = 0.45
# VADER's "neg" is the share of the text carrying negative weight.
MIXED_NEGATIVE_SHARE = 0.15

_vader = SentimentIntensityAnalyzer()
_vader.lexicon.update(CUSTOMER_SERVICE_WORDS)

# --- Arabic ----------------------------------------------------------------------------------

_DIACRITICS = re.compile("[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")
_INVISIBLE = re.compile("[\u00ad\u061c\u200b-\u200f\u202a-\u202e\u2060\u2066-\u2069\ufeff]")
_REPEATED_LETTER = re.compile(r"(.)\1{2,}")
_LETTER_FORMS = str.maketrans("أإآٱىةؤئکیھہ", "اااايهويكيهه")


def normalize_arabic(text: str) -> str:
    """Remove the spelling differences that do not change a word."""
    text = _INVISIBLE.sub("", text)
    text = _DIACRITICS.sub("", text)
    text = text.translate(_LETTER_FORMS)
    # Stretched words: ممتااااز is ممتاز.
    return _REPEATED_LETTER.sub(r"\1", text)


def _word_set(words: str) -> frozenset:
    return frozenset(normalize_arabic(word) for word in words.split())


ARABIC_POSITIVE = _word_set(
    """
    ممتاز رائع رائعه جميل جميله حلو حلوه جيد جيده روعه تحفه شكرا اشكر اشكركم مشكور مشكورين
    افضل احسن اجمل اروع الذ انظف ممتع لذيذ طيب نظيف نضيف سريع مريح انصح ينصح احببت احب اعجبني
    عجبني يجنن خرافي مبدع موفق راقي مميز متميز رهيب فخم نايس تمام عظيم مذهل يستاهل يستحق كويس جامد
    استمتعت سعيد مبسوط راضي ناجح احترافي مناسب جبار لطيف محترم حبيت حبيتها ابداع شهي بطل
    يعجبني تعجبني عجبتني اعجبتني تستاهل
    """
)
ARABIC_NEGATIVE = _word_set(
    """
    سيء سيئ رديء رديئ ردي زباله مقرف مزعج فاشل خايس تعبان وسخ قذر مغشوش تقليد كذب كذاب نصاب نصب
    احتيال سرقه حرامي مشكله مشاكل عطل عطلان خربان خراب معطل تالف تلف تلفت مكسور متاخر تاخير تاخر
    الغاء الغيت ضاع ضاعت ضائع فقدت مفقود ندمت ندم خساره خسران اسوا سوء وحش بطيء بطيئ بايخ تافه
    ضعيف غلط خطا عيب اشتكي شكوي استرجاع مرتجع استرداد اهمال مهمل وقح طفشت كارثه مصيبه زفت يقرف
    مللت ممل مخيب خيبه ضرر غش خدعه فاسد بايت للاسف الاسف غالي باهظ نادم نقص ناقص قديم بارد
    """
)
ARABIC_NEGATIVE |= _word_set(
    """
    انكسر ينكسر تكسر مهترئ صعوبه يفتقد انقطع ينقطع تعطل يتعطل اخيس تسمم مزري تعيس محبط اغبي مهزله
    """
)
# Words that lean negative in a review but are not a complaint by themselves.
ARABIC_WEAK_NEGATIVE = _word_set("عادي اقل مبالغ ابدا متوسط مقبول")
ARABIC_NEGATIONS = _word_set("ما لا لم لن ليس ليست مش مو مب موب غير بدون ماهو ماهي مافي مفيش ولا عدم وغير ولم")
# What follows these words is what the writer really means: "جميل لكن يتعطل".
ARABIC_CONTRASTS = _word_set("لكن لاكن ولكن بس الا رغم")

# Complaints that a single word does not carry. Written after normalization.
ARABIC_PROBLEM_PHRASES = re.compile(
    "|".join(
        normalize_arabic(phrase)
        for phrase in (
            "لم يصل", "لم تصل", "ما وصل", "ماوصل", "ما رد", "ماردو", "لم يرد", "لا يرد", "لا يعمل", "لايعمل",
            "ما يشتغل", "مايشتغل", "لا يشتغل", "مش شغال", "لا انصح", "ما انصح", "لا تشتروا", "لا تشتري",
            "لا تعمل", "لاتعمل", "لم تعمل", "لم يعمل", "لا تصلح", "لا يصلح", "غير صالح", "غير مرضي", "لم استلم",
            "ما استلمت", "لن اكرر", "لن اعود", "لن ارجع", "ما اعيد", "ما ارجع", "لا فايده", "بدون فايده",
        )
    )
)

ARABIC_WORD_WEIGHT = 2.0
ARABIC_WEAK_WEIGHT = 0.8
NEGATED_WEIGHT = -0.75
NEGATION_REACH = 2
BEFORE_CONTRAST = 0.5
AFTER_CONTRAST = 1.5

_ARABIC_LETTER = re.compile("[\u0621-\u064a\u066e-\u06d3]")
_LATIN_LETTER = re.compile("[A-Za-z]")
_ARABIC_WORD = re.compile("[\u0621-\u064a\u066e-\u06d3]+")

_PREFIXES = ("وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ك", "ل")
_SUFFIXES = ("هم", "ها", "كم", "نا", "ون", "ين", "ات", "ان", "يه", "ه", "ي")
_MIN_STEM = 3


def _word_forms(word: str):
    """Yield the word, then the word with common attached letters removed."""
    stems = [word]
    stems += [word[len(p):] for p in _PREFIXES if word.startswith(p) and len(word) - len(p) >= _MIN_STEM]
    for stem in stems:
        yield stem
        for suffix in _SUFFIXES:
            if stem.endswith(suffix) and len(stem) - len(suffix) >= _MIN_STEM:
                yield stem[: -len(suffix)]


def _arabic_polarity(word: str) -> float:
    for form in _word_forms(word):
        if form in ARABIC_POSITIVE:
            return ARABIC_WORD_WEIGHT
        if form in ARABIC_NEGATIVE:
            return -ARABIC_WORD_WEIGHT
        if form in ARABIC_WEAK_NEGATIVE:
            return -ARABIC_WEAK_WEIGHT
    return 0.0


def _attached_negation(word: str) -> float:
    """Negation written as part of the word: ماتستاهل, لايعجبني."""
    if word[:2] in ("ما", "لا") and len(word) - 2 >= _MIN_STEM:
        rest = word[2:]
        for candidate in (rest, "ي" + rest[1:]):
            polarity = _arabic_polarity(candidate)
            if polarity:
                return polarity * NEGATED_WEIGHT
    return 0.0


POSITIVE_EMOJI = "😍🥰😊😀😃😄🤩👍👌❤💙💚🌹👏"
NEGATIVE_EMOJI = "😡🤬😠👎💔😢😭😞😤🤮"


def _emoji_weight(text: str) -> float:
    return ARABIC_WORD_WEIGHT * (sum(ch in POSITIVE_EMOJI for ch in text) - sum(ch in NEGATIVE_EMOJI for ch in text))


def _squash(total: float) -> float:
    """The same squashing VADER uses, so that both languages share one scale."""
    return total / math.sqrt(total * total + 15)


def _arabic_score(text: str) -> tuple:
    """Return the score, and whether the comment names a problem even if it also has praise."""
    normalized = normalize_arabic(text)
    words = _ARABIC_WORD.findall(normalized)
    last_contrast = max((i for i, w in enumerate(words) if w in ARABIC_CONTRASTS), default=None)
    total = _emoji_weight(text)
    has_problem = total < 0
    for i, word in enumerate(words):
        weight = _arabic_polarity(word)
        if weight:
            if any(w in ARABIC_NEGATIONS for w in words[max(0, i - NEGATION_REACH):i]):
                weight *= NEGATED_WEIGHT
        else:
            weight = _attached_negation(word)
        if last_contrast is not None:
            weight *= AFTER_CONTRAST if i > last_contrast else BEFORE_CONTRAST
        has_problem = has_problem or weight <= -ARABIC_WEAK_WEIGHT - 0.5
        total += weight
    phrases = len(ARABIC_PROBLEM_PHRASES.findall(normalized))
    total -= ARABIC_WORD_WEIGHT * phrases
    return _squash(total), has_problem or phrases > 0


def _english_score(text: str) -> tuple:
    scores = _vader.polarity_scores(text)
    phrases = len(PROBLEM_PHRASES.findall(text))
    score = max(-1.0, scores["compound"] - PHRASE_PENALTY * phrases)
    return score, phrases > 0 or scores["neg"] >= MIXED_NEGATIVE_SHARE


def detect_language(text: str) -> str:
    arabic = len(_ARABIC_LETTER.findall(text))
    return "ar" if arabic and arabic >= len(_LATIN_LETTER.findall(text)) else "en"


# --- Intent ----------------------------------------------------------------------------------

_BUG_EN = re.compile(
    r"\b(bug|bugs|error|errors|crash\w*|glitch\w*|broken|freez\w+|not working|(doesn'?t|does not|won'?t) (work|load|open))\b",
    re.IGNORECASE,
)
_SUGGESTION_EN = re.compile(
    r"\b(i suggest|suggestion|would be (nice|great|better|good)|you should (add|have|offer)|could you add|please add"
    r"|feature request|why not|i wish|how about)\b",
    re.IGNORECASE,
)
_QUESTION_EN = re.compile(r"\?|^\s*(what|when|where|why|how|who|which|can|could|do|does|is|are|will)\b", re.IGNORECASE)
_BUG_AR = re.compile(
    "|".join(
        normalize_arabic(w)
        for w in ("عطل", "معطل", "عطلان", "خربان", "خطا تقني", "لا يعمل", "لايعمل", "ما يشتغل", "مايشتغل", "يهنج", "يعلق", "مش شغال")
    )
)
_SUGGESTION_AR = re.compile(
    "|".join(normalize_arabic(w) for w in ("اقترح", "اقتراح", "ياريت", "يا ريت", "اتمنى", "نتمنى", "لو تضيفون", "اتمني"))
)
_QUESTION_AR = re.compile("[?؟]|^\\s*(" + "|".join(normalize_arabic(w) for w in "هل متى كيف اين ليش لماذا وين ايش ماذا".split()) + ")\\b")


def detect_intent(text: str, language: str, score: float) -> str:
    """Pick the intent. Sentiment decides between praise and complaint, so "not good" is no praise."""
    arabic = language == "ar"
    subject = normalize_arabic(text) if arabic else text
    if (_BUG_AR if arabic else _BUG_EN).search(subject):
        return "bug_report"
    if score < NEGATIVE_BELOW:
        return "complaint"
    if (_SUGGESTION_AR if arabic else _SUGGESTION_EN).search(subject):
        return "suggestion"
    if score >= POSITIVE_ABOVE[language]:
        return "praise"
    if (_QUESTION_AR if arabic else _QUESTION_EN).search(subject):
        return "question"
    return "feedback"


def determine_priority(emotion: str, intent: str) -> str:
    """Determine priority level based on emotion and intent"""
    if emotion == "anger" and intent in ("bug_report", "complaint"):
        return "Critical"
    if emotion == "anger" or intent == "bug_report" or (emotion == "sadness" and intent == "complaint"):
        return "High"
    if emotion == "sadness" or intent == "complaint":
        return "Medium"
    return "Low"


def emotion_for(score: float, language: str) -> str:
    if score >= POSITIVE_ABOVE[language]:
        return "joy"
    if score <= ANGER_BELOW:
        return "anger"
    if score < NEGATIVE_BELOW:
        return "sadness"
    return "neutral"


def analyze_sentiment_locally(text: str) -> dict:
    """Analyze one comment. Returns emotion, intent, priority, needs_ticket, response and confidence."""
    language = detect_language(text)
    score, has_problem = _arabic_score(text) if language == "ar" else _english_score(text)
    emotion = emotion_for(score, language)
    intent = detect_intent(text, language, score)
    priority = determine_priority(emotion, intent)
    return {
        "emotion": emotion,
        "intent": intent,
        "priority": priority,
        "needs_ticket": has_problem or emotion in ("anger", "sadness") or intent in ("complaint", "bug_report"),
        "suggested_response": RESPONSES[language][emotion],
        # A strength score, not a probability. tools/evaluate_analyzer.py shows how it relates to accuracy.
        "confidence": round(min(0.95, 0.5 + abs(score) * 0.45), 2),
    }
