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

        // First check for exact matches in conversations
        for (const conv of this.trainingData.conversations) {
            if (conv.variations.includes(message.toLowerCase())) {
                return {
                    response: this.getRandomResponse(conv.responses),
                    confidence: 100,
                    type: 'chat'
                };
            }
        }

        // Then check for math patterns
        const mathPattern = /[\d+\-*/()=xy]/;
        if (mathPattern.test(message)) {
            return {
                response: message,
                confidence: 90,
                type: 'math'
            };
        }

        // Check for similar conversations
        const match = this.matcher.findBestMatch(message);
        if (match && match.score > 0.6) {
            return {
                response: this.getRandomResponse(match.data.responses),
                confidence: match.score * 100,
                type: 'chat'
            };
        }

        // Default response for unknown input
        return {
            response: "I'm not sure how to respond to that. Would you like to try a math problem?",
            confidence: 50,
            type: 'chat'
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
