# guardiao-da-memoria

Skill do Claude Code: a metacognição do agente. Ao fim de uma tarefa longa, depois de uma correção do dono, quando um erro se repete e na revisão da semana, o Claude separa o fato da história que contou, acha o padrão e decide onde o aprendizado vai morar (memória, skill, hook, código ou nada). Depois ele poda o que ficou velho.

Até 28/10/2026 se chamava `chave-mestre`; a frase "chave mestre" ainda aciona a skill. Inspirada num reel sobre metacognição ("a habilidade que prevê sucesso melhor que o QI").

## O que ela faz

**Banco de recuperação.** Antes de apagar ou reescrever, a memória é copiada para `~/.claude/memoria-recuperacao/` (`scripts/banco.py`). O script só apaga com o veredito REMOVER de um conferente registrado, com prova, e guarda a versão atual se ela mudou. `banco.py restaurar` devolve qualquer uma. Limite: o script não confere quem deu o veredito nem bloqueia um `rm` feito por fora dele. Isso depende do Claude seguir a skill.

**Travas automáticas** (`scripts/vigia.py`, opcionais, ligadas por hooks):

| Evento | Comando | O que faz |
|---|---|---|
| UserPromptSubmit | `vigia.py correcao` | A fala do dono que é um pedido para lembrar, uma correção ou um acerto confirmado entra na fila (`correcoes.jsonl`) |
| PreCompact e SessionEnd | `vigia.py diario` | Diário da sessão em `diario/`: as falas desses tipos, as recusas do dono (comando e motivo), os erros de ferramenta e os arquivos editados |
| SessionStart | `vigia.py inicio` | Avisa da fila do projeto, da revisão semanal vencida, do `MEMORY.md` grande e dos erros que já se repetiram |

Comandos do banco para elas: `fila`, `tratada`, `duplicadas`, `repetidos`, `saude`, `historico` e `revisao-feita` (veja o topo de `scripts/banco.py`).

## Como instalar

1. Copie a pasta `guardiao-da-memoria` para `~/.claude/skills/`.
2. Ponha esta linha no `~/.claude/CLAUDE.md`. Sem ela, a skill quase nunca entra sozinha, porque o Claude vai direto à pasta de memória (veja os testes):

   ```text
   Antes de abrir, escrever, editar ou apagar qualquer memória, e antes de responder o que você aprendeu, carregue a skill guardiao-da-memoria.
   ```

3. Opcional, para as travas automáticas: acrescente os hooks no `~/.claude/settings.json`. Precisa de Python 3.8 ou mais novo.
   - No Windows, o Claude Code normalmente roda os hooks no Git Bash: deixe `python`. Se o seu roda em PowerShell, troque `$HOME` pelo caminho completo da sua pasta de usuário.
   - No Mac e no Linux, troque `python` por `python3` se `python` não existir.

   ```json
   {
     "hooks": {
       "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "python \"$HOME/.claude/skills/guardiao-da-memoria/scripts/vigia.py\" correcao", "timeout": 15 }] }],
       "PreCompact": [{ "hooks": [{ "type": "command", "command": "python \"$HOME/.claude/skills/guardiao-da-memoria/scripts/vigia.py\" diario", "timeout": 60 }] }],
       "SessionEnd": [{ "hooks": [{ "type": "command", "command": "python \"$HOME/.claude/skills/guardiao-da-memoria/scripts/vigia.py\" diario", "timeout": 60 }] }],
       "SessionStart": [{ "hooks": [{ "type": "command", "command": "python \"$HOME/.claude/skills/guardiao-da-memoria/scripts/vigia.py\" inicio", "timeout": 15 }] }]
     }
   }
   ```

   Se o seu `settings.json` já tem hooks nesses eventos, acrescente estes itens às listas que já existem. O diário lê a transcrição inteira na primeira vez, e depois só o que é novo. Por isso ele tem 60 s: uma transcrição de centenas de MB pode levar mais de 15 s.

   Sem o passo 3, só o banco de recuperação funciona: a fila, o diário e os avisos ficam vazios.

Para desligar as travas, tire esses hooks. Para apagar tudo o que elas gravaram, apague `~/.claude/memoria-recuperacao/`, mas isso leva junto as cópias do banco.

## Privacidade

Tudo fica no seu computador: os scripts usam só a biblioteca padrão do Python, não acessam a internet e não pedem chave. A fila e o diário guardam trechos da sua fala e o começo dos comandos que você recusou, como as transcrições do Claude Code já guardam. `banco.py historico` lê as transcrições de todos os projetos dos últimos 30 dias para montar o diário. Antes de gravar, senha, token, e-mail, CPF, CNPJ e telefone são mascarados, mas nem toda forma de escrever é pega, e nome de pessoa não é. `banco.py revisao-feita` (manual) apaga o diário, as posições, os erros e as correções já tratadas com mais de 60 dias, e corta o `vigia-erros.log` quando ele passa de 512 KB.

O banco só aceita memórias em `~/.claude/projects/<projeto>/memory/`, a pasta de memória do Claude Code. Se a sua estiver em outro lugar, ele recusa.

## Território

- Cuida de: o que o Claude aprendeu, e de como ele registra, confere, corrige e esquece as próprias memórias e regras.
- Não cuida de:
  - melhorar arquivos de skill a partir de observações registradas (`task-observer`);
  - ensinar um assunto ao dono (`teach`);
  - conferir trabalho antes de sair do computador (`um-faz-outro-confere`).

  Essas vizinhas são opcionais.

## Ideias trazidas de outras skills

Foi trazida só a ideia, nenhum código. As licenças foram conferidas nas páginas abaixo em 28/10/2026: claude-reflect, claude-diary e memory-engine são MIT, e a página do memory-reflect não mostra a licença.

- claude-reflect: <https://github.com/BayramAnnakov/claude-reflect>
- claude-diary: <https://github.com/rlancemartin/claude-diary>
- memory-engine: <https://github.com/HelloRuru/claude-memory-engine>
- memory-reflect: <https://github.com/basicmachines-co/basic-memory-skills>

| Ideia | De onde veio |
|---|---|
| Fila de correções no UserPromptSubmit, pedido explícito para lembrar, acerto confirmado, recusas do dono, `duplicadas`, `historico` | claude-reflect |
| Diário antes do resumo; padrão com 2 vezes e regra dura com 3; correção que contradiz uma regra que já existe passa na frente | claude-diary |
| Erros repetidos lembrados no começo da sessão; 3 vezes em dias diferentes; `saude` e o limite do `MEMORY.md` | memory-engine |
| "(a confirmar)" em vez de descartar; memória fora do índice; registro de cada revisão (`revisoes.md`) | memory-reflect |

Ficaram de fora:
- a passagem de contexto para a próxima sessão, que é território de outra skill;
- achar skills novas em padrões repetidos, que é território da task-observer;
- um modelo de IA conferindo cada mensagem, porque custa por chamada;
- o backup das memórias na nuvem, porque tiraria as memórias do computador.

## Testes (28/10/2026, Sonnet)

Só os testes das travas automáticas podem ser rodados por quem instala. Os outros números são o relato do autor sobre testes feitos no computador dele.

- **Acionamento 5 + 5:** só pela descrição, 0 de 5 nos pedidos certos (em 3 versões da descrição); com a linha no `CLAUDE.md`, 9 de 10.
- **Comportamento**, com e sem a skill (2 repetições por cenário):
  - Faxina de memórias: com a skill, fez cópia no banco e teve conferente antes de apagar em 2 de 2; sem a skill, em 0 de 2. As duas versões juntaram a duplicada, resolveram o conflito e mantiveram a memória certa.
  - Erro repetido: igual com e sem a skill.
- **Banco de recuperação:** 2 rodadas de conferente (sonnet-high); na 1ª, 10 problemas; na 2ª, nenhum.
- **Travas automáticas:** `python testes/teste_vigia.py` roda 102 checagens numa pasta isolada, todas ok. Elas cobrem:
  - os tipos de fala;
  - a máscara de senha, CPF e telefone;
  - a fila;
  - o diário sem repetir;
  - 10 abas ao mesmo tempo;
  - HTML colado (menos de 3 s);
  - a caixa da letra do drive;
  - a recusa do dono, com o motivo;
  - a linha incompleta;
  - os avisos do começo da sessão;
  - `duplicadas`, `repetidos` com FORTE, `saude` e `historico`;
  - a poda de 60 dias.

O código das travas teve 2 rodadas de revisão por outro agente (sonnet-high): na 1ª, 13 achados; na 2ª, 5 parciais e 3 defeitos novos. As ideias trazidas de outras skills tiveram 1 rodada, com 17 achados. Todos foram corrigidos e estão cobertos por testes.

## Licença

Apache 2.0. Copyright 2026 Marcos Bruno Araujo (MB Gestão).
