const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const wikiService = require('./src/services/wikiService');
const chatService = require('./src/services/chatService');
const textGenService = require('./src/services/textGenService');
const multer = require('multer');
const upload = multer({ dest: 'uploads/' });
const app = express();
const port = process.env.PORT || 3001;
    
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

// Update generateResponse function
function generateResponse(input, type, data) {
    const personalities = trainingData.personalities;
    const friendly = personalities.friendly;
    
    const prefix = friendly.prefixes[Math.floor(Math.random() * friendly.prefixes.length)];
    const suffix = friendly.suffixes[Math.floor(Math.random() * friendly.suffixes.length)];
    
    if (type === 'math') {
        // For math problems, keep the structured JSON format
        return {
            format: 'json',
            problem: {
                type: 'Math Problem',
                input: data.input
            },
            steps: data.steps,
            solution: {
                answer: data.answer,
                confidence: data.confidence || 95.5
            }
        };
    } else {
        // For conversations, return plain text with emojis
        const baseResponses = trainingData.conversations.find(c => 
            c.variations.some(v => v.includes(input.toLowerCase()))
        )?.responses || ["I understand, but could you rephrase that?"];
        
        const baseResponse = baseResponses[Math.floor(Math.random() * baseResponses.length)];
        return `${prefix} ${baseResponse} ${suffix}`;
    }
}

// Update findBestMatch function
function findBestMatch(input) {
    input = input.toLowerCase().trim();
    
    // Check for math patterns first
    const mathPattern = /[\d+\-*/()=x]/;
    if (mathPattern.test(input)) {
        // Process as math problem
        const result = processMathProblem(input);
        return generateResponse(input, 'math', result);
    }

    // Generate contextual response for non-math inputs
    const context = {
        greeting: /^(hi|hello|hey|good\s*(morning|afternoon|evening))/i,
        farewell: /^(bye|goodbye|see\s*you|cya)/i,
        thanks: /^(thanks|thank\s*you|thx)/i,
        help: /^(help|assist|guide)/i
    };

    for (const [type, pattern] of Object.entries(context)) {
        if (pattern.test(input)) {
            return generateResponse(input, 'conversation', { context: type });
        }
    }

    // Default response generation
    return generateResponse(input, 'conversation', { context: 'general' });
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

// Update chat endpoint to use Python chat model
app.post('/chat', async (req, res) => {
    const message = req.body.message;
    console.log('Received message:', message);
    
    try {
        const pythonProcess = spawn('python3', [
            path.join(__dirname, 'src', 'chat_model.py'),
            message
        ], {
            env: {
                ...process.env,
                PYTHONIOENCODING: 'utf-8',
                PYTHONUTF8: '1',
                PATH: process.env.PATH
            }
        });

        let result = '';
        let errorOutput = '';

        pythonProcess.stdout.on('data', (data) => {
            result += data.toString();
            console.log('Python output:', data.toString());
        });

        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
            console.error('Python error:', data.toString());
        });

        await new Promise((resolve, reject) => {
            pythonProcess.on('close', (code) => {
                console.log('Python process exited with code:', code);
                if (code !== 0) {
                    reject(new Error(`Python process failed: ${errorOutput}`));
                } else {
                    resolve();
                }
            });
        });

        const cleanResponse = result.trim();
        console.log('Sending response:', cleanResponse);
        res.send(cleanResponse);
    } catch (error) {
        console.error('Server error:', error);
        res.status(500).send("😅 Oops! Had a little trouble there. Could you try again?");
    }
});

// Add text generation endpoint
app.post('/generate', (req, res) => {
    const { message } = req.body;
    try {
        const response = textGenService.generateResponse(message);
        res.json({ text: response });
    } catch (error) {
        console.error('Text generation error:', error);
        res.status(500).json({ 
            text: "I'm having trouble processing that. Could you rephrase?" 
        });
    }
});

// Add feedback endpoint
app.post('/feedback', async (req, res) => {
    const { positive, solution, equations } = req.body;
    
    if (positive) {
        try {
            // Store feedback in training data
            const feedback = {
                timestamp: new Date().toISOString(),
                solution,
                equations,
                type: 'positive'
            };
            
            // Read current feedback file or create new one
            const feedbackPath = path.join(__dirname, 'data', 'feedback.json');
            let feedbackData = [];
            
            try {
                feedbackData = JSON.parse(fs.readFileSync(feedbackPath, 'utf8'));
            } catch (e) {
                // File doesn't exist or is invalid, start fresh
            }
            
            feedbackData.push(feedback);
            fs.writeFileSync(feedbackPath, JSON.stringify(feedbackData, null, 2));
            
            res.json({ success: true });
        } catch (error) {
            console.error('Error saving feedback:', error);
            res.status(500).json({ error: 'Failed to save feedback' });
        }
    } else {
        res.json({ success: true }); // Always return success for negative feedback
    }
});

// Update the processImage endpoint
app.post('/processImage', upload.single('image'), async (req, res) => {
    if (!req.file) {
        return res.status(400).send('No image uploaded');
    }

    try {
        const pythonProcess = spawn('python3', [
            path.join(__dirname, 'src', 'screen_capture.py'),
            req.file.path
        ]);

        let result = '';
        let errorOutput = '';

        pythonProcess.stdout.on('data', (data) => {
            result += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });

        pythonProcess.on('close', (code) => {
            // Clean up uploaded file
            fs.unlinkSync(req.file.path);

            if (code !== 0) {
                return res.status(500).send(errorOutput);
            }

            try {
                const parsedResult = JSON.parse(result);
                // Check if text contains math operators or numbers
                const hasMath = /[\d+\-*/()=x²³¹⁴⁵⁶⁷⁸⁹⁰]+/.test(parsedResult.text);
                
                res.json({
                    text: parsedResult.text,
                    isMath: hasMath,
                    message: hasMath ? "Math problem: yes" : "Math problem: no"
                });
            } catch (parseError) {
                res.status(500).send('Error parsing OCR result');
            }
        });
    } catch (error) {
        // Clean up file if there's an error
        if (req.file) {
            fs.unlinkSync(req.file.path);
        }
        console.error('Image processing error:', error);
        res.status(500).send('Error processing image');
    }
});

// Start server
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    console.log('Press Ctrl+C to quit.');
});
