import re
import sys

def post_process_latex(text: str) -> str:
    # 1. Extract content from <final_code> if present
    match = re.search(r'<final_code>(.*?)</final_code>', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    else:
        # fallback: remove markdown blocks if no tag found
        text = re.sub(r'^```[a-zA-Z]*\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'```$', '', text, flags=re.MULTILINE)
        
    # 2. Check for mismatched begins/ends
    begins = len(re.findall(r'\\begin\{.*?\}', text))
    ends = len(re.findall(r'\\end\{.*?\}', text))
    
    if begins != ends:
        print(f"WARNING: Mismatched \\begin ({begins}) and \\end ({ends}) tags found!", file=sys.stderr)

    # 3. Replace Markdown bold/italic (Basic fixes if the model failed)
    text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)
    text = re.sub(r'\*(.*?)\*', r'\\textit{\1}', text)
    
    # 4. Replace $$ ... $$ with \begin{align} ... \end{align}
    def replace_display_math(m):
        content = m.group(1).strip()
        return f"\\begin{{align}}\n{content}\n\\end{{align}}"
        
    text = re.sub(r'\$\$(.*?)\$\$', replace_display_math, text, flags=re.DOTALL)
    
    # 5. Fix common unescaped ampersands outside of math/table environments (Naive fix, can be expanded)
    # Note: Full LaTeX parsing is complex, this serves as a basic automated check.
    
    return text.strip()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            processed = post_process_latex(content)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(processed)
            print(f"Successfully post-processed LaTeX in: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        content = sys.stdin.read()
        print(post_process_latex(content))
