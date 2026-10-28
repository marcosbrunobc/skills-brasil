# Fluxos de robô e passagem para humano

Pressupõe API oficial (Cloud API). Configuração de webhook e número: MCP `whatsapp_business_tools`. Aqui só o desenho da conversa.

## Método (grafo com pontos de controle)
```
[entrada] -> [janela?] -> [identidade/opt-in] -> [classificar] -> [rotear]
                                                                     |
              +------------------+------------------+----------------+
              v                  v                  v                v
          [resposta fixa]   [ferramenta]       [humano direto]   [fora do escopo]
                                 |                  ^
                                 v                  |
                         [precisa aprovação?] --sim-+
                                 | não
                                 v
                        [checagem de qualidade] -> [enviar] -> [registrar]
```
Nós:
1. **Janela?** Se a janela de 24h está fechada, só modelo aprovado. Se a conversa começou pelo negócio, o primeiro passo é um modelo com botão.
2. **Identidade e opt-in.** Antes de falar de agendamento específico, confirmar que é a pessoa certa (nome + parte da data de nascimento). Registrar o aceite e a categoria.
3. **Classificar.** Intenção (agendar, remarcar, cancelar, preço, endereço/horário, pagamento, dúvida clínica, reclamação, sair/parar, outra) e sinais de urgência ou irritação. Baixa confiança = humano ou pergunta de esclarecimento (uma só).
4. **Rotear.** Cada intenção tem destino: resposta fixa, ferramenta ou humano.
5. **Ferramentas.** Agenda (consultar/criar/remarcar), FAQ aprovada pela clínica, status de pagamento, geração de link. Só leitura quando possível; gravação com confirmação do usuário ("Confirma terça, 14h30?").
6. **Aprovação humana** antes de enviar: reembolso, desconto, preço fora da tabela, reclamação, qualquer pergunta clínica, urgência, jurídico, menor de idade, mudança de dado cadastral, exclusão de dados (LGPD).
7. **Checagem de qualidade** (automática, antes de cada envio): janela aberta? Categoria correta? Dado sensível na mensagem? Promessa ou valor não autorizado? Tom pt-BR cortês? Mais de um chamado? Tamanho curto?
8. **Registrar**: intenção, decisão, quem aprovou, horário, opt-in.

## Padrão 1: agendamento
```
"quero marcar" -> identificar paciente -> [lista de horários livres (ferramenta)]
 -> botão/lista: escolher horário -> confirmar em uma frase -> criar na agenda
 -> mensagem de confirmação -> (D-1) lembrete modelo utility com Confirmar/Remarcar
```
- Máximo 3 botões de resposta; mais opções, use lista.
- Sem horário livre: oferecer lista de espera e passar para humano.

## Padrão 2: lembrete e confirmação
```
[job D-1] -> janela fechada -> modelo lembrete -> resposta:
   Confirmar -> marca confirmado, agradece (janela aberta, texto livre)
   Remarcar  -> padrão 1 (remarcação)
   Não poderei -> libera horário, oferece remarcar
   sem resposta -> segundo toque único (modelo) ou ligação humana; não insistir mais
```

## Padrão 3: dúvida clínica ou pós-atendimento
```
mensagem com dor/sintoma/medicamento/resultado/inchaço/sangramento
 -> classificar "clínica" -> NÃO responder conteúdo clínico
 -> resposta fixa: "Entendi. Vou chamar a equipe agora. Em urgência, ligue para {{telefone}}."
 -> alerta imediato ao profissional (com resumo, sem repetir dados sensíveis em canais abertos)
 -> humano responde
```
- O robô nunca diagnostica, nem indica medicamento ou dose, nem tranquiliza ("é normal").
- Palavras de alerta (exemplos): dor forte, sangramento, inchaço, febre, alergia, não consigo abrir a boca, dificuldade para respirar. Mensagem de emergência: orientar ligar para a clínica ou procurar pronto-atendimento (192 SAMU em emergência) e acionar humano.

## Padrão 4: preço e orçamento
```
"quanto custa?" -> valor tabelado e permitido? sim -> responder com a faixa autorizada pela clínica
                                             não/dúvida -> humano
```
- Preço e desconto: seguir as regras de publicidade e ética da profissão (conferir texto vigente) e a Commerce Policy da Meta. Desconto fora da tabela = aprovação humana.

## Padrão 5: pagamento
```
pedido de pagamento -> gerar link/Pix (ferramenta) -> enviar (janela aberta: texto livre; fechada: modelo utility)
 -> webhook de pagamento -> recibo
```
- Nunca receber número de cartão, senha ou documento completo no chat. Reembolso: humano.

## Padrão 6: reativação (marketing) com consentimento
```
[lista com opt-in de marketing] -> segmentar -> modelo marketing (poucos por vez)
 -> resposta positiva: abre janela -> padrão 1
 -> "Parar mensagens": registrar opt-out, confirmar uma vez, encerrar
 -> erro 131049: não reenviar antes de 24h
```
Monitorar qualidade e leitura. Qualidade caindo: reduzir volume, melhorar texto, rever lista.

## Padrão 7: reclamação
```
tom negativo/palavra "reclamação", "péssimo", "processo", "advogado", "Procon"
 -> pedir desculpa breve e neutra, sem admitir culpa nem prometer indenização
 -> humano (gestor) com resumo -> registrar
```

## Regras de passagem para humano
Passar sempre quando:
- pergunta clínica, urgência, reclamação, ameaça jurídica, reembolso, desconto, preço fora da tabela, menor de idade, pedido LGPD (acesso, correção, exclusão), pedido de falar com pessoa;
- 2 mal-entendidos seguidos ou baixa confiança na classificação;
- usuário irritado, caixa alta repetida, palavrões;
- ferramenta falhou duas vezes.

Como passar:
1. Avisar o usuário em uma frase: o que vai acontecer e quando ("Já chamei a recepção. Atendemos de segunda a sexta, das 8h às 18h; retornamos até as 10h do próximo dia útil.").
2. Entregar ao humano: nome, intenção, últimas mensagens, o que o robô já fez, urgência.
3. Robô para de responder aquele assunto até o humano devolver ou encerrar. Se a janela de 24h vai expirar, o humano responde antes ou usa modelo.
4. Fora do horário: dizer horário e opção de ligar; abrir tarefa para a manhã.
5. Humano pode devolver ao robô com tag de estado.

A política da Meta exige caminho claro de escalonamento em automações (atendente, telefone, e-mail, formulário). Deixe o caminho visível em toda conversa.

## Respostas fixas úteis (pt-BR)
- Entrada: `Olá! Sou o assistente virtual da {{clinica}}. Posso ajudar com agendamento, endereço e horários. Para falar com a equipe, escreva "atendente".`
- Não entendi: `Não entendi bem. Pode escolher uma das opções abaixo ou escrever "atendente"?`
- Opt-out: `Tudo bem, não enviaremos mais essas mensagens. Se mudar de ideia, é só nos chamar.`
- Urgência: `Entendi. Vou avisar a equipe agora. Se for urgente, ligue para {{telefone}}.`
- Fora do horário: `Estamos fora do horário. Atendemos {{horario}}. Deixe sua mensagem e retornamos assim que abrirmos.`

## Testes antes de ligar
- 20 conversas simuladas por intenção, incluindo erros de digitação, áudio (se o robô não lê áudio, diga e ofereça humano), mensagem de terceiro, número errado, opt-out no meio do fluxo.
- Verificar: nenhum dado sensível sai em modelo; todo caminho tem saída humana; janela fechada nunca envia texto livre.
