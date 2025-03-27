import { defineConfig } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';
import { pluginNodePolyfill } from '@rsbuild/plugin-node-polyfill';
// import tailwindcssPlugin from 'rsbuild-plugin-tailwindcss';

export default defineConfig({
  plugins: [
    pluginReact(),
    pluginNodePolyfill(),
    // Skip Tailwind plugin for now to get the app running
    // Will re-enable once we figure out the correct import
  ],
  source: {
    entry: {
      index: './src/main.tsx'
    }
  },
  server: {
    port: 1420 // Same port that Tauri expects by default
  },
  html: {
    title: 'Kled.io - Development Environment Manager'
  },
  tools: {
    rspack: {
      // Add any rspack-specific options here if needed
    }
  },
  output: {
    target: ['es2020'],
    charset: false,
    inlineStyles: false,
    cssModules: {
      // Enable CSS modules for all .module extension files
      auto: true
    }
  }
});
