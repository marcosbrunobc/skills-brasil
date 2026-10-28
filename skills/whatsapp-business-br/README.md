# whatsapp-business-br

Skill do Claude Code para escrever e desenhar mensagens e robôs de WhatsApp Business que passam nas políticas da Meta e funcionam para o público brasileiro, usando só a API oficial (WhatsApp Business Cloud API).

## Território
Este skill cuida de:
- modelos de mensagem (marketing, utility, autenticação), variáveis, botões, pegadinhas de aprovação;
- janela de atendimento de 24 horas;
- redação de opt-in e opt-out;
- desenho de fluxos de conversa (classificar, rotear, ferramentas, aprovação humana, checagem de qualidade) e passagem para humano;
- tom em pt-BR e cuidado com dados de saúde (LGPD) nas mensagens;
- noção do modelo de preço por mensagem.

Não cuida de:
- configurar conta, número, verificação, token ou webhook: MCP `whatsapp_business_tools`;
- DMs do Instagram: `ig-dm`;
- sequências de e-mail: `emails`;
- prospecção fria por e-mail ou LinkedIn: `outreach-specialist`;
- textos de site e página de vendas: `copywriting`.

## Arquivos
- `SKILL.md`: instruções principais, fluxos e checklist.
- `reference/modelos.md`: regras de modelos e 10 exemplos.
- `reference/politicas.md`: janela, opt-in, conteúdo proibido, qualidade, preço.
- `reference/fluxos.md`: padrões de fluxo e passagem para humano.
- `fontes.md`: fontes oficiais com data de acesso e lista do que não foi verificado.

## Avisos
- Não substitui as políticas oficiais da Meta nem aconselhamento jurídico. As regras e os preços mudam; confira as fontes.
- Valores em reais: sempre "conferir preço atual" na tabela oficial.
- Não instala nada e não configura conta.

## Licença
Apache 2.0. Copyright 2026 Marcos Bruno Araujo (MB Gestão).
