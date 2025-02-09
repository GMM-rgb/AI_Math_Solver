const express = require('express');
const bodyParser = require('body-parser');
const { execFile } = require('child_process');
const path = require('path');
const multer = require('multer');
const upload = multer({ storage: multer.memoryStorage() });

const app = express();
app.use(bodyParser.json());

const PYTHON_PATH = process.env.PYTHON_PATH || 'python3';
const SRC_DIR = path.join(__dirname, 'src');

// Update the Python module execution to include src directory in PYTHONPATH
const execOptions = {
    cwd: __dirname,
    env: {
        ...process.env,
        PYTHONPATH: `${process.env.PYTHONPATH || ''}:${__dirname}`
    }
};
    
// Add detailed logging for static files
app.use((req, res, next) => {
    console.log(`${req.method} ${req.path}`);
    next();
});

// Serve static files from 'public' directory with proper MIME types
app.use(express.static('public', {
    setHeaders: (res, path) => {
        if (path.endsWith('.js')) {
            res.setHeader('Content-Type', 'application/javascript');
        }
    }
}));

app.post('/solveMath', (req, res) => {
    if (!req.body.problem) {
        return res.status(400).send('No math problem provided');
    }
    console.log('Received problem:', req.body.problem);
    execFile(PYTHON_PATH, ['-m', 'src.ai_model', req.body.problem], execOptions, (error, stdout, stderr) => {
        if (error) { 
            console.error('Math model error:', stderr);
            res.status(500).send(stderr);
            return;
        }
        res.send(stdout);
    });
});

app.get('/captureAndSolve', (req, res) => {
    // First capture screen text
    execFile(PYTHON_PATH, ['-m', 'src.screen_capture'], execOptions, (error, stdout, stderr) => {
        if (error) {
            console.error('Screen capture error:', stderr);
            return res.status(500).send(stderr);
        }
        
        // Use the captured text as math problem input
        const capturedText = stdout.trim();
        console.log('Captured text:', capturedText);
        
        // Try to solve the captured math problem
        execFile(PYTHON_PATH, ['-m', 'src.chat_model', capturedText], execOptions, (error, stdout, stderr) => {
            if (error) {
                console.error('Math solving error:', stderr);
                return res.status(500).send(stderr);
            }
            res.send(stdout);
        });
    });
});

app.post('/chat', (req, res) => {
    if (!req.body.message) {
        return res.status(400).send('No message provided');
    }
    
    const pythonProcess = execFile(PYTHON_PATH, 
        ['-m', 'src.chat_model', req.body.message], 
        execOptions,
        (error, stdout, stderr) => {
            if (error) {
                console.error('Chat error:', stderr);
                res.status(500).send(stderr);
                return;
            }
            
            if (stdout.trim() === 'USE_MATH_MODEL') {
                execFile(PYTHON_PATH, 
                    ['-m', 'src.ai_model', req.body.message], 
                    execOptions,
                    (error2, stdout2, stderr2) => {
                        if (error2) {
                            console.error('Math model error:', stderr2);
                            res.status(500).send(stderr2);
                            return;
                        }
                        res.send(stdout2);
                    }
                );
            } else {
                res.send(stdout);
            }
        }
    );
});

app.post('/training/add', (req, res) => {
    const { category, item } = req.body;
    execFile(PYTHON_PATH, ['-m', 'src.training_manager', 'add', category, JSON.stringify(item)], execOptions, 
        (error, stdout, stderr) => {
            if (error) {
                res.status(500).send(stderr);
                return;
            }
            res.send(stdout);
    });
});

app.post('/training/variation', (req, res) => {
    const { category, input, variation } = req.body;
    execFile(PYTHON_PATH, ['-m', 'src.training_manager', 'add_variation', category, input, variation], execOptions, 
        (error, stdout, stderr) => {
            if (error) {
                res.status(500).send(stderr);
                return;
            }
            res.send(stdout);
    });
});

app.post('/training/response', (req, res) => {
    const { input, response } = req.body;
    execFile(PYTHON_PATH, ['-m', 'src.training_manager', 'add_response', input, response], execOptions, 
        (error, stdout, stderr) => {
            if (error) {
                res.status(500).send(stderr);
                return;
            }
            res.send(stdout);
    });
});

app.get('/api/training/math', (req, res) => {
    execFile(PYTHON_PATH, ['-m', 'src.training_manager', 'get_math_problems'], execOptions, (error, stdout, stderr) => {
        if (error) {
            console.error('Training data error:', stderr);
            return res.status(500).send(stderr);
        }
        try {
            const data = JSON.parse(stdout);
            res.json(data);
        } catch (e) {
            res.status(500).send('Error parsing training data');
        }
    });
});

app.post('/processImage', upload.single('image'), (req, res) => {
    if (!req.file) {
        return res.status(400).send('No image uploaded');
    }

    // Process image using screen_capture.py
    const tempFilePath = path.join(__dirname, 'temp', `upload_${Date.now()}.png`);
    require('fs').writeFileSync(tempFilePath, req.file.buffer);

    execFile(PYTHON_PATH, ['-m', 'src.screen_capture', tempFilePath], execOptions, (error, stdout, stderr) => {
        // Clean up temp file
        require('fs').unlinkSync(tempFilePath);

        if (error) {
            console.error('Image processing error:', stderr);
            return res.status(500).send(stderr);
        }
        res.send(stdout.trim());
    });
});

// Add error handling middleware
app.use((err, req, res, next) => {
    console.error('Server error:', err);
    res.status(500).json({
        error: 'Internal server error',
        message: err.message
    });
});

// Modify the server startup
const startServer = async () => {
    try {
        const port = process.env.PORT || 3001;
        app.listen(port, () => {
            console.log(`Server running on port ${port}`);
        });
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
};

startServer();
