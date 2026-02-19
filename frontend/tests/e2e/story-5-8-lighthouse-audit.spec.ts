/**
 * Lighthouse Performance Audit Tests
 *
 * Story 5-8: Performance Optimization (AC7)
 * Automated Lighthouse-style performance audit validation
 * Tests bundle sizes and performance metrics
 *
 * @tags e2e widget story-5-8 performance lighthouse audit
 * @priority P2
 */

import { test, expect } from '@playwright/test';

test.describe('Performance - Lighthouse Audit (AC7)', () => {
  test.slow();

  test('[P2] widget bundle performance budget validation', async ({ page }) => {
    const umdResponse = await page.request.get('/dist/widget/widget.umd.js');
    expect(umdResponse.ok()).toBe(true);
    const umdBody = await umdResponse.text();
    const umdSizeKB = new TextEncoder().encode(umdBody).length / 1024;

    const esResponse = await page.request.get('/dist/widget/widget.es.js');
    expect(esResponse.ok()).toBe(true);
    const esBody = await esResponse.text();
    const esSizeKB = new TextEncoder().encode(esBody).length / 1024;

    console.log('\n=== Bundle Performance Budget ===');
    console.log(`UMD Bundle: ${umdSizeKB.toFixed(1)}KB`);
    console.log(`ES Bundle: ${esSizeKB.toFixed(1)}KB`);
    console.log(`Budget: 100KB (gzipped) / 200KB (raw)`);
    console.log('===================================\n');

    expect(umdSizeKB, 'UMD bundle should be under 200KB raw').toBeLessThan(200);
    expect(esSizeKB, 'ES bundle should be under 200KB raw').toBeLessThan(200);

    if (umdSizeKB <= 120 && esSizeKB <= 120) {
      console.log('✅ Bundles meet optimal <120KB budget');
    } else if (umdSizeKB <= 150 && esSizeKB <= 150) {
      console.log('⚠️ Bundles within acceptable range (120-150KB)');
    } else {
      console.log('❌ Bundles exceed optimal budget but under max');
    }
  });

  test('[P2] production build minification validation', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.es.js');
    const body = await response.text();

    const hasConsoleLog = body.includes('console.log(');
    const hasConsoleDebug = body.includes('console.debug(');
    const hasDebugger = body.includes('debugger');
    const hasConsoleError = body.includes('console.error');
    const hasConsoleWarn = body.includes('console.warn');

    console.log('\n=== Minification Validation ===');
    console.log(`console.log removed: ${!hasConsoleLog ? '✅' : '❌'}`);
    console.log(`console.debug removed: ${!hasConsoleDebug ? '✅' : '❌'}`);
    console.log(`debugger removed: ${!hasDebugger ? '✅' : '❌'}`);
    console.log(`console.error preserved: ${hasConsoleError ? '✅' : '❌'}`);
    console.log(`console.warn preserved: ${hasConsoleWarn ? '✅' : '❌'}`);
    console.log('================================\n');

    expect(hasConsoleLog, 'console.log should be removed').toBe(false);
    expect(hasConsoleDebug, 'console.debug should be removed').toBe(false);
    expect(hasDebugger, 'debugger statements should be removed').toBe(false);
    expect(hasConsoleError || hasConsoleWarn, 'console.error/warn should be preserved').toBe(true);
  });

  test('[P2] core web vitals on main app', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    const coreWebVitals = await page.evaluate(async () => {
      await new Promise(resolve => setTimeout(resolve, 1000));

      const paintEntries = performance.getEntriesByType('paint');
      const fcp = paintEntries.find(e => e.name === 'first-contentful-paint')?.startTime || 0;

      let lcp = 0;
      try {
        const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
        if (lcpEntries.length > 0) {
          lcp = (lcpEntries[lcpEntries.length - 1] as any).startTime;
        }
      } catch {
        lcp = 0;
      }

      let cls = 0;
      try {
        const clsEntries = performance.getEntriesByType('layout-shift');
        for (const entry of clsEntries) {
          if (!(entry as any).hadRecentInput) {
            cls += (entry as any).value;
          }
        }
      } catch {
        cls = 0;
      }

      const navEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const domContentLoaded = navEntry?.domContentLoadedEventEnd || 0;
      const loadComplete = navEntry?.loadEventEnd || 0;

      return { fcp, lcp, cls, domContentLoaded, loadComplete };
    });

    console.log('\n=== Core Web Vitals ===');
    console.log(`FCP (First Contentful Paint): ${coreWebVitals.fcp.toFixed(0)}ms`);
    console.log(`LCP (Largest Contentful Paint): ${coreWebVitals.lcp.toFixed(0)}ms`);
    console.log(`CLS (Cumulative Layout Shift): ${coreWebVitals.cls.toFixed(4)}`);
    console.log(`DOM Content Loaded: ${coreWebVitals.domContentLoaded.toFixed(0)}ms`);
    console.log(`Load Complete: ${coreWebVitals.loadComplete.toFixed(0)}ms`);
    console.log('========================\n');

    const fcpScore = coreWebVitals.fcp <= 1800 ? '✅ GOOD' : coreWebVitals.fcp <= 3000 ? '⚠️ NEEDS IMPROVEMENT' : '❌ POOR';
    const lcpScore = coreWebVitals.lcp <= 2500 ? '✅ GOOD' : coreWebVitals.lcp <= 4000 ? '⚠️ NEEDS IMPROVEMENT' : '❌ POOR';
    const clsScore = coreWebVitals.cls <= 0.1 ? '✅ GOOD' : coreWebVitals.cls <= 0.25 ? '⚠️ NEEDS IMPROVEMENT' : '❌ POOR';

    console.log(`FCP Score: ${fcpScore}`);
    console.log(`LCP Score: ${lcpScore}`);
    console.log(`CLS Score: ${clsScore}`);

    expect(coreWebVitals.fcp, 'FCP should be under 3s').toBeLessThan(3000);
    expect(coreWebVitals.cls, 'CLS should be under 0.25').toBeLessThan(0.25);
  });

  test('[P2] performance regression detection', async ({ page }) => {
    const baselineMetrics = {
      maxFCP: 3000,
      maxLCP: 4000,
      maxCLS: 0.25,
      maxUmdBundle: 200,
      maxEsBundle: 200,
    };

    const umdResponse = await page.request.get('/dist/widget/widget.umd.js');
    const umdSizeKB = umdResponse.ok() ? new TextEncoder().encode(await umdResponse.text()).length / 1024 : 0;

    const esResponse = await page.request.get('/dist/widget/widget.es.js');
    const esSizeKB = esResponse.ok() ? new TextEncoder().encode(await esResponse.text()).length / 1024 : 0;

    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    const perfMetrics = await page.evaluate(async () => {
      await new Promise(resolve => setTimeout(resolve, 1000));

      const paintEntries = performance.getEntriesByType('paint');
      const fcp = paintEntries.find(e => e.name === 'first-contentful-paint')?.startTime || 0;

      let lcp = 0;
      try {
        const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
        if (lcpEntries.length > 0) {
          lcp = (lcpEntries[lcpEntries.length - 1] as any).startTime;
        }
      } catch {
        lcp = 0;
      }

      let cls = 0;
      try {
        const clsEntries = performance.getEntriesByType('layout-shift');
        for (const entry of clsEntries) {
          if (!(entry as any).hadRecentInput) {
            cls += (entry as any).value;
          }
        }
      } catch {
        cls = 0;
      }

      return { fcp, lcp, cls };
    });

    const regressions: string[] = [];

    if (perfMetrics.fcp > baselineMetrics.maxFCP) {
      regressions.push(`FCP regression: ${perfMetrics.fcp.toFixed(0)}ms > ${baselineMetrics.maxFCP}ms baseline`);
    }
    if (perfMetrics.lcp > baselineMetrics.maxLCP) {
      regressions.push(`LCP regression: ${perfMetrics.lcp.toFixed(0)}ms > ${baselineMetrics.maxLCP}ms baseline`);
    }
    if (perfMetrics.cls > baselineMetrics.maxCLS) {
      regressions.push(`CLS regression: ${perfMetrics.cls.toFixed(4)} > ${baselineMetrics.maxCLS} baseline`);
    }
    if (umdSizeKB > baselineMetrics.maxUmdBundle) {
      regressions.push(`UMD bundle regression: ${umdSizeKB.toFixed(1)}KB > ${baselineMetrics.maxUmdBundle}KB baseline`);
    }
    if (esSizeKB > baselineMetrics.maxEsBundle) {
      regressions.push(`ES bundle regression: ${esSizeKB.toFixed(1)}KB > ${baselineMetrics.maxEsBundle}KB baseline`);
    }

    console.log('\n=== Performance Regression Check ===');
    console.log(`FCP: ${perfMetrics.fcp.toFixed(0)}ms (baseline: ${baselineMetrics.maxFCP}ms)`);
    console.log(`LCP: ${perfMetrics.lcp.toFixed(0)}ms (baseline: ${baselineMetrics.maxLCP}ms)`);
    console.log(`CLS: ${perfMetrics.cls.toFixed(4)} (baseline: ${baselineMetrics.maxCLS})`);
    console.log(`UMD Bundle: ${umdSizeKB.toFixed(1)}KB (baseline: ${baselineMetrics.maxUmdBundle}KB)`);
    console.log(`ES Bundle: ${esSizeKB.toFixed(1)}KB (baseline: ${baselineMetrics.maxEsBundle}KB)`);
    console.log('=====================================\n');

    if (regressions.length > 0) {
      console.log('⚠️ Performance regressions detected:');
      regressions.forEach(r => console.log(`  - ${r}`));
    } else {
      console.log('✅ No performance regressions detected');
    }

    expect(regressions, 'No performance regressions should be detected').toHaveLength(0);
  });
});
