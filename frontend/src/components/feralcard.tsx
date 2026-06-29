import React from 'react';
import Link from 'next/link';

interface FeralProps {
  id: number;
  nome: string;
  especialidade: string;
  brio: number;
  tino: number;
}

export default function FeralCard({ id, nome, especialidade, brio, tino }: FeralProps) {
  return (
    <Link href={`/personagem/${id}`}>
      <div className="bg-wildcard p-6 rounded-lg border border-zinc-800 hover:border-wildorange/60 cursor-pointer transition-all duration-300 transform hover:-translate-y-1 shadow-md">
        <span className="text-xs font-bold text-wildorange uppercase tracking-widest">{especialidade}</span>
        <h2 className="text-2xl font-black text-white mt-1">{nome}</h2>
        <div className="mt-4 pt-4 border-t border-zinc-800 flex justify-between text-xs text-zinc-400">
          <span>Brio: +{brio}</span>
          <span>Tino: +{tino}</span>
        </div>
      </div>
    </Link>
  );
}