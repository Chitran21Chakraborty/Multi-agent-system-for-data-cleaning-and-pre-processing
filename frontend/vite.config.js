import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/preprocess': 'http://localhost:8000',
      '/results': 'http://localhost:8000',
      '/download': 'http://localhost:8000',
      '/stream': 'http://localhost:8000',
      '/chat': 'http://localhost:8000'
    }
  }
});
