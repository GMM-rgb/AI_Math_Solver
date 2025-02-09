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

        const lowerMessage = message.toLowerCase().trim();

        // Check all conversations for matches including variations
        for (const conv of this.trainingData.conversations) {
            if (conv.variations.includes(lowerMessage)) {
                const response = this.getRandomResponse(conv.responses);
                const timeEmoji = this.getTimeEmoji();
                const personalityEmojis = this.getPersonalityEmojis();
                
                return {
                    response: `${response} ${personalityEmojis} ${timeEmoji}`,
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

    getTimeEmoji() {
        const hour = new Date().getHours();
        return hour < 12 ? "🌅" : (hour < 17 ? "☀️" : "🌙");
    }

    getPersonalityEmojis() {
        const mood = this.trainingData.personalities.friendly;
        return mood.suffixes[Math.floor(Math.random() * mood.suffixes.length)];
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
        
        // Add random prefix from personality if available
        if (this.trainingData.personalities?.friendly?.prefixes) {
            const prefixes = this.trainingData.personalities.friendly.prefixes;
            const randomPrefix = prefixes[Math.floor(Math.random() * prefixes.length)];
            return `${randomPrefix} ${response}`;
        }
        
        return response;
    }
}

module.exports = new ChatService();
