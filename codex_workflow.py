#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
codex_workflow.py — Codex 版两阶段工作流入口

用法：
  python codex_workflow.py prepare <CSV路径>
  python codex_workflow.py validate <结果JSON路径>
  python codex_workflow.py finalize <CSV路径> --self-result <结果JSON路径>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from main import run_workflow
from personality import build_analysis_prompt, validate_analysis_result


def _abs(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def _load_json(path: str) -> dict:
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def _write_prompt_file(
    output_dir: str,
    csv_file: str,
    self_input_path: str,
    partner_input_path: str | None,
    self_result_path: str,
    partner_result_path: str | None,
) -> str:
    prompt_path = os.path.join(output_dir, 'codex_analysis_prompt.md')
    self_input = _load_json(self_input_path)
    self_prompt = build_analysis_prompt(self_input, '自己')

    sections = [
        '# Codex Personality Analysis Prompt',
        '',
        '请在当前工作区完成以下任务：',
        '',
        f'1. 读取 `{_abs(self_input_path)}`。',
    ]

    if partner_input_path:
        sections.append(f'2. 读取 `{_abs(partner_input_path)}`。')
        sections.append(f'3. 将自己的分析结果写入 `{_abs(self_result_path)}`。')
        sections.append(f'4. 将对方的分析结果写入 `{_abs(partner_result_path)}`。')
        sections.append(f'5. 完成后运行：`python codex_workflow.py finalize "{_abs(csv_file)}" --output "{_abs(output_dir)}" --self-result "{_abs(self_result_path)}" --partner-result "{_abs(partner_result_path)}"`')
    else:
        sections.append(f'2. 将自己的分析结果写入 `{_abs(self_result_path)}`。')
        sections.append(f'3. 完成后运行：`python codex_workflow.py finalize "{_abs(csv_file)}" --output "{_abs(output_dir)}" --self-result "{_abs(self_result_path)}"`')

    sections.extend([
        '',
        '要求：',
        '- 必须输出严格合法的 JSON，不要夹带解释文字。',
        '- evidence 必须引用样本中真实出现的原文。',
        '- Big Five 是重点，MBTI 仅供参考并说明不确定性。',
        '- reliability 只描述数据里能客观看到的事实。',
        '',
        '## 自己',
        '',
        self_prompt,
    ])

    if partner_input_path and partner_result_path:
        partner_input = _load_json(partner_input_path)
        partner_prompt = build_analysis_prompt(partner_input, '对方')
        sections.extend([
            '',
            '## 对方',
            '',
            partner_prompt,
        ])

    with open(prompt_path, 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(sections) + '\n')

    return prompt_path


def prepare(args: argparse.Namespace) -> int:
    result = run_workflow(
        csv_file=args.csv_file,
        output=args.output,
        sample_size=args.sample_size,
        self_name=args.self_name,
        partner_name=args.partner_name,
    )

    self_input_path = result.get('personality_input_path')
    partner_input_path = result.get('partner_input_path')
    if not self_input_path:
        print('❌ 未生成 personality_input.json，无法继续。')
        return 1

    output_dir = result['output_dir']
    self_result_path = os.path.join(output_dir, 'personality_result.json')
    partner_result_path = os.path.join(output_dir, 'partner_result.json') if partner_input_path else None
    prompt_path = _write_prompt_file(
        output_dir=output_dir,
        csv_file=args.csv_file,
        self_input_path=self_input_path,
        partner_input_path=partner_input_path,
        self_result_path=self_result_path,
        partner_result_path=partner_result_path,
    )

    print('\n🧭 Codex 工作流已准备完成')
    print(f'  Prompt 文件：{prompt_path}')
    print(f'  自己输入：   {self_input_path}')
    if partner_input_path:
        print(f'  对方输入：   {partner_input_path}')
        print(f'  结果路径：   {self_result_path} / {partner_result_path}')
    else:
        print(f'  结果路径：   {self_result_path}')
    print('\n下一步：在 Codex 中让它读取上述 prompt 文件，写出结果 JSON。')
    return 0


def validate(args: argparse.Namespace) -> int:
    data = _load_json(args.result)
    errors = validate_analysis_result(data)
    if errors:
        print(f'❌ 校验失败：{args.result}')
        for item in errors:
            print(f'  - {item}')
        return 1

    print(f'✅ 校验通过：{args.result}')
    return 0


def finalize(args: argparse.Namespace) -> int:
    self_errors = validate_analysis_result(_load_json(args.self_result))
    if self_errors:
        print(f'❌ 自己的人格分析结果不合法：{args.self_result}')
        for item in self_errors:
            print(f'  - {item}')
        return 1

    partner_result = args.partner_result
    if partner_result:
        partner_errors = validate_analysis_result(_load_json(partner_result))
        if partner_errors:
            print(f'❌ 对方的人格分析结果不合法：{partner_result}')
            for item in partner_errors:
                print(f'  - {item}')
            return 1

    result = run_workflow(
        csv_file=args.csv_file,
        output=args.output,
        personality_result_path=args.self_result,
        partner_personality_result_path=partner_result,
        self_name=args.self_name,
        partner_name=args.partner_name,
    )

    print('\n✅ 最终报告已渲染完成')
    print(f"  HTML 报告：{result['report_path']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Codex 版微信聊天记录分析工作流')
    subparsers = parser.add_subparsers(dest='command', required=True)

    prepare_parser = subparsers.add_parser('prepare', help='生成图表、分析输入和 Codex prompt 文件')
    prepare_parser.add_argument('csv_file', help='导出的聊天 CSV 路径')
    prepare_parser.add_argument('--output', default='./wechat_analysis_output', help='输出目录')
    prepare_parser.add_argument('--sample-size', type=int, default=100, help='采样消息数上限')
    prepare_parser.add_argument('--self-name', default=None, help='覆盖自己的显示名称')
    prepare_parser.add_argument('--partner-name', default=None, help='覆盖对方的显示名称')
    prepare_parser.set_defaults(func=prepare)

    validate_parser = subparsers.add_parser('validate', help='校验人格分析结果 JSON 是否可用于报告')
    validate_parser.add_argument('result', help='人格分析结果 JSON 路径')
    validate_parser.set_defaults(func=validate)

    finalize_parser = subparsers.add_parser('finalize', help='读取人格分析结果 JSON 并生成最终报告')
    finalize_parser.add_argument('csv_file', help='导出的聊天 CSV 路径')
    finalize_parser.add_argument('--output', default='./wechat_analysis_output', help='输出目录')
    finalize_parser.add_argument('--self-result', required=True, help='自己的人格分析结果 JSON 路径')
    finalize_parser.add_argument('--partner-result', default=None, help='对方的人格分析结果 JSON 路径')
    finalize_parser.add_argument('--self-name', default=None, help='覆盖自己的显示名称')
    finalize_parser.add_argument('--partner-name', default=None, help='覆盖对方的显示名称')
    finalize_parser.set_defaults(func=finalize)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
