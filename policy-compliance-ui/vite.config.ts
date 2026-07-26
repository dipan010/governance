import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    // When VITE_USE_MOCK=false the app talks to the FastAPI backend here.
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
