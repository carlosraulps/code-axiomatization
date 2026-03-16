# Code Axiomatization Skill

An AI Agent Skill that takes unstructured or loosely structured mathematical and physical text/formulas and synthesizes them into a rigorous, formal axiomatic LaTeX structure.

## Overview
This repository contains the skill configuration and an MCP Server, designed to be seamlessly integrated with both **Anthropic Claude Desktop** and **Gemini CLI**.

### Expected Input
Unstructured text containing mathematical derivations, physical explanations, or rough math notes.

### Expected Output
A fully rigorous, compilable LaTeX structure utilizing standard AMS-LaTeX environments: `\begin{definition}`, `\begin{axiom}`, `\begin{theorem}`, `\begin{proof}`, etc. All equations will be properly formatted and labeled using the AMS standard `\begin{align}` or `\begin{equation}`.

---

## 🚀 Gemini CLI Integration

We provide a direct skill file ready for [Gemini CLI](https://geminicli.com/docs/cli/skills/). 
The skill is defined in `.gemini/skills/axiomatize.md`.

### Usage
If you are inside this repository, you can directly run:
```bash
cat physics_notes.txt | gemini axiomatize > output.tex
```

To install the skill globally so you can use it from anywhere:
```bash
mkdir -p ~/.gemini/skills
cp .gemini/skills/axiomatize.md ~/.gemini/skills/
```
Then run from anywhere: `cat input.txt | gemini axiomatize > output.tex`

---

## 🤖 Claude Desktop Integration (MCP)

For Anthropic Claude, this skill is exposed as a [Model Context Protocol (MCP)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) Prompt using `FastMCP`. Claude can natively consume this prompt to configure its behavior and synthesize your math text.

### Installation

1. Add the MCP server to your Claude Desktop configuration:

Open your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the following configuration (replace `/path/to/code-axiomatization` with the absolute path to this folder):

```json
{
  "mcpServers": {
    "code-axiomatization": {
      "command": "uvx",
      "args": [
        "--from",
        "/path/to/code-axiomatization",
        "code-axiomatization"
      ]
    }
  }
}
```

### Usage
Once Claude Desktop is restarted, click the "Attach" (paperclip) icon in Claude, navigate to "Prompts", and you will see the **axiomatize** prompt. You can provide the text, and Claude will directly generate the formal LaTeX output!

---

## Skill Instructions (`SKILL.md`)

If you want to use this in a Custom GPT or standard LLM UI, simply copy the contents of `SKILL.md` into the *System Prompt* or *Instructions* field of your agent.
