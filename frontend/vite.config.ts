import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [
    react({
      jsxInject: `import React from 'react'`
    })
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') }
  },
  css: { postcss: './postcss.config.cjs' },
  server: { port: 5173, open: true },
  build: { outDir: 'dist' },
});
