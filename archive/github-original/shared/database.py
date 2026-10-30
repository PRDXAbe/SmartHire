"""Shared database connection — MongoDB with in-memory fallback for demos."""
from pymongo import MongoClient
from shared.config import MONGO_URI, DB_NAME
from shared.memory_db import get_demo_database, MemoryCollection

# Global flag: set to True to force demo mode (no MongoDB)
FORCE_DEMO_MODE = False

class Database:
    """MongoDB connection with automatic in-memory fallback."""
    _client = None
    _db = None
    _demo_mode = False

    @classmethod
    def get_client(cls):
        if cls._client is None and not cls._demo_mode:
            try:
                cls._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
                cls._client.server_info()  # Test connection
            except Exception as e:
                print(f"[Database] MongoDB unavailable ({e}), switching to demo mode")
                cls._demo_mode = True
                cls._client = None
        return cls._client

    @classmethod
    def get_db(cls):
        if cls._demo_mode or FORCE_DEMO_MODE:
            cls._demo_mode = True
            return get_demo_database()
        
        if cls._db is None:
            client = cls.get_client()
            if client:
                cls._db = client[DB_NAME]
            else:
                cls._demo_mode = True
                return get_demo_database()
        return cls._db

    @classmethod
    def is_demo_mode(cls):
        """Check if running in demo mode."""
        return cls._demo_mode or FORCE_DEMO_MODE

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None


# Collection references (works with both MongoDB and memory DB)
def get_collection(name: str):
    """Get a database collection by name."""
    return Database.get_db()[name]


# Candidate collections
def candidates_collection():
    return get_collection("candidates")

def resumes_collection():
    return get_collection("resumes")

def aptitude_results_collection():
    return get_collection("aptitude_results")

def coding_results_collection():
    return get_collection("coding_results")

def interview_results_collection():
    return get_collection("interview_results")

def composite_scores_collection():
    return get_collection("composite_scores")

def jobs_collection():
    return get_collection("jobs")

def sessions_collection():
    return get_collection("sessions")


# Demo mode utilities
def export_demo_data(directory: str = "demo_data"):
    """Export all in-memory data to JSON files (demo mode only)."""
    if Database.is_demo_mode():
        get_demo_database().export_all(directory)

def clear_demo_data():
    """Clear all in-memory data (demo mode only)."""
    from shared.memory_db import reset_demo_database
    reset_demo_database()
    Database._db = None
