import React from 'react';

interface LogoProps extends React.SVGProps<SVGSVGElement> {
    size?: number | string;
}

export const Logo: React.FC<LogoProps> = ({ size = 40, className, ...props }) => {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 64 64"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className={className}
            {...props}
        >
            <defs>
                <linearGradient id="logoGradient" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#60a5fa" />
                </linearGradient>
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                    <feMerge>
                        <feMergeNode in="coloredBlur" />
                        <feMergeNode in="SourceGraphic" />
                    </feMerge>
                </filter>
            </defs>

            {/* Background Shape - Subtle Hexagon or Circle */}
            <path
                d="M32 4 L58 19 V45 L32 60 L6 45 V19 Z"
                fill="url(#logoGradient)"
                fillOpacity="0.1"
                stroke="url(#logoGradient)"
                strokeWidth="1.5"
                strokeOpacity="0.3"
            />

            {/* Distribution Curve */}
            <path
                d="M12 42 C12 42, 20 42, 24 24 C 28 6, 36 6, 40 24 C 44 42, 52 42, 52 42"
                stroke="url(#logoGradient)"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
                filter="url(#glow)"
            />

            {/* Data Points / Bars */}
            <circle cx="32" cy="18" r="3" fill="#fff" fillOpacity="0.9" />
            <circle cx="24" cy="28" r="2" fill="#fff" fillOpacity="0.6" />
            <circle cx="40" cy="28" r="2" fill="#fff" fillOpacity="0.6" />
        </svg>
    );
};
