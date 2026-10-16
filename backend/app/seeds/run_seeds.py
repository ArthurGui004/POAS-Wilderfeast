"""
Executa todos os seeds na ordem correta.

Pré-requisito: tabelas criadas com `alembic upgrade head`.
Uso (a partir da pasta backend):  python -m app.seeds.run_seeds
Ajuste os imports abaixo se os arquivos estiverem em outro pacote.
"""

import asyncio
import sys

from app.database import engine
from app.seeds.seed_condicao import criar_condicoes_padrao
from app.seeds.seed_estilo import criar_estilos_padrao
from app.seeds.seed_habilidade import criar_habilidades_padrao
from app.seeds.seed_monstro import criar_monstros_padrao
from app.seeds.seed_tracos import criar_tracos_padrao

# Ordem importa: monstros dependem de estilos, habilidades, traços e técnicas.
ETAPAS = [
    ("Estilos", criar_estilos_padrao),
    ("Habilidades", criar_habilidades_padrao),
    ("Condições", criar_condicoes_padrao),
    ("Traços", criar_tracos_padrao),
    # ("Monstros", criar_monstros_padrao),
]


async def main() -> int:
    falhas = []
    try:
        for nome, etapa in ETAPAS:
            print(f"\n=== {nome} ===")
            try:
                erros = await etapa()
                if erros:
                    falhas.append(f"{nome} ({erros} erro(s))")
            except Exception as e:
                falhas.append(f"{nome}: {e}")
                print(f"  ❌ Falha na etapa '{nome}': {e}")
    finally:
        await engine.dispose()

    if falhas:
        print("\n⚠️  Concluído com problemas:")
        for f in falhas:
            print(f"  - {f}")
        return 1

    print("\n✅ Todos os seeds foram aplicados sem erros.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))