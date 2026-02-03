#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function validateApiVersion(srcDir = './src') {
    if (!fs.existsSync(srcDir)) return 0;
    
    const violations = [];
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
                const content = fs.readFileSync(filePath, 'utf-8');
                const matches = content.match(/['"`](\/api\/(?!v1\/)[^'"`]+)['"`]/g);
                if (matches && matches.length > 0) {
                    violations.push(path.relative(srcDir, filePath));
                }
            }
        }
    }
    walk(srcDir);
    
    if (violations.length > 0) {
        console.log('API version prefix violations:');
        violations.forEach(f => console.log(`  - ${f}`));
        return 1;
    }
    return 0;
}

process.exit(validateApiVersion());
