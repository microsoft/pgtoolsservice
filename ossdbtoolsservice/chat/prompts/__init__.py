from pathlib import Path


def load_prompt(name: str) -> str:
    """Load a prompt from the prompts directory"""
    HERE = Path(__file__).parent
    prompt_path = HERE / f"{name}.md"
    with open(prompt_path, "r") as f:
        return f.read().strip()
