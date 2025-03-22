import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";  // Add this

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // Add Tailwind as a Vite plugin
  ],
});
