const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const wikiService = require('./src/services/wikiService');
const chatService = require('./src/services/chatService');
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.static('public'));
app.use(bodyParser.json());

// Serve static files from the public directory
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Load training data
const trainingData = JSON.parse(fs.readFileSync(path.join(__dirname, 'data', 'training_data.json'), 'utf8'));

function findBestMatch(input) {
    input = input.toLowerCase().trim();
    
    // Check for conversation patterns first
    for (const conv of trainingData.conversations) {
        if (conv.variations.includes(input)) {
            return {
                type: 'conversation',
                response: conv.responses[Math.floor(Math.random() * conv.responses.length)]
            };
        }
    }

    // Check for math problems
    for (const problem of trainingData.math_problems) {
        if (problem.variations.includes(input) || problem.input === input) {
            return {
                format: 'json',
                problem: {
                    type: 'Math Problem',
                    input: problem.input
                },
                steps: problem.steps,
                solution: {
                    answer: problem.answer,
                    confidence: 95.5
                }
            };
        }
    }

    // Try to identify math operators
    const operators = trainingData.math_patterns.operators;
    for (const [op, patterns] of Object.entries(operators)) {
        if (patterns.some(pattern => input.includes(pattern))) {
            // Process as math problem
            return processMathProblem(input, op);
        }
    }

    return {
        type: 'conversation',
        response: "I'm not sure how to solve that problem. Could you rephrase it?"
    };
}

function processMathProblem(input, operator) {
    // Basic math processing logic
    const numbers = input.split(/[+\-*/x=]/).map(n => parseFloat(n.trim()));
    let result;
    
    switch(operator) {
        case 'plus':
            result = numbers[0] + numbers[1];
            break;
        case 'minus':
            result = numbers[0] - numbers[1];
            break;
        case 'times':
            result = numbers[0] * numbers[1];
            break;
        case 'divide':
            result = numbers[0] / numbers[1];
            break;
        default:
            return null;
    }

    return {
        format: 'json',
        problem: {
            type: 'Math Problem',
            input: input
        },
        steps: [`Calculated ${numbers[0]} ${operator} ${numbers[1]}`],
        solution: {
            answer: result,
            confidence: 98.5
        }
    };
}

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
    console.log('Received message:', message);  // Server-side logging
    
    try {
        // Process message through chat service first
        const processedMessage = await chatService.processMessage(message);
        console.log('Processed message:', processedMessage);  // Server-side logging
        
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
        let errorOutput = '';

        pythonProcess.stdout.setEncoding('utf8');
        pythonProcess.stderr.setEncoding('utf8');

        pythonProcess.stdout.on('data', (data) => {
            result += data.toString();
            console.log('Python output:', data.toString());  // Server-side logging
        });

        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
            console.error('Python error:', data.toString());  // Server-side logging
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
        console.error('Server error:', error);  // Server-side logging
        res.status(500).send('Error processing request');
    }
});

// Start server
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    console.log('Press Ctrl+C to quit.');
});
