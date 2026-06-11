---
description: Sync tr/en locale keys and hunt hardcoded mobile strings, report and optionally fix.
---

Run an i18n sync and hardcoded-string hunt.

## Workflow
1. Use the **i18n-checker** subagent to:
   - Compare `tr.json` and `en.json` for key parity (report keys missing on either side, empty/untranslated values).
   - Hunt hardcoded user-facing strings in `mobile/**` components/screens/hooks (distinguish real UI copy from ids/keys/logs); suggest a key path and `t('...')` replacement for each.
   - Validate automotive terms against the glossary (yağ tıpası=drain plug, buji=spark plug, kayış=belt, triger=timing belt, hava filtresi=air filter, polen filtresi=cabin filter, akü=battery, yağ filtresi=oil filter) and flag mistranslations.
2. Produce the report: missing/extra keys, hardcoded strings with `file:line`, and glossary issues.

## Optional fix
If $ARGUMENTS contains `fix` (or the user asks to fix):
- Add missing keys to BOTH locale files (placeholder + TODO marker for values needing human translation; never guess Turkish technical terms outside the glossary).
- Replace hardcoded strings with `t()` calls and add their tr/en entries.
- Align glossary translations.
- Keep JSON valid and consistent with existing style; do not delete keys without confirming they are unused.

## Output
Report parity result, hardcoded strings found/fixed, glossary corrections, and which items still need human translation.
