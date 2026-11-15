# Hello World Agent

A simple Hello World AI agent for learning and onboarding purposes.

## Business challenge

New users starting with AI agents need a simple, working example they can run and interact with — a "Hello World" agent that responds to messages, serving as a foundation for learning how agents work.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Agent responds successfully to every call | — | 100% successful response rate | — | Agent onboarding / first use | user |

## Key Milestones

1. **Agent is set up** — Project scaffolded and dependencies installed
2. **Agent is running** — Agent server starts without errors
3. **User sends a message** — A greeting or simple question is sent to the agent
4. **Agent returns a response** — Agent replies with a meaningful greeting or answer

## Business Architecture (RBA)

### End-to-End Process

Governance (IT Management)

### Process Hierarchy

```
Governance (Level 1)
└── IT Management (Level 2)
    └── Developer Onboarding
        └── Agent Development Learning
        └── Hello World Prototype
```

### Summary

The challenge maps to IT capability enablement — specifically helping developers get started with AI agent development on SAP BTP through a minimal working prototype.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ------------------ | ------------------- | ---- | ------------------- |
| Simple agent that responds to greetings | Pro-code Python A2A Agent | — | — | — | — | — | No | No external APIs needed; self-contained agent |

### Key findings

- No external APIs or MCP servers are required for this Hello World agent.
- The solution is fully self-contained — the agent responds using its own logic and an LLM backend.
- The Python A2A protocol is the recommended approach for building agents on SAP BTP.
- OpenTelemetry instrumentation will be included for observability from the start.
- This agent serves as a learning template — it can be extended later with MCP tool calls or workflows.

## Recommendations

### Hello World Python Agent

#### Executive Summary

A minimal Python A2A agent that greets users and answers basic questions.

#### Recommended Solution

A pro-code Python agent following the A2A protocol, with no external tool integrations. The agent will respond to any incoming message with a friendly greeting or simple reply. It includes OpenTelemetry instrumentation and a basic test suite as a best-practice foundation.

#### Problem Statement

New developers have no simple starting point to understand how AI agents work on SAP BTP.

#### Affected User Roles

- Developer / engineer new to AI agents on SAP BTP

#### Important factors

##### Low barrier to entry
No external system credentials or API keys are needed — the agent runs standalone.

##### Extensible foundation
The Hello World structure can be extended incrementally with MCP tools, skills, and workflows.

#### Potential risks

##### Oversimplification
The example may feel too simple; clear documentation should guide users on next steps.

#### Recommended solution category

AI Agent

#### Intent fit
95%
