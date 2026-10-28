# Políticas, janela, opt-in, qualidade e preço

Resumo com palavras próprias a partir das páginas listadas em `../fontes.md` (acesso 28/10/2026). Não substitui as políticas oficiais da Meta. Itens "a confirmar" não foram verificados em fonte oficial.

## Janela de atendimento de 24 horas
- Abre quando o usuário envia mensagem ou liga para o negócio. Cada nova mensagem ou ligação do usuário reinicia as 24h.
- Dentro: mensagens livres (texto, imagem, documento, botões de resposta até 3, listas, Flows, CTA de URL). Sem aprovação prévia.
- Fora: só modelos aprovados.
- Opt-in vale dentro e fora da janela.
- Mensagem do negócio não prorroga a janela; só a do usuário.
- Prática: se o fluxo precisa de resposta tardia, envie antes um modelo com botão de resposta rápida.
- Código de erro de envio fora da janela: a confirmar na referência da Messages API (comumente 131047; não confirmado nas páginas lidas).

## Opt-in
- Obrigatório antes de enviar. Deve dizer: que a pessoa aceita receber mensagens do negócio, o nome do negócio, e conformidade com a lei aplicável.
- Métodos citados pela Meta: SMS, site, telefone (URA), presencial ou papel. O negócio escolhe.
- Boas práticas oficiais: opt-in separado por categoria (avisos de consulta x promoções), explicar o valor, fluxo simples.
- Brasil: a página da Meta não traz regra específica; vale a LGPD. Número informado para cuidar da consulta não é, por si, aceite para marketing.
- Texto de opt-in sugerido (ficha, site, recepção): `Autorizo a [Nome da clínica] a me enviar mensagens por WhatsApp sobre meus agendamentos e atendimento. Para receber também novidades e ofertas, marque esta opção: [ ]. Posso parar a qualquer momento enviando SAIR.`
- Guardar prova do opt-in: data, texto exibido, canal.

## Opt-out
- Respeitar qualquer pedido de parar, por qualquer canal, e retirar da lista. Instruções de saída claras.
- Palavras de saída para o robô tratar: sair, parar, cancelar, stop, "não quero receber". Confirmar uma vez e não enviar mais marketing.
- Parar marketing não impede avisos de agendamento, se o paciente aceitou essa categoria. Pergunte qual categoria ele quer parar.

## Conteúdo proibido ou restrito (política de mensagens)
- Restritos: armas, álcool e tabaco, medicamentos (prescrição ou outros), produtos médicos e de saúde, criptomoeda, apostas, produtos adultos, namoro, marketing multinível, certos empréstimos.
- Medicamento isento de prescrição: permitido só em países listados (Brasil consta), conforme a lei local, sem direcionar a menores de 18. Prescrição: não.
- Proibido: golpe, spam, mensagens enganosas ou surpreendentes, ameaças, discriminação, conteúdo sexual, dados sensíveis (cartão completo, número de documento), compartilhar a conversa de um cliente com outro.
- Saúde: não usar WhatsApp para telemedicina nem para enviar ou pedir dados de saúde onde a lei proíbe enviá-los a sistemas sem o padrão exigido. A Meta declara que a plataforma não é compatível com HIPAA e não garante atender setores altamente regulados. Consulte jurídico (LGPD, CFO, CFM) para o caso concreto.
- IA: o negócio pode usar IA no atendimento próprio (FAQ, agendamento, status). Provedores de assistentes de IA de uso geral são proibidos de usar a plataforma (termos, §4.7). Dados da plataforma não podem treinar modelos de IA. Automação exige caminho claro para atendente humano.

## LGPD e saúde (resumo, não é parecer jurídico)
- Dado de saúde é dado pessoal sensível (LGPD art. 5º, II). O tratamento exige base do art. 11: consentimento específico e destacado, ou hipóteses como tutela da saúde em procedimento feito por profissional ou serviço de saúde.
- Princípios do art. 6º: finalidade, necessidade (mínimo), segurança.
- Prática nas mensagens: mínimo necessário. Lembrete = nome, data, hora, local. Sem especialidade, procedimento, diagnóstico ou resultado.
- Mensagem ao número errado pode ser incidente com dado sensível. Confirme o número no cadastro; no robô, confirme identidade (nome e parte da data de nascimento) antes de falar de agendamento específico.
- Direitos do titular (art. 18): acesso, correção, eliminação, revogação do consentimento. O robô encaminha esses pedidos ao responsável.
- Contratar plataforma não transfere a responsabilidade da clínica.
- Orientação oficial específica da ANPD sobre lembretes por WhatsApp: não encontrada (a confirmar).

## Horário e etiqueta no Brasil
- Lei específica de horário para mensagens no WhatsApp: não verificada (a confirmar com jurídico). Boa prática: marketing em horário comercial e dias úteis, evitando noites, domingos e feriados; lembrete de consulta com antecedência razoável (por exemplo, véspera).
- Responda rápido dentro da janela. Informe o horário do atendimento humano e o que acontece fora dele.

## Qualidade, limites e penalidades
- Qualidade do modelo (`quality_score`): verde, amarelo, vermelho, desconhecido (novo). Sinais: feedback negativo de usuários e baixa leitura. Vermelho: pausa de 3h na 1ª vez, 6h na 2ª, desativa na 3ª.
- Limite de mensagens: calculado por portfólio de negócios, em usuários únicos contatados fora da janela em 24h móveis. Começa em 250; sobe para 2.000 (verificar a empresa, ou enviar 2.000 mensagens de modelos de qualidade alta a usuários únicos em 30 dias) e depois escala automaticamente (10 mil, 100 mil, ilimitado) com boa qualidade e uso de pelo menos metade do limite nos últimos 7 dias. Confirmar valores atuais na página.
- Limite por usuário de marketing: a Meta pode limitar quantos modelos de marketing um usuário recebe; erro 131049; esperar 24h antes de reenviar. Marketing dentro de janela aberta não conta.
- Aplicação: aviso, bloqueios de 1 a 30 dias, trava de conta, desativação. Feedback negativo excessivo pode limitar ou desligar a conta.
- Boa prática: segmentar, baixa frequência, opt-in claro, texto útil, botão de parar.

## Preço (verificar sempre; "conferir preço atual")
- Desde 1/jul/2025: cobrança por mensagem entregue, não mais por conversa. O valor depende da categoria e do país do destinatário. Tabela oficial: https://business.whatsapp.com/products/platform-pricing#rates. O Brasil é mercado próprio na tabela; cobrança em BRL liberada gradualmente desde jul/2026 (fatura emitida pela Facebook Brasil). Valores em reais: conferir preço atual.
- Modelos (marketing, utility, autenticação) são cobrados por mensagem entregue.
- Texto livre dentro da janela (categoria service): passou a ser cobrado por mensagem a partir de 1/out/2026, com franquia gratuita por número (a página principal cita 1.000 por mês; a página de mensagens sem modelo não repete: a confirmar).
- Utility dentro de janela aberta: era gratuita desde 1/jul/2025; a página oficial indica cobrança a partir de 1/out/2026. Não prometa "grátis" ao cliente sem conferir a tabela vigente.
- Janela de entrada gratuita: usuário que chega por anúncio Click to WhatsApp abre até 7 dias com mensagens normais gratuitas.
- Meta Business Agent (agente de IA da Meta): categoria própria, cobrada por token desde 2026. Só importa se usar o agente da Meta (a confirmar).
- Mudanças de preço ocorrem só no primeiro dia de um trimestre, com aviso prévio.
- É preciso ter forma de pagamento cadastrada (cartão ou linha de crédito) para não interromper envios.
