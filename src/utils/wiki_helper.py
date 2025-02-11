try:
    import wikipedia
    print("wikipedia module imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")
    wikipedia = None

import re
from typing import Dict, List, Optional

class WikiHelper:
    def __init__(self):
        self.cache: Dict[str, str] = {}
        self.wikipedia_available = wikipedia is not None
        print(f"Wikipedia available: {self.wikipedia_available}")
        
    def search_term(self, term: str) -> Optional[str]:
        """Search Wikipedia for a term and return a summary"""
        if not self.wikipedia_available:
            print(f"Cannot search for {term}, wikipedia module not available.")
            return None
            
        if term in self.cache:
            print(f"Returning cached result for {term}")
            return self.cache[term]
            
        try:
            # Search Wikipedia
            page = wikipedia.page(term)
            summary = page.summary
            # Clean and store in cache
            cleaned_summary = re.sub(r'\([^)]*\)', '', summary)
            self.cache[term] = cleaned_summary
            return cleaned_summary
        except Exception as e:
            print(f"Error searching for {term}: {e}")
            return None

    def get_definition(self, term: str) -> Optional[str]:
        """Get a short definition of a term"""
        summary = self.search_term(term)
        if summary:
            # Try to get first sentence as definition
            first_sentence = summary.split('. ')[0]
            return first_sentence + '.'
        return None

    def get_related_terms(self, term: str) -> List[str]:
        """Get related terms for a concept"""
        try:
            return wikipedia.search(term, results=5)
        except Exception as e:
            print(f"Error getting related terms for {term}: {e}")
            return []

if __name__ == "__main__":
    helper = WikiHelper()
    definition = helper.get_definition("Artificial Intelligence")
    print(definition)
