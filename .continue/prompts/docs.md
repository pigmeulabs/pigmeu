name: DocGenerate
version: 0.0.1
schema: v1
prompts:
  - name: DocGeneratePrompt
    description: DocGeneratePrompt
    prompt: >-
      Please generate a comprehensive external documentation file for the
      following Python module.

      Requirements:

      Overview of the module's purpose and architecture

      Description of key classes, functions, and their responsibilities

      Usage examples with code snippets

      Installation and dependency instructions (mention Docker or venv if
      applicable)

      Notes on extensibility or integration into larger systems

      Format output as Markdown (or RST if specified)
