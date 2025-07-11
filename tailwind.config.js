/** @type {import('tailwindcss').Config} */

const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
	content: [
		'static/css/select2.css',
		'./templates/**/*.html',
		'./templates/**/**/*.html',
		// Templates in other apps ( the app name needs to end with _app)
		'./*_app/templates/**/*.html',
		// look in all js files in the assets folder
		'./assets/**/*.js',
		'./assets/*.js'
		// Ignore files in node_modules
		// '!../**/node_modules',
		// '!../**/node_modules',
		// Include JavaScript files that might contain Tailwind CSS classes
		// '../**/*.js',
		// Include Python files that might contain Tailwind CSS classes
		// '../**/*.py',
	],
	theme: {
    extend: {
      fontFamily: {
        sans: ['Inter var', ...defaultTheme.fontFamily.sans],
      },
    },
  },
	plugins: [
		require('@tailwindcss/typography'),
		require('@tailwindcss/forms'),
		require('@tailwindcss/aspect-ratio'),
	]
}
