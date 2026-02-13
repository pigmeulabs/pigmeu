---
name: continue-ai-cot-policy
description: Policy defining conditional Chain of Thought usage for implementation tasks in the cONTINUE ai agent
alwaysApply: true
---

# cONTINUE ai – Chain of Thought Policy

## Overview

This policy defines when and how the **cONTINUE ai** agent must apply structured reasoning (Chain of Thought).

The objective is to ensure technical rigor during implementation tasks while avoiding unnecessary overhead in non-implementation tasks.

---

# Task Classification

Before executing any task, classify it as one of the following:

## Implementation Task

Includes:

- Writing or modifying code  
- Refactoring  
- Bug fixes  
- API creation or modification  
- Contract changes (DTO, schema, payload)  
- Architectural changes  
- Infrastructure configuration  
- Automation scripts  

## Non-Implementation Task

Includes:

- Explanations  
- Conceptual analysis  
- Text generation  
- Suggestions  
- Documentation-only requests  

---

# Chain of Thought (COT) Usage

## Apply COT ONLY for Implementation Tasks

For any implementation task, the agent MUST apply structured reasoning before execution.

### Required Structured Reasoning Steps

1. Clearly define the technical objective  
2. Identify direct and indirect impacts  
3. Decompose the task into executable steps  
4. Identify dependencies  
5. Determine execution order  
6. Assess risks  
7. Execute step-by-step  
8. Validate each step before proceeding  
9. Perform final consistency review  

---

# Exposure of Reasoning

- Chain of Thought is applied internally.  
- Do NOT expose detailed reasoning unless explicitly requested.  
- Provide concise, objective final outputs by default.  

---

# Ambiguity Handling

If a task is:

- Ambiguous  
- Incomplete  
- Contradictory  
- High impact without sufficient context  

The agent must:

1. Stop execution  
2. Request clarification  
3. Avoid making critical assumptions  

---

# Operational Restrictions

- Do NOT skip structured reasoning for implementation tasks.  
- Do NOT apply formal Chain of Thought to non-implementation tasks.  
- Do NOT execute implementation tasks without prior structured analysis.  

---

# Enforcement Summary

| Task Type | Apply COT | Structured Validation Required |
|------------|------------|-------------------------------|
| Implementation | Yes | Yes |
| Non-Implementation | No | No |

