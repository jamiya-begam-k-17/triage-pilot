# DECISIONS.md

> **TL;DR:** TriagePilot automates the caseworker's morning triage workflow, but policy decisions stay in deterministic backend code. The LLM is only used to draft triage notes after an action is confirmed as permitted. Restricted cases are structurally stopped and escalated or handed off to a human, with every decision recorded in the execution trace.

## 1. Policy decision comes before action

The workflow is deliberately structured as:

`UNDERSTAND → DECIDE → ACT`

For each referral, the agent retrieves the resident's relevant history and identifies the requested action. The policy is then evaluated before any triage action is performed.

The policy check is not a prompt instruction. It is an explicit backend control-flow gate.

The result is one of:

- `PERMITTED` → continue to triage-note generation.
- `REQUIRES_APPROVAL` → create an escalation package and stop.
- `HANDOFF` → create a caseworker handoff and stop.

There is no path from `REQUIRES_APPROVAL` or `HANDOFF` into the permitted-action branch.

## 2. Relevant history is selected before drafting

The agent does not blindly pass the resident's entire history to the triage process.

`get_relevant_history()` selects the events relevant to the current referral. Those events are then used as context for the workflow and, when permitted, the triage note.

This keeps the generated note focused on evidence relevant to the referral.

## 3. What the agent cannot do without a human

The agent cannot independently complete an action that the policy marks as requiring approval.

For those cases, the workflow:

1. records the policy decision;
2. creates an escalation package;
3. records a hard stop;
4. returns without performing the requested action.

Cases requiring human caseworker handling are similarly stopped and handed off.

A separate hard stop applies to households containing a person under 18. These referrals cannot reach triage-note generation and are handed off to a caseworker instead.

These restrictions are enforced by backend control flow, not by LLM instructions. The agent can prepare information for a human, but it cannot cross these policy boundaries by itself.

## 4. The LLM is used for drafting, not authorization

The LLM API is used to generate the triage note only after the referral has been determined to be `PERMITTED`.

The order is deliberately:

`policy decision → PERMITTED → LLM triage note → save note`

The LLM does not decide whether an action is permitted, override the policy evaluator, or enforce the approval gate.

This keeps language generation separate from authority decisions.

## 5. Policy is separated from the workflow

The authority rules live in the policy/configuration layer rather than being scattered throughout the agent.

The workflow asks the policy layer for a decision and acts on that result.

This was intentional because the problem states that the requirements will change on day two. A policy change should not require redesigning the entire workflow.

## 6. Every decision is traceable

The execution trace records the important stages of each referral:

- referral being processed;
- relevant history retrieved;
- requested action;
- policy decision;
- policy reason/reference;
- action taken or not taken;
- escalation or handoff;
- triage-note generation.

Hard stops are explicitly recorded.

This allows a supervisor to reconstruct what the agent did, why it did it, and what it deliberately did not do.

## 7. One restricted referral does not stop the queue

Referrals are processed independently.

If one referral requires approval or human handoff, that case stops, but the remaining referrals continue through the workflow.

This allows permitted morning work to continue without allowing an out-of-authority case to derail the entire run.

## 8. UI is separate from the safety logic

The Streamlit UI provides visibility into the backend through:

- dashboard;
- referral queue;
- referral details;
- execution trace;
- policy reasons;
- escalation and handoff outcomes.

The UI does not implement the authority boundary. Safety decisions remain in the backend so the guardrails do not depend on the interface being used.

## 9. Deliberate scope cuts

The implementation focuses on the required morning workflow and guardrails rather than building a production case-management system.

I deliberately kept:

- approval handling as a demonstrated backend hard stop rather than a real authentication/approval service;
- resident history as the provided mock API;
- LLM integration limited to triage-note drafting;
- the Streamlit UI as a visibility layer rather than a second workflow engine.

The first production improvements would be persistent approval state, authenticated supervisor actions, stronger audit storage, and additional failure/retry handling around external services.

## Final design principle

TriagePilot is not designed to be an unrestricted autonomous caseworker.

It automates the repetitive parts of the morning workflow, uses the LLM where language generation is useful, and stops when the policy requires a human.

**The agent can prepare a case for a human, but it cannot silently act beyond its authority.**