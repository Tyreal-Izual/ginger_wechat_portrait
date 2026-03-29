"""
personality.py — Codex 工作流使用的人格分析辅助工具

职责：
1. 过滤消息样本，减少超长文本噪音
2. 生成给 Codex/其他兼容代理使用的分析提示词
3. 校验最终人格分析 JSON 是否满足报告生成要求
"""

from __future__ import annotations

import json
import re
from typing import Any

from features import extract_features

BIG5_KEYS = (
    'openness',
    'conscientiousness',
    'extraversion',
    'agreeableness',
    'neuroticism',
)

MBTI_DIMS = ('EI', 'SN', 'TF', 'JP')
STYLE_LIST_KEYS = ('strengths', 'fun_facts')

SCHEMA_SNIPPET = """```json
{
  "big5": {
    "openness": {"score": 0-100, "level": "低/中/高", "evidence": "原文片段", "note": "一句解读"},
    "conscientiousness": {"score": 0-100, "level": "低/中/高", "evidence": "原文片段", "note": "一句解读"},
    "extraversion": {"score": 0-100, "level": "低/中/高", "evidence": "原文片段", "note": "一句解读"},
    "agreeableness": {"score": 0-100, "level": "低/中/高", "evidence": "原文片段", "note": "一句解读"},
    "neuroticism": {"score": 0-100, "level": "低/中/高", "evidence": "原文片段", "note": "一句解读"}
  },
  "mbti": {
    "type": "四字母",
    "confidence": "低/中/高",
    "note": "置信度说明",
    "dims": {
      "EI": {"lean": "E或I", "strength": "明显/轻微", "reason": "简短理由"},
      "SN": {"lean": "S或N", "strength": "明显/轻微", "reason": "简短理由"},
      "TF": {"lean": "T或F", "strength": "明显/轻微", "reason": "简短理由"},
      "JP": {"lean": "J或P", "strength": "明显/轻微", "reason": "简短理由"}
    }
  },
  "style": {
    "one_line": "一句生动描述",
    "summary": "2-3句聊天风格描述",
    "strengths": ["特点1", "特点2", "特点3"],
    "fun_facts": ["有趣发现1", "有趣发现2"]
  },
  "reliability": "对样本量、时间跨度和观察范围的客观说明"
}
```"""


def filter_messages(messages: list[str], max_length: int = 150) -> list[str]:
    """过滤超长消息，减少转发内容或文档片段对人格分析的干扰。"""
    return [message for message in messages if len(message) <= max_length]


def extract_json_from_text(raw: str) -> dict[str, Any]:
    """从模型输出文本中提取 JSON 块。"""
    match = re.search(r'```json\s*([\s\S]+?)\s*```', raw)
    json_str = match.group(1) if match else raw
    return json.loads(json_str)


def build_analysis_prompt(input_payload: dict[str, Any], subject_name: str) -> str:
    """根据生成好的 personality_input.json 构建给 Codex 的分析提示词。"""
    sample_messages = filter_messages(input_payload.get('sample_messages', []))
    top_words = input_payload.get('top_words', [])
    features = input_payload.get('features', {})
    stats_summary = input_payload.get('stats_summary', {})

    sample_block = '\n'.join(f'- {message}' for message in sample_messages) or '- （无可用样本）'
    top_words_text = ', '.join(
        f"{item.get('word', '')}:{item.get('count', 0)}" for item in top_words[:30]
    ) or '无'
    features_text = ', '.join(f'{key}={value}' for key, value in features.items()) or '无'
    stats_text = json.dumps(stats_summary, ensure_ascii=False, indent=2)

    return f"""你是一位语言学人格研究者，正在分析「{subject_name}」的微信聊天记录样本。

请基于以下信息输出严格符合 schema 的 JSON，不要添加额外解释文字。

【样本过滤规则】
- 已过滤超过 150 字的超长消息
- evidence 必须引用下方样本中真实出现的原文片段
- Big Five 是重点，MBTI 仅供参考，需如实体现不确定性
- reliability 只描述数据中实际能观察到的事实

【统计摘要】
{stats_text}

【语言特征】
{features_text}

【高频词】
{top_words_text}

【消息样本】
{sample_block}

【输出 schema】
{SCHEMA_SNIPPET}
"""


def validate_analysis_result(data: Any) -> list[str]:
    """校验分析结果 JSON，返回错误列表；空列表表示校验通过。"""
    errors: list[str] = []

    if not isinstance(data, dict):
        return ['结果 JSON 顶层必须是对象']

    big5 = data.get('big5')
    if not isinstance(big5, dict):
        errors.append('缺少 big5 对象')
    else:
        for trait in BIG5_KEYS:
            item = big5.get(trait)
            if not isinstance(item, dict):
                errors.append(f'big5.{trait} 必须是对象')
                continue
            score = item.get('score')
            if not isinstance(score, (int, float)) or not 0 <= score <= 100:
                errors.append(f'big5.{trait}.score 必须是 0-100 数字')
            for field in ('level', 'evidence', 'note'):
                if not isinstance(item.get(field), str) or not item.get(field).strip():
                    errors.append(f'big5.{trait}.{field} 必须是非空字符串')

    mbti = data.get('mbti')
    if not isinstance(mbti, dict):
        errors.append('缺少 mbti 对象')
    else:
        for field in ('type', 'confidence', 'note'):
            if not isinstance(mbti.get(field), str) or not mbti.get(field).strip():
                errors.append(f'mbti.{field} 必须是非空字符串')

        dims = mbti.get('dims')
        if not isinstance(dims, dict):
            errors.append('mbti.dims 必须是对象')
        else:
            for dim in MBTI_DIMS:
                item = dims.get(dim)
                if not isinstance(item, dict):
                    errors.append(f'mbti.dims.{dim} 必须是对象')
                    continue
                for field in ('lean', 'strength', 'reason'):
                    if not isinstance(item.get(field), str) or not item.get(field).strip():
                        errors.append(f'mbti.dims.{dim}.{field} 必须是非空字符串')

    style = data.get('style')
    if not isinstance(style, dict):
        errors.append('缺少 style 对象')
    else:
        for field in ('one_line', 'summary'):
            if not isinstance(style.get(field), str) or not style.get(field).strip():
                errors.append(f'style.{field} 必须是非空字符串')
        for field in STYLE_LIST_KEYS:
            value = style.get(field)
            if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
                errors.append(f'style.{field} 必须是非空字符串列表')

    if not isinstance(data.get('reliability'), str) or not data.get('reliability').strip():
        errors.append('reliability 必须是非空字符串')

    return errors
