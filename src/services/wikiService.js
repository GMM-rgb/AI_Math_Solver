const wiki = require('wikijs').default;

class WikiService {
    constructor() {
        this.cache = new Map();
    }

    async getDefinition(term) {
        try {
            // Check cache first
            if (this.cache.has(term)) {
                return this.cache.get(term);
            }

            // Search Wikipedia
            const page = await wiki().page(term);
            const summary = await page.summary();
            
            // Get first sentence as definition
            const definition = summary.split('. ')[0] + '.';
            
            // Cache the result
            this.cache.set(term, definition);
            
            return definition;
        } catch (error) {
            console.error('Wiki lookup error:', error);
            return null;
        }
    }

    async getRelatedTerms(term) {
        try {
            const results = await wiki().search(term, 5);
            return results.results;
        } catch (error) {
            console.error('Wiki search error:', error);
            return [];
        }
    }
}

module.exports = new WikiService();
