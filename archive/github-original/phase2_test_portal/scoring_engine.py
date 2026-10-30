"""Scoring engine — weighted composite scoring and candidate ranking."""
from shared.database import (
    aptitude_results_collection,
    coding_results_collection,
    interview_results_collection,
    composite_scores_collection,
    candidates_collection
)
from shared.config import APTITUDE_WEIGHT, CODING_WEIGHT, INTERVIEW_WEIGHT


class ScoringEngine:
    """Calculate composite scores and rank candidates."""

    def calculate_composite_score(
        self,
        candidate_id: str,
        aptitude_weight: float = APTITUDE_WEIGHT,
        coding_weight: float = CODING_WEIGHT,
        interview_weight: float = INTERVIEW_WEIGHT
    ) -> dict:
        """
        Calculate weighted composite score for a candidate.

        Args:
            candidate_id: Candidate's unique ID
            aptitude_weight: Weight for aptitude score (default 0.3)
            coding_weight: Weight for coding score (default 0.4)
            interview_weight: Weight for interview score (default 0.3)

        Returns:
            Composite score dict
        """
        # Fetch aptitude result
        aptitude = aptitude_results_collection().find_one({"candidate_id": candidate_id})
        aptitude_score = aptitude.get("percentage", 0) if aptitude else 0

        # Fetch coding results (may have multiple problems)
        coding_results = list(coding_results_collection().find({"candidate_id": candidate_id}))
        if coding_results:
            # Average percentage across all submitted problems
            coding_score = sum(r.get("percentage", 0) for r in coding_results) / len(coding_results)
        else:
            coding_score = 0

        # Fetch interview result
        interview = interview_results_collection().find_one({"candidate_id": candidate_id})
        interview_score = interview.get("overall_score", 0) if interview else 0

        # Calculate composite
        composite = (
            aptitude_score * aptitude_weight +
            coding_score * coding_weight +
            interview_score * interview_weight
        )

        result = {
            "candidate_id": candidate_id,
            "aptitude_score": round(aptitude_score, 2),
            "coding_score": round(coding_score, 2),
            "interview_score": round(interview_score, 2),
            "composite_score": round(composite, 2),
            "weights": {
                "aptitude": aptitude_weight,
                "coding": coding_weight,
                "interview": interview_weight
            }
        }

        # Store in database
        composite_scores_collection().update_one(
            {"candidate_id": candidate_id},
            {"$set": result},
            upsert=True
        )

        return result

    def rank_candidates(self, job_id: str = None) -> list:
        """
        Rank all candidates by composite score.

        Args:
            job_id: Optional filter by job posting

        Returns:
            List of candidate rankings
        """
        query = {}
        if job_id:
            query["job_id"] = job_id

        # Get all composite scores
        scores = list(composite_scores_collection().find(query, {"_id": 0}))

        # Sort by composite score descending
        scores.sort(key=lambda x: x["composite_score"], reverse=True)

        # Add rank
        ranked = []
        for i, s in enumerate(scores, 1):
            # Fetch candidate details
            candidate = candidates_collection().find_one({"candidate_id": s["candidate_id"]})
            ranked.append({
                "rank": i,
                "candidate_id": s["candidate_id"],
                "name": candidate.get("name", "Unknown") if candidate else "Unknown",
                "email": candidate.get("email", "N/A") if candidate else "N/A",
                "composite_score": s["composite_score"],
                "aptitude_score": s["aptitude_score"],
                "coding_score": s["coding_score"],
                "interview_score": s["interview_score"]
            })

        return ranked

    def get_candidate_report(self, candidate_id: str) -> dict:
        """
        Generate a comprehensive report for a single candidate.

        Args:
            candidate_id: Candidate's unique ID

        Returns:
            Full candidate report dict
        """
        candidate = candidates_collection().find_one({"candidate_id": candidate_id})
        if not candidate:
            return None

        aptitude = aptitude_results_collection().find_one({"candidate_id": candidate_id})
        coding_results = list(coding_results_collection().find({"candidate_id": candidate_id}))
        interview = interview_results_collection().find_one({"candidate_id": candidate_id})
        composite = composite_scores_collection().find_one({"candidate_id": candidate_id})

        return {
            "candidate": {
                "id": candidate.get("candidate_id"),
                "name": candidate.get("name"),
                "email": candidate.get("email"),
                "role": candidate.get("role"),
                "resume_match_score": candidate.get("resume_match_score", 0)
            },
            "aptitude": aptitude,
            "coding": coding_results,
            "interview": interview,
            "composite": composite
        }


def main():
    """Test scoring engine locally."""
    engine = ScoringEngine()

    # Example: rank all candidates
    rankings = engine.rank_candidates()
    print("=== Candidate Rankings ===")
    for r in rankings:
        print(f"#{r['rank']}: {r['name']} — {r['composite_score']}%")


if __name__ == "__main__":
    main()
