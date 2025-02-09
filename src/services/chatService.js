const PatternMatcher = require('../utils/pattern_matcher');
const fs = require('fs').promises;
const path = require('path');

class ChatService {
    constructor() {
        this.trainingData = null;
        this.matcher = null;
        this.initialized = false;
    }

    async initialize() {
        if (!this.initialized) {
            try {
                const trainingDataPath = path.join(__dirname, '../../data/training_data.json');
                const data = await fs.readFile(trainingDataPath, 'utf8');
                this.trainingData = JSON.parse(data);
                this.matcher = new PatternMatcher(this.trainingData);
                this.initialized = true;
            } catch (error) {
                console.error('Failed to initialize chat service:', error);
                throw error;
            }
        }
    }

    async processMessage(message) {
        if (!this.initialized) {
            await this.initialize();
        }

        const match = this.matcher.findBestMatch(message);
        
        if (match) {
            switch (match.type) {
                case 'conversation':
                    return {
                        response: this.getRandomResponse(match.data.responses),
                        confidence: match.score * 100,
                        type: 'chat'
                    };
                    
                case 'math_pattern':
                    return {
                        response: message,
                        confidence: 100,
                        type: 'math'
                    };
            }
        }

        // Default to math processing if no conversational match
        return {
            response: message,
            confidence: 60,
            type: 'math'
        };
    }

    getRandomResponse(responses) {
        if (!Array.isArray(responses) || responses.length === 0) {
            return "I'm not sure how to respond to that.";
        }
        return responses[Math.floor(Math.random() * responses.length)];
    }
}

module.exports = new ChatService();
