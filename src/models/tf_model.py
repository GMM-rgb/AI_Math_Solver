import json
import os
import random
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class MathTFModel:
    def __init__(self):
        self.initialized = False
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        self.training_data = self._load_training_data()
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.conversation_vectors = None
        self.initialize_model()

    def _load_training_data(self):
        """Load training data from JSON file"""
        try:
            with open(os.path.join(self.data_dir, 'training_data.json'), 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading training data: {e}")
            return {}

    def initialize_model(self):
        """Initialize the model with conversation data"""
        try:
            # Extract all conversation variations
            conversations = self.training_data.get('conversations', [])
            texts = []
            for conv in conversations:
                texts.extend(conv.get('variations', []))

            if texts:
                # Create TF-IDF vectors
                self.conversation_vectors = self.vectorizer.fit_transform(texts)
                self.conversations_map = {}
                idx = 0
                for conv in conversations:
                    for _ in conv.get('variations', []):
                        self.conversations_map[idx] = conv
                        idx += 1
                self.initialized = True
        except Exception as e:
            print(f"Error initializing model: {e}")

    def get_response(self, message):
        """Get appropriate response using TF-IDF similarity"""
        try:
            if not message or not self.initialized:
                return self._get_default_response()

            # Transform input message
            message_vector = self.vectorizer.transform([message])
            
            # Calculate similarity with all conversations
            similarities = cosine_similarity(message_vector, self.conversation_vectors)[0]
            
            # Get best match
            best_idx = np.argmax(similarities)
            if similarities[best_idx] > 0.3:  # Similarity threshold
                matched_conv = self.conversations_map.get(best_idx)
                if matched_conv and matched_conv.get('responses'):
                    return random.choice(matched_conv['responses'])

            return self._get_default_response()

        except Exception as e:
            print(f"Error getting response: {e}")
            return self._get_default_response()

    def _get_default_response(self):
        """Return a default response"""
        return "I'm here to help with math! Try asking me a calculation."

    def get_personality(self, prefix=True):
        """Get personality elements from training data"""
        try:
            personalities = self.training_data.get('personalities', {}).get('friendly', {})
            if prefix:
                return random.choice(personalities.get('prefixes', ['Hello!']))
            return random.choice(personalities.get('suffixes', ['😊']))
        except Exception as e:
            print(f"Error getting personality: {e}")
            return 'Hello!' if prefix else '😊'
