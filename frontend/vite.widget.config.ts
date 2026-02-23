import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { visualizer } from 'rollup-plugin-visualizer';
import { readFileSync } from 'fs';

const pkg = JSON.parse(readFileSync('./package.json', 'utf-8'));

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      filename: 'dist/widget/stats.html',
      gzipSize: true,
      open: false,
    }),
  ],
  build: {
    lib: {
      entry: path.resolve(__dirname, './src/widget/loader.ts'),
      name: 'ShopBotWidget',
      formats: ['umd', 'es'],
      fileName: (format) => `widget.${format}.js`,
      cssFileName: 'widget',
    },
    outDir: 'dist/widget',
    emptyOutDir: true,
    sourcemap: false,
    minify: false, // Disable for debugging
    rollupOptions: {
      output: {
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
    __VITE_WIDGET_VERSION__: JSON.stringify(pkg.version),
  },
});
