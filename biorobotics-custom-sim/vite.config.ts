import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import wasm from "vite-plugin-wasm";
import topLevelAwait from "vite-plugin-top-level-await";

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss(), wasm(), topLevelAwait()],
  optimizeDeps: {
    exclude: ['@dimforge/rapier3d']
  }
});
