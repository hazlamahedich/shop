/**
 * Performance monitoring script for Story 9-1
 * Runs Lighthouse audits and validates performance budgets
 */

import lighthouse from 'lighthouse';
import chromeLauncher from 'chrome-launcher';
import fs from 'fs';
import path from 'path';

const PERFORMANCE_BUDGETS = {
  'first-contentful-paint': { target: 2000, unit: 'ms' },
  'largest-contentful-paint': { target: 2500, unit: 'ms' },
  'cumulative-layout-shift': { target: 0.1, unit: 'score' },
  'total-blocking-time': { target: 300, unit: 'ms' },
  'speed-index': { target: 3000, unit: 'ms' },
};

async function runLighthouse(url) {
  const chrome = await chromeLauncher.launch({
    chromeFlags: ['--headless', '--disable-gpu', '--no-sandbox'],
  });

  const options = {
    logLevel: 'info',
    output: ['html', 'json'],
    onlyCategories: ['performance', 'accessibility'],
    port: chrome.port,
  };

  const runnerResult = await lighthouse(url, options);

  await chrome.kill();

  return runnerResult;
}

function validatePerformance(lighthouseResult) {
  const audits = lighthouseResult.lhr.audits;
  const failures = [];

  console.log('\n📊 Performance Metrics:\n');

  for (const [metric, budget] of Object.entries(PERFORMANCE_BUDGETS)) {
    const audit = audits[metric];
    const value = audit.numericValue;

    const status = value <= budget.target ? '✅' : '❌';
    console.log(`${status} ${metric}: ${value.toFixed(2)}${budget.unit} (target: ${budget.target}${budget.unit})`);

    if (value > budget.target) {
      failures.push({
        metric,
        actual: value,
        target: budget.target,
      });
    }
  }

  return failures;
}

async function main() {
  const url = process.env.TEST_URL || 'http://localhost:5173/widget-test';
  
  console.log(`🚀 Running Lighthouse on ${url}\n`);

  try {
    const result = await runLighthouse(url);

    const reportPath = path.join(process.cwd(), '.lighthouseci');
    if (!fs.existsSync(reportPath)) {
      fs.mkdirSync(reportPath, { recursive: true });
    }

    const timestamp = Date.now();
    fs.writeFileSync(
      path.join(reportPath, `lighthouse-report-${timestamp}.html`),
      result.report[0]
    );
    fs.writeFileSync(
      path.join(reportPath, `lighthouse-report-${timestamp}.json`),
      result.report[1]
    );

    console.log(`\n📄 Reports saved to ${reportPath}\n`);

    const failures = validatePerformance(result);

    if (failures.length > 0) {
      console.error(`\n❌ ${failures.length} performance budget(s) exceeded:\n`);
      failures.forEach(f => {
        console.error(`  - ${f.metric}: ${f.actual.toFixed(2)} > ${f.target}`);
      });
      process.exit(1);
    }

    console.log('\n✅ All performance budgets passed!\n');
    process.exit(0);
  } catch (error) {
    console.error('❌ Lighthouse run failed:', error);
    process.exit(1);
  }
}

main();
