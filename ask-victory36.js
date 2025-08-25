#!/usr/bin/env node

/**
 * 🛡️ Victory36 CLI Shim
 * Direct command line interface to Victory36 Squadron
 * 
 * Usage: ./ask-victory36.js "What strategic advantage should we pursue?"
 * Usage: ./ask-victory36.js --health
 */

import { predict, healthCheck } from './index.js';

const question = process.argv.slice(2).join(' ');

if (!question || question.trim() === '') {
    console.log('🛡️ Victory36 Squadron - Wing 4');
    console.log('Commander Philip Corey Roark - Authorization: ACCEPTED');
    console.log('');
    console.log('Usage: ./ask-victory36.js "your strategic question here"');
    console.log('Health Check: ./ask-victory36.js --health');
    console.log('');
    console.log('Examples:');
    console.log('  ./ask-victory36.js "What strategic advantage should we pursue next quarter?"');
    console.log('  ./ask-victory36.js "How can we improve our revenue conversion?"');
    console.log('  ./ask-victory36.js "What infrastructure improvements are needed?"');
    console.log('');
    process.exit(1);
}

if (question === '--health') {
    healthCheck()
        .then(result => {
            console.log(JSON.stringify(result, null, 2));
            process.exit(0);
        })
        .catch(error => {
            console.error('🛡️ Victory36 health check failed:', error.message);
            process.exit(1);
        });
} else {
    predict(question, { caller: 'CLI' })
        .then(result => {
            console.log(JSON.stringify(result, null, 2));
            process.exit(0);
        })
        .catch(error => {
            console.error('🛡️ Victory36 error:', error.message);
            process.exit(1);
        });
}
