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

    // Add Levenshtein distance calculation
    levenshteinDistance(a, b) {
        if (a.length === 0) return b.length;
        if (b.length === 0) return a.length;

        const matrix = [];

        // Initialize matrix
        for (let i = 0; i <= b.length; i++) {
            matrix[i] = [i];
        }
        for (let j = 0; j <= a.length; j++) {
            matrix[0][j] = j;
        }

        // Fill matrix
        for (let i = 1; i <= b.length; i++) {
            for (let j = 1; j <= a.length; j++) {
                if (b.charAt(i - 1) === a.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,    // substitution
                        matrix[i][j - 1] + 1,        // insertion
                        matrix[i - 1][j] + 1         // deletion
                    );
                }
            }
        }

        return matrix[b.length][a.length];
    }

    // Calculate similarity based on Levenshtein
    calculateSimilarity(str1, str2) {
        const maxLength = Math.max(str1.length, str2.length);
        if (maxLength === 0) return 1.0;
        const distance = this.levenshteinDistance(str1, str2);
        return 1 - (distance / maxLength);
    }

    async processMessage(message) {
        if (!this.initialized) {
            await this.initialize();
        }

        const lowerMessage = message.toLowerCase().trim();

        // First check exact matches
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

            // Check for fuzzy matches using Levenshtein
            const similarities = conv.variations.map(variation => 
                this.calculateSimilarity(lowerMessage, variation)
            );
            const bestSimilarity = Math.max(...similarities);
            
            if (bestSimilarity > 0.8) {  // 80% similarity threshold
                const response = this.getRandomResponse(conv.responses);
                const timeEmoji = this.getTimeEmoji();
                const personalityEmojis = this.getPersonalityEmojis();
                return {
                    response: `${response} ${personalityEmojis} ${timeEmoji}`,
                    confidence: Math.floor(bestSimilarity * 100),
                    type: 'chat'
                };
            }
        }

        // Continue with math pattern check
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
