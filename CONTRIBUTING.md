# Contributing

Contributions are welcome — new scenarios, additional attack variants within
existing scenarios, UI improvements, and fixes are all fair game.

## Ground rules

- **Every scenario stays local-only and clearly labeled as intentionally
  vulnerable.** Don't add anything that could cause real-world harm if
  someone copy-pasted a "payload" out of context (no real malware, no real
  working exploits against third-party services, no real secrets).
- All fake data (customers, accounts, API keys) must be obviously synthetic.
- Each scenario should map to exactly one OWASP LLM Top 10 (2025) category —
  check `docs/OWASP_MAPPING.md` before adding a new one to avoid duplicates.
- Keep the vulnerability realistic: base new scenarios on patterns described
  in the OWASP guidance, published research, or real (already public)
  incident writeups, not novel attack techniques.

## Adding a scenario

1. `app/scenarios/<your_id>/scenario.py` — export `SCENARIO = Scenario(...)`.
   See `app/scenarios/base.py` for required fields and any existing scenario
   (e.g. `llm06_excessive_agency`) as a template.
2. Write `objective_md`, `hints_md`, and `fix_md` in the same voice as
   existing scenarios: objective states the goal without spelling out the
   exact exploit steps; hints nudge without solving it; fix explains root
   cause + concrete remediation.
3. Implement `check_flag` to detect successful exploitation programmatically
   where possible. If a scenario is more qualitative (e.g. misinformation),
   a best-effort heuristic plus clear guidance in `objective_md` for manual
   verification is fine.
4. Test it end-to-end locally before opening a PR.

## Pull requests

- Keep PRs scoped to one scenario or one fix at a time where possible.
- Describe what OWASP category it covers and how to verify the exploit
  works as intended.
- Run the app locally and confirm the flag actually triggers before
  submitting.

## Reporting issues

Open a GitHub issue with steps to reproduce. If you find a way to break out
of a scenario's intended sandboxing (e.g. affecting another scenario's
state, or anything beyond the scenario's own mock data), please flag that
clearly — it's a bug in the training app itself, not a training objective.
