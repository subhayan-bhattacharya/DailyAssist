import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH ?? '/',
  resolve: {
    alias: {
      'aws-amplify': path.resolve(__dirname, 'node_modules/aws-amplify'),
    },
    dedupe: ['aws-amplify'],
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
});
