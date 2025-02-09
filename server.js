const express = require('express');
const path = require('path');
const { spawn } = require('child_process');
const wikiService = require('./src/services/wikiService');
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Serve static files from the public directory
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Wiki definition endpoint
app.post('/wiki/define', async (req, res) => {
    const { term } = req.body;
    try {
        const definition = await wikiService.getDefinition(term);
        res.json({ definition });
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch definition' });
    }
});

// Chat endpoint that communicates with Python
app.post('/chat', async (req, res) => {
    const message = req.body.message;
    
    // Check if it's a definition request
    if (message.toLowerCase().includes('what is') || message.toLowerCase().includes('define')) {
        const term = message.toLowerCase()
            .replace('what is', '')
            .replace('define', '')
            .trim();
            
        try {
            const definition = await wikiService.getDefinition(term);
            if (definition) {
                return res.json({
                    type: 'definition',
                    term,
                    definition,
                    confidence: 90
                });
            }
        } catch (error) {
            console.error('Wiki error:', error);
        }
    }
    
    // If not a definition request or wiki lookup failed, use Python chat
    const pythonProcess = spawn('python', [
        path.join(__dirname, 'src', 'chat_model.py'),
        message
    ]);

    let result = '';

    pythonProcess.stdout.on('data', (data) => {
        result += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            res.status(500).send('Error processing request');
            return;
        }
        res.send(result);
    });
});

// Start server
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    console.log('Press Ctrl+C to quit.');
});
