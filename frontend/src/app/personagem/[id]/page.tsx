'use client';

export default function FichaPersonagemPage() {
  const estilos = [
    { nome: 'Ligeiro', valor: 3 },
    { nome: 'Poderoso', valor: 4 },
    { nome: 'Preciso', valor: 2 },
    { nome: 'Sagaz', valor: 1 }
  ];

  const habilidades = [
    'Agarrar', 'Armazenar', 'Procurar', 'Mover', 'Estudar', 'Sobreviver', 
    'Socializar', 'Intimidar', 'Furtividade', 'Exibir', 'Cozinhar', 'Curar'
  ];

  return (
    <main className="min-h-screen bg-wilddark text-zinc-100 p-6 md:p-12">
      <div className="max-w-5xl mx-auto bg-wildcard border-2 border-wildorange/30 rounded-xl p-8 shadow-2xl">
        
        {/* Cabeçalho da Ficha */}
        <div className="flex flex-col md:flex-row justify-between border-b border-zinc-800 pb-6 mb-8 gap-4">
          <div>
            <h1 className="text-4xl font-black text-white uppercase tracking-tight">Kaelen, o Feral</h1>
            <p className="text-wildorange font-bold uppercase tracking-wider text-sm mt-1">Origem: Assado de Monstro Inicial (Três Pratos)</p>
          </div>
          <div className="bg-wilddark p-4 rounded-lg border border-zinc-700 min-w-[200px] text-center">
            <span className="text-xs uppercase text-zinc-400 font-bold block">Utensílio de Combate</span>
            <span className="text-lg font-bold text-white">Cutelo Pesado (Durabilidade: 8/10)</span>
          </div>
        </div>

        {/* Status Vitais com Sincronização em Tempo Real (Automatizados) */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-red-950/20 border border-red-800 p-4 rounded-lg text-center">
            <h3 className="text-xs font-bold text-red-500 uppercase">Vigor Atual</h3>
            <span className="text-3xl font-black block mt-1">12 / 15</span>
          </div>
          <div className="bg-amber-950/20 border border-amber-700 p-4 rounded-lg text-center">
            <h3 className="text-xs font-bold text-amber-500 uppercase">Brio (Combate)</h3>
            <span className="text-3xl font-black block mt-1">+3</span>
          </div>
          <div className="bg-teal-950/20 border border-teal-700 p-4 rounded-lg text-center">
            <h3 className="text-xs font-bold text-teal-500 uppercase">Tino (Gastronomia)</h3>
            <span className="text-3xl font-black block mt-1">+2</span>
          </div>
          <div className="bg-zinc-800 border border-zinc-700 p-4 rounded-lg text-center">
            <h3 className="text-xs font-bold text-zinc-400 uppercase">Harmonia</h3>
            <span className="text-3xl font-black block mt-1">4 / 5</span>
          </div>
        </div>

        {/* Distribuição de Dados e Rolagens */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          {/* Seção de Estilos (Atributos Básicos 0-5) */}
          <div className="space-y-4">
            <h2 className="text-xl font-black text-wildorange tracking-wider uppercase border-b border-zinc-800 pb-2">Estilos Básicos</h2>
            {estilos.map((e) => (
              <div key={e.nome} className="flex justify-between items-center bg-wilddark p-3 rounded-lg border border-zinc-800">
                <span className="font-bold text-sm uppercase tracking-wide">{e.nome}</span>
                <div className="flex gap-1.5">
                  {[1, 2, 3, 4, 5].map((circle) => (
                    <div key={circle} className={`w-4 h-4 rounded-full border ${circle <= e.valor ? 'bg-wildorange border-wildorange shadow-sm shadow-wildorange/40' : 'bg-zinc-800 border-zinc-700'}`} />
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Seção das 12 Habilidades Core do Sistema */}
          <div>
            <h2 className="text-xl font-black text-wildorange tracking-wider uppercase border-b border-zinc-800 pb-2 mb-4">Habilidades</h2>
            <div className="grid grid-cols-2 gap-2.5">
              {habilidades.map((hab) => (
                <div key={hab} className="flex justify-between items-center bg-wilddark p-2.5 rounded border border-zinc-800 text-sm">
                  <span className="text-zinc-300 uppercase text-xs tracking-wide">{hab}</span>
                  <span className="font-extrabold text-wildorange bg-wildorange/10 px-2 py-0.5 rounded text-xs">+1</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Automação de Mutações (Recálculo automático ao consumir monstros) */}
        <div className="mt-8 pt-6 border-t border-zinc-800">
          <h2 className="text-xl font-black text-wildorange tracking-wider uppercase mb-4">Traços Ativos (Mutações de Alimentos)</h2>
          <div className="bg-wilddark p-4 rounded-lg border border-zinc-800">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-bold text-white text-base">Garras Retráteis <span className="text-xs text-wildorange font-medium bg-orange-950/40 px-2 py-0.5 rounded ml-2">Origem: Dracofante</span></h4>
                <p className="text-xs text-zinc-400 mt-1">Garante +1 d6 extra em testes do estilo Ligeiro ao atacar em ambientes de mata fechada.</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>
  );
}