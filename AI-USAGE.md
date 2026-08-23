# AI-USAGE.md

## Summary

AI tools were used as development assistants during the project for architecture exploration, implementation support, debugging, testing, documentation, and frontend development.

I remained responsible for the final architecture, policy boundaries, integration decisions, testing, and behavior of the submitted system. AI-generated suggestions and code were reviewed, adapted, integrated, and tested before inclusion.

## ChatGPT

ChatGPT was used as a development and reasoning assistant throughout the backend implementation.

Main uses included:

- Exploring and refining the architecture.
- Designing the deterministic policy evaluation and hard-stop boundaries.
- Implementing and debugging backend components.
- Designing relevant-history selection before triage-note generation.
- Designing the Groq/OpenAI triage-note integration.
- Reasoning about fallback behavior when no API key is configured.
- Debugging runtime and syntax errors.
- Reviewing workflow traces and test failures.
- Refining documentation and implementation decisions.

A key design decision was to keep policy authorization outside the LLM. The LLM is only invoked after the backend has determined that a referral is `PERMITTED`.

## Claude

Claude was used for the Streamlit frontend.

It was given the existing backend structure and used to scaffold and connect the UI to the available workflow data. The resulting interface was reviewed and adjusted so that the UI displays backend decisions rather than implementing a separate policy layer.

## Human responsibility

I made and validated the final engineering decisions, including:

- Overall project architecture.
- `UNDERSTAND → DECIDE → ACT` workflow.
- Deterministic policy enforcement.
- Hard-stop behavior for restricted actions.
- Human escalation and handoff behavior.
- Relevant-history selection.
- LLM invocation boundaries.
- Groq/OpenAI provider configuration and deterministic fallback.
- Backend/UI separation.
- Testing and validation of the complete workflow.

I am responsible for understanding and explaining the submitted implementation, including why each safety boundary exists and how the system behaves when presented with cases outside its authority.