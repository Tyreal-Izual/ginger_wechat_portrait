---
name: analyze-wechat
description: Analyze a local WeChat contact conversation in this repository by exporting chat data, preparing Codex personality inputs, generating structured result JSON, and rendering the final HTML report. Use when the user asks to analyze WeChat messages, generate the chat portrait report, or continue an existing WeChat analysis run from a CSV or prepared JSON files.
---

# Analyze WeChat

## Overview

Use this skill to run the end-to-end WeChat analysis workflow in this repository. It handles the practical flow that previously lived behind Claude Code's `/analyze-wechat` command, but adapted for Codex.

## Workflow

1. Resolve the starting point.
   - If the user already provides a CSV export path, start from `codex_workflow.py prepare <csv>`.
   - If the user already provides `personality_result.json` and wants the final report, start from `codex_workflow.py finalize`.
   - Otherwise, prepare the environment and export the target contact from the local decrypted WeChat database.

2. Prepare the Python environment.
   - Prefer the repo-local `.venv` when present.
   - Otherwise use the active environment if imports work.
   - If core imports fail, install `requirements.txt`.
   - Core commands in this repo expect to run from the repository root that contains `export_contact.py`, `main.py`, and `codex_workflow.py`.

3. Check whether local WeChat data is ready.
   - If `config.json` already points at a valid decrypted database, continue.
   - Otherwise inspect `~/Documents/wechat-db-decrypt-macos` and the repo docs.
   - If no key or decrypted database exists yet, stop and guide the user through the manual `Terminal.app` step described in `安装指南.md`. Do not pretend Codex can run the `lldb` key-extraction step itself.

4. Export the requested contact.
   - Run `python export_contact.py --contact "<联系人名>"`.
   - If multiple contacts match, show the choices and ask the user which one to use.
   - Capture the `EXPORT_PATH:` value from the command output.

5. Prepare Codex analysis inputs.
   - Run `python codex_workflow.py prepare "<csv_path>"`.
   - This generates charts, `personality_input.json`, optional `partner_input.json`, and `wechat_analysis_output/codex_analysis_prompt.md`.

6. Produce the result JSON files.
   - Read `wechat_analysis_output/codex_analysis_prompt.md`.
   - Write `wechat_analysis_output/personality_result.json`.
   - If `partner_input.json` exists, also write `wechat_analysis_output/partner_result.json`.
   - Evidence must quote real message snippets from the sampled inputs.

7. Validate and finalize.
   - Run `python codex_workflow.py validate <result-json>` on each produced JSON file when practical.
   - Run `python codex_workflow.py finalize "<csv_path>" --self-result ... [--partner-result ...]`.
   - Tell the user where `report.html` was written.

## Operational Rules

- Keep all writes inside this repository unless the user explicitly wants something elsewhere.
- Do not modify or overwrite the user's source chat export unless asked.
- Treat SIP and `Terminal.app` key extraction as manual user steps.
- If dependencies are missing, install them before concluding the workflow is broken.
- If the user asks for the original command-like experience, tell them to invoke this skill with `$analyze-wechat`.

## Key Commands

```bash
python export_contact.py --contact "联系人名"
python codex_workflow.py prepare ./export_xxx.csv
python codex_workflow.py validate ./wechat_analysis_output/personality_result.json
python codex_workflow.py finalize ./export_xxx.csv --self-result ./wechat_analysis_output/personality_result.json
```

## References

- For the manual decrypt and SIP prerequisites, read `安装指南.md` in the repo root.
- For the public-facing usage flow, read `README.md` in the repo root.
- For command templates and recovery steps, read `references/workflow.md`.
