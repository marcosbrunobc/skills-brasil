---
name: financas-empresa-br
description: Brazilian small-business finance and tax basics for a founder moving from pessoa física to a CNPJ - PF vs MEI vs Simples Nacional vs Lucro Presumido, MEI limits and CNAE fit, Simples annexes and Fator R, pró-labore vs distribuição de lucros, carnê-leão, NFS-e padrão nacional, reforma tributária (CBS/IBS), cash flow, simplified DRE, PF/PJ separation, tax reserve and unit economics per product. Triggers - "MEI ou Simples", "quanto de imposto", "abrir CNPJ", "nota fiscal", "pró-labore", "carnê-leão", "fluxo de caixa", "DRE", "reserva de imposto", "reforma tributária", "lucro por produto". Not for pricing or packaging strategy - use pricing. Not for building spreadsheet files - use xlsx. Not for growth strategy - use strategic-planning. Not for privacy or legal documents (LGPD, terms) - use lgpd-br.
---

# Finanças de pequena empresa no Brasil

Escopo: dinheiro e imposto básicos de quem fatura como PF e vai abrir PJ. Não substitui contador. Números mudam todo ano: antes de afirmar qualquer valor, confira a data em `reference/` e a fonte em `fontes.md`. Tudo marcado CONFERIR não foi verificado.

## Regras de conduta

1. Nunca afirmar número de imposto sem data e fonte. Se o dado não está em `reference/`, dizer "CONFERIR" e indicar onde conferir.
2. Dar o cálculo com premissas explícitas, não só o resultado.
3. Perguntar o que falta (atividade/CNAE, faturamento 12 meses, quem paga, folha) antes de recomendar regime.
4. Responder em pt-BR, curto, com o próximo passo prático.
5. Em caso de red flag (seção abaixo), recomendar contador e parar de simular.

## Fluxo de decisão: PF -> MEI -> Simples

Colete: (a) atividade real e CNAE candidato; (b) faturamento dos últimos 12 meses e projeção; (c) quem paga (consumidor PF, empresa PJ, plataforma estrangeira); (d) quer sócio ou funcionário?; (e) despesas dedutíveis relevantes.

1. **Continuar PF** serve enquanto: renda baixa, sem cliente PJ exigindo nota, sem risco de ultrapassar a faixa do carnê-leão. Custo: tabela progressiva do IRPF (`reference/regimes.md`), sem nota fiscal própria, patrimônio misturado.
2. **MEI** só se TODAS as checagens passarem:
   - Faturamento anual <= teto vigente (2026: R$ 81.000; muda em 2027, ver regimes.md).
   - Ocupação consta no Anexo XI da Resolução CGSN 140/2018 (conferir CNAE no gov.br). Consultoria, desenvolvimento de software, agência, gestão de tráfego e social media geralmente NÃO constam: CONFERIR o CNAE exato.
   - Sem sócio, sem outra empresa em nome do titular, um estabelecimento.
   - Aceita limite de empregados (1 em 2026; 2 a partir de 2027 pela LC 238/2026).
   Se falhar em qualquer uma: ir para ME no Simples.
3. **ME no Simples Nacional**: padrão para serviços até R$ 360 mil (ME) / R$ 4,8 milhões (EPP). Passos: escolher CNAE, descobrir anexo (III ou V), calcular Fator R, definir pró-labore, emitir NFS-e pelo Emissor Nacional.
4. **Lucro Presumido**: só considerar se a conta mostrar carga menor que o Simples (margem alta, folha baixa, faturamento perto do teto) ou se exigência de cliente/atividade. Pedir simulação ao contador.

Detalhes e números: `reference/regimes.md`.

## Simples: anexo e Fator R

- Fator R = folha dos 12 meses (salários + pró-labore + encargos + FGTS) / receita bruta dos 12 meses. >= 28% leva atividades do art. 18 §5º-M ao Anexo III; abaixo disso, Anexo V (alíquota inicial bem maior).
- Pró-labore maior reduz imposto do DAS, mas aumenta INSS e IRRF. Compare o custo total, não só o DAS.
- Conferir no CNAE se a atividade realmente está sujeita ao Fator R (CONFERIR).

## Pró-labore x distribuição de lucros

- Sócio que trabalha na empresa deve receber pró-labore (mínimo: salário mínimo, R$ 1.621 em 2026). INSS do sócio: 11% sobre o pró-labore até o teto (R$ 8.475,55 em 2026). IRRF pela tabela mensal.
- Lucro contábil apurado (DRE correta) pode ser distribuído ao sócio, em regra isento de IRPF; a Lei 15.270/2025 criou retenção de 10% sobre dividendos acima de R$ 50 mil/mês de uma mesma empresa (início: CONFERIR).
- Nunca retirar dinheiro "do caixa" sem classificar como pró-labore, distribuição ou reembolso.

## Reserva de imposto (como calcular)

Passo a passo sobre o faturamento bruto do mês:
1. Regime e alíquota efetiva: MEI = valor fixo do DAS (R$ 86,05 serviços em 2026, fora a obrigação anual); Simples = alíquota efetiva = (RBT12 x alíquota nominal - parcela a deduzir) / RBT12; PF = IRPF estimado pela tabela do mês.
2. Somar INSS do pró-labore e IRRF se houver.
3. Reserva = faturamento x alíquota efetiva + encargos do pró-labore + 10% de folga para a primeira vez.
4. Guardar a reserva em conta separada no dia em que o dinheiro entra.
Premissas obrigatórias na resposta: regime, anexo, RBT12, Fator R, data da tabela. Exemplo e modelo: `reference/rotina-financeira.md`.

Sem regime definido (ainda PF): reserva provisória = rendimento tributável do mês passado pela tabela progressiva mensal 2026 + 10%. Para app stores e plataformas estrangeiras, ver carnê-leão em `reference/obrigacoes-2026.md`.

## Rotina de fechamento mensal (30 min)

1. Exportar entradas de cada frente (lojas de apps, Kiwify, redes, serviços, clínica) e conciliar com o extrato.
2. Classificar: receita bruta, taxas de plataforma, impostos, custos diretos, despesas fixas.
3. Gerar DRE simplificada e lucro por produto (modelo em `rotina-financeira.md`).
4. Apurar e pagar: DAS/DARF do carnê-leão (prazos: último dia útil / dia 20, ver calendário).
5. Transferir reserva de imposto e pró-labore; só o excedente fica livre.
6. Registrar pendências: nota não emitida, recibo faltando, pagamento atrasado.

## Red flags: chamar contador

- Faturamento perto de 80% do teto do regime, ou crescimento brusco.
- Dúvida de CNAE/anexo, ou atividade mista (produto digital + serviço + clínica).
- Receita do exterior volumosa, ou cliente PJ estrangeiro (câmbio, IOF, tratado).
- Funcionário, sócio novo, ou mudança de regime no meio do ano.
- Notificação da Receita, malha fina, dívida ativa, DAS em atraso.
- Venda de produto físico, importação ou licenciamento de marca.
- Atividade de saúde (clínica odontológica): regras próprias, Receita Saúde, ISS e CNAE específicos.
- Qualquer decisão acima de R$ 10 mil de efeito tributário.

## Reforma tributária (resumo)

2026 é ano-teste: CBS 0,9% e IBS 0,1% nos documentos fiscais, com dispensa de recolhimento para quem cumpre as obrigações acessórias. Optantes do Simples só aplicam as regras CBS/IBS a partir de 1/1/2027. Detalhes e calendário em `reference/obrigacoes-2026.md`. Em 2026 a ação real para ME/EPP no Simples é emitir NFS-e pelo Emissor Nacional a partir de 1/11/2026.
