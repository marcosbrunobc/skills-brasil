# Fontes (acesso em 2026-10-28)

Todas consultadas em 28/10/2026. As páginas da Meta mudam sem aviso: reconfira antes de afirmar algo a um cliente. Páginas em `developers.facebook.com/docs/...` redirecionam para `developers.facebook.com/documentation/business-messaging/whatsapp/...`.

## Oficiais (Meta / WhatsApp)
| Assunto | URL | Fatos usados |
|---|---|---|
| Visão geral de modelos | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/overview | 3 categorias; modelos são o único tipo fora da janela; parâmetros nomeados/posicionais; 100 modelos/hora; 250 modelos (portfólio não verificado) ou até 6.000 (verificado); arquivamento após 12 meses de inatividade |
| Categorização | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-categorization.md | definições; reclassificação (aviso de 1 dia, 60 dias para contestar); padrão desde 9/abr/2025; níveis de restrição por má classificação |
| Revisão e rejeição | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-review.md | motivos de rejeição; revisão até 24h; sem variável no início/fim; duplicados |
| Componentes e limites | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/components.md | cabeçalho 60, corpo 1.024, rodapé 60, botões 25; contagem de botões; agrupamento de respostas rápidas |
| Modelos utility | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/utility-templates/utility-templates/ | utility sem material de marketing; limites repetidos |
| Qualidade do modelo | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-quality.md | verde/amarelo/vermelho/desconhecido |
| Pausa de modelos | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-pausing.md | 3h, 6h, desativado |
| Limite por usuário (marketing) | https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/marketing-templates/per-user-limits.md | erro 131049; esperar 24h |
| Limites de mensagens | https://developers.facebook.com/documentation/business-messaging/whatsapp/messaging-limits.md | níveis 250, 2.000, 10 mil, 100 mil, ilimitado; portfólio; caminho para 2.000 |
| Enviar mensagens e janela de 24h | https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages | janela de atendimento, tipos de mensagem, modelos fora da janela, TTL |
| Opt-in | https://developers.facebook.com/documentation/business-messaging/whatsapp/getting-opt-in.md | o que o opt-in deve informar; métodos; boas práticas; opt-out |
| Aplicação de políticas | https://developers.facebook.com/documentation/business-messaging/whatsapp/policy-enforcement.md | aviso, bloqueios, trava, desativação; feedback negativo |
| Política de mensagens do WhatsApp Business | https://whatsappbusiness.com/pt-br/policy/ (antigo https://business.whatsapp.com/policy) | opt-in, categorias restritas (medicamentos, produtos de saúde), OTC no Brasil, dados sensíveis, automação com escalonamento humano, opt-out |
| Commerce Policy | https://www.facebook.com/policies_center/commerce | citada pela política e pela revisão de modelos; conteúdo não lido na íntegra |
| Termos da plataforma WhatsApp Business | https://www.facebook.com/legal/Meta-Terms-for-WhatsApp-Business-Platform | §4.7 provedores de IA de uso geral; §4.2 não é HIPAA, não prometem setores regulados |
| Preços | https://developers.facebook.com/docs/whatsapp/pricing | cobrança por mensagem desde 1/jul/2025; categorias; datas de out/2026; Brasil e BRL |
| Mensagens sem modelo (preço) | https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/non-template-messages.md | service cobrado a partir de 1/out/2026; utility em janela cobrada a partir de 1/out/2026 |
| Tabela de preços | https://business.whatsapp.com/products/platform-pricing#rates | valores por mercado (não lidos: conferir preço atual) |
| Índice da documentação | https://developers.facebook.com/documentation/business-messaging/whatsapp/llms.txt | lista de páginas |

## Legislação brasileira
| Assunto | URL | Fatos usados |
|---|---|---|
| LGPD (Lei 13.709/2018) | https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm | art. 5º II, 6º, 7º, 11, 18 (lidos; trecho final da página não lido) |

## Secundárias (não oficiais; só contexto, não usadas como regra)
- Cobertura de imprensa sobre a proibição de IA de uso geral em 15/jan/2026 (resultado de busca; confirmado depois nos termos oficiais, §4.7): https://respond.io/blog/whatsapp-chatbot-policy-2026
- Guias de fornecedores sobre LGPD e lembretes de consulta (ex.: https://confidata.com.br/blog/lgpd-clinicas-medicas-guia-adequacao-2026): usados só para a prática de minimização; sem valor normativo.

## Não verificado / a confirmar
1. Código de erro de envio fora da janela (131047 comum, não visto nas páginas lidas).
2. Franquia gratuita de 1.000 mensagens de service por mês: citada na página de preços, ausente na página de mensagens sem modelo.
3. Valores em R$ por categoria: não coletados; sempre "conferir preço atual".
4. Rodapé aceita variáveis? Página de componentes diz que não; página utility diz que sim. Tratado como não.
5. Regra oficial de formato de emoji e limite de variáveis por tamanho de texto: Meta não dá número.
6. Orientação oficial da ANPD sobre lembretes de consulta por WhatsApp: não encontrada.
7. Regra legal brasileira de horário para mensagens comerciais por WhatsApp: não verificada.
8. Texto vigente do código de ética odontológico após CFO-271/2025 (preço, desconto): não lido aqui.
9. Meta Business Agent: preço e escopo só pela página de preços; não aprofundado.
10. Commerce Policy e Integrity and content guidelines lidos apenas via resumo da política de mensagens.
