#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function validateColocation(srcDir = './src') {
    if (!fs.existsSync(srcDir)) return 0;
    
    const missing = [];
    function walk(dir) {
        const files = fs.readdirSync(dir);
        for (const file of files) {
            const filePath = path.join(dir, file);
            const stat = fs.statSync(filePath);
            if (stat.isDirectory()) {
                if (!['node_modules', '.git', 'dist', 'build'].includes(file)) {
                    walk(filePath);
                }
            } else if (file.match(/\.(ts|tsx)$/)) {
                if (!file.includes('.test.')) {
                    const dirname = path.dirname(filePath);
                    const basename = path.basename(filePath, path.extname(filePath));
                    const testFile = path.join(dirname, `${basename}.test${path.extname(filePath)}`);
                    if (!fs.existsSync(testFile)) {
                        missing.push(path.relative(srcDir, filePath));
                    }
                }
            }
        }
    }
    walk(srcDir);
    
    if (missing.length > 0) {
        console.log('Missing test files:');
        missing.forEach(f => console.log(`  - ${f}`));
        return 1;
    }
    return 0;
}

process.exit(validateColocation());
