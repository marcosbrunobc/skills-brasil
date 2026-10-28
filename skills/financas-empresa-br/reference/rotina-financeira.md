# Rotina financeira: caixa, DRE, lucro por produto, separação PF/PJ

Os exemplos usam números ilustrativos, marcados como tal. Alíquotas e tabelas vêm de `regimes.md` (fontes em `../fontes.md`). Taxas de plataformas (Apple, Google, Kiwify, afiliados) mudam: CONFERIR nas páginas oficiais de cada uma antes de usar.

## 1. Separar PF e PJ

Regra única: dinheiro da empresa só vira dinheiro pessoal por três portas, todas registradas.

| Porta | O que é | Registro |
|---|---|---|
| Pró-labore | salário do sócio que trabalha | folha, INSS e IRRF |
| Distribuição de lucros | lucro apurado em DRE | ata/registro e DRE do período |
| Reembolso | despesa da empresa paga do bolso | nota/recibo no CNPJ |

Estrutura mínima de contas (PJ):
1. Conta de recebimento (entrada de lojas, Kiwify, clientes).
2. Conta/CDB de reserva de imposto (nunca gastar daqui).
3. Conta de operação (custos, ferramentas, anúncios).
4. Conta de pró-labore/lucro para transferências ao sócio.

Antes do CNPJ (ainda PF): manter mesmo assim uma conta separada só para a atividade e uma subconta de reserva. Isso facilita carnê-leão, livro-caixa e a migração.

Proibido: pagar cartão pessoal com a conta PJ; receber de cliente PJ na conta pessoal quando o contrato é da empresa; misturar assinatura de ferramenta pessoal e profissional.

## 2. Fluxo de caixa

Duas visões, ambas simples:

**Realizado (mensal):** saldo inicial + entradas pagas - saídas pagas = saldo final. Só movimentação real do extrato.

**Projetado (13 semanas):** coluna por semana, linhas:
1. Saldo inicial
2. Entradas previstas (por frente: apps, Kiwify, serviços, clínica), com data real de repasse da plataforma, não data da venda
3. Saídas fixas (ferramentas, contador, DAS, pró-labore, INSS)
4. Saídas variáveis (anúncios, comissões, freelancers)
5. Saldo final e colchão mínimo

Colchão sugerido (premissa, ajustável): 3 meses de saídas fixas. Alerta: saldo projetado menor que 1 mês de saídas fixas em qualquer semana.

Cuidado com o repasse: venda no dia 5 pode cair no dia 35 (Kiwify e lojas têm prazos próprios; CONFERIR). O imposto geralmente é devido por competência/recebimento conforme o regime: MEI e Simples (regime de caixa ou competência, CONFERIR a opção do PGDAS-D) e carnê-leão (data do recebimento).

## 3. DRE simplificada (modelo mensal)

| Linha | Cálculo |
|---|---|
| (+) Receita bruta | soma das vendas/serviços do mês, antes de taxas |
| (-) Devoluções e reembolsos | chargebacks, estornos, garantia Kiwify |
| (=) Receita líquida de devoluções | |
| (-) Impostos sobre receita | DAS (Simples) ou alocação da reserva |
| (-) Taxas de plataforma | lojas de apps, Kiwify, gateway |
| (=) Receita líquida | |
| (-) Custos diretos | infra, API de IA, anúncios do produto, comissão de afiliado, suporte |
| (=) Margem de contribuição | |
| (-) Despesas fixas | contador, ferramentas, aluguel, internet |
| (-) Pró-labore + encargos | se sócio trabalha |
| (=) Resultado operacional | |
| (-) Reserva extra de IR (se Lucro Presumido) | |
| (=) Lucro distribuível | só o que está em caixa e sobra após reserva |

Pontos de cuidado:
- Receita bruta é o que o cliente pagou, mesmo que a plataforma retenha parte. Isso é o que entra no limite do MEI/Simples (conferir com contador como tratar taxas de marketplace; CONFERIR).
- Lucro contábil não é saldo bancário. Só distribuir lucro que existe no DRE e em caixa.
- Pró-labore entra como despesa, distribuição não.

## 4. Lucro por produto (unit economics)

Para cada produto/app/página/serviço:

1. Receita bruta do produto
2. (-) Taxa da plataforma do produto
3. (-) Imposto alocado: alíquota efetiva do regime x receita do produto
4. (-) Custos diretos do produto
5. (=) Margem de contribuição do produto
6. (-) Rateio de fixos (por receita ou por esforço; escolher uma regra e manter)
7. (=) Lucro do produto

Métricas por tipo:

| Tipo | Métricas | Fórmulas |
|---|---|---|
| App por assinatura | ARPU, churn, LTV, CAC | LTV = ARPU mensal x margem de contribuição % / churn mensal; payback = CAC / (ARPU x margem) |
| Infoproduto (Kiwify) | ticket líquido, taxa de reembolso, CAC por venda | ticket líquido = preço - taxa - afiliado - imposto |
| Serviço/agência | margem por projeto, horas, receita por hora | margem = preço - custo direto (horas x custo/hora + ferramentas) |
| Rede social | RPM, receita por post/vídeo, custo de produção | receita por conteúdo / custo de produção |
| Clínica | margem por procedimento | preço - material - laboratório - hora clínica |

Exemplo ilustrativo (números inventados): app com R$ 5.000 de assinaturas no mês.
- Taxa da loja: 15% (premissa; CONFERIR o programa vigente) = R$ 750
- Imposto alocado: 6% de R$ 5.000 = R$ 300
- Custos diretos (servidor + IA): R$ 400
- Margem de contribuição: 5.000 - 750 - 300 - 400 = R$ 3.550 (71%)
Se o rateio de fixos for R$ 800, lucro do produto = R$ 2.750.

Decisão que a conta suporta: parar, manter ou investir. Produto com margem de contribuição negativa por 3 meses sem tendência de melhora: parar ou repensar preço (a estratégia de preço é do skill `pricing`).

## 5. Reserva de imposto: modelo e exemplo

Fórmula: reserva do mês = receita bruta x alíquota efetiva + INSS e IRRF do pró-labore + folga de 10%.

Exemplo ilustrativo, ME no Simples, serviços, RBT12 = R$ 120.000, receita do mês R$ 10.000:

| Cenário | Pró-labore | Fator R | Anexo | Alíquota efetiva (RBT12 <= 180k) | DAS do mês |
|---|---|---|---|---|---|
| A | R$ 1.621 (mínimo) | 12 x 1.621 / 120.000 = 16,2% | V | 15,5% | R$ 1.550 |
| B | R$ 2.800 | 12 x 2.800 / 120.000 = 28,0% | III | 6,0% | R$ 600 |

Cenário B (premissas): atividade sujeita ao Fator R; sócio sem outra renda; INSS do sócio 11% e IRRF zerado pelo redutor da Lei 15.270 (2.800 - 308 de INSS = 2.492 de base; 7,5% x 2.492 - 182,16 = R$ 4,74, menos que o redutor de R$ 312,89, logo imposto retido R$ 0). Sem folha de funcionários além do sócio.
- INSS A: 11% x 1.621 = R$ 178,31. INSS B: 11% x 2.800 = R$ 308,00. Diferença R$ 129,69.
- Economia de DAS no cenário B: 1.550 - 600 = R$ 950.
- Ganho líquido aproximado: 950 - 129,69 = R$ 820,31 por mês. Os R$ 1.179 a mais de pró-labore saem da empresa mas chegam ao sócio; sem eles seriam lucro distribuível, então o efeito para o sócio é só o INSS extra (e o menor DAS).

Essa conta só vale se a atividade estiver sujeita ao Fator R e se a RBT12 se mantiver em torno de R$ 120.000. Reavalie todo mês: o Fator R usa janela de 12 meses móvel. Confirme com o contador.

Reserva final no cenário B: 600 (DAS) + 308 (INSS) + 0 (IRRF) = R$ 908; com folga de 10%: ~R$ 999. Guardar na conta de reserva no dia da entrada do dinheiro.

Para MEI: reserva = DAS fixo (R$ 86,05 em serviços, 2026) + 6% a 10% do faturamento como folga para o dia em que virar ME (a diferença de imposto retroativo pode pegar de surpresa).

Para PF (carnê-leão): reserva provisória = imposto estimado pela tabela progressiva do mês sobre a renda tributável (após livro-caixa) + 10%. Em 2026 o imposto líquido é zero até R$ 5.000/mês de renda, se for a única fonte (ver `regimes.md` seção 4).

## 6. Fechamento mensal (checklist)

- [ ] Extratos de todas as contas e plataformas exportados
- [ ] Entradas conciliadas por frente e por produto
- [ ] Notas emitidas para todo serviço (NFS-e pelo Emissor Nacional)
- [ ] DAS/DARF calculados e pagos até o prazo
- [ ] Reserva de imposto transferida
- [ ] Pró-labore pago e INSS/IRRF recolhidos
- [ ] DRE do mês e lucro por produto atualizados
- [ ] Lucro distribuído só se DRE positiva e caixa suficiente
- [ ] Pendências anotadas (nota faltando, recibo, comprovante de câmbio)
