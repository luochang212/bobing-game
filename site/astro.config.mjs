// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// GitHub Pages 项目页：https://luochang212.github.io/bobing-game/
export default defineConfig({
  site: 'https://luochang212.github.io',
  base: '/bobing-game',
  vite: {
    plugins: [tailwindcss()],
  },
});
