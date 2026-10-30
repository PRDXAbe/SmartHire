"""Flask-SocketIO WebSocket server for real-time AI interview orchestration."""
import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from shared.database import candidates_collection, interview_results_collection
from shared.config import OLLAMA_API_URL, OLLAMA_MODEL

from ai_interviewer import AIInterviewer

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Initialize AI interviewer
interviewer = AIInterviewer(ollama_url=OLLAMA_API_URL, model=OLLAMA_MODEL)

# Active interview sessions
active_interviews = {}


@app.route("/api/interview/start", methods=["POST"])
def start_interview():
    """Initialize a new AI interview session."""
    data = request.json
    candidate_id = data.get("candidate_id", "demo-candidate")

    role = data.get("role", "general")
    interview_type = data.get("interview_type", "hr_screening")

    # Generate seed questions
    seed_questions = interviewer.generate_seed_questions(role, interview_type)

    # Create interview session
    session = {
        "candidate_id": candidate_id,
        "role": role,
        "interview_type": interview_type,
        "start_time": datetime.utcnow().isoformat(),
        "transcript": [],
        "ai_questions": seed_questions,
        "current_question_index": 0,
        "candidate_answers": [],
        "emotion_scores": [],
        "engagement_scores": [],
        "active": True
    }

    active_interviews[candidate_id] = session

    return jsonify({
        "message": "Interview session initialized.",
        "session_id": candidate_id,
        "first_question": seed_questions[0] if seed_questions else "Tell me about yourself.",
        "seed_questions": seed_questions
    }), 200


@app.route("/api/interview/end", methods=["POST"])
def end_interview():
    """End an AI interview session and calculate scores."""
    data = request.json
    candidate_id = data.get("candidate_id", "demo-candidate")

    if candidate_id not in active_interviews:
        return jsonify({"error": "No active interview session."}), 400

    session = active_interviews[candidate_id]
    session["active"] = False
    session["end_time"] = datetime.utcnow().isoformat()

    # Calculate scores
    scores = interviewer.calculate_interview_scores(session)

    # Store results
    result = {
        "candidate_id": candidate_id,
        "role": session["role"],
        "start_time": session["start_time"],
        "end_time": session["end_time"],
        "transcript": session["transcript"],
        "communication_score": scores["communication_score"],
        "emotion_score": scores["emotion_score"],
        "confidence_score": scores["confidence_score"],
        "relevance_score": scores["relevance_score"],
        "eye_contact_score": scores.get("eye_contact_score", 0),
        "overall_score": scores["overall_score"],
        "question_answers": session["candidate_answers"]
    }

    interview_results_collection().insert_one(result)

    # Remove from active sessions
    del active_interviews[candidate_id]

    return jsonify({
        "message": "Interview completed.",
        "scores": scores
    }), 200


@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection."""
    print(f"Client connected: {request.sid}")
    emit("connected", {"message": "Connected to SmartHire interview server."})


@socketio.on("start_interview")
def handle_start_interview(data):
    """Handle interview start from client."""
    candidate_id = data.get("candidate_id")
    if candidate_id in active_interviews:
        emit("interview_started", {
            "first_question": active_interviews[candidate_id]["ai_questions"][0]
        })


@socketio.on("candidate_answer")
def handle_candidate_answer(data):
    """Handle candidate's speech-to-text answer."""
    candidate_id = data.get("candidate_id")
    answer_text = data.get("text", "").strip()

    if not candidate_id or not answer_text:
        return

    print(f"[{candidate_id}] Candidate: {answer_text}")

    if candidate_id not in active_interviews:
        return

    session = active_interviews[candidate_id]

    # Add to transcript
    session["transcript"].append({
        "speaker": "candidate",
        "text": answer_text,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Store candidate answer
    session["candidate_answers"].append({
        "question": session["ai_questions"][session["current_question_index"]] if session["current_question_index"] < len(session["ai_questions"]) else "",
        "answer": answer_text,
        "timestamp": datetime.utcnow().isoformat()
    })

    try:
        # Generate AI follow-up
        ai_response = interviewer.generate_follow_up(
            session["ai_questions"],
            session["transcript"],
            session["current_question_index"]
        )

        # Move to next question if applicable
        if ai_response.get("next_question"):
            session["current_question_index"] += 1
            # Add next question to transcript
            session["transcript"].append({
                "speaker": "ai",
                "text": ai_response["next_question"],
                "timestamp": datetime.utcnow().isoformat()
            })

        print(f"[{candidate_id}] AI: {ai_response['response']}")

        emit("ai_response", {
            "ai_text": ai_response["response"],
            "is_follow_up": ai_response["is_follow_up"],
            "next_question": ai_response.get("next_question")
        })

    except Exception as e:
        print(f"Error generating AI response: {e}")
        # Fallback response
        emit("ai_response", {
            "ai_text": "Thank you for your response. Let's continue with the next question.",
            "is_follow_up": False,
            "next_question": session["ai_questions"][session["current_question_index"] + 1] if session["current_question_index"] + 1 < len(session["ai_questions"]) else None
        })


@socketio.on("video_frame_analysis")
def handle_video_frame(data):
    """Handle video frame for emotion/engagement analysis."""
    candidate_id = data.get("candidate_id")
    frame_data = data.get("frame")  # Base64 encoded frame

    if not candidate_id or not frame_data:
        return

    # Analyze emotion and engagement (Phase 3 vision module)
    # This will be wired up when vision_analysis module is ready
    pass


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection."""
    print(f"Client disconnected: {request.sid}")


if __name__ == "__main__":
    socketio.run(app, debug=True, port=5003)
