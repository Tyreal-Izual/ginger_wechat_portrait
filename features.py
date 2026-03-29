"""
features.py — 提取用于人格分析的可量化语言特征
"""

from typing import List

_OPINION_WORDS = ['我觉得', '我认为', '感觉', '我想', '我希望', '在我看来', '我以为']
_EMOTION_POS = ['开心', '高兴', '快乐', '喜欢', '爱', '棒', '不错', '满意', '幸福', '兴奋']
_EMOTION_NEG = ['难过', '伤心', '生气', '烦', '焦虑', '担心', '害怕', '失望', '委屈', '无聊']
_PLANNING_WORDS = ['打算', '计划', '准备', '决定', '目标', '将来', '以后', '未来']
_CERTAINTY_POS = ['一定', '肯定', '确定', '绝对', '必须']
_CERTAINTY_NEG = ['可能', '也许', '大概', '应该', '或许', '不确定']
_FIRST_PERSON = ['我', '我的', '我觉得', '我认为', '我想']
_SOCIAL_WORDS = ['朋友', '大家', '我们', '一起', '聚', '出去', '玩']


def _rate(texts: List[str], words: List[str]) -> float:
    """words 中任意词出现在消息里的比例"""
    hits = sum(1 for text in texts if any(word in text for word in words))
    return round(hits / len(texts) * 100, 1) if texts else 0.0


def extract_features(messages: List[str]) -> dict:
    """从消息列表中提取可量化的语言特征"""
    if not messages:
        return {}

    avg_len = round(sum(len(message) for message in messages) / len(messages), 1)
    return {
        'avg_length': avg_len,
        'opinion_rate': _rate(messages, _OPINION_WORDS),
        'positive_emotion': _rate(messages, _EMOTION_POS),
        'negative_emotion': _rate(messages, _EMOTION_NEG),
        'planning_rate': _rate(messages, _PLANNING_WORDS),
        'certainty_high': _rate(messages, _CERTAINTY_POS),
        'certainty_low': _rate(messages, _CERTAINTY_NEG),
        'question_rate': round(
            sum(1 for message in messages if '?' in message or '？' in message) / len(messages) * 100,
            1,
        ),
        'social_rate': _rate(messages, _SOCIAL_WORDS),
        'first_person_rate': _rate(messages, _FIRST_PERSON),
        'sample_count': len(messages),
        'total_words': sum(len(message) for message in messages),
    }
