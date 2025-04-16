import React from 'react';

interface ScissorsLogoProps {
  className?: string;
  size?: number;
}

export const ScissorsLogo: React.FC<ScissorsLogoProps> = ({ 
  className = '', 
  size = 24 
}) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 512 512" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <circle cx="256" cy="256" r="240" fill="currentColor" />
      
      {/* 剪刀图案 */}
      <g stroke="white" strokeWidth="16" fill="none">
        {/* 上剪刀刀片 */}
        <path d="M120 180 C 160 180, 230 170, 350 230 L 380 260 L 350 290 C 230 350, 160 340, 120 340 C 80 340, 60 320, 60 280 C 60 240, 80 220, 120 220 C 140 220, 160 240, 160 280 C 160 320, 140 340, 120 340" />
        
        {/* 下剪刀刀片 */}
        <path d="M120 180 C 160 180, 230 190, 350 130 L 380 100 L 350 70 C 230 10, 160 20, 120 20 C 80 20, 60 40, 60 80 C 60 120, 80 140, 120 140 C 140 140, 160 120, 160 80 C 160 40, 140 20, 120 20" transform="translate(0, 300)" />
        
        {/* 剪刀手柄圆环 */}
        <circle cx="120" cy="180" r="40" />
        <circle cx="120" cy="340" r="40" />
      </g>
    </svg>
  );
};

export default ScissorsLogo; 