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
                    format: 'json',
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
    
    // Spawn Python process with proper environment
    try {
        const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
        const projectRoot = __dirname;
        
        const pythonProcess = spawn(pythonPath, [
            path.join(projectRoot, 'src', 'chat_model.py'),
            message
        ], {
            env: {
                ...process.env,
                PYTHONPATH: projectRoot,
                PYTHONIOENCODING: 'utf-8',
                PYTHONUTF8: '1',
                LANG: 'en_US.UTF-8'
            },
            cwd: projectRoot  // Set working directory to project root
        });

        let result = '';
        let errorOutput = '';

        pythonProcess.stdout.setEncoding('utf8');
        pythonProcess.stderr.setEncoding('utf8');

        pythonProcess.stdout.on('data', (data) => {
            result += data.toString('utf8');
        });

        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
            console.error(`Python Error: ${data}`);
        });

        // Use Promise to handle process completion
        await new Promise((resolve, reject) => {
            pythonProcess.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Python process exited with code ${code}: ${errorOutput}`));
                } else {
                    resolve();
                }
            });
            
            pythonProcess.on('error', (err) => {
                reject(new Error(`Failed to start Python process: ${err.message}`));
            });
        });

        // Try to parse result as JSON, fallback to plain text
        try {
            const jsonResult = JSON.parse(result);
            res.json(jsonResult);
        } catch {
            res.send(result);
        }
    } catch (error) {
        console.error('Server error:', error);
        res.status(500).json({
            error: 'Error processing request',
            details: error.message,
            format: 'json'
        });
    }
});

// Start server
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    console.log('Press Ctrl+C to quit.');
});
