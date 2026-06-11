---
description: Run the safety-auditor across all AI prompts and task guides and produce the KRİTİK/YÜKSEK/ORTA report.
---

Run a full Usta safety audit.

## Workflow
1. Use the **safety-auditor** subagent to scan ALL AI prompt files (`backend/prompts/**`) and every maintenance task guide.
2. Have it check every rule:
   - Mandatory "büyük ihtimalle" hedging; no definitive-diagnosis phrasing.
   - `guvenlik_uyarisi` required wherever content touches sıcak motor, kriko, akü, yakıt, soğutma basıncı, fren, or LPG.
   - NO LPG-system modification instructions anywhere (KRİTİK if found).
   - Every task guide has a "vazgeç, tamirciye git" exit.
   - Response schema completeness (guvenlik_uyarisi + tamirciye_git_onerisi fields).
   - `metalik_vuruntu` always urgent + tamirciye_git_onerisi true.
3. Have it read/update its project memory at `.claude/memory/safety-auditor.md`.

## Output
Produce the report grouped **KRİTİK / YÜKSEK / ORTA**, each finding with `file:line`, the violated rule, and a concrete fix suggestion. End with counts and an overall block/pass recommendation (any KRİTİK = block).

If $ARGUMENTS is provided, narrow the audit scope to those files/paths; otherwise audit everything.
