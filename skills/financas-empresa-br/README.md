# financas-empresa-br

Skill própria do Claude Code para finanças e impostos básicos de pequena empresa no Brasil. Autoria: Marcos Bruno Araujo (MB Gestão). Licença Apache 2.0.

## Aviso importante

Este material **não substitui contador**. **Números mudam todo ano: confira a fonte** antes de decidir. Tudo marcado "CONFERIR" não foi verificado em fonte oficial. Dados de referência: pesquisa de 2026-10-28 (ver `fontes.md`).

## Território (exclusivo)

Esta skill é dona de: PF x MEI x Simples Nacional x Lucro Presumido; limites e CNAE do MEI; anexos do Simples e Fator R; pró-labore x distribuição de lucros; carnê-leão (inclui renda de plataformas); NFS-e padrão nacional; reforma tributária (CBS/IBS, ano-teste 2026); fluxo de caixa; DRE simplificada; separação PF/PJ; reserva de imposto; lucro por produto.

Não é dona de (use a skill indicada):
- Preço e pacotes: `pricing`
- Arquivos de planilha: `xlsx`
- Estratégia de crescimento: `strategic-planning`
- Privacidade e documentos jurídicos: `lgpd-br`

## Estrutura

| Arquivo | Conteúdo |
|---|---|
| `SKILL.md` | Fluxo de decisão, reserva de imposto, fechamento mensal, red flags |
| `reference/regimes.md` | Comparação de regimes com números e datas |
| `reference/obrigacoes-2026.md` | Calendário de obrigações, NFS-e, carnê-leão, reforma tributária |
| `reference/rotina-financeira.md` | Caixa, DRE, lucro por produto, separação PF/PJ |
| `fontes.md` | Fontes com URL, tipo e data de acesso; lista do que falta verificar |
| `LICENSE` | Apache 2.0 |

## Instalação

Esta pasta é um rascunho em `skills-proprias`. Não está instalada. Para usar, copie a pasta para `~/.claude/skills/financas-empresa-br/` somente depois de conferir sobreposição com as skills existentes.

## Manutenção

Revisar em janeiro de cada ano (salário mínimo, teto do INSS, tabela do IRPF, DAS-MEI, teto do MEI) e quando sair norma nova (CGSN, LC, Ato Conjunto RFB/CGIBS). Atualizar `fontes.md` com a nova data de acesso.
