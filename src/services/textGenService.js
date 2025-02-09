const fs = require('fs');
const path = require('path');

class TextGenerationService {
    constructor() {
        this.sources = {
            conversations: this._loadJson('training_data.json'),
            feedback: this._loadJson('feedback.json'),
            memories: this._loadJson('memories.json')
        };
    }

    _loadJson(filename) {
        try {
            return JSON.parse(fs.readFileSync(
                path.join(__dirname, '..', '..', 'data', filename), 
                'utf8'
            ));
        } catch (e) {
            return {};
        }
    }

    generateResponse(input, context = {}) {
        const personality = context.personality || 'friendly';
        const sources = this._findRelevantSources(input);
        const baseResponse = this._generateBaseResponse(sources, input);
        return this._addPersonality(baseResponse, personality);
    }

    _findRelevantSources(input) {
        const relevantSources = {
            conversations: [],
            memories: [],
            feedback: []
        };

        // Check conversations
        this.sources.conversations?.conversations?.forEach(conv => {
            if (this._isRelevant(input, conv)) {
                relevantSources.conversations.push(conv);
            }
        });

        // Check memories
        this.sources.memories?.forEach(memory => {
            if (this._isRelevant(input, memory)) {
                relevantSources.memories.push(memory);
            }
        });

        return relevantSources;
    }

    _isRelevant(input, source) {
        const inputWords = input.toLowerCase().split(' ');
        const sourceWords = (source.input || '').toLowerCase().split(' ');
        return inputWords.some(word => 
            sourceWords.includes(word) || 
            this._findSimilarWord(word, sourceWords)
        );
    }

    _findSimilarWord(word, words) {
        return words.some(w => 
            (word.length > 3 && w.includes(word)) ||
            (w.length > 3 && word.includes(w))
        );
    }

    _generateBaseResponse(sources, input) {
        if (sources.conversations.length > 0) {
            const responses = sources.conversations
                .map(conv => conv.responses)
                .flat();
            return responses[Math.floor(Math.random() * responses.length)];
        }

        // Fallback to default response
        return "I understand your question. Let me help with that.";
    }

    _addPersonality(response, type = 'friendly') {
        const personalities = this.sources.conversations?.personalities || {
            friendly: {
                prefixes: ["Hey!", "Oh!", "Let's see..."],
                suffixes: ["😊", "✨", "💫"]
            }
        };

        const personality = personalities[type];
        if (!personality) return response;

        const prefix = personality.prefixes[
            Math.floor(Math.random() * personality.prefixes.length)
        ];
        const suffix = personality.suffixes[
            Math.floor(Math.random() * personality.suffixes.length)
        ];

        return `${prefix} ${response} ${suffix}`;
    }
}

module.exports = new TextGenerationService();
