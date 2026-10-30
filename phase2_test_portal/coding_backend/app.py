"""Flask API for coding test — problem serving, code submission, and grading."""
import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from shared.database import candidates_collection, coding_results_collection
from local_executor import LocalCodeExecutor

app = Flask(__name__)
CORS(app)

# Initialize local code executor (no API key needed)
executor = LocalCodeExecutor(time_limit=5.0, memory_limit=128000)

# Load problems bank
PROBLEMS_PATH = os.path.join(os.path.dirname(__file__), "problems_bank.json")
with open(PROBLEMS_PATH, "r") as f:
    problems_data = json.load(f)

# Active coding sessions
active_sessions = {}


@app.route("/api/coding/problems", methods=["GET"])
def get_problems():
    """Get list of available coding problems (without test cases)."""
    role = request.args.get("role", "general")
    difficulty = request.args.get("difficulty", "all")

    problems = []
    for prob in problems_data["problems"]:
        # Filter by role
        if role != "general" and role not in prob.get("role_tags", []):
            continue

        # Filter by difficulty
        if difficulty != "all" and prob["difficulty"] != difficulty:
            continue

        problems.append({
            "id": prob["id"],
            "title": prob["title"],
            "difficulty": prob["difficulty"],
            "description": prob["description"],
            "examples": prob["examples"],
            "constraints": prob.get("constraints", []),
            "starter_code_python": prob.get("starter_code_python", "")
        })

    return jsonify(problems), 200


@app.route("/api/coding/problems/<problem_id>", methods=["GET"])
def get_problem(problem_id):
    """Get a specific problem (without test cases)."""
    for prob in problems_data["problems"]:
        if prob["id"] == problem_id:
            return jsonify({
                "id": prob["id"],
                "title": prob["title"],
                "difficulty": prob["difficulty"],
                "description": prob["description"],
                "examples": prob["examples"],
                "constraints": prob.get("constraints", []),
                "starter_code_python": prob.get("starter_code_python", "")
            }), 200

    return jsonify({"error": "Problem not found."}), 404


@app.route("/api/coding/execute", methods=["POST"])
def execute_code():
    """Execute candidate's code against a single test case (run mode)."""
    data = request.json
    source_code = data.get("source_code")
    language = data.get("language", "python")
    stdin = data.get("stdin", "")

    if not source_code:
        return jsonify({"error": "source_code is required."}), 400

    result = executor.quick_execute(source_code, language, stdin)

    return jsonify(result), 200


@app.route("/api/coding/submit", methods=["POST"])
def submit_solution():
    """Submit candidate's solution for grading against all test cases."""
    data = request.json
    candidate_id = data.get("candidate_id", "demo-candidate")

    problem_id = data.get("problem_id")
    source_code = data.get("source_code")
    language = data.get("language", "python")

    if not problem_id or not source_code:
        return jsonify({"error": "problem_id and source_code are required."}), 400

    # Find the problem
    problem = None
    for prob in problems_data["problems"]:
        if prob["id"] == problem_id:
            problem = prob
            break

    if not problem:
        return jsonify({"error": "Problem not found."}), 404

    # Run against all test cases
    test_cases = problem["test_cases"]
    time_limit = problem.get("time_limit_seconds", 2)
    memory_limit = problem.get("memory_limit_kb", 128000)

    result = executor.run_test_cases(
        source_code=source_code,
        test_cases=test_cases,
        language=language
    )

    # Add metadata
    result["candidate_id"] = candidate_id
    result["problem_id"] = problem_id
    result["problem_title"] = problem["title"]
    result["difficulty"] = problem["difficulty"]
    result["language"] = language
    result["submitted_at"] = datetime.utcnow().isoformat()
    result["source_code"] = source_code

    # Store in MongoDB
    coding_results_collection().insert_one(result)

    return jsonify(result), 200


@app.route("/api/coding/results/<candidate_id>", methods=["GET"])
def get_results(candidate_id):
    """Retrieve coding test results for a candidate."""

    results = list(coding_results_collection().find(
        {"candidate_id": candidate_id},
        {"_id": 0, "source_code": 0}  # Exclude source code from listing
    ))

    if not results:
        return jsonify({"error": "No results found."}), 404

    return jsonify(results), 200


@app.route("/api/coding/bank-summary", methods=["GET"])
def get_bank_summary():
    """Get a summary of the problem bank."""
    summary = {
        "total_problems": len(problems_data["problems"]),
        "by_difficulty": {},
        "by_role": {}
    }

    for prob in problems_data["problems"]:
        diff = prob["difficulty"]
        summary["by_difficulty"][diff] = summary["by_difficulty"].get(diff, 0) + 1

        for tag in prob.get("role_tags", []):
            summary["by_role"][tag] = summary["by_role"].get(tag, 0) + 1

    return jsonify(summary), 200


if __name__ == "__main__":
    app.run(debug=True, port=5002)
