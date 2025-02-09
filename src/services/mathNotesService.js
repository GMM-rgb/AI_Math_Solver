const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

class MathNotesService {
    constructor() {
        this.notesCache = new Map();
        this.localNotesPath = path.join(__dirname, '..', '..', 'data', 'math_notes');
    }

    async fetchNotes(topic) {
        try {
            // Check cache first
            if (this.notesCache.has(topic)) {
                return this.notesCache.get(topic);
            }

            // Check local notes first
            const localNotes = await this.getLocalNotes(topic);
            if (localNotes) {
                this.notesCache.set(topic, localNotes);
                return localNotes;
            }

            // Fetch from online sources (example: Wolfram Alpha API)
            const response = await axios.get(`https://api.wolframalpha.com/v2/query`, {
                params: {
                    input: topic,
                    format: 'plaintext',
                    output: 'JSON',
                    appid: process.env.WOLFRAM_APP_ID
                }
            });

            const notes = this._extractNotes(response.data);
            this.notesCache.set(topic, notes);
            return notes;
        } catch (error) {
            console.error('Error fetching math notes:', error);
            return null;
        }
    }

    async getLocalNotes(topic) {
        try {
            const notesFile = path.join(this.localNotesPath, `${topic.toLowerCase()}.json`);
            const data = await fs.readFile(notesFile, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            return null;
        }
    }

    _extractNotes(data) {
        // Extract relevant information from API response
        const notes = {
            topic: data.queryresult?.pods?.[0]?.subpods?.[0]?.plaintext || '',
            examples: data.queryresult?.pods?.[1]?.subpods?.[0]?.plaintext || '',
            formulas: data.queryresult?.pods?.[2]?.subpods?.[0]?.plaintext || ''
        };
        return notes;
    }
}

module.exports = new MathNotesService();
