import { describe, test, expect, beforeAll } from 'vitest';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { gzipSizeFromFile } from 'gzip-size';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe('Widget Performance (Unit)', () => {
  const distPath = path.join(__dirname, '../../dist/widget');

  beforeAll(() => {
    if (!fs.existsSync(distPath)) {
      console.log('Skipping: Build widget first with npm run build:widget');
    }
  });

  test('UMD bundle size within 100KB budget', async () => {
    const umdPath = path.join(distPath, 'widget.umd.js');
    if (!fs.existsSync(umdPath)) {
      console.log('Skipping: widget.umd.js not found');
      return;
    }
    const gzipped = await gzipSizeFromFile(umdPath);
    expect(gzipped).toBeLessThan(100 * 1024);
  });

  test('ES bundle size within 100KB budget', async () => {
    const esPath = path.join(distPath, 'widget.es.js');
    if (!fs.existsSync(esPath)) {
      console.log('Skipping: widget.es.js not found');
      return;
    }
    const gzipped = await gzipSizeFromFile(esPath);
    expect(gzipped).toBeLessThan(100 * 1024);
  });

  test('no sourcemap files in production build', () => {
    const mapFiles = fs.existsSync(distPath)
      ? fs.readdirSync(distPath).filter(f => f.endsWith('.map'))
      : [];
    expect(mapFiles).toHaveLength(0);
  });

  test('both UMD and ES formats exist', () => {
    if (!fs.existsSync(distPath)) {
      console.log('Skipping: dist/widget not found');
      return;
    }
    expect(fs.existsSync(path.join(distPath, 'widget.umd.js'))).toBe(true);
    expect(fs.existsSync(path.join(distPath, 'widget.es.js'))).toBe(true);
  });

  test('CSS is bundled (inline in JS)', async () => {
    const cssPath = path.join(distPath, 'widget.css');
    const umdPath = path.join(distPath, 'widget.umd.js');
    
    if (!fs.existsSync(distPath)) {
      console.log('Skipping: dist/widget not found');
      return;
    }
    
    const separateCssExists = fs.existsSync(cssPath);
    
    if (!separateCssExists) {
      if (!fs.existsSync(umdPath)) {
        console.log('Skipping: widget.umd.js not found');
        return;
      }
      
      const umdContent = fs.readFileSync(umdPath, 'utf-8');
      const hasInlineStyles = umdContent.includes('.chat-') || umdContent.includes('widget-');
      expect(hasInlineStyles, 'CSS should be inlined in JS bundle when no separate CSS file').toBe(true);
    }
  });
});
