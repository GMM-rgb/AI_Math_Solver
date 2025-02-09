if (typeof window === 'undefined') {
    const tf = require('@tensorflow/tfjs-node');
} else {
    if (!window.tf) {
        throw new Error('TensorFlow.js is not loaded! Make sure to include the CDN script.');
    }
}

class MathTFModel {
    constructor() {
        this.model = null;
        this.initialized = false;
        this.inputShape = [6];
        this.outputShape = 1;
    }

    async initModel() {
        if (this.initialized) return true;
        
        try {
            this.model = tf.sequential();
            
            this.model.add(tf.layers.dense({
                units: 32,
                activation: 'relu',
                inputShape: this.inputShape
            }));
            
            this.model.add(tf.layers.dense({
                units: this.outputShape
            }));

            this.model.compile({
                optimizer: 'adam',
                loss: 'meanSquaredError'
            });

            this.initialized = true;
            return true;
        } catch (error) {
            console.error('Model initialization failed:', error);
            return false;
        }
    }

    async train(features, labels) {
        if (!this.initialized) {
            await this.initModel();
        }

        try {
            console.log('Training model with', features.length, 'samples');
            const xs = tf.tensor2d(features);
            const ys = tf.tensor2d(labels, [labels.length, 1]);

            await this.model.fit(xs, ys, {
                epochs: 100,
                batchSize: 32,
                shuffle: true,
                verbose: 0
            });

            // Clean up tensors
            xs.dispose();
            ys.dispose();
            
            console.log('Model training completed');
            return true;
        } catch (error) {
            console.error('Error training model:', error);
            throw error;
        }
    }

    predict(features) {
        if (!this.initialized) throw new Error('Model not initialized');
        const input = tf.tensor2d([features]);
        const prediction = this.model.predict(input);
        const result = prediction.dataSync();
        input.dispose();
        prediction.dispose();
        return result[0];
    }

    dispose() {
        if (this.model) {
            this.model.dispose();
            this.initialized = false;
            console.log('Model disposed');
        }
    }

    // Helper method to normalize features if needed
    normalizeFeatures(features) {
        // Implement feature normalization if needed
        return features;
    }

    // Method to save the model state
    async saveModel() {
        if (this.model) {
            try {
                await this.model.save('localstorage://math-model');
                console.log('Model saved to localStorage');
            } catch (error) {
                console.error('Error saving model:', error);
            }
        }
    }

    // Method to load the model state
    async loadModel() {
        try {
            this.model = await tf.loadLayersModel('localstorage://math-model');
            this.initialized = true;
            console.log('Model loaded from localStorage');
        } catch (error) {
            console.error('Error loading model:', error);
            await this.initModel();
        }
    }
}

// Make it available globally
window.MathTFModel = MathTFModel;

export default MathTFModel;
