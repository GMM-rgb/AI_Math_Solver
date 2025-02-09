const tf = require('@tensorflow/tfjs-node');

class MathModel {
    constructor() {
        this.model = null;
        this.initialized = false;
    }

    async initialize() {
        if (this.initialized) {
            return;
        }

        try {
            this.model = await this.createModel();
            this.initialized = true;
            console.log('Math model initialized successfully');
        } catch (error) {
            console.error('Failed to initialize math model:', error);
            throw error;
        }
    }

    async createModel() {
        const model = tf.sequential();
        
        // Input layer
        model.add(tf.layers.dense({
            units: 64,
            activation: 'relu',
            inputShape: [6]  // [num1, num2, isAdd, isSub, isMul, isDiv]
        }));
        
        // Hidden layer
        model.add(tf.layers.dense({
            units: 32,
            activation: 'relu'
        }));
        
        // Output layer
        model.add(tf.layers.dense({
            units: 1
        }));

        model.compile({
            optimizer: 'adam',
            loss: 'meanSquaredError'
        });

        return model;
    }

    async train(features, labels) {
        if (!this.initialized) {
            await this.initialize();
        }

        const xs = tf.tensor2d(features);
        const ys = tf.tensor2d(labels, [labels.length, 1]);

        try {
            await this.model.fit(xs, ys, {
                epochs: 100,
                batchSize: 32,
                shuffle: true,
                verbose: 0
            });
            
            xs.dispose();
            ys.dispose();
            return true;
        } catch (error) {
            console.error('Training error:', error);
            throw error;
        }
    }

    async predict(features) {
        if (!this.initialized) {
            throw new Error('Model not initialized');
        }

        const input = tf.tensor2d([features]);
        try {
            const prediction = this.model.predict(input);
            const result = await prediction.data();
            
            input.dispose();
            prediction.dispose();
            
            return result[0];
        } catch (error) {
            console.error('Prediction error:', error);
            throw error;
        }
    }

    isInitialized() {
        return this.initialized;
    }

    dispose() {
        if (this.model) {
            this.model.dispose();
            this.initialized = false;
        }
    }
}

// Export a singleton instance
module.exports = new MathModel();
