# Calendário de obrigações (base: 2026)

Acesso às fontes: 2026-10-28. Códigos [F#] em `../fontes.md`. CONFERIR = verificar o prazo do ano na fonte oficial; datas de 2027 podem ser publicadas depois desta pesquisa.

## 1. Mensais

| Obrigação | Quem | Prazo | Observação |
|---|---|---|---|
| DAS-MEI (PGMEI) | MEI | dia 20 do mês seguinte [F5] | R$ 86,05 para serviços em 2026. Multa 0,33%/dia, teto 20%, mais juros Selic (fonte secundária; CONFERIR) |
| DAS Simples (PGDAS-D) | ME/EPP | dia 20 do mês seguinte (CONFERIR no PGDAS-D) | Apuração mensal com declaração da receita; guarda NFS-e emitidas |
| Carnê-leão | PF que recebe de outra PF ou do exterior [F12] | último dia útil do mês seguinte ao recebimento [F12] | Pelo "Carnê-Leão Web" ou app; DARF (código 0190, CONFERIR). Sem imposto se o redutor zerar o mês (ver abaixo) |
| INSS e IRRF do pró-labore | PJ com sócio | normalmente até dia 20 do mês seguinte (CONFERIR eSocial/DCTFWeb) | Pró-labore mínimo = salário mínimo R$ 1.621 [F10] |
| NFS-e | quem presta serviço | na prestação do serviço | Ver seção 3 |

## 2. Anuais

| Obrigação | Quem | Prazo | Observação |
|---|---|---|---|
| DASN-SIMEI | MEI | até 31 de maio do ano seguinte (declaração de 2026 vence em 2027) [F13]; CONFERIR | Informa receita bruta do ano e se houve empregado |
| DEFIS | ME/EPP no Simples | 31 de março do ano seguinte (CONFERIR) | Substitui DASN para quem não é MEI |
| IRPF (DIRPF) | PF obrigada | período anunciado pela Receita; em geral março a maio (CONFERIR para 2027) | Ano-calendário 2026 aplica o redutor da Lei 15.270/2025 [F11] |
| Opção por regime/semestre IBS/CBS fora do DAS | optantes Simples | 1 a 30 de setembro para vigorar em janeiro; 1 a 31 de março para julho (Res. CGSN 190/2026; fonte secundária, CONFERIR) [F14] | Só relevante a partir de 2027 |
| Opção pelo Simples Nacional | empresas novas / migrantes | janeiro de cada ano, ou até 30 dias após abertura (CONFERIR no Portal do Simples Nacional [F3]) | Fonte secundária mencionou uma janela em setembro de 2026 ligada à reforma; não confirmada, CONFERIR |

## 3. NFS-e padrão nacional

| Fato | Data | Fonte |
|---|---|---|
| MEI que presta serviço a PJ emite NFS-e pelo Padrão Nacional | desde 1/9/2023 (Res. CGSN 169/2022) | [F7] (fonte secundária; CONFERIR) |
| Municípios devem aderir ao Padrão Nacional | desde 1/1/2026 (LC 214/2025); obrigação do contribuinte depende de o município ter migrado | [F7] (secundária; CONFERIR no seu município) |
| ME e EPP do Simples emitem NFS-e pelo Emissor Nacional (web ou API) | 1/11/2026 (Res. CGSN 191/2026, que revogou a Res. 189/2026 que previa 1/9/2026) | [F6] Receita Federal |
| Regras CBS/IBS no documento do Simples | a partir de 1/1/2027 | [F6] |
| Município com sistema próprio | pode manter consulta e emissão retroativa para fatos até 31/10/2026 (exemplo: São Paulo) | [F16] |

Em 2026 o prazo para o Simples é novembro; a ação é cadastrar-se no Emissor Nacional (nfse.gov.br) e emitir as notas por ele a partir de 1/11/2026. DAS continua sendo apurado no PGDAS-D [F6][F16].

Profissional de saúde PF (dentista): desde 1/1/2025 deve emitir o recibo "Receita Saúde" [F12].

## 4. Carnê-leão: regra e plataformas

Regra [F12]: residente que recebe rendimentos de pessoa física ou do exterior deve apurar e recolher o imposto pela tabela progressiva mensal, até o último dia útil do mês seguinte. Pode deduzir livro-caixa (autônomo), dependentes, previdência oficial e pensão. Rendimentos do exterior são convertidos em reais pelas cotações do Banco Central; imposto pago no exterior pode gerar crédito (limitado, e dependente de tratado ou reciprocidade; CONFERIR).

Tabela mensal 2026 e redutor: `regimes.md` seção 4 [F11]. Resumo: renda tributável mensal até R$ 5.000 não paga imposto líquido em 2026, desde que seja a única fonte do mês; com várias fontes, pode haver diferença na declaração anual [F11].

Classificação dos recebimentos do founder (nenhuma confirmada em fonte oficial nesta pesquisa; levar ao contador):

| Origem do dinheiro | Pagador | Tratamento provável | Status |
|---|---|---|---|
| Assinaturas via App Store / Google Play | empresas estrangeiras ou brasileiras do grupo da loja | Se pago do exterior: carnê-leão com conversão pela cotação; se pago por PJ brasileira, pode haver tratamento diferente | CONFERIR |
| Kiwify (produtor) | plataforma PJ brasileira repassa vendas a compradores PF | Muitos contadores tratam como rendimento de PF sujeito a carnê-leão; outros como rendimento recebido de PJ na declaração anual | CONFERIR |
| Monetização de redes sociais (AdSense, bônus, publi) | PJ brasileira ou exterior | Depende do pagador (retenção na fonte versus exterior) | CONFERIR |
| Serviço a empresa brasileira | PJ | Retenção na fonte pela empresa (tabela IRRF); declarar na DIRPF | CONFERIR |
| Atendimento odontológico a pacientes PF | PF | Carnê-leão + Receita Saúde [F12] | Regra geral confirmada |

Recomendação operacional: registrar cada recebimento com data, pagador, país, valor em moeda original e em reais, e guardar comprovante. Isso serve para qualquer das hipóteses.

## 5. Reforma tributária (LC 214/2025) em 2026

| Tema | Fato | Fonte |
|---|---|---|
| Alíquotas-teste 2026 | CBS 0,9% e IBS 0,1% nos documentos fiscais | [F15] Receita Federal / consulta da Fazenda SP |
| Cobrança em 2026 | contribuintes que cumprem as obrigações acessórias ficam dispensados do recolhimento (art. 348, §1º, LC 214/2025); valor eventualmente pago compensa PIS/Cofins | [F15] |
| Campos IBS/CBS em NF-e, NFC-e, NFS-e (regime regular) | preenchimento obrigatório a partir de 3/8/2026 | [F17] CGIBS |
| Optantes do Simples/MEI em 2026 | sem mudança de recolhimento; destaque de IBS/CBS e regras próprias só a partir de 1/1/2027 | [F6][F15] |
| CBS plena e fim de PIS/Cofins | 2027 | fonte secundária [F14]; CONFERIR |
| Redução gradual de ICMS/ISS e extinção | 2029 a 2032 (redução), 1/1/2033 (extinção) | fonte secundária [F14]; CONFERIR |
| Resoluções CGSN de transição | 190/2026 (IBS/CBS no DAS), 191/2026 (NFS-e), 192/2026 (CGIBS no fluxo de arrecadação) | [F14] secundária; CONFERIR texto no DOU |

O que fazer em 2026 (ME/EPP no Simples): (1) emitir NFS-e pelo Emissor Nacional desde 1/11/2026; (2) manter o contador informado para ajustes do ERP; (3) não recolher guia nova de CBS/IBS; (4) em 2027, decidir com o contador se opta por recolher IBS/CBS fora do DAS.

## 6. MEI em 2027 (LC 238/2026)

- Teto: R$ 110.000 em 2027 e R$ 140.000 em 2028 [F2].
- Até 2 empregados [F2].
- Perdão de dívidas federais até 13/10/2026 com condições [F2].
- Antes de qualquer decisão de enquadramento para 2027, ler o texto da lei (número e prazos de adaptação do PGMEI: CONFERIR).
