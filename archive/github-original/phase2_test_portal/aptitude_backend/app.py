"""Flask API for aptitude test — question serving, submission, and grading."""
import os
import sys
from datetime import datetime
from bson import ObjectId
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from shared.database import candidates_collection, aptitude_results_collection
from grader import AptitudeGrader

app = Flask(__name__)
CORS(app)

# Custom JSON encoder to handle MongoDB ObjectId
class CustomJSONEncoder:
    @staticmethod
    def encode(obj):
        from flask import jsonify
        import json
        return json.dumps(obj, default=CustomJSONEncoder.json_serial)
    
    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

# Initialize grader
QUESTION_BANK_PATH = os.path.join(os.path.dirname(__file__), "question_bank.json")
grader = AptitudeGrader(QUESTION_BANK_PATH)

# Active test sessions: {candidate_id: {"start_time": datetime, "answers": {}, "submitted": bool}}
active_sessions = {}


def sanitize_for_json(obj):
    """Recursively convert MongoDB ObjectId and other non-serializable types to strings."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


@app.route("/api/aptitude/generate", methods=["POST"])
def generate_test():
    """Generate an aptitude test for a candidate."""
    data = request.json
    candidate_id = data.get("candidate_id", "demo-candidate")
    role = data.get("role", "general")
    questions_per_section = data.get("questions_per_section", 5)

    test_questions = grader.generate_test(role=role, num_questions_per_section=questions_per_section)

    # Initialize active session
    active_sessions[candidate_id] = {
        "start_time": datetime.utcnow().isoformat(),
        "answers": {},
        "submitted": False,
        "total_questions": len(test_questions)
    }

    return jsonify({
        "test_id": candidate_id,
        "questions": test_questions,
        "total_questions": len(test_questions),
        "time_limit_minutes": 30
    }), 200


@app.route("/api/aptitude/submit-answer", methods=["POST"])
def submit_answer():
    """Submit a single answer during the test."""
    try:
        data = request.json
        candidate_id = data.get("candidate_id", "demo-candidate")

        if candidate_id not in active_sessions:
            return jsonify({"error": "No active test session."}), 400

        session = active_sessions[candidate_id]
        if session["submitted"]:
            return jsonify({"error": "Test already submitted."}), 400

        question_id = data.get("question_id")
        answer = data.get("answer")

        if not question_id or not answer:
            return jsonify({"error": "question_id and answer are required."}), 400

        session["answers"][question_id] = answer

        return jsonify({"message": "Answer recorded."}), 200
    except Exception as e:
        print(f"Error during answer submission: {e}")
        return jsonify({"error": f"Failed to record answer: {str(e)}"}), 500


@app.route("/api/aptitude/submit", methods=["POST"])
def submit_test():
    """Submit the complete aptitude test for grading."""
    try:
        data = request.json
        candidate_id = data.get("candidate_id", "demo-candidate")

        if candidate_id not in active_sessions:
            return jsonify({"error": "No active test session."}), 400

        session = active_sessions[candidate_id]
        if session["submitted"]:
            return jsonify({"error": "Test already submitted."}), 400

        # Mark as submitted
        session["submitted"] = True
        session["end_time"] = datetime.utcnow().isoformat()

        # Grade the submission
        results = grader.grade_submission(session["answers"])
        results["candidate_id"] = candidate_id
        results["start_time"] = session["start_time"]
        results["end_time"] = session["end_time"]
        results["answers_count"] = len(session["answers"])

        # Store in MongoDB (with error handling)
        try:
            aptitude_results_collection().insert_one(results)
        except Exception as db_error:
            print(f"Warning: Failed to store results in MongoDB: {db_error}")
            # Continue anyway - don't fail the submission if DB is down

        # Remove from active sessions
        del active_sessions[candidate_id]

        # Sanitize results before sending (convert ObjectId, datetime, etc.)
        sanitized_results = sanitize_for_json(results)

        return jsonify({
            "message": "Test submitted successfully.",
            "results": sanitized_results
        }), 200
    except Exception as e:
        print(f"Error during test submission: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500


@app.route("/api/aptitude/results/<candidate_id>", methods=["GET"])
def get_results(candidate_id):
    """Retrieve aptitude test results for a candidate."""

    result = aptitude_results_collection().find_one(
        {"candidate_id": candidate_id},
        {"_id": 0}
    )

    if not result:
        return jsonify({"error": "No results found."}), 404

    # Sanitize result before sending (convert ObjectId, datetime, etc.)
    sanitized_result = sanitize_for_json(result)

    return jsonify(sanitized_result), 200


@app.route("/api/aptitude/bank", methods=["GET"])
def get_question_bank_summary():
    """Get a summary of the question bank (for admin)."""
    summary = {}
    for section, difficulties in grader.question_bank.items():
        summary[section] = {}
        for difficulty, questions in difficulties.items():
            summary[section][difficulty] = len(questions)
    return jsonify(summary), 200


if __name__ == "__main__":
    app.run(debug=True, port=5001)
