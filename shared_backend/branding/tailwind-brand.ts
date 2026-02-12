/**
 * CareerTrojan — Shared Brand Theme (Tailwind CSS)
 * =================================================
 *
 * Import into each app's tailwind.config.ts:
 *   import { brandTheme } from '../../../shared_backend/branding/tailwind-brand';
 *   export default { theme: { extend: brandTheme } }
 *
 * Keeps colors, fonts, and spacing consistent across admin/user/mentor.
 */
export const brandTheme = {
  colors: {
    brand: {
      primary: '#4338ca',
      'primary-light': '#6366f1',
      'primary-dark': '#312e81',
      secondary: '#764ba2',
    },
    accent: {
      admin: '#60a5fa',
      user: '#6366f1',
      mentor: '#4ade80',
    },
    surface: {
      dark: '#1e293b',
      light: '#f8fafc',
    },
    bg: {
      dark: '#0f172a',
      light: '#f8fafc',
    },
  },
  fontFamily: {
    sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
    mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
  },
};
