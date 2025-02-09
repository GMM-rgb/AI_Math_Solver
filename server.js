const express = require('express');
const path = require('path');
const { spawn } = require('child_process');
const wikiService = require('./src/services/wikiService');
const chatService = require('./src/services/chatService');
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
    
    try {
        // Process message through chat service first
        const processedMessage = await chatService.processMessage(message);
        
        if (processedMessage.type === 'chat') {
            return res.send(processedMessage.response);
        }

        // Continue with Python processing for math
        const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
        const projectRoot = __dirname;
        
        const pythonProcess = spawn(pythonPath, [
            path.join(projectRoot, 'src', 'chat_model.py'),
            processedMessage.response
        ], {
            env: {
                ...process.env,
                PYTHONIOENCODING: 'utf-8',
                PYTHONUTF8: '1',
                LANG: 'C.UTF-8'
            }
        });

        let result = '';

        pythonProcess.stdout.setEncoding('utf8');
        pythonProcess.stderr.setEncoding('utf8');

        pythonProcess.stdout.on('data', (data) => {
            result += data.toString();
        });

        let errorOutput = '';

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

        // Clean up the response
        result = result.trim();
        
        // If it's HTML (math solution), send as-is
        if (result.startsWith('<')) {
            res.send(result);
        } else {
            // For regular chat messages, send as plain text
            res.send(result);
        }
    } catch (error) {
        console.error('Server error:', error);
        res.status(500).send('Error processing request');
    }
});

// Start server
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    console.log('Press Ctrl+C to quit.');
});
