/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
    "./src/pages/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        text: "var(--text)",
        "text-muted": "var(--text-muted)",
        accent: "var(--accent)",
        "accent-hover": "var(--accent-hover)",
        border: "var(--border)",
        navbar: "var(--navbar-bg)",
        "btn-accent": "var(--btn-accent-bg)",
        "btn-accent-hover": "var(--btn-accent-hover-bg)",
        "btn-accent-text": "var(--btn-accent-text)",
        "btn-default": "var(--btn-default-bg)",
        "btn-default-hover": "var(--btn-default-hover-bg)",
        "btn-default-text": "var(--btn-default-text)",
        logo: "var(--logo-color)",
      },
    },
  },
  plugins: [],
};
