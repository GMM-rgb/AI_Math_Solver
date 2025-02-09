class PatternMatcher {
    constructor(trainingData) {
        this.data = trainingData;
        this.threshold = 0.7; // Similarity threshold
    }

    findBestMatch(input) {
        let bestScore = 0;
        let bestMatch = null;

        // Check conversations first
        for (const conv of this.data.conversations) {
            // Check main input
            const mainScore = this.similarity(input, conv.input);
            if (mainScore > bestScore && mainScore >= this.threshold) {
                bestScore = mainScore;
                bestMatch = {
                    type: 'conversation',
                    data: conv,
                    score: mainScore
                };
            }

            // Check variations
            if (conv.variations) {
                for (const variation of conv.variations) {
                    const score = this.similarity(input, variation);
                    if (score > bestScore && score >= this.threshold) {
                        bestScore = score;
                        bestMatch = {
                            type: 'conversation',
                            data: conv,
                            score: score
                        };
                    }
                }
            }
        }

        // Check math patterns
        if (this.data.math_patterns) {
            for (const [key, patterns] of Object.entries(this.data.math_patterns)) {
                if (Array.isArray(patterns)) {
                    for (const pattern of patterns) {
                        if (input.toLowerCase().includes(pattern.toLowerCase())) {
                            return {
                                type: 'math_pattern',
                                pattern: key,
                                matched: pattern,
                                score: 1
                            };
                        }
                    }
                }
            }
        }

        return bestMatch;
    }

    similarity(str1, str2) {
        const s1 = str1.toLowerCase();
        const s2 = str2.toLowerCase();
        const pairs1 = this.wordPairs(s1);
        const pairs2 = this.wordPairs(s2);
        const union = pairs1.size + pairs2.size;
        const intersection = new Set([...pairs1].filter(x => pairs2.has(x))).size;
        return (2.0 * intersection) / union;
    }

    wordPairs(str) {
        const pairs = new Set();
        const words = str.split(/\s+/);
        for (let i = 0; i < words.length - 1; i++) {
            pairs.add(`${words[i]} ${words[i + 1]}`);
        }
        return pairs;
    }
}

module.exports = PatternMatcher;
