import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
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
    sourcemap: true, // Set to false for production CDN to reduce bundle size by ~500KB
    minify: 'terser',
    terserOptions: {
      compress: {
        // Keep console.error and console.warn for error reporting
        // For production CDN, consider using pure_funcs: ['console.log', 'console.debug']
        drop_console: false,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      external: ['react', 'react-dom'],
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
  },
});
