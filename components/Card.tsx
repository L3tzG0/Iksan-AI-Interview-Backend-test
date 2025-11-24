
import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> = ({ children, className = '', ...props }) => {
  return (
    <div
      className={`bg-white/95 p-6 md:p-7 rounded-[14px] border border-white/80 shadow-soft backdrop-blur-sm transition duration-300 hover:-translate-y-0.5 hover:shadow-elice ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
