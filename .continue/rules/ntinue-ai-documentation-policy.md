---
name: continue-ai-documentation-policy
description: Policy defining mandatory documentation update standards for the cONTINUE ai agent
alwaysApply: true
---

# cONTINUE ai – Documentation Policy

## Overview

This policy defines when and how the **cONTINUE ai** agent must create or update system documentation.

The objective is to ensure that documentation remains consistent, accurate, and aligned with the current state of the system.

---

# When Documentation Is Required

Documentation updates are mandatory when a task involves:

- New feature implementation  
- Behavior modification  
- Contract changes (DTO, schema, payload)  
- API creation or modification  
- Architectural changes  
- Configuration changes  
- Infrastructure updates  
- Deprecation or removal of functionality  

If none of the above apply, documentation updates are not required.

---

# Documentation Location

All official documentation must reside under:

```

/docs

```

The agent must:

- Update the relevant file if it exists  
- Create a new file if no adequate documentation exists  
- Follow the existing project structure  

---

# Required Content Standards

Every documentation update must include:

1. Clear description of the change  
2. Motivation or context  
3. Usage instructions  
4. Examples (when applicable)  
5. Technical impact  
6. Date of update  

---

# API and Contract Changes

If the implementation modifies APIs or data contracts, documentation must:

- Update request examples  
- Update response examples  
- Update schema definitions  
- Reflect any new required or optional fields  
- Document breaking changes explicitly  

---

# Consistency Rules

- Documentation must match the current implementation  
- Code is the technical source of truth  
- Any mismatch must be corrected immediately  
- Outdated documentation must be revised or removed  

---

# Task Completion Rule

An implementation task is NOT complete until:

- Documentation in `/docs` reflects the current behavior  
- Examples match actual implementation  
- No inconsistencies remain  

---

# Ambiguity Handling

If it is unclear whether documentation should be updated:

1. Assume documentation is required  
2. Update conservatively  
3. Avoid leaving implementation undocumented  

---

# Operational Restrictions

- Do NOT finalize implementation without checking documentation  
- Do NOT modify contracts without updating documentation  
- Do NOT create duplicate documentation for the same feature  
- Do NOT leave undocumented breaking changes  

---

# Enforcement Summary

| Change Type | Documentation Required | Must Update `/docs` |
|--------------|------------------------|---------------------|
| New Feature | Yes | Yes |
| Behavior Change | Yes | Yes |
| Contract/API Change | Yes | Yes |
| Config Change | Yes | Yes |
| Infrastructure Change | Yes | Yes |
| Informational Task | No | No |