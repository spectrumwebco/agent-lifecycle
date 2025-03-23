import { defineConfig } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';
import { pluginTailwindCSS } from '@rsbuild/plugin-tailwindcss';

export default defineConfig({
  plugins: [
    pluginReact(),
    pluginTailwindCSS(),
  ],
  source: {
    entry: {
      index: './src/index.tsx',
    },
  },
  server: {
    port: 1420, // Same port that Tauri expects by default
  },
  html: {
    title: 'Kled.io - Development Environment Manager',
  },
  tools: {
    rspack: {
      // Add any rspack-specific options here if needed
    },
  },
  output: {
    target: ['es2020'],
    charset: false,
    inlineStyles: false,
    cssModules: {
      // Enable CSS modules for all .module extension files
      auto: true,
    },
  },
});
