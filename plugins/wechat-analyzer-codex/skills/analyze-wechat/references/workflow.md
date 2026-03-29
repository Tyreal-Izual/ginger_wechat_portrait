# Analyze WeChat Workflow Reference

## Repository root

Run commands from the repository root containing:

- `export_contact.py`
- `codex_workflow.py`
- `README.md`
- `安装指南.md`

## Environment setup

Preferred environment options:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Or, if the user already has a usable conda environment:

```bash
conda activate general
pip install -r requirements.txt
```

## Export command

```bash
python export_contact.py --contact "联系人名"
```

Look for:

- `EXPORT_PATH:...`
- `META_PATH:...`

## Prepare command

```bash
python codex_workflow.py prepare "./export_xxx.csv"
```

This creates:

- `wechat_analysis_output/personality_input.json`
- `wechat_analysis_output/partner_input.json`
- `wechat_analysis_output/codex_analysis_prompt.md`

## Validation command

```bash
python codex_workflow.py validate "./wechat_analysis_output/personality_result.json"
```

## Finalize command

Single-person result:

```bash
python codex_workflow.py finalize "./export_xxx.csv" \
  --self-result "./wechat_analysis_output/personality_result.json"
```

Dual-person result:

```bash
python codex_workflow.py finalize "./export_xxx.csv" \
  --self-result "./wechat_analysis_output/personality_result.json" \
  --partner-result "./wechat_analysis_output/partner_result.json"
```

## Manual decrypt reminder

If the user has not yet prepared the local decrypted WeChat database, follow `安装指南.md`.

The `lldb`-based key extraction step must be run manually in system `Terminal.app`, not inside Codex.
