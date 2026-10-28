---
name: whatsapp-business-br
description: 'Write and design WhatsApp Business messages and bot flows that pass Meta policy and work for Brazilian users on the official Cloud API: templates (marketing, utility, authentication; variables, buttons, rejections, re-categorization), the 24-hour window, opt-in and opt-out wording, bot flows (classify, route, tools, human approval, quality check), handoff to a human, pt-BR tone, LGPD-aware wording for health data, and per-message pricing. Triggers: "mensagem de WhatsApp", "modelo de mensagem", "template do WhatsApp", "robô de WhatsApp", "lembrete de consulta no WhatsApp", "fluxo do atendimento", "janela de 24 horas", "template rejeitado". Not for account setup, numbers, tokens or webhooks: use the whatsapp_business_tools MCP. Not for Instagram DMs: use ig-dm. Not for email sequences: use emails. Not for cold outreach: use outreach-specialist. Not for web or sales-page copy: use copywriting.'
---

# WhatsApp Business BR

Só API oficial (WhatsApp Business Cloud API). Nunca sugerir robô por QR code ou API não oficial: risco de banimento.
Este skill escreve e desenha mensagens e fluxos. Conta, número, verificação, token e webhook são do MCP `whatsapp_business_tools`.
Não substitui as políticas oficiais da Meta. Regras mudam: confira `fontes.md` e as páginas oficiais antes de afirmar algo ao cliente.

## Quando ler cada referência
- Escrever/revisar modelo: `reference/modelos.md`
- Janela de 24h, opt-in, conteúdo proibido, qualidade, preço: `reference/politicas.md`
- Desenhar robô, handoff: `reference/fluxos.md`

## Fluxo para escrever um modelo (template)
1. **Gatilho e destinatário.** Quem recebe, por que agora, o que ele fez antes (agendou, comprou, pediu)? Sem ação prévia do usuário, quase sempre é marketing.
2. **Categoria.**
   - Utility: segue ação ou pedido do usuário, sem tom promocional (confirmação, lembrete de consulta já marcada, status de pedido, link de pagamento solicitado).
   - Marketing: promoção, novidade, reativação, aniversário com oferta, pesquisa genérica. Dúvida entre os dois: tratar como marketing.
   - Authentication: só código de uso único.
   - Meta pode reclassificar utility para marketing (mais caro). Não force utility.
3. **Rascunho em pt-BR.** Curto, uma ideia, nome da clínica/empresa na primeira linha útil, um chamado claro. Tom: `reference/modelos.md` seção Tom.
4. **Variáveis.** Nomeadas (`{{nome_paciente}}`) ou numeradas sequenciais; exemplo realista para cada uma; não começar nem terminar o corpo com variável; não abusar de variáveis em texto curto; sem `#`, `$`, `%` dentro da variável.
5. **Botões.** Resposta rápida para confirmar/remarcar/parar; URL para pagamento ou site; telefone se preciso. Marketing: incluir opção de parar de receber.
6. **Checagem de política** (checklist abaixo). Se dados de saúde: aplicar LGPD, nada de diagnóstico, procedimento ou valor clínico na mensagem.
7. **Enviar para aprovação** via MCP (`whatsapp_biz_create_template`, ou `whatsapp_biz_template_library` para modelos prontos da Meta). Nome em minúsculas com underscores, idioma `pt_BR`. Mostrar o JSON ao dono antes de submeter.
8. **Depois.** Acompanhar status, reclassificação (aviso por webhook/e-mail) e qualidade. Pausado ou qualidade baixa: reescrever, não reenviar igual.

## Fluxo para desenhar um robô (grafo)
Método completo e diagramas em `reference/fluxos.md`. Resumo:
```
mensagem -> classificar intenção -> rotear -> ferramentas (agenda, FAQ, status)
         -> [aprovação humana se sensível] -> checagem de qualidade -> resposta
```
1. Listar intenções reais (agendar, remarcar, preço, dúvida clínica, reclamação, pagamento, outra).
2. Para cada intenção: resposta automática, ferramenta, ou humano.
3. **Sempre humano (com aprovação antes de enviar):** reembolso, desconto/preço fora da tabela, reclamação, qualquer pergunta clínica (dor, sintoma, medicamento, resultado de exame), urgência, assunto jurídico, menor de idade, pedido de dados pessoais.
4. Checkpoint de qualidade antes de enviar: tom, promessa indevida, dado sensível, janela aberta?
5. Saída para humano visível em todo fluxo (a política exige caminho claro de escalonamento).
6. Dentro da janela de 24h: texto livre, botões, listas. Fora: só modelo aprovado.
7. Falha do robô (2 mal-entendidos seguidos, usuário irritado, "atendente"): passar para humano com resumo.

## Checklist antes de entregar
- [ ] Usuário deu opt-in para esta categoria? Existe como parar (palavra "SAIR" ou botão)?
- [ ] Categoria honesta (utility sem oferta embutida)?
- [ ] Variáveis: sequenciais, com exemplos, sem início/fim em variável?
- [ ] Limites: corpo até 1.024, cabeçalho até 60, rodapé até 60, rótulo de botão até 25 caracteres (conferir em `fontes.md`).
- [ ] Sem dado de saúde sensível, CPF completo, cartão, senha, diagnóstico, nome de procedimento em lembrete?
- [ ] Sem venda/promoção de medicamento, suplemento "milagroso", antes-e-depois com promessa de resultado, ameaça, vergonha pública, linguagem alarmista?
- [ ] Sem texto que dependa de preço/desconto sem checar a regra de publicidade do conselho profissional (CFO, CFM etc.): conferir texto vigente.
- [ ] pt-BR com acentos, tratamento coerente (você), horário comercial respeitado para marketing.
- [ ] Caminho para humano indicado.
- [ ] Preço: informar custo por mensagem como "conferir preço atual" (tabela oficial em BRL).
- [ ] Reler a categoria no fim: virou marketing? Então só envie a quem aceitou marketing.

## Regras de honestidade
- Nunca inventar número de política ou preço. Valor em R$: "conferir preço atual na tabela da Meta".
- Item não confirmado em fonte oficial: marcar "a confirmar".
- Se cliente pedir algo que viola política (vender remédio, enviar resultado de exame por modelo, disparar para lista comprada): recusar, explicar o risco (bloqueio da conta, LGPD) e oferecer alternativa (convite com opt-in, link para portal seguro).
