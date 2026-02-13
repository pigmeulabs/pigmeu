---
name: Segmentation
description: Comportamento de segmentação de tarefas do Agente
---

When operating in "Agent" mode and the user requests implementation of multiple features, tasks, or code changes:

1. First, generate a simple numbered list of planned tasks.
2. Ask the user to specify which tasks should be executed.
3. Implement only the tasks explicitly selected by the user.
4. After implementation, present:
   - The updated numbered list
   - Status of each task (Completed / Pending)
5. Ask the user which pending tasks should be executed next.

Never implement all tasks automatically without user confirmation.