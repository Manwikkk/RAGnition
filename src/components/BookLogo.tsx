import React from "react";

export default function BookLogo({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="36"
      height="36"
      viewBox="0 0 36 36"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="logoGrad" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C3AED" />
          <stop offset="0.6" stopColor="#9F44F0" />
          <stop offset="1" stopColor="#EC4899" />
        </linearGradient>
      </defs>
      {/* Plain gradient rounded square */}
      <rect x="1" y="1" width="34" height="34" rx="10" fill="url(#logoGrad)" />
      {/* Subtle outer stroke for definition */}
      <rect x="1" y="1" width="34" height="34" rx="10" stroke="rgba(255,255,255,0.15)" strokeWidth="1" fill="none" />
    </svg>
  );
}
