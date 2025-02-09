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

        // First check for greetings
        const lowerMessage = message.toLowerCase().trim();
        if (this.isGreeting(lowerMessage)) {
            const hour = new Date().getHours();
            let greeting;
            if (hour < 12) {
                greeting = "Good morning! Ready for some math? 🌅";
            } else if (hour < 17) {
                greeting = "Good afternoon! Let's solve some problems! 🌞";
            } else {
                greeting = "Good evening! Time for some math fun! 🌙";
            }
            return {
                response: greeting,
                confidence: 100,
                type: 'chat'
            };
        }

        // First check for exact matches in conversations
        for (const conv of this.trainingData.conversations) {
            if (conv.variations.includes(lowerMessage)) {
                return {
                    response: this.getRandomResponse(conv.responses),
                    confidence: 100,
                    type: 'chat'
                };
            }
        }

        // Then check for similar conversations
        const match = this.matcher.findBestMatch(lowerMessage);
        if (match && match.data && match.data.responses && match.score > 0.6) {
            return {
                response: this.getRandomResponse(match.data.responses),
                confidence: match.score * 100,
                type: 'chat'
            };
        }

        // Then check for math patterns (if no conversation match found)
        const mathPattern = /[\d+\-*/()=xy]/;
        if (mathPattern.test(message)) {
            return {
                response: message,
                confidence: 90,
                type: 'math'
            };
        }

        // Default response for unknown input
        return {
            response: "I'm not sure how to respond to that. Would you like to try a math problem?",
            confidence: 50,
            type: 'chat'
        };
    }

    isGreeting(message) {
        const greetings = [
            'hi', 'hello', 'hey', 'good morning', 'good afternoon', 
            'good evening', 'yo', "what's up", 'howdy', 'hola', 
            'hi there', 'hello there', 'hey there', 'whats up', 
            'how are you', "how's it going", 'sup'
        ];
        return greetings.some(greeting => message.includes(greeting));
    }

    getRandomResponse(responses) {
        if (!Array.isArray(responses) || responses.length === 0) {
            return "I'm not sure how to respond to that.";
        }
        const response = responses[Math.floor(Math.random() * responses.length)];
        return response || "I'm not sure how to respond to that.";
    }
}

module.exports = new ChatService();
