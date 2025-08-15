#!/usr/bin/env node

/**
 * 🎭 ASOOS CLI EXECUTABLE WRAPPER
 * Terminal interface for the Aixtiv Symphony Orchestrating Operating System
 * 
 * Victory36 Protected & Elite11 Orchestrated
 * Created: Victory Day August 15, 2025
 */

import { ASOOSCLISystem } from './ASOOS-CLI-System.js';
import readline from 'readline';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class ASOOSTerminalInterface {
    constructor() {
        this.cli = new ASOOSCLISystem();
        this.rl = null;
        this.isInteractive = false;
    }

    async initialize() {
        // Check if we're running interactively or with arguments
        const args = process.argv.slice(2);
        
        if (args.length > 0) {
            // Non-interactive mode - execute single command
            await this.executeSingleCommand(args.join(' '));
        } else {
            // Interactive mode
            await this.startInteractiveMode();
        }
    }

    async executeSingleCommand(command) {
        try {
            const result = await this.cli.processCommand(command);
            console.log(result);
            process.exit(0);
        } catch (error) {
            console.error(`Error: ${error.message}`);
            process.exit(1);
        }
    }

    async startInteractiveMode() {
        this.isInteractive = true;
        
        this.rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            prompt: '🎭 asoos> ',
            history: [],
            historySize: 100
        });

        // Handle Ctrl+C gracefully
        this.rl.on('SIGINT', () => {
            console.log('\n\n✨ Thank you for using ASOOS! Victory36 protecting your journey...');
            process.exit(0);
        });

        // Handle command input
        this.rl.on('line', async (input) => {
            const command = input.trim();
            
            if (command === '') {
                this.rl.prompt();
                return;
            }
            
            if (command.toLowerCase() === 'exit' || command.toLowerCase() === 'quit') {
                console.log('\n✨ Farewell! ASOOS will be here when you return.');
                process.exit(0);
            }
            
            if (command.toLowerCase() === 'clear') {
                console.clear();
                this.cli.initializeCLI();
                this.rl.prompt();
                return;
            }
            
            try {
                const result = await this.cli.processCommand(command);
                console.log(result);
            } catch (error) {
                console.error(`❌ Error: ${error.message}`);
                console.log('Type "help" for available commands.');
            }
            
            this.rl.prompt();
        });

        // Start the interactive session
        console.log('Interactive mode started. Type "exit" to quit, "clear" to reset, or "help" for commands.\n');
        this.rl.prompt();
    }
}

// Global error handlers
process.on('uncaughtException', (error) => {
    console.error('\n🛡️ Victory36 Protection Activated - Uncaught Exception:');
    console.error(error.message);
    console.error('\nPlease report this to the ASOOS team. Session state preserved.');
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('\n🛡️ Victory36 Protection Activated - Unhandled Rejection:');
    console.error(reason);
    console.error('\nPlease report this to the ASOOS team. Session state preserved.');
});

// Initialize and start the CLI
const terminal = new ASOOSTerminalInterface();
terminal.initialize().catch((error) => {
    console.error('Failed to initialize ASOOS CLI:', error.message);
    process.exit(1);
});

/**
 * USAGE EXAMPLES:
 * 
 * Interactive Mode:
 * $ node asoos-cli.js
 * 
 * Single Command Mode:
 * $ node asoos-cli.js help
 * $ node asoos-cli.js demo
 * $ node asoos-cli.js code debug "my error"
 * $ node asoos-cli.js mcp list
 * $ node asoos-cli.js org scan
 * $ node asoos-cli.js copilot
 * 
 * To make globally available:
 * $ npm link
 * $ asoos help
 * $ asoos demo
 * $ asoos code debug "Cannot read property 'map' of undefined"
 */
