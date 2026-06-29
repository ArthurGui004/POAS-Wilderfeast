import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export default function Input({ label, ...props }: InputProps) {
  return (
    <div className="flex flex-col mb-4">
      <label className="text-xs text-zinc-400 uppercase font-bold mb-1">
        {label}
      </label>
      <input 
        className="w-full bg-wilddark text-white p-3 rounded border border-zinc-700 focus:border-wildorange outline-none transition-colors focus:ring-1 focus:ring-wildorange" 
        {...props} 
      />
    </div>
  );
}