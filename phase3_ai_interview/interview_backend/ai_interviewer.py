"""AI Interviewer — Ollama integration for question generation and follow-up logic."""
import os
import json
import requests
from shared.config import OLLAMA_API_URL, OLLAMA_MODEL


class AIInterviewer:
    """AI-powered interviewer using Ollama LLM."""

    def __init__(self, ollama_url=None, model=None):
        self.base_url = ollama_url or OLLAMA_API_URL
        self.model = model or OLLAMA_MODEL

    def generate_seed_questions(self, role: str, interview_type: str = "hr_screening") -> list:
        """
        Generate structured seed questions for the interview.

        Args:
            role: Job role (swe, ds, ml, backend, data_eng, general)
            interview_type: Type of interview (hr_screening, technical, behavioral)

        Returns:
            List of seed questions
        """
        # Load question bank if available
        question_bank_path = os.path.join(os.path.dirname(__file__), "..", "interview_questions.json")
        if os.path.exists(question_bank_path):
            with open(question_bank_path, "r") as f:
                bank = json.load(f)
            
            # Get questions for this role
            role_questions = bank.get(role, bank.get("general", []))
            
            # Filter by category
            categories = []
            if interview_type == "hr_screening":
                categories = ["introduction", "behavioral", "cultural_fit"]
            elif interview_type == "technical":
                categories = ["technical", "problem_solving"]
            else:
                categories = list(role_questions.keys())

            questions = []
            for cat in categories:
                if cat in role_questions:
                    questions.extend(role_questions[cat][:3])  # Take 3 per category

            if questions:
                return [q["question"] for q in questions[:5]]

        # Fallback: Use LLM to generate questions
        prompt = self._build_question_prompt(role, interview_type)
        response = self._call_ollama(prompt, max_tokens=500)
        
        # Parse response into questions (expecting numbered list)
        questions = []
        for line in response.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                questions.append(line.lstrip("0123456789.- "))

        return questions[:5] if questions else [
            "Tell me about yourself and your background.",
            "Why are you interested in this role?",
            "What are your key strengths?",
            "Describe a challenging project you worked on.",
            "Where do you see yourself in 5 years?"
        ]

    def generate_follow_up(
        self,
        seed_questions: list,
        transcript: list,
        current_question_index: int
    ) -> dict:
        """
        Generate a follow-up question or response based on candidate's answer.

        Args:
            seed_questions: List of planned questions
            transcript: Conversation transcript so far
            current_question_index: Index of current question

        Returns:
            {
                "response": str,
                "is_follow_up": bool,
                "next_question": str or None
            }
        """
        if not transcript:
            return {
                "response": seed_questions[0] if seed_questions else "Tell me about yourself.",
                "is_follow_up": False,
                "next_question": seed_questions[1] if len(seed_questions) > 1 else None
            }

        # Get last candidate answer
        last_answer = None
        for entry in reversed(transcript):
            if entry.get("speaker") == "candidate":
                last_answer = entry.get("text")
                break

        if not last_answer:
            return {
                "response": "Could you elaborate on that?",
                "is_follow_up": True,
                "next_question": None
            }

        current_q = seed_questions[current_question_index] if current_question_index < len(seed_questions) else ""

        # Check if we have a next question ready
        has_next = current_question_index + 1 < len(seed_questions)
        next_question = seed_questions[current_question_index + 1] if has_next else None

        # Try to use Ollama for personalized response
        ai_response = self._call_ollama_follow_up(current_q, last_answer)

        # If Ollama failed, use generic response
        if not ai_response or "warning" in ai_response.lower() or "not running" in ai_response.lower():
            ai_response = f"Thank you for sharing that. {self._get_generic_acknowledgment()}"

        # Determine if we should move to next question
        is_follow_up = len(last_answer.split()) > 15  # If answer is substantive

        return {
            "response": ai_response.strip(),
            "is_follow_up": is_follow_up,
            "next_question": next_question if is_follow_up else None
        }

    def calculate_interview_scores(self, session: dict) -> dict:
        """
        Calculate composite interview scores from session data.

        Args:
            session: Interview session dict

        Returns:
            Score dict with weighted composite
        """
        transcript = session.get("transcript", [])
        
        # Extract candidate answers
        candidate_text = " ".join([t["text"] for t in transcript if t.get("speaker") == "candidate"])

        # Communication score (based on text analysis)
        word_count = len(candidate_text.split())
        avg_answer_length = word_count / max(len([t for t in transcript if t.get("speaker") == "candidate"]), 1)
        communication_score = min(100, avg_answer_length * 2)  # Scale based on verbosity

        # Relevance score (will be calculated by NLP module)
        relevance_score = 70  # Placeholder — will be wired to Sentence-BERT

        # Confidence score (composite)
        confidence_score = (communication_score * 0.6 + relevance_score * 0.4)

        # Emotion score (from vision module — placeholder)
        emotion_score = 75

        # Eye contact (from vision module — placeholder)
        eye_contact_score = 70

        # Overall weighted composite
        overall_score = (
            communication_score * 0.25 +
            relevance_score * 0.25 +
            confidence_score * 0.20 +
            emotion_score * 0.15 +
            eye_contact_score * 0.15
        )

        return {
            "communication_score": round(communication_score, 2),
            "relevance_score": round(relevance_score, 2),
            "confidence_score": round(confidence_score, 2),
            "emotion_score": round(emotion_score, 2),
            "eye_contact_score": round(eye_contact_score, 2),
            "overall_score": round(overall_score, 2)
        }

    def _get_generic_acknowledgment(self) -> str:
        """Get a generic acknowledgment when Ollama is not available."""
        acknowledgments = [
            "That's a great perspective. Let's move on.",
            "Interesting experience! I'd like to hear more about your goals.",
            "Thank you for sharing. Let's continue to the next question.",
            "Good to know! Now let me ask you something else."
        ]
        # Simple rotation based on time
        import time
        return acknowledgments[int(time.time()) % len(acknowledgments)]

    def _call_ollama_follow_up(self, question: str, answer: str) -> str:
        """Generate a follow-up using Ollama with fallback."""
        prompt = f"""You are an AI HR interviewer conducting a job interview.

Current question: {question}
Candidate's answer: {answer}

Based on the candidate's answer:
1. First, acknowledge their response positively (one sentence)
2. Keep your response conversational and under 30 words

Your response:"""

        return self._call_ollama(prompt, max_tokens=80)

    def _build_question_prompt(self, role: str, interview_type: str) -> str:
        """Build prompt for LLM question generation."""
        return f"""Generate 5 interview questions for a {role} candidate. 
Interview type: {interview_type}

Requirements:
- Mix of behavioral, technical, and cultural fit questions
- Open-ended questions that encourage detailed responses
- Number each question
- Keep questions concise

Questions:"""

    def _call_ollama(self, prompt: str, max_tokens: int = 200) -> str:
        """
        Call Ollama API for text generation.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7
                }
            }

            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            return response.json().get("response", "")

        except requests.exceptions.ConnectionError:
            print(f"Warning: Ollama not running at {self.base_url}. Using fallback responses.")
            return ""
        except Exception as e:
            print(f"Ollama API error: {e}")
            return ""


if __name__ == "__main__":
    interviewer = AIInterviewer()
    
    # Test question generation
    questions = interviewer.generate_seed_questions("swe", "hr_screening")
    print("Generated Questions:")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")
