import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import re

class SelfLearner:
    def __init__(self, data_file: str = 'data/self_training.json'):
        self.data_file = Path(__file__).parent.parent.parent / data_file
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load or create self-training data"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "learned_concepts": {},
            "definitions": {},
            "patterns": {},
            "conversation_history": [],
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
                "total_conversations": 0,
                "learning_sessions": 0
            }
        }

    def _save_data(self):
        """Save current data to file"""
        self.data["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    def learn_from_conversation(self, user_msg: str, ai_response: str):
        """Learn from conversation patterns"""
        # Extract potential math concepts
        math_terms = re.findall(r'\b(?:sum|difference|product|quotient|equation|variable|coefficient|term|expression|formula)\b', 
                              user_msg + ' ' + ai_response, 
                              re.IGNORECASE)
        
        # Update learned concepts
        for term in math_terms:
            term = term.lower()
            if term not in self.data["learned_concepts"]:
                self.data["learned_concepts"][term] = {
                    "occurrences": 0,
                    "context_examples": []
                }
            self.data["learned_concepts"][term]["occurrences"] += 1
            if len(self.data["learned_concepts"][term]["context_examples"]) < 5:
                self.data["learned_concepts"][term]["context_examples"].append({
                    "user_msg": user_msg,
                    "ai_response": ai_response,
                    "timestamp": datetime.now().isoformat()
                })

        # Store conversation
        self.data["conversation_history"].append({
            "user_msg": user_msg,
            "ai_response": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update metadata
        self.data["metadata"]["total_conversations"] += 1
        self._save_data()

    def add_definition(self, term: str, definition: str):
        """Add or update a definition"""
        self.data["definitions"][term.lower()] = {
            "definition": definition,
            "added": datetime.now().isoformat()
        }
        self._save_data()

    def get_definition(self, term: str) -> str:
        """Get definition for a term"""
        return self.data["definitions"].get(term.lower(), {}).get("definition")

    def get_learned_concepts(self) -> Dict[str, Any]:
        """Get all learned concepts"""
        return self.data["learned_concepts"]

    def find_similar_conversations(self, query: str, limit: int = 3) -> List[Dict]:
        """Find similar past conversations"""
        # Simple word matching for now
        query_words = set(query.lower().split())
        similar = []
        
        for conv in self.data["conversation_history"]:
            conv_words = set(conv["user_msg"].lower().split())
            intersection = query_words & conv_words
            if intersection:
                similar.append(conv)
                
        return sorted(similar, 
                     key=lambda x: len(set(x["user_msg"].lower().split()) & query_words),
                     reverse=True)[:limit]
