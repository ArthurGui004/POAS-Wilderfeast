import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
  children: React.ReactNode;
}

export default function Button({ variant = 'primary', children, ...props }: ButtonProps) {
  const baseStyle = "w-full font-bold py-3 rounded mt-2 transition-all uppercase tracking-wider text-sm shadow-lg disabled:opacity-50 disabled:cursor-not-allowed";
  
  const variants = {
    primary: "bg-wildorange text-white hover:bg-orange-700 shadow-wildorange/20",
    secondary: "bg-wildcard text-wildorange border border-wildorange/50 hover:bg-wildorange/10"
  };

  return (
    <button className={`${baseStyle} ${variants[variant]}`} {...props}>
      {children}
    </button>
  );
}