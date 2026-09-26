export default function Logo({ className = 'h-9 w-9' }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <defs>
        <linearGradient id="logo-gradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#8b5cf6" />
          <stop offset="1" stopColor="#3b82f6" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#logo-gradient)" />
      <rect x="7" y="9" width="18" height="13" rx="4" fill="none" stroke="#fff" strokeWidth="2" />
      <circle cx="12" cy="15.5" r="1.6" fill="#fff" />
      <circle cx="16" cy="15.5" r="1.6" fill="#fff" />
      <circle cx="20" cy="15.5" r="1.6" fill="#fff" />
    </svg>
  )
}
