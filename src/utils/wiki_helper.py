import wikipedia
import re
from typing import Dict, List, Optional

class WikiHelper:
    def __init__(self):
        self.cache: Dict[str, str] = {}
        
    def search_term(self, term: str) -> Optional[str]:
        """Search Wikipedia for a term and return a summary"""
        if term in self.cache:
            return self.cache[term]
            
        try:
            # Search Wikipedia
            page = wikipedia.page(term)
            summary = page.summary
            # Clean and store in cache
            cleaned_summary = re.sub(r'\([^)]*\)', '', summary)
            self.cache[term] = cleaned_summary
            return cleaned_summary
        except:
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
        except:
            return []
