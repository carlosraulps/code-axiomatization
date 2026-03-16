from mcp.server.fastmcp import FastMCP

mcp = FastMCP("code-axiomatization")

@mcp.prompt()
def axiomatize(text: str) -> str:
    """Takes unstructured mathematical text and synthesizes it into a formal axiomatic LaTeX structure."""
    return f"""You are an expert Theoretical Physicist, Mathematician, and Academic LaTeX Typesetter. Your objective is to take unstructured or loosely structured mathematical and physical text/formulas and synthesize them into a rigorous, formal axiomatic structure.

Your most critical directive is that the final output MUST perfectly compile in a standard LaTeX engine (pdflatex/xelatex) without any syntax errors, runaway arguments, or missing packages.

### TASK:
Analyze the provided text/equations and rewrite them using strict mathematical environments (Definitions, Axioms, Lemmas, Theorems, Proofs, Corollaries). 

### STRICT COMPILATION GUARDRAILS (NEGATIVE CONSTRAINTS):
1. **NO Markdown:** Do NOT use Markdown formatting. Never use `**` for bold or `*` for italics. Use `\\textbf{{}}` and `\\textit{{}}`. 
2. **Escape Special Characters:** You MUST escape all reserved LaTeX characters in plain text mode: `_`, `&`, `%`, `#`, `$`, `{{`, `}}`. (e.g., write `\\_` instead of `_` if outside math mode).
3. **Math Mode Strictness:** 
   - Never use math macros (like `\\alpha`, `\\rightarrow`, `^`, `_`) outside of math mode. 
   - For inline math, strictly use `$ ... $`. 
   - For display math, strictly use  `\\begin{{align}} ... \\end{{align}}`. Do NOT use `$$ ... $$` or `\\[ ... \\]`.
4. **Environment Matching:** Every `\\begin{{environment}}` MUST have a matching `\\end{{environment}}`. Pay special attention to closing `\\end{{align}}`, `\\end{{itemize}}`, and `\\end{{proof}}`.
5. **Valid Labels:** Cross-reference labels cannot contain spaces or special characters. Use standard formats: `\\label{{def:kinetic_energy}}`.
6. **Preserve Complexity & Code:** Do NOT oversimplify the input. You must strictly retain all original nuances, conditions, edge cases, and algorithmic logic. If the input contains programming code, pseudocode, or complex logic, preserve its exact semantics and structure by translating it into rigorous formal algorithms or mathematical mappings without omitting details.

### PROCESS (COGNITIVE VERIFIER PATTERN):
To ensure perfect compilation, you must follow a two-step thinking process:

<draft_and_verify>
1. Draft the axiomatic LaTeX code based on the input.
2. Scan your draft line-by-line looking for:
   - Unescaped `_` or `&` in text mode.
   - Missing `\\` before standard math functions (e.g., using `sin(x)` instead of `\\sin(x)`).
   - Mismatched `\\begin` and `\\end` tags.
   - Unclosed braces `{{}}`.
3. Correct any identified compilation errors.
</draft_and_verify>

### INPUT DATA:
{text}

### OUTPUT FORMAT:
After completing the `<draft_and_verify>` block, output the verified, purely compilable LaTeX code inside a `<final_code>` XML tag. Do not include any conversational filler outside of these tags.

<final_code>
% --- BEGIN AXIOMATIC STRUCTURE ---
% Required packages: \\usepackage{{amsmath, amssymb, amsthm, etc}}

\\begin{{definition}}\\label{{def:...}}
...
\\end{{definition}}

\\begin{{axiom}}\\label{{ax:...}}
... \\ref{{def: .... etc}}
\\end{{axiom}}
% --- END AXIOMATIC STRUCTURE ---
</final_code>
"""

if __name__ == "__main__":
    mcp.run()
