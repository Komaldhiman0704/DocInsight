import React from 'react'

/**
 * DocInsight Logo Component - Minimal Clean Edition
 * Simple, modern design with:
 * - Bold document shape
 * - Simple accent line
 * - Minimalist aesthetic
 * - Clean and professional
 */
export default function Logo({ size = 24, animated = false, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`${className}`}
    >
      <defs>
        <linearGradient id="simpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1e40af" />
          <stop offset="100%" stopColor="#0c2d6b" />
        </linearGradient>
      </defs>

      {/* Simple document shape - main body */}
      <path
        d="M 35 20 L 75 20 Q 85 20 85 30 L 85 95 Q 85 105 75 105 L 35 105 Q 25 105 25 95 L 25 30 Q 25 20 35 20 Z"
        fill="url(#simpleGrad)"
      />

      {/* Simple fold corner */}
      <path
        d="M 75 20 L 85 30 L 75 30 Z"
        fill="url(#simpleGrad)"
        opacity="0.8"
      />

      {/* Clean accent line - represents insight */}
      <line
        x1="35"
        y1="55"
        x2="75"
        y2="55"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
        opacity="0.9"
      />

      {/* Two smaller lines below */}
      <line
        x1="35"
        y1="70"
        x2="65"
        y2="70"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
        opacity="0.7"
      />

      <line
        x1="35"
        y1="83"
        x2="60"
        y2="83"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
        opacity="0.5"
      />

      {/* Optional simple pulse when animated */}
      {animated && (
        <g style={{ animation: 'simplePulse 2s ease-in-out infinite' }}>
          <circle
            cx="60"
            cy="60"
            r="50"
            fill="none"
            stroke="url(#simpleGrad)"
            strokeWidth="1"
            opacity="0.4"
          />
        </g>
      )}

      <style>{`
        @keyframes simplePulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.7; }
        }
      `}</style>
    </svg>
  )
}
