# Modelos de mensagem (templates)

Fontes e datas em `../fontes.md`. Regras podem mudar: confira antes de submeter.

## Regras técnicas (resumo)
- Categorias: `UTILITY`, `MARKETING`, `AUTHENTICATION`. A Meta pode aprovar como marketing um modelo enviado como utility (padrão desde 9/abr/2025) ou reclassificar um modelo já aprovado, em geral com aviso de 1 dia (e-mail, WhatsApp Manager, webhook `template_category_update`); há 60 dias para contestar. Contas com histórico de má classificação podem ter mudança imediata e restrições.
- Componentes: cabeçalho (opcional; texto até 60 caracteres e 1 variável, ou imagem/vídeo/documento), corpo (obrigatório, até 1.024), rodapé (opcional, até 60; a página de componentes diz sem variáveis, outra página diz que aceita: tratar como sem variáveis), botões.
- Botões: resposta rápida (rótulo até 25), URL (até 2; rótulo até 25; 1 variável no fim do endereço), telefone (1), copiar código (1; valor até 20 caracteres). Até 10 botões no total. Se misturar resposta rápida com outros tipos, agrupe as respostas rápidas juntas (antes ou depois). Com mais de 3 botões, só 2 aparecem e o resto fica em "Ver todas as opções".
- Variáveis: formato `named` (minúsculas e underscore: `{{nome_paciente}}`) ou `positional` (`{{1}}`, `{{2}}` em sequência). Exemplo obrigatório para cada uma. Não começar nem terminar o modelo com variável. Evitar muitas variáveis em texto curto. Sem caracteres especiais como `#`, `$`, `%` na variável. A Meta não traduz: escreva tudo em pt-BR.
- Nome do modelo: minúsculas, números e underscore. Mesmo corpo e rodapé de um modelo existente é rejeitado (duplicado).
- Autenticação: só código de uso único, via modelo da biblioteca; sem URL, mídia ou emoji.
- Rejeições comuns: variável mal formatada, variável no início ou no fim, categoria errada (`INCORRECT_CATEGORY`), pedir dado sensível (cartão completo, número de documento), ameaça ou vergonha pública, golpe ou spam, violação da Commerce Policy (descrição e preço de bens e serviços entram aqui), duplicado.
- Revisão: automática e manual, até 24h. Modelo novo começa com qualidade "pendente". Qualidade vermelha: pausa de 3h, depois 6h, depois desativado.

## Tom em pt-BR
- "Você", frases curtas, primeira linha com o nome da clínica ou do paciente. Sem CAIXA ALTA, no máximo 1 emoji.
- Modelo fixo é enviado a qualquer hora: evite "Bom dia" e use "Olá".
- Dê saída: "Responda SAIR para não receber mais" (marketing) ou botão "Parar mensagens".
- Não prometa resultado clínico. Não use urgência falsa.
- Saúde: nunca procedimento, diagnóstico, dente, exame ou valor clínico no texto do modelo. Quem precisa do detalhe recebe por canal autenticado (portal, ligação, presencial).

## 10 modelos de exemplo
Nomes de variável são sugestões. Todos exigem opt-in do paciente ou cliente.

### 1. Lembrete de consulta (utility)
- Nome: `lembrete_consulta_v1` | Categoria: UTILITY | Idioma: pt_BR
- Variáveis: `nome_paciente` (ex.: Maria), `data` (ex.: 12/11), `hora` (ex.: 14h30), `nome_clinica` (ex.: Clínica Sorriso)
- Corpo: `Olá, {{nome_paciente}}. Lembramos do seu horário na {{nome_clinica}} em {{data}}, às {{hora}}. Podemos confirmar sua presença?`
- Botões: resposta rápida "Confirmar", "Remarcar", "Não poderei ir"
- Nota: sem especialidade nem procedimento (LGPD, dado de saúde). Termina em pergunta, não em variável.

### 2. Confirmação de agendamento (utility)
- Nome: `confirmacao_agendamento_v1` | UTILITY
- Variáveis: `nome_paciente`, `data`, `hora`, `endereco` (ex.: Rua das Flores, 100, Fortaleza)
- Corpo: `{{nome_paciente}}, seu horário está confirmado para {{data}}, às {{hora}}. Endereço: {{endereco}}. Chegue 10 minutos antes, por favor.`
- Rodapé: `Para alterar, use um dos botões.`
- Botões: resposta rápida "Remarcar"; URL "Ver no mapa" (1 variável no fim do endereço)

### 3. Cuidado pós-atendimento, sem diagnóstico (utility)
- Nome: `cuidado_pos_atendimento_v1` | UTILITY se for só acompanhamento ligado ao atendimento; se a Meta achar o texto educativo ou promocional, vira marketing
- Variáveis: `nome_paciente`, `nome_clinica`, `telefone_clinica`
- Corpo: `Olá, {{nome_paciente}}. Aqui é a {{nome_clinica}}. Como você está após o atendimento de hoje? Se tiver dúvida sobre as orientações que recebeu, responda esta mensagem ou ligue para {{telefone_clinica}}. Em caso de urgência, não espere resposta por aqui: ligue.`
- Botões: resposta rápida "Estou bem", "Quero falar com a equipe"
- Nota: não cite procedimento, medicamento, dose ou sintoma. Dúvida clínica vai para humano (ver `fluxos.md`). Modelo termina em ponto, não em variável.

### 4. Link de pagamento solicitado (utility)
- Nome: `link_pagamento_v1` | UTILITY (o paciente pediu o link)
- Variáveis: `nome_cliente`, `referencia` (ex.: consulta de 12/11), `valor` (ex.: R$ 150,00; conferir regra de preço e publicidade da profissão)
- Corpo: `{{nome_cliente}}, conforme você pediu, segue o link para pagamento de {{referencia}}, no valor de {{valor}}. O link é pessoal.`
- Botões: URL "Pagar agora" (variável no fim do endereço)
- Nota: preço em modelo pode atrair a Commerce Policy; mantenha só o que o cliente pediu. Nunca peça número de cartão pelo chat.

### 5. Pix (utility)
- Nome: `pix_pagamento_v1` | UTILITY
- Variáveis: `nome_cliente`, `referencia`
- Corpo: `{{nome_cliente}}, aqui está o pagamento de {{referencia}} por Pix. Toque no botão para abrir a página com o código e copie para o app do seu banco.`
- Botões: URL "Abrir Pix" (página sua com o Pix copia e cola)
- Nota: o botão "copiar código" aceita só 20 caracteres, pequeno demais para um Pix copia e cola completo. Alternativas: página própria ou o recurso de pagamentos da plataforma (a confirmar com o MCP `whatsapp_biz_configure_payments`).

### 6. Pesquisa de satisfação ligada ao atendimento (utility)
- Nome: `pesquisa_apos_atendimento_v1` | UTILITY (precisa citar um atendimento específico; pesquisa genérica vira marketing)
- Variáveis: `nome_paciente`, `data`
- Corpo: `Olá, {{nome_paciente}}. Sobre seu atendimento de {{data}}: como foi sua experiência? Sua opinião ajuda a melhorar nosso trabalho.`
- Botões: resposta rápida "Ótima", "Regular", "Precisa melhorar"

### 7. Aniversário (marketing)
- Nome: `aniversario_v1` | MARKETING
- Variáveis: `nome_paciente`, `nome_clinica`
- Corpo: `Feliz aniversário, {{nome_paciente}}! A equipe da {{nome_clinica}} deseja um dia especial para você.`
- Rodapé: `Responda SAIR para não receber mensagens de datas especiais.`
- Botões: resposta rápida "Obrigado!"
- Nota: sem desconto aqui. Se incluir oferta, siga as regras de publicidade profissional (a CFO-271/2025 alterou o código de ética odontológico: conferir o texto vigente antes de usar desconto ou preço). Variável não pode ficar no fim: a frase final cobre isso.

### 8. Reativação de paciente (marketing)
- Nome: `reativacao_paciente_v1` | MARKETING
- Variáveis: `nome_paciente`, `nome_clinica`
- Corpo: `Olá, {{nome_paciente}}. Faz um tempo que não nos vemos na {{nome_clinica}}. Quer que a gente veja um horário para você? Responda aqui e nossa equipe retorna.`
- Rodapé: `Responda SAIR para parar de receber.`
- Botões: resposta rápida "Quero um horário", "Agora não", "Parar mensagens"
- Nota: só para quem deu opt-in de marketing. Não mencione tratamento anterior (dado de saúde). Respeite o limite por usuário de marketing (erro 131049: aguardar 24h).

### 9. Retorno depois de avaliação ou orçamento (marketing)
- Nome: `retorno_avaliacao_v1` | MARKETING (padrão seguro)
- Variáveis: `nome_paciente`, `nome_clinica`
- Corpo: `Olá, {{nome_paciente}}. Aqui é a {{nome_clinica}}. Ficou com alguma dúvida sobre o que conversamos na sua última visita? Estamos à disposição para ajudar.`
- Botões: resposta rápida "Tenho dúvidas", "Já resolvi"
- Nota: não repita valores nem procedimentos do orçamento.

### 10. Código de verificação (authentication)
- Nome: o da biblioteca de autenticação | AUTHENTICATION
- Criar via `whatsapp_biz_template_library` (modelo de código com botão). Sem URL, mídia ou emoji; parâmetro até 15 caracteres.
- Uso: login do portal do paciente, confirmação de telefone. Nunca para outros fins.

## Modelos que não devem existir
- Resultado de exame, laudo, diagnóstico ou nome de tratamento no modelo.
- "Última chance" ou "só hoje" com pressão em saúde.
- Cobrança com ameaça ou exposição ("seu nome será negativado"): rejeição por conteúdo abusivo ou ameaçador.
- Promoção de medicamento ou suplemento.
