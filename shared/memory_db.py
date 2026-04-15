"""In-memory database fallback for demos (no MongoDB required)."""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class MemoryCollection:
    """In-memory collection that mimics basic MongoDB operations."""

    def __init__(self, name: str):
        self.name = name
        self.documents: List[Dict[str, Any]] = []
        self._id_counter = 0

    def insert_one(self, document: Dict[str, Any]) -> Any:
        """Insert a document and return a mock InsertOneResult."""
        self._id_counter += 1
        document["_id"] = f"mem_{self.name}_{self._id_counter}"
        document["_inserted_at"] = datetime.utcnow().isoformat()
        self.documents.append(document)
        return MockInsertResult(document["_id"])

    def find(self, query: Dict[str, Any] = None, projection: Dict[str, Any] = None) -> "MemoryCursor":
        """Find documents matching query."""
        if query is None:
            query = {}
        
        results = []
        for doc in self.documents:
            if self._matches_query(doc, query):
                # Apply projection (exclude fields)
                if projection:
                    filtered_doc = {k: v for k, v in doc.items() if k not in projection}
                    results.append(filtered_doc)
                else:
                    results.append(doc)
        
        return MemoryCursor(results)

    def find_one(self, query: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find one document matching query."""
        cursor = self.find(query)
        docs = list(cursor)
        return docs[0] if docs else None

    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> Any:
        """Update one document (simplified)."""
        for doc in self.documents:
            if self._matches_query(doc, query):
                if "$set" in update:
                    doc.update(update["$set"])
                return MockUpdateResult(1)
        return MockUpdateResult(0)

    def delete_one(self, query: Dict[str, Any]) -> Any:
        """Delete one document."""
        for i, doc in enumerate(self.documents):
            if self._matches_query(doc, query):
                self.documents.pop(i)
                return MockDeleteResult(1)
        return MockDeleteResult(0)

    def count_documents(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching query."""
        return len(list(self.find(query)))

    def _matches_query(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Check if document matches query (simple equality only)."""
        for key, value in query.items():
            if doc.get(key) != value:
                return False
        return True

    def to_list(self) -> List[Dict[str, Any]]:
        """Return all documents as list."""
        return self.documents.copy()

    def export_to_json(self, filepath: str):
        """Export all documents to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2, default=str)
        print(f"[MemoryDB] Exported {len(self.documents)} documents to {filepath}")


class MemoryCursor:
    """Cursor that wraps a list of documents."""

    def __init__(self, documents: List[Dict[str, Any]]):
        self.documents = documents

    def __iter__(self):
        return iter(self.documents)

    def __next__(self):
        return next(iter(self.documents))

    def to_list(self, length: int = None) -> List[Dict[str, Any]]:
        """Return documents as list."""
        return self.documents[:length] if length else self.documents


class MockInsertResult:
    def __init__(self, inserted_id: str):
        self.inserted_id = inserted_id


class MockUpdateResult:
    def __init__(self, modified_count: int):
        self.modified_count = modified_count


class MockDeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count


class MemoryDatabase:
    """In-memory database that provides collection access."""

    def __init__(self):
        self._collections: Dict[str, MemoryCollection] = {}

    def __getitem__(self, name: str) -> MemoryCollection:
        """Get or create a collection."""
        if name not in self._collections:
            self._collections[name] = MemoryCollection(name)
        return self._collections[name]

    def get_collection(self, name: str) -> MemoryCollection:
        """Get a collection by name."""
        return self[name]

    def list_collection_names(self) -> List[str]:
        """List all collection names."""
        return list(self._collections.keys())

    def export_all(self, directory: str = "demo_data"):
        """Export all collections to JSON files."""
        os.makedirs(directory, exist_ok=True)
        for name, collection in self._collections.items():
            filepath = os.path.join(directory, f"{name}.json")
            collection.export_to_json(filepath)

    def clear_all(self):
        """Clear all collections."""
        for collection in self._collections.values():
            collection.documents.clear()
            collection._id_counter = 0


# Singleton instance for demo mode
_demo_db = None


def get_demo_database() -> MemoryDatabase:
    """Get or create the global demo database."""
    global _demo_db
    if _demo_db is None:
        _demo_db = MemoryDatabase()
        print("[MemoryDB] Demo mode: Using in-memory storage (no MongoDB)")
    return _demo_db


def reset_demo_database():
    """Reset the demo database (for testing)."""
    global _demo_db
    if _demo_db:
        _demo_db.clear_all()
    _demo_db = None
