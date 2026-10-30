"""Aptitude test grading logic."""
import json
import os


class AptitudeGrader:
    """Handles scoring and section-wise breakdown for aptitude tests."""

    def __init__(self, question_bank_path=None):
        if question_bank_path:
            with open(question_bank_path, "r") as f:
                self.question_bank = json.load(f)
        else:
            self.question_bank = None

    def grade_submission(self, candidate_answers: dict) -> dict:
        """
        Grade a candidate's aptitude test submission.
        
        Args:
            candidate_answers: {question_id: selected_answer, ...}
        
        Returns:
            {
                "total_score": float,
                "total_questions": int,
                "percentage": float,
                "sections": {
                    "logical_reasoning": {"correct": int, "total": int, "percentage": float},
                    ...
                }
            }
        """
        if not self.question_bank:
            raise ValueError("Question bank not loaded.")

        # Build answer key
        answer_key = {}
        section_map = {}  # question_id -> section
        for section, difficulties in self.question_bank.items():
            for difficulty, questions in difficulties.items():
                for q in questions:
                    answer_key[q["id"]] = q["correct"]
                    section_map[q["id"]] = section

        # Grade by section
        section_scores = {}
        total_correct = 0
        total_questions = 0

        for q_id, user_answer in candidate_answers.items():
            section = section_map.get(q_id)
            if section is None:
                continue

            if section not in section_scores:
                section_scores[section] = {"correct": 0, "total": 0}

            section_scores[section]["total"] += 1
            total_questions += 1

            if user_answer == answer_key.get(q_id):
                section_scores[section]["correct"] += 1
                total_correct += 1

        # Calculate percentages
        for section in section_scores:
            s = section_scores[section]
            s["percentage"] = round((s["correct"] / s["total"]) * 100, 2) if s["total"] > 0 else 0

        total_percentage = round((total_correct / total_questions) * 100, 2) if total_questions > 0 else 0

        return {
            "total_score": total_correct,
            "total_questions": total_questions,
            "percentage": total_percentage,
            "sections": section_scores
        }

    def generate_test(self, role: str = "general", num_questions_per_section: int = 10) -> list:
        """
        Dynamically generate a test by selecting questions from the bank.

        Args:
            role: Role-specific filtering (currently uses all questions)
            num_questions_per_section: Questions per section (not per difficulty)

        Returns:
            List of question dicts (without correct answers exposed)
        """
        test_questions = []

        for section, difficulties in self.question_bank.items():
            # Collect all questions from all difficulties for this section
            section_questions = []
            for difficulty, questions in difficulties.items():
                for q in questions:
                    # Add difficulty to question if not present
                    if "difficulty" not in q:
                        q["difficulty"] = difficulty
                    section_questions.append(q)
            
            # Select questions (distribute across difficulties)
            selected = section_questions[:num_questions_per_section]
            for q in selected:
                test_questions.append({
                    "id": q["id"],
                    "question": q["question"],
                    "options": q["options"],
                    "section": section,
                    "difficulty": q["difficulty"]
                })

        return test_questions


def main():
    """Test the grader locally."""
    grader = AptitudeGrader("question_bank.json")
    
    # Simulate candidate answers
    sample_answers = {
        "lr_e_001": "30",
        "lr_e_002": "NBPHQ",
        "qa_e_001": "30",
        "va_e_001": "Plentiful",
        "dt_e_001": "Hyper Text Markup Language"
    }
    
    result = grader.grade_submission(sample_answers)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
