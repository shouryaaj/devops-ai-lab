# Before AI vs After AI - measured results

## 1. Build-failure diagnosis: 3 levels of AI use (6 bugs, set A)

- **Level 1 - Self:** developer reads the log and fixes it, no AI
- **Level 2 - Chatbot:** copy log -> paste into an LLM chat -> read reply -> type fix
- **Level 3 - Pipeline AI:** Jenkins sends the log to the local LLM automatically

| Scenario | L1 Self (s) | L1 ok | L2 Chatbot (s) | L2 ok | L3 Pipeline AI (s) | L3 ok |
|---|---|---|---|---|---|---|
| S1_logic_bug | 60.6 | yes | 8.0 | yes | 9.4 | 1/1 |
| S2_syntax_error | 52.9 | yes | 41.6 | yes | 10.3 | 1/1 |
| S3_missing_dependency | 36.6 | yes | 25.1 | yes | 6.4 | 1/1 |
| S4_key_typo | 36.0 | yes | 11.5 | yes | 10.6 | 1/1 |
| S5_config_typo | 15.9 | no | 94.7 | yes | 9.1 | 0/1 |
| S6_wrong_status | 28.3 | yes | 37.1 | yes | 12.2 | 1/1 |

| Metric | L1 Self | L2 Chatbot | L3 Pipeline AI | L3 vs L1 |
|---|---|---|---|---|
| Avg time per failure (s) | 38.4 | 36.3 | 9.7 | -75% (better) |
| Correct (%) | 83 | 100 | 83 | +0% (better) |
| Lines a developer must read | 42 | 42 + chat reply | 4 | -90% (better) |


Model: `mistral:latest`, ~13 tokens/s on this laptop

## 2. Secret detection before commit (Git pre-commit hook)

| Method | Secrets caught | False alarms | Accuracy |
|---|---|---|---|
| **Before:** regex hook | 4/6 | 4/6 | 50% |
| **After:** LLM only | 6/6 | 5/6 | 58% |
| **After:** regex OR LLM (hook default) | 6/6 | 5/6 | 58% |
| **After:** regex AND LLM | 4/6 | 4/6 | 50% |

LLM check time per commit: ~6.4s (regex: ~0s)

## 3. Docker image (naive vs AI-optimised Dockerfile)

| Metric | Before AI (Dockerfile.naive) | After AI (Dockerfile.optimized) | Change |
|---|---|---|---|
| Image size (MB) | 416.9 | 44.9 | -89% (better) |
| Layers | 18.0 | 19.0 | +6% (worse) |
| Cold build (s) | 7.5 | 3.8 | -49% (better) |
| Rebuild after code change (s) | 7.0 | 1.1 | -84% (better) |
| Start-up (s) | 0.2 | 0.5 | +188% (worse) |
| Runs as | root | appuser | |

