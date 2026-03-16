import re
import logging
import os
from typing import List, Set

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DocumentChunker:
    """
    Handles the splitting of Markdown and LaTeX documents into logical chunks
    while ensuring math environments are never split in the middle.
    """
    
    def __init__(self, target_lines: int = 75):
        self.target_lines = target_lines

    def chunk_document(self, file_path: str) -> List[str]:
        """
        Reads the input file and splits it into safe, logical chunks.
        
        Args:
            file_path (str): The path to the input .md or .tex file.
            
        Returns:
            List[str]: A list of text chunks.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        return self._smart_split(lines)

    def _smart_split(self, lines: List[str]) -> List[str]:
        """
        Splits lines into chunks without breaking display math or LaTeX environments.
        """
        chunks: List[str] = []
        current_chunk: List[str] = []
        
        in_display_math = False
        in_bracket_math = False
        env_stack: List[str] = []
        
        # Regex patterns to detect environment boundaries
        display_math_toggle = re.compile(r'(?<!\\)\$\$')
        bracket_math_open = re.compile(r'(?<!\\)\\\[')
        bracket_math_close = re.compile(r'(?<!\\)\\\]')
        begin_env = re.compile(r'\\begin\{([^}]+)\}')
        end_env = re.compile(r'\\end\{([^}]+)\}')

        for line in lines:
            current_chunk.append(line)
            
            # Count $$ occurrences on this line to toggle display math state
            dollars = len(display_math_toggle.findall(line))
            if dollars % 2 != 0:
                in_display_math = not in_display_math
                
            if bracket_math_open.search(line):
                in_bracket_math = True
            if bracket_math_close.search(line):
                in_bracket_math = False
                
            for match in begin_env.finditer(line):
                env_stack.append(match.group(1))
            for match in end_env.finditer(line):
                if env_stack and env_stack[-1] == match.group(1):
                    env_stack.pop()
                    
            is_inside_math = in_display_math or in_bracket_math or len(env_stack) > 0
            
            # Split if we reached the target lines AND we are strictly outside any math/env blocks
            if len(current_chunk) >= self.target_lines and not is_inside_math:
                chunks.append("".join(current_chunk))
                current_chunk = []
                
        if current_chunk:
            chunks.append("".join(current_chunk))
            
        return chunks


class AgentMemory:
    """
    Maintains the Global State for the distillation agent.
    Keeps track of all \\label{} tags generated across chunks.
    """
    def __init__(self):
        self.labels: Set[str] = set()
        
    def add_labels(self, new_labels: List[str]) -> None:
        """Adds new labels to the global memory."""
        for label in new_labels:
            clean_label = label.strip()
            if clean_label:
                self.labels.add(clean_label)
        
    def get_labels_context(self) -> str:
        """Returns the context string of previously defined labels for the LLM."""
        if not self.labels:
            return "No previous labels defined."
        return "PREVIOUSLY DEFINED LABELS:\n" + ", ".join(sorted(self.labels))


class AxiomatizationWorker:
    """
    Handles the LLM interaction, executes the smart distillation prompt,
    extracts XML tags, and performs retry-loop validation.
    """
    
    SYSTEM_PROMPT = """You are an elite Theoretical Physicist and Academic Typesetter. Your task is to distill a chunk of a physics/math document into a pure, formal axiomatic LaTeX structure.

### CRITICAL DIRECTIVE: SMART DISTILLATION
You are building an axiomatic foundation, not a textbook. 
- **WHAT TO KEEP:** You must extract all fundamental concepts and map them to strict environments: \\begin{definition}, \\begin{axiom}, \\begin{lemma}, \\begin{theorem}, \\begin{proof}, \\begin{corollary}. You must also preserve user conceptual questions or insights using \\begin{note}[Handwritten].
- **WHAT TO OMIT:** You MUST silently discard repetitive algebraic shuffling, routine numerical calculations (e.g., plugging numbers into a formula to get a final value), and redundant examples. Keep the core logical steps of a proof, but compress trivial intermediate algebra.

### RULES:
1. **Memory:** You are provided with "PREVIOUSLY DEFINED LABELS". If referencing a past concept, use \\ref{...} with those exact labels.
2. **Labeling:** Every new environment and major equation must have a unique \\label{...}.
3. **Strict Formatting:** Output MUST be perfectly compilable LaTeX. No markdown (`**` or `*`). Escape special characters in text mode (`\\_`, `\\&`).
4. **Draft and Verify:** Use a <draft_and_verify> block to explicitly state what core concepts you are extracting and what numerical/repetitive noise you are intentionally omitting.

### OUTPUT FORMAT:
<draft_and_verify>
1. Extracting: [List the core theorems/definitions]
2. Omitting: [List the numericals/repetitive algebra discarded]
3. Compilability check: [Verify labels and syntax]
</draft_and_verify>

<new_labels>
[comma-separated list of new \\label{} tags created]
</new_labels>

<final_code>
% Your rigorous, distilled LaTeX code here
</final_code>"""

    def __init__(self, memory: AgentMemory, max_retries: int = 3):
        self.memory = memory
        self.max_retries = max_retries
        
    def _mock_call_llm_api(self, system_prompt: str, user_prompt: str) -> str:
        """
        Mocks the LLM API call. In a real system, this integrates with OpenAI/Gemini/Anthropic.
        """
        # Simulated response for testing purposes
        return """<draft_and_verify>
1. Extracting: Core definition of Energy
2. Omitting: Trivial algebraic expansion steps
3. Compilability check: Labels verified
</draft_and_verify>
<new_labels>
def:energy, eq:kinetic
</new_labels>
<final_code>
\\begin{definition}\\label{def:energy}
Energy is defined strictly.
\\end{definition}
\\begin{equation}\\label{eq:kinetic}
K = \\frac{1}{2}mv^2
\\end{equation}
</final_code>"""

    def process_chunk(self, chunk_text: str) -> str:
        """
        Feeds a chunk to the LLM, validates the output, and updates memory.
        
        Args:
            chunk_text (str): The text chunk to process.
            
        Returns:
            str: The distilled and validated LaTeX code for this chunk.
        """
        user_prompt = f"{self.memory.get_labels_context()}\n\n### CHUNK CONTENT:\n{chunk_text}"
        
        for attempt in range(self.max_retries):
            try:
                # 1. Call LLM
                response = self._mock_call_llm_api(self.SYSTEM_PROMPT, user_prompt)
                
                # 2. Extract <final_code> and <new_labels>
                code_match = re.search(r'<final_code>(.*?)</final_code>', response, re.DOTALL)
                labels_match = re.search(r'<new_labels>(.*?)</new_labels>', response, re.DOTALL)
                
                if not code_match:
                    raise ValueError("LLM response missing <final_code> tags.")
                    
                final_code = code_match.group(1).strip()
                
                # 3. Basic Structural Validation: Check \begin vs \end counts
                begins = len(re.findall(r'\\begin\{.*?\}', final_code))
                ends = len(re.findall(r'\\end\{.*?\}', final_code))
                if begins != ends:
                    raise ValueError(f"Mismatched environments: {begins} \\begin vs {ends} \\end tags.")
                    
                # 4. Update Memory
                if labels_match:
                    new_labels_str = labels_match.group(1)
                    new_labels = [l.strip() for l in new_labels_str.split(',')]
                    self.memory.add_labels(new_labels)
                    
                return final_code
                
            except Exception as e:
                logger.warning(f"Chunk processing attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    logger.error("Max retries reached. Returning commented error chunk.")
                    return f"% ERROR: Failed to distill chunk after {self.max_retries} attempts.\n"
                    
        return ""


class MasterPipeline:
    """
    Orchestrates the entire agentic workflow: reading, chunking, distilling, and assembling.
    """
    def __init__(self, target_lines: int = 75, max_retries: int = 3):
        self.chunker = DocumentChunker(target_lines=target_lines)
        self.memory = AgentMemory()
        self.worker = AxiomatizationWorker(self.memory, max_retries=max_retries)
        
    def run(self, input_path: str, output_path: str) -> None:
        """
        Executes the distillation pipeline on a given file.
        
        Args:
            input_path (str): The raw .md or .tex document path.
            output_path (str): The path to save the final distilled .tex document.
        """
        logger.info(f"Starting Axiomatic Distillation for: {input_path}")
        
        # 1. Chunking
        chunks = self.chunker.chunk_document(input_path)
        logger.info(f"Document successfully split into {len(chunks)} chunks.")
        
        # 2. Processing Chunks Sequentially
        all_distilled_latex = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}...")
            distilled_latex = self.worker.process_chunk(chunk)
            all_distilled_latex.append(distilled_latex)
            
        # 3. Assemble and Save
        final_document = "% --- DISTILLED AXIOMATIC DOCUMENT ---\n\n"
        final_document += "\n\n% --- NEXT CHUNK ---\n\n".join(all_distilled_latex)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_document)
            
        logger.info(f"Distillation complete! Output saved to: {output_path}")

if __name__ == "__main__":
    # --- Quick Demonstration ---
    logger.info("Running demonstration script...")
    
    # Create a mock input file
    mock_input_path = "mock_input.tex"
    mock_output_path = "distilled_output.tex"
    with open(mock_input_path, 'w', encoding='utf-8') as f:
        f.write("Some long physics document...\n$$ E = mc^2 $$\n\\begin{equation}\nF = ma\n\\end{equation}\n")
        
    pipeline = MasterPipeline()
    pipeline.run(mock_input_path, mock_output_path)
    
    # Cleanup mock files
    if os.path.exists(mock_input_path):
        os.remove(mock_input_path)
    if os.path.exists(mock_output_path):
        os.remove(mock_output_path)
