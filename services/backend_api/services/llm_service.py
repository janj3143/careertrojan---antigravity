
# CareerTrojan LLM Service Stub
# Bridges the gap for local runtime operations without heavy GPU dependency

class LLMService:
    def __init__(self):
        self.available = True
        
    def complete(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Simulated completion for runtime environment
        """
        return f"Simulated AI Response to: {prompt[:50]}..."
        
    def analyze_resume(self, text: str) -> dict:
        return {
            "summary": "Strong candidate profile.",
            "score": 85,
            "skills": ["Python", "React", "FastAPI"]
        }
