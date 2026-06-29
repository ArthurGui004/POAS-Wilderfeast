'use client';
import { useState } from 'react';

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <main className="min-h-screen bg-wilddark flex items-center justify-center p-4">
      <div className="bg-wildcard border-2 border-wildorange/20 p-8 rounded-lg shadow-2xl w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold text-wildorange tracking-wider uppercase font-serif">
            WILDERFEAST
          </h1>
          <p className="text-gray-400 text-sm mt-1">Gerenciador de Automatização Gastronômica</p>
        </div>

        <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
          {!isLogin && (
            <div>
              <label className="text-xs text-gray-400 uppercase font-bold">Nome do Caçador</label>
              <input type="text" className="w-full bg-wilddark text-white p-3 rounded mt-1 border border-zinc-700 focus:border-wildorange outline-none transition-colors" placeholder="Ex: Arthur Vale" />
            </div>
          )}
          <div>
            <label className="text-xs text-gray-400 uppercase font-bold">E-mail</label>
            <input type="email" className="w-full bg-wilddark text-white p-3 rounded mt-1 border border-zinc-700 focus:border-wildorange outline-none transition-colors" placeholder="seu@email.com" />
          </div>
          <div>
            <label className="text-xs text-gray-400 uppercase font-bold">Senha</label>
            <input type="password" className="w-full bg-wilddark text-white p-3 rounded mt-1 border border-zinc-700 focus:border-wildorange outline-none transition-colors" placeholder="••••••••" />
          </div>

          <button className="w-full bg-wildorange text-white font-bold py-3 rounded mt-2 hover:bg-orange-700 transition-colors uppercase tracking-wider text-sm shadow-lg shadow-wildorange/20">
            {isLogin ? 'Sentar à Fogueira (Entrar)' : 'Forjar Registro (Cadastrar)'}
          </button>
        </form>

        <div className="text-center mt-6">
          <span className="text-sm text-gray-500 cursor-pointer hover:text-wildorange transition-colors" onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? 'Novo por aqui? Junte-se à matilha.' : 'Já possui registro? Faça seu login.'}
          </span>
        </div>
      </div>
    </main>
  );
}