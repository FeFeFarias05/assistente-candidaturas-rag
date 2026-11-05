# Linha de base: versão sem RAG (Dia 2)

Modelo: `gpt-5.4-mini`. Material: `data/sample` (fictício, 4 trechos). Prompt: `prompts/analyze.md` (sem ajustes após os testes).
Serve para comparar com a versão RAG no Dia 6 (CA10).

| Vaga | Iscas (ausentes no perfil) | Resultado |
|------|----------------------------|-----------|
| vaga1 (PT, Derevo) | C#, jQuery, gestão administrativa | As 3 foram para **Lacunas**. Nenhuma virou ponto forte. Formação (Eng. de Software vs. SI/CC/TI) tratada como parcial. |
| vaga3 (EN, BairesDev) | "1 ano de React" (perfil: ~6 meses), inglês avançado (perfil: B2) | "1 ano de React" em **Lacunas**, com a diferença explicitada. Rascunho em inglês. |

## Invenções
0 tecnologias, métricas ou empresas inventadas nas 2 vagas.

## Inflações leves (suporte parcial tratado como forte)
- vaga3, "code reviews": o perfil só teve os próprios pull requests revisados; não revisou os de outros.
- vaga3, "English": o perfil tem B2 e a vaga prefere avançado.

## Observações
- As citações são por arquivo/página (`curriculo.pdf#p1`). Com RAG, passam a ser por trecho.
- Todo o material foi enviado à API (modo `--no-rag` só roda com o material fictício, a menos que se use `--yes-send-all`).
