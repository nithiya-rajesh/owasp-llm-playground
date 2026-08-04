# OWASP LLM Top 10 (2025) — Scenario Mapping

Reference: https://genai.owasp.org/llm-top-10/

| OWASP ID | Category | Scenario | Core mechanism demonstrated |
|---|---|---|---|
| LLM01:2025 | Prompt Injection | `llm01_prompt_injection` | Indirect injection via unsanitized RAG document retrieval; instructions and data share one channel with no separation. |
| LLM01:2025 | Prompt Injection | `llm01_direct_multiturn_injection` | A planted "note" in one turn is trusted as verified policy and acted on in a later turn — no document/RAG pipeline involved. |
| LLM01:2025 | Prompt Injection | `llm01_cross_agent_propagation` | A separate, upstream-compromised "Research Agent"'s output carries an embedded handoff instruction that a second "Approval Agent" trusts as pre-vetted. |
| LLM02:2025 | Sensitive Information Disclosure | `llm02_sensitive_info_disclosure` | No field-level redaction on tool output; a live secret placed directly in the system prompt. |
| LLM02:2025 | Sensitive Information Disclosure | `llm02_error_message_disclosure` | A raw, unsanitized tool error message leaks internal infrastructure details (connection strings, hostnames). |
| LLM02:2025 | Sensitive Information Disclosure | `llm02_cross_agent_data_leakage` | An internal agent has no authorization boundary based on which agent is asking, leaking data across an internal/external agent trust boundary. |
| LLM03:2025 | Supply Chain | `llm03_supply_chain` | Untrusted third-party plugin metadata (from a typosquatted entry) is trusted and injected into model context like first-party content. |
| LLM03:2025 | Supply Chain | `llm03_malicious_finetune_adapter` | A community-uploaded model adapter's own metadata carries a hidden backdoor trigger phrase, trusted the same as verified content. |
| LLM03:2025 | Supply Chain | `llm03_compromised_subagent_registry` | A typosquatted, unverified sub-agent selected from a specialist registry alters the orchestrator's own authorization behavior via its self-declared notes. |
| LLM04:2025 | Data and Model Poisoning | `llm04_data_model_poisoning` | Unmoderated user-submitted "feedback" directly and immediately influences output shown to other users. |
| LLM04:2025 | Data and Model Poisoning | `llm04_fewshot_poisoning` | Unmoderated user-submitted "example" Q&A pairs are treated as trusted few-shot grounding data for future answers. |
| LLM05:2025 | Improper Output Handling | `llm05_improper_output_handling` | Model-authored HTML is rendered without escaping/sanitization — stored XSS primitive. |
| LLM05:2025 | Improper Output Handling | `llm05_ssrf_via_agent_output` | A "fetch this URL" tool has no allowlist on destination host — a model-chosen internal address gets fetched server-side (simulated). |
| LLM06:2025 | Excessive Agency | `llm06_excessive_agency` | A high-impact, irreversible tool (fund transfer) executes with no confirmation step, no allowlist, no limits. |
| LLM06:2025 | Excessive Agency | `llm06_unscoped_admin_api` | A single agent has access to one broad admin tool far exceeding what its stated job requires, with no per-action authorization. |
| LLM06:2025 | Excessive Agency | `llm06_orchestrator_blind_trust` | A privileged orchestrator executes a lower-privileged sub-agent's recommendation with no independent re-evaluation. |
| LLM07:2025 | System Prompt Leakage | `llm07_system_prompt_leakage` | A real secret lives in the system prompt; the model's own "never reveal this" instruction is the only safeguard. |
| LLM07:2025 | System Prompt Leakage | `llm07_error_channel_leakage` | A diagnostic tool's debug/error path echoes back system prompt content — a leakage channel unrelated to direct extraction attempts. |
| LLM08:2025 | Vector and Embedding Weaknesses | `llm08_vector_embedding_weaknesses` | A shared vector store has no tenant/namespace isolation on retrieval, leaking cross-tenant confidential data. |
| LLM08:2025 | Vector and Embedding Weaknesses | `llm08_embedding_keyword_stuffing` | A keyword-stuffed adversarial document artificially games similarity-search ranking regardless of genuine relevance. |
| LLM08:2025 | Vector and Embedding Weaknesses | `llm08_shared_memory_poisoning` | A planted entry in shared multi-agent workspace memory is trusted by a second agent as verified fact, with no provenance tracking. |
| LLM09:2025 | Misinformation | `llm09_misinformation` | A system prompt suppresses appropriate uncertainty, pushing the model to state fabricated facts confidently when it has no supporting data. |
| LLM09:2025 | Misinformation | `llm09_citation_hallucination` | The model fabricates a plausible-looking citation with no real source behind it, when retrieval genuinely returns nothing. |
| LLM10:2025 | Unbounded Consumption | `llm10_unbounded_consumption` | A pagination tool has no iteration cap, no per-session cost ceiling, and no circuit breaker — modeling runaway cost/DoS risk. |
| LLM10:2025 | Unbounded Consumption | `llm10_recursive_subagent_loop` | A "delegate to sub-agent" tool's own output keeps steering the orchestrator into further recursive delegation, with no depth cap. |

## Notes on fidelity

Each scenario models the *mechanism* behind its OWASP category with realistic
(if simplified) mock services — fake customer databases, a toy vector store,
a mock plugin marketplace, and so on — rather than wiring up real production
infrastructure. This keeps the lab runnable with just an Anthropic API key
and no other dependencies, while preserving the actual security lesson: the
missing control (authorization check, output sanitization, tenant
isolation, confirmation step, rate limit, etc.) is the same missing control
you'd need to add in a real system facing the same category of risk.

## Suggested learning order

1. **LLM01, LLM06, LLM07** — the most common and easiest to intuitively grasp.
2. **LLM02, LLM03** — access-control and trust-boundary issues.
3. **LLM04, LLM05, LLM08** — require understanding a bit more of the
   surrounding system (feedback loops, output rendering, multi-tenancy).
4. **LLM09, LLM10** — more qualitative / systemic issues; best tackled last
   once the mechanical injection/agency patterns feel familiar.
