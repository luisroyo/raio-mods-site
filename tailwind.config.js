module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        'neon-cyan': '#06b6d4',
        'neon-green': '#22c55e',
        'accent-cyan': '#06b6d4',
        'accent-blue': '#3b82f6',
        'accent-purple': '#8b5cf6',
        'accent-green': '#22c55e',
        'accent-amber': '#f59e0b',
      },
      boxShadow: {
        'neon-cyan': '0 0 20px rgba(6, 182, 212, 0.15), 0 0 40px rgba(6, 182, 212, 0.05)',
      }
    },
  },
  plugins: [],
}
