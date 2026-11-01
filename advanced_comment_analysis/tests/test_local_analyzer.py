"""The offline analyzer on the kinds of comment it used to get wrong."""
import pytest

from app.services.local_analyzer import (
    RESPONSES,
    analyze_sentiment_locally,
    detect_language,
    determine_priority,
    normalize_arabic,
)

NEGATIVE = ("anger", "sadness")


@pytest.mark.parametrize(
    "comment, intent, ticket",
    [
        # These all came back as sadness with a ticket before, or worse.
        ("The staff were wonderful", "praise", False),
        ("I love this tissue box", "praise", False),
        ("What time do you open on Friday?", "question", False),
        ("My flight is at 9.", "feedback", False),
        ("Please show me the menu", "feedback", False),
        ("Could you add dark mode?", "suggestion", False),
        ("This API keeps crashing!", "bug_report", True),
        ("I lost my luggage and nobody replied for two weeks", "complaint", True),
        ("Not good at all", "complaint", True),
        ("Thank you so much, this was excellent", "praise", False),
        ("Been on hold for 3 hours", "complaint", True),
        ("The app won't open on my phone", "bug_report", True),
        # Arabic.
        ("شكرا جزيلا الخدمة ممتازة", "praise", False),
        ("ضاعت حقيبتي ولم يرد علي أحد، خدمة سيئة جدا", "complaint", True),
        ("متى تفتحون يوم الجمعة؟", "question", False),
        ("هل التوصيل متاح في الدوحة؟", "question", False),
        ("التطبيق لا يعمل منذ أمس", "bug_report", True),
        ("ياريت تضيفون خدمة التوصيل", "suggestion", False),
        ("الطلب لم يصل حتى الآن", "complaint", True),
    ],
)
def test_intent_and_ticket(comment, intent, ticket):
    result = analyze_sentiment_locally(comment)
    assert result["intent"] == intent
    assert result["needs_ticket"] is ticket


@pytest.mark.parametrize(
    "comment",
    [
        "مش حلو",
        "غير جيد",
        "ما عجبني",
        "لا انصح به",
        "ماتستاهل سعرها",
        "لايعجبني",
    ],
)
def test_arabic_negation_turns_praise_into_complaint(comment):
    result = analyze_sentiment_locally(comment)
    assert result["emotion"] in NEGATIVE
    assert result["needs_ticket"] is True


@pytest.mark.parametrize(
    "comment",
    [
        "ممتاز",
        "ممتااااز",
        "مُمْتَاز",
        "الخدمة ممتازة",
        "مم\u200fتاز",
    ],
)
def test_arabic_spelling_variants_are_understood(comment):
    assert analyze_sentiment_locally(comment)["emotion"] == "joy"


@pytest.mark.parametrize(
    "comment",
    [
        "The food was good but the waiter was rude",
        "جميل لكن يتعطل بسرعة",
    ],
)
def test_mixed_comment_still_opens_a_ticket(comment):
    assert analyze_sentiment_locally(comment)["needs_ticket"] is True


def test_reply_is_in_the_language_of_the_comment():
    arabic = analyze_sentiment_locally("الخدمة سيئة جدا")
    assert arabic["suggested_response"] in RESPONSES["ar"].values()
    english = analyze_sentiment_locally("The service was terrible")
    assert english["suggested_response"] in RESPONSES["en"].values()


def test_comment_with_no_signal_is_neutral_and_opens_no_ticket():
    for comment in ("My flight is at 9.", "رحلتي الساعة التاسعة", "12345", "..."):
        result = analyze_sentiment_locally(comment)
        assert result["emotion"] == "neutral"
        assert result["needs_ticket"] is False


def test_stronger_language_gets_higher_confidence():
    weak = analyze_sentiment_locally("My flight is at 9.")["confidence"]
    strong = analyze_sentiment_locally("This is the worst, most terrible service, I hate it")["confidence"]
    assert 0.5 <= weak < strong <= 0.95


@pytest.mark.parametrize(
    "text, language",
    [
        ("Hello there", "en"),
        ("مرحبا بكم", "ar"),
        ("الخدمة ممتازة thanks", "ar"),
        ("12345", "en"),
    ],
)
def test_detect_language(text, language):
    assert detect_language(text) == language


@pytest.mark.parametrize(
    "raw, clean",
    [
        ("أحمد", "احمد"),
        ("إسلام", "اسلام"),
        ("مدرسة", "مدرسه"),
        ("مستشفى", "مستشفي"),
        ("مـــدرسة", "مدرسه"),
        ("مُحَمَّد", "محمد"),
        ("كتاب", "كتاب"),
        ("کتاب", "كتاب"),
        ("ممتاااز", "ممتاز"),
    ],
)
def test_normalize_arabic(raw, clean):
    assert normalize_arabic(raw) == clean


@pytest.mark.parametrize(
    "emotion, intent, priority",
    [
        ("anger", "complaint", "Critical"),
        ("anger", "bug_report", "Critical"),
        ("anger", "feedback", "High"),
        ("neutral", "bug_report", "High"),
        ("sadness", "complaint", "High"),
        ("sadness", "feedback", "Medium"),
        ("neutral", "complaint", "Medium"),
        ("neutral", "question", "Low"),
        ("joy", "praise", "Low"),
    ],
)
def test_priority(emotion, intent, priority):
    assert determine_priority(emotion, intent) == priority
