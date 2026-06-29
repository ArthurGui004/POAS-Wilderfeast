'use client';
import Link from 'next/link';

export default function HomePage() {
  // Mock inicial simulando os Ferais carregados do banco
  const personagens = [
    { id: 1, nome: "Kaelen", especialidade: "Açougueiro", brio: 3, tino: 2 },
    { id: 2, nome: "Maeve", especialidade: "Molheira", brio: 1, tino: 4 }
  ];

  return (
    <main className="min-h-screen bg-wilddark text-zinc-100 p-8">
      <header className="max-w-6xl mx-auto flex justify-between items-center mb-12 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-3xl font-black text-wildorange tracking-wide">SUA MATILHA</h1>
          <p className="text-zinc-400 text-sm">Selecione um Caçador ou inicie um novo Banquete.</p>
        </div>
        <button className="bg-wildorange hover:bg-orange-700 text-white font-bold px-5 py-2.5 rounded transition-all text-sm uppercase">
          Mago de Criação (+)
        </button>
      </header>

      <section className="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {personagens.map((p) => (
          <Link href={`/personagem/${p.id}`} key={p.id}>
            <div className="bg-wildcard p-6 rounded-lg border border-zinc-800 hover:border-wildorange/60 cursor-pointer transition-all duration-300 transform hover:-translate-y-1 shadow-md">
              <span className="text-xs font-bold text-wildorange uppercase tracking-widest">{p.especialidade}</span>
              <h2 className="text-2xl font-black text-white mt-1">{p.nome}</h2>
              <div className="mt-4 pt-4 border-t border-zinc-800 flex justify-between text-xs text-zinc-400">
                <span>Brio: {p.brio}</span>
                <span>Tino: {p.tino}</span>
              </div>
            </div>
          </Link>
        ))}
      </section>
    </main>
  );
}