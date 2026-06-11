---
description: Create a new maintenance task guide for $ARGUMENTS, with camera-verification prompt, safety audit, mechanic-exit, and i18n keys.
---

Create a new Usta maintenance task guide for: **$ARGUMENTS**

Follow this workflow end to end. Do not skip the safety or i18n steps.

## 1. Draft the guide
- Read existing task guides to match format and conventions (Glob/Grep for guide/rehber files under `backend/`).
- Draft clear, ordered, beginner-safe steps for "$ARGUMENTS" (tools needed, what to check, what to do).
- Use mandatory hedging ("büyük ihtimalle") for any diagnostic statement; never definitive.
- Include `guvenlik_uyarisi` wherever the steps touch sıcak motor, kriko, akü, yakıt, soğutma basıncı, fren, or LPG.
- NEVER include LPG-system modification steps.
- Include an explicit "vazgeç, tamirciye git" (give up, go to mechanic) exit path.

## 2. Camera-verification prompt
- Use the **vision-prompt-engineer** subagent to author the camera-verification prompt for this task under `backend/prompts/vision/`, embedding the JSON schema, the 3x3 location dictionary, few-shot examples, JSON-only output, vehicle-context-first, and all safety rules. Target `claude-sonnet-4-5` (Opus forbidden).

## 3. Safety audit
- Use the **safety-auditor** subagent to audit both the drafted guide and the new vision prompt. Resolve every KRİTİK and YÜKSEK finding before proceeding. Confirm the tamirciye-git exit exists.

## 4. i18n
- Use the **i18n-checker** subagent to ensure every user-facing string in the guide has keys in both `tr.json` and `en.json` (no hardcoded strings) and that automotive terms match the glossary.

## 5. Report
Summarize: guide file, vision prompt file, safety-audit result (must be clean of KRİTİK/YÜKSEK), confirmation of the mechanic-exit, and i18n keys added.
