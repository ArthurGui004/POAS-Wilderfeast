import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Wilderfeast | Automação',
  description: 'Sistema de Automação para o RPG Gastronômico Wilderfeast',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="bg-wilddark text-zinc-100 min-h-screen flex flex-col">
        {/* Aqui você poderia adicionar um Header global no futuro, se quiser */}
        <main className="flex-grow">
          {children}
        </main>
      </body>
    </html>
  );
}