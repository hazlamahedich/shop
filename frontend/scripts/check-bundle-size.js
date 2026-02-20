import { gzipSizeFromFile } from 'gzip-size';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const umdPath = path.join(__dirname, '../dist/widget/widget.umd.js');
const esPath = path.join(__dirname, '../dist/widget/widget.es.js');

async function checkBundleSize() {
  if (!fs.existsSync(umdPath) || !fs.existsSync(esPath)) {
    console.error('❌ Widget build not found. Run npm run build:widget first.');
    process.exit(1);
  }

  const umdGzipped = await gzipSizeFromFile(umdPath);
  const esGzipped = await gzipSizeFromFile(esPath);

  console.log(`UMD gzipped: ${(umdGzipped / 1024).toFixed(1)} KB`);
  console.log(`ES gzipped: ${(esGzipped / 1024).toFixed(1)} KB`);

  const limit = 100 * 1024;
  if (umdGzipped > limit || esGzipped > limit) {
    console.error('❌ Bundle exceeds 100KB limit!');
    process.exit(1);
  }
  console.log('✅ Bundle within size budget');
}

checkBundleSize();
