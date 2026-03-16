import re
import logging
from typing import List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class LLMOutputFormatError(Exception):
    """Raised when the LLM output does not contain the required <final_code> tags."""
    pass

class LaTeXEnvironmentError(Exception):
    """Raised when there are mismatched or unclosed LaTeX environments."""
    pass

class LaTeXSyntaxError(Exception):
    """Raised when basic LaTeX syntax errors (like unescaped chars outside math mode) are detected."""
    pass

def extract_latex(text: str) -> str:
    """
    Extracts the LaTeX code strictly from within <final_code> and </final_code> tags.
    
    Args:
        text (str): The raw output string from the LLM.
        
    Returns:
        str: The extracted LaTeX code.
        
    Raises:
        LLMOutputFormatError: If the <final_code> tags are missing or malformed.
    """
    logger.info("Extracting LaTeX from <final_code> tags.")
    match = re.search(r'<final_code>(.*?)</final_code>', text, flags=re.DOTALL)
    if not match:
        raise LLMOutputFormatError("Missing or malformed <final_code> tags in LLM output.")
    return match.group(1).strip()

def sanitize_output(latex_code: str) -> str:
    """
    Sanitizes the extracted LaTeX code by stripping trailing/leading whitespace and
    removing obvious conversational filler.
    
    Args:
        latex_code (str): The extracted LaTeX code.
        
    Returns:
        str: The sanitized LaTeX code.
    """
    logger.info("Sanitizing extracted LaTeX code.")
    # Strip leading/trailing whitespace
    cleaned = latex_code.strip()
    
    # Remove common conversational fillers that might have bled in at the start
    fillers = [
        r"^Here is your code:\s*",
        r"^Here is the LaTeX code:\s*",
        r"^Certainly!.*?\n",
        r"^Sure!.*?\n",
        r"^```[a-zA-Z]*\n", # Remove starting markdown code block
    ]
    for filler in fillers:
        cleaned = re.sub(filler, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
    # Remove closing markdown code block if present
    cleaned = re.sub(r"```\s*$", "", cleaned)
    
    return cleaned.strip()

def validate_environments(latex_code: str) -> None:
    """
    Validates that all \\begin{env} have a matching \\end{env} using a stack-based parser.
    
    Args:
        latex_code (str): The sanitized LaTeX code.
        
    Raises:
        LaTeXEnvironmentError: If an environment fails to close or mismatches.
    """
    logger.info("Validating LaTeX environments.")
    # Find all \begin{...} and \end{...} tags in order of appearance
    env_pattern = re.compile(r'\\(begin|end)\{([^}]+)\}')
    matches = env_pattern.finditer(latex_code)
    
    stack: List[str] = []
    
    for match in matches:
        tag_type = match.group(1) # 'begin' or 'end'
        env_name = match.group(2)
        
        if tag_type == 'begin':
            stack.append(env_name)
        elif tag_type == 'end':
            if not stack:
                raise LaTeXEnvironmentError(f"Found \\end{{{env_name}}} without a corresponding \\begin.")
            
            last_env = stack.pop()
            if last_env != env_name:
                raise LaTeXEnvironmentError(f"Environment mismatch: Expected \\end{{{last_env}}}, but found \\end{{{env_name}}}.")
                
    if stack:
        unclosed = ", ".join(stack)
        raise LaTeXEnvironmentError(f"Unclosed environments at end of document: {unclosed}")

def detect_syntax_errors(latex_code: str) -> None:
    """
    Detects residual Markdown artifacts and common unescaped characters outside of math mode.
    Note: This is a heuristic-based detection.
    
    Args:
        latex_code (str): The sanitized LaTeX code.
        
    Raises:
        LaTeXSyntaxError: If invalid syntax or unescaped characters are found.
    """
    logger.info("Scanning for LaTeX syntax errors and markdown artifacts.")
    
    # 1. Detect Markdown bold/italic. We look for ** or * not followed by math stuff.
    # A simple heuristic: if we see ** it's almost certainly a markdown artifact.
    if re.search(r'\*\*(.*?)\*\*', latex_code):
        raise LaTeXSyntaxError("Detected Markdown bold syntax (**...**). Use \\textbf{} instead.")
    
    # 2. Detect unescaped underscores (_) or ampersands (&) outside of math mode.
    # To do this safely with regex, we can try to mask out the math modes first.
    
    # Mask inline math $...$
    masked_code = re.sub(r'(?<!\\)\$.*?(?<!\\)\$', 'MATH_MODE_MASK', latex_code, flags=re.DOTALL)
    # Mask display math $$...$$ (even though it shouldn't be used, we mask to avoid false positives)
    masked_code = re.sub(r'(?<!\\)\$\$.*?(?<!\\)\$\$', 'MATH_MODE_MASK', masked_code, flags=re.DOTALL)
    # Mask standard math environments
    math_envs = ['equation', 'equation*', 'align', 'align*', 'gather', 'gather*', 'math', 'displaymath']
    for env in math_envs:
        masked_code = re.sub(rf'\\begin\{{{env}\}}.*?\\end\{{{env}\}}', 'MATH_MODE_MASK', masked_code, flags=re.DOTALL)
    
    # Also mask URLs, labels, refs, and cite which might legitimately contain unescaped characters or shouldn't be touched
    masked_code = re.sub(r'\\url\{.*?\}', 'URL_MASK', masked_code)
    masked_code = re.sub(r'\\href\{.*?\}\{.*?\}', 'HREF_MASK', masked_code)
    masked_code = re.sub(r'\\label\{.*?\}', 'LABEL_MASK', masked_code)
    masked_code = re.sub(r'\\ref\{.*?\}', 'REF_MASK', masked_code)
    masked_code = re.sub(r'\\eqref\{.*?\}', 'EQREF_MASK', masked_code)
    masked_code = re.sub(r'\\cite\{.*?\}', 'CITE_MASK', masked_code)

    # Now check for unescaped _ or & in the masked code
    # We look for _ or & that is NOT preceded by a backslash
    unescaped_char_match = re.search(r'(?<!\\)([_&])', masked_code)
    if unescaped_char_match:
        char = unescaped_char_match.group(1)
        raise LaTeXSyntaxError(f"Detected unescaped special character '{char}' outside of math mode. Use '\\{char}' instead.")


def process_llm_response(raw_text: str) -> str:
    """
    Main pipeline function to extract, sanitize, and validate the LLM's LaTeX output.
    
    Args:
        raw_text (str): The raw string output from the LLM.
        
    Returns:
        str: The fully validated and sanitized LaTeX code.
        
    Raises:
        LLMOutputFormatError
        LaTeXEnvironmentError
        LaTeXSyntaxError
    """
    logger.info("Starting LLM response processing pipeline.")
    try:
        # Step 1: Extraction
        latex_code = extract_latex(raw_text)
        
        # Step 2: Sanitization
        sanitized_code = sanitize_output(latex_code)
        
        # Step 3: Structural Validation
        validate_environments(sanitized_code)
        
        # Step 4: Syntax & Hallucination Detection
        detect_syntax_errors(sanitized_code)
        
        logger.info("Processing pipeline completed successfully. Code is valid.")
        return sanitized_code
        
    except (LLMOutputFormatError, LaTeXEnvironmentError, LaTeXSyntaxError) as e:
        logger.error(f"Validation failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Mock LLM strings for demonstration
    
    # 1. Valid Output
    valid_mock = \"\"\"
<final_code>
% --- BEGIN AXIOMATIC STRUCTURE ---
\\begin{definition}\\label{def:force}
Force is defined as the rate of change of momentum.
\\end{definition}

\\begin{theorem}\\label{thm:newton2}
Newton's Second Law.
\\end{theorem}
\\begin{proof}
By Definition \\ref{def:force}, we have:
\\begin{align}
F = m a
\\end{align}
\\end{proof}
% --- END AXIOMATIC STRUCTURE ---
</final_code>
\"\"\"

    # 2. Invalid Output - Mismatched Environments
    mismatched_mock = \"\"\"
<final_code>
\\begin{theorem}
Some text
\\begin{align}
E = mc^2
\\end{equation}
\\end{theorem}
</final_code>
\"\"\"

    # 3. Invalid Output - Unescaped Underscore in text
    syntax_error_mock = \"\"\"
<final_code>
\\begin{definition}
This is a test_variable in text mode.
\\end{definition}
</final_code>
\"\"\"

    print("--- Testing Valid Mock ---")
    try:
        clean_code = process_llm_response(valid_mock)
        print("Result:\n", clean_code)
    except Exception as e:
        print("Error:", e)
        
    print("\\n--- Testing Mismatched Environment Mock ---")
    try:
        process_llm_response(mismatched_mock)
    except Exception as e:
        print("Caught Expected Error:", type(e).__name__, "-", e)
        
    print("\\n--- Testing Syntax Error Mock ---")
    try:
        process_llm_response(syntax_error_mock)
    except Exception as e:
        print("Caught Expected Error:", type(e).__name__, "-", e)
