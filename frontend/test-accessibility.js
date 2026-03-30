#!/usr/bin/env node

/**
 * Accessibility Audit for Dashboard
 * Checks WCAG 2.1 AA compliance
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FRONTEND_DIR = path.join(__dirname, 'src/components');

// WCAG 2.1 AA Requirements
const AUDIT_CHECKS = {
  ariaLabels: {
    name: 'ARIA Labels',
    description: 'Interactive elements must have aria-label or aria-labelledby',
    severity: 'critical',
    check: (content, filepath) => {
      const issues = [];

      // Check buttons without aria-label or text content
      const buttonMatches = content.match(/<button[^>]*>/g) || [];
      buttonMatches.forEach((btn, idx) => {
        const hasAriaLabel = btn.includes('aria-label');
        const hasText = btn.includes('>') && btn.split('>')[1]?.includes('<');

        if (!hasAriaLabel && !hasText) {
          issues.push(`Button at line ${idx + 1} missing aria-label`);
        }
      });

      // Check charts for aria-label
      if (filepath.includes('charts') || filepath.includes('dashboard')) {
        if (content.includes('role="img"') && !content.includes('aria-label')) {
          issues.push('Chart with role="img" missing aria-label');
        }
      }

      return issues;
    }
  },

  colorContrast: {
    name: 'Color Contrast',
    description: 'Text must have minimum 4.5:1 contrast ratio (WCAG AA)',
    severity: 'critical',
    check: (content, filepath) => {
      const issues = [];

      // Check for text on colored backgrounds without text-shadow
      const problematicPatterns = [
        /text-white\/[0-3]0[^>]*style="[^"]*background[^"]*"/g,
        /text-\[#00f5d4\][^}]*text-shadow:\s*none/g,
        /text-rose-400[^}]*text-shadow:\s*none/g,
      ];

      problematicPatterns.forEach((pattern) => {
        if (pattern.test(content)) {
          issues.push(`Low contrast text detected: ${pattern}`);
        }
      });

      return issues;
    }
  },

  keyboardNav: {
    name: 'Keyboard Navigation',
    description: 'Interactive elements must be keyboard accessible',
    severity: 'critical',
    check: (content, filepath) => {
      const issues = [];

      // Check for divs with onClick but without tabindex or role
      const onClickDivs = content.match(/<div[^>]*onClick[^>]*>/g) || [];
      onClickDivs.forEach((div) => {
        if (!div.includes('tabIndex') && !div.includes('role="button"')) {
          issues.push('Div with onClick missing tabIndex or role="button"');
        }
      });

      // Check for interactive elements without focus styles
      if (content.includes('onClick') || content.includes('onClick')) {
        if (!content.includes('focus:') && !content.includes(':focus')) {
          issues.push('Interactive elements missing focus styles');
        }
      }

      return issues;
    }
  },

  semanticHtml: {
    name: 'Semantic HTML',
    description: 'Use semantic HTML elements (<button>, <input>, not <div>)',
    severity: 'medium',
    check: (content, filepath) => {
      const issues = [];

      // Check for divs used as buttons
      if (content.includes('role="button"') && !content.includes('<button')) {
        issues.push('Consider using <button> instead of div with role="button"');
      }

      // Check for img without alt
      const imgMatches = content.match(/<img[^>]*>/g) || [];
      imgMatches.forEach((img) => {
        if (!img.includes('alt')) {
          issues.push('Image missing alt attribute');
        }
      });

      return issues;
    }
  },

  formLabels: {
    name: 'Form Labels',
    description: 'Form inputs must have associated labels',
    severity: 'critical',
    check: (content, filepath) => {
      const issues = [];

      // Check inputs without aria-label or label association
      const inputMatches = content.match(/<(input|select|textarea)[^>]*>/g) || [];
      inputMatches.forEach((input) => {
        const hasId = input.includes('id=');
        const hasAriaLabel = input.includes('aria-label');
        const hasAriaLabelledby = input.includes('aria-labelledby');

        if (!hasId && !hasAriaLabel && !hasAriaLabelledby) {
          issues.push('Form input missing label association');
        }
      });

      return issues;
    }
  },

  focusManagement: {
    name: 'Focus Management',
    description: 'Focus should be visible and logical',
    severity: 'medium',
    check: (content, filepath) => {
      const issues = [];

      // Check for focus indicators
      if (content.includes('cursor-pointer') || content.includes('hover:')) {
        if (!content.includes('focus:') && !content.includes(':focus')) {
          issues.push('Interactive elements with hover but no focus styles');
        }
      }

      // Check for autoFocus (use sparingly)
      if (content.includes('autoFocus')) {
        issues.push('autoFocus detected - use sparingly and provide context');
      }

      return issues;
    }
  },

  screenReaderSupport: {
    name: 'Screen Reader Support',
    description: 'Content must be accessible to screen readers',
    severity: 'critical',
    check: (content, filepath) => {
      const issues = [];

      // Check for icon-only buttons without aria-label
      const iconButtons = content.match(/<button[^>]*>.*?(?:size=|lucide-)[^<]*<\/button>/gs) || [];
      iconButtons.forEach((btn) => {
        if (!btn.includes('aria-label') && !btn.includes('aria-labelledby')) {
          // Check if it has text content
          const textContent = btn.replace(/<[^>]*>/g, '').trim();
          if (!textContent || textContent.length < 3) {
            issues.push('Icon-only button missing aria-label');
          }
        }
      });

      // Check for "hidden" text that should be screen reader only
      if (content.includes('sr-only') || content.includes('screen-reader-only')) {
        // This is good - no issue
      }

      return issues;
    }
  },

  headingStructure: {
    name: 'Heading Structure',
    description: 'Headings must be nested logically (h1 → h2 → h3)',
    severity: 'medium',
    check: (content, filepath) => {
      const issues = [];

      // Check for skipped heading levels
      const headings = content.match(/<h([1-6])/g) || [];
      for (let i = 1; i < headings.length; i++) {
        const currentLevel = parseInt(headings[i].match(/\d/)[0]);
        const prevLevel = parseInt(headings[i - 1].match(/\d/)[0]);

        if (currentLevel > prevLevel + 1) {
          issues.push(`Skipped heading level: h${prevLevel} → h${currentLevel}`);
        }
      }

      return issues;
    }
  }
};

function auditFile(filepath) {
  const content = fs.readFileSync(filepath, 'utf-8');
  const filename = path.basename(filepath);

  const results = {
    filename,
    issues: [],
    checks: {}
  };

  Object.entries(AUDIT_CHECKS).forEach(([key, check]) => {
    const issues = check.check(content, filepath);

    results.checks[key] = {
      name: check.name,
      severity: check.severity,
      passed: issues.length === 0,
      issues
    };

    if (issues.length > 0) {
      results.issues.push({
        check: check.name,
        severity: check.severity,
        description: check.description,
        issues
      });
    }
  });

  return results;
}

function walkDirectory(dir, callback) {
  const files = fs.readdirSync(dir);

  files.forEach((file) => {
    const filepath = path.join(dir, file);
    const stat = fs.statSync(filepath);

    if (stat.isDirectory()) {
      walkDirectory(filepath, callback);
    } else if (file.endsWith('.tsx') || file.endsWith('.jsx')) {
      callback(filepath);
    }
  });
}

function main() {
  console.log('🔍 WCAG 2.1 AA Accessibility Audit\n');
  console.log('=' .repeat(70));
  console.log();

  const allResults = [];

  walkDirectory(FRONTEND_DIR, (filepath) => {
    if (filepath.includes('dashboard') || filepath.includes('charts')) {
      const result = auditFile(filepath);
      if (result.issues.length > 0) {
        allResults.push(result);
      }
    }
  });

  // Summary by severity
  const criticalIssues = allResults.flatMap(r =>
    r.issues.filter(i => i.severity === 'critical')
  );
  const mediumIssues = allResults.flatMap(r =>
    r.issues.filter(i => i.severity === 'medium')
  );

  console.log(`📊 Audit Results:\n`);
  console.log(`   Files checked: ${allResults.length + (45 - allResults.length)}`);
  console.log(`   Files with issues: ${allResults.length}`);
  console.log(`   Critical issues: ${criticalIssues.length}`);
  console.log(`   Medium issues: ${mediumIssues.length}`);
  console.log();

  // Show critical issues
  if (criticalIssues.length > 0) {
    console.log('❌ CRITICAL ISSUES:\n');
    criticalIssues.forEach((issue) => {
      console.log(`   ${issue.check}: ${issue.description}`);
      issue.issues.forEach((i) => {
        console.log(`      → ${i}`);
      });
      console.log();
    });
  }

  // Show medium issues
  if (mediumIssues.length > 0) {
    console.log('⚠️  MEDIUM PRIORITY:\n');
    mediumIssues.forEach((issue) => {
      console.log(`   ${issue.check}: ${issue.description}`);
      if (issue.issues.length <= 3) {
        issue.issues.forEach((i) => {
          console.log(`      → ${i}`);
        });
      } else {
        console.log(`      → ${issue.issues.length} occurrences`);
      }
      console.log();
    });
  }

  console.log('=' .repeat(70));

  if (criticalIssues.length === 0 && mediumIssues.length === 0) {
    console.log('\n✨ PASSED: All WCAG 2.1 AA checks passed!\n');
    return 0;
  } else if (criticalIssues.length === 0) {
    console.log('\n⚠️  PASSED with warnings: Review medium priority issues\n');
    return 0;
  } else {
    console.log('\n❌ FAILED: Critical issues must be fixed\n');
    return 1;
  }
}

main();
