import typography from '@tailwindcss/typography'

const token = (name) => `rgb(var(--${name}) / <alpha-value>)`

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        canvas: token('canvas'),
        surface: token('surface'),
        raised: token('raised'),
        line: token('line'),
        fg: token('fg'),
        muted: token('muted'),
        subtle: token('subtle'),
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      typography: {
        DEFAULT: {
          css: {
            // Prose follows the theme tokens, so it also flips to light when printing.
            '--tw-prose-body': 'rgb(var(--muted))',
            '--tw-prose-headings': 'rgb(var(--fg))',
            '--tw-prose-bold': 'rgb(var(--fg))',
            '--tw-prose-links': 'rgb(var(--fg))',
            '--tw-prose-counters': 'rgb(var(--subtle))',
            '--tw-prose-bullets': 'rgb(var(--subtle))',
            '--tw-prose-hr': 'rgb(var(--line))',
            '--tw-prose-quotes': 'rgb(var(--fg))',
            '--tw-prose-quote-borders': 'rgb(var(--line))',
            '--tw-prose-code': 'rgb(var(--fg))',
            '--tw-prose-th-borders': 'rgb(var(--line))',
            '--tw-prose-td-borders': 'rgb(var(--line))',
          },
        },
      },
    },
  },
  plugins: [typography],
}
