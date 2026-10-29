---
name: guardiao-da-memoria
description: 'Load this before you open, write, edit or delete any memory file, and before you answer what you learned. It holds a method (written 28/10/2026) for how Claude''s knowledge evolves; the built-in memory instructions only say how to write a memory file, not how to tell fact from the story told about it, when a mistake becomes a pattern, where a lesson should live (memory, skill, hook, code or nothing) or how to prune. Use it at the end of a long task or session, after the owner corrects you, when the same mistake happens a second time, when two memories disagree, when asked to review or clean memories, and in the weekly review. Also on "o que você aprendeu", "aprenda com isso", "não repita esse erro", "revise suas memórias", "revisão da semana", "metacognição", "guardião da memória", "chave mestre". Not for improving a skill file from logged observations: use task-observer. Not for teaching the owner a subject: use teach. Not for checking work before it leaves the computer: use um-faz-outro-confere.'
---

# Guardião da memória: como o meu conhecimento evolui

Neste texto, "dono" é a pessoa com quem você trabalha: o usuário que instalou a skill.

Quem vive no automático sente e reage. Quem observa o próprio pensamento dá um passo para fora do momento, separa o que aconteceu da história que contou sobre isso e enxerga o padrão que repete. Para mim, isso decide o que vira memória, o que vira regra, o que vira código e o que é esquecido.

Saber mais não é o objetivo. O objetivo é errar menos da mesma forma e dar ao dono respostas que continuam certas na semana seguinte.

## O ciclo do Observador

1. **Fato.** Escreva o que aconteceu de forma que outro agente possa conferir: a frase exata do dono, o comando e a saída, o arquivo e a linha, a data. Sem adjetivo e sem culpa.
2. **História.** Separe o que é interpretação: "o dono prefere X", "essa ferramenta não funciona", "isso sempre quebra". Para cada uma, diga de onde veio (dito pelo dono, visto uma vez, deduzido) e que fato a confirmaria ou a derrubaria. Uma história sem fato que a sustente não vira regra.
3. **Padrão.** Uma vez é incidente, duas vezes é padrão, três vezes em dias diferentes pede regra dura (hook, script ou teste), não mais prosa. Procure nas memórias e no histórico se já aconteceu. Nomeie o padrão em uma frase pela causa, não pelo sintoma ("eu assumo o caminho sem listar a pasta", e não "o arquivo foi sobrescrito").
4. **Forma.** Escolha onde o aprendizado vai morar (tabela abaixo). A forma mais forte que couber vence: o que o computador consegue checar não fica só em prosa.
5. **Poda.** Toda inclusão pede uma revisão do que já existe. A memória que o fato novo contradiz é corrigida ou apagada, duas que dizem o mesmo viram uma, e data relativa ("ontem", "quinta") vira data absoluta. Apagar e reescrever seguem o banco de recuperação, logo abaixo.

## Banco de recuperação

Nenhuma memória é apagada ou reescrita sem uma cópia antes, e quem achou o problema não é quem decide: um conferente novo decide. O script fica em `scripts/banco.py`, e o banco em `~/.claude/memoria-recuperacao/`. Mexa só na pasta de memória da sessão atual.

1. **Guardar.** Antes de apagar, juntar ou reescrever uma memória, rode `python <pasta desta skill>/scripts/banco.py guardar <arquivo> --motivo "..." --prova "..."`. A prova é o fato que contradiz a memória (caminho que não existe, frase do dono com data, saída de comando). O script devolve um id. Se você mexer na memória depois de guardar, guarde de novo.
2. **Conferir.** Chame um subagente novo pela ferramenta Agent: um modelo menor (por exemplo, `haiku`) para checagem mecânica (o caminho existe? a data bate?) e um mais forte (por exemplo, Sonnet com esforço alto) para julgamento. Mande exatamente isto, sem o seu raciocínio:

   ```
   Você é o conferente. Você não escreveu esta memória e não sugeriu tirá-la.
   MEMÓRIA INTEIRA: <conteúdo do arquivo>
   PEDIDO: tirar esta memória (ou trocar pelo texto novo: <texto>) porque <motivo>.
   PROVA APRESENTADA: <prova>
   Confira a prova você mesmo (abra o arquivo, rode o comando, leia a frase do dono).
   Responda uma palavra e a sua prova:
   REMOVER = a memória está errada, velha ou repetida, e o pedido está certo.
   MANTER = a memória está certa e deve ficar como estava.
   NAO_VERIFICAVEL = não dá para provar nem um nem outro.
   ```

   Registre: `banco.py veredito <id> REMOVER|MANTER|NAO_VERIFICAVEL --prova "..." --conferente haiku|sonnet|sonnet-high|opus|opus-high|dono` (o banco só registra o nome).
3. **Agir pelo veredito.**
   - REMOVER, para apagar: `banco.py apagar <id>`. O script tira o arquivo e a linha do `MEMORY.md`; a cópia fica no banco.
   - REMOVER, para reescrever ou juntar: só agora edite a memória. A versão antiga já está no banco.
   - MANTER: a memória fica como estava.
   - NAO_VERIFICAVEL: não mexa. Leve ao dono como "CONFERIR" na revisão semanal das memórias.
4. **Recuperar.** `banco.py listar` mostra o que está no banco. `banco.py restaurar <id>` devolve a memória e a linha do índice (no fim do índice). Se a memória atual for diferente, o script guarda essa versão antes de restaurar.

O script recusa apagar sem o veredito REMOVER, recusa veredito sem prova ou de conferente fora da lista, guarda a versão atual se ela mudou depois de guardada e só aceita arquivos de `~/.claude/projects/<projeto>/memory/`. O script não sabe se o conferente foi mesmo outro agente, nem impede um `rm` ou um Write feito por fora dele: essa parte depende de você seguir esta skill. Uma memória nova, que não substitui nenhuma, não passa pelo banco. Para só acrescentar informação a uma memória, sem tirar nem mudar nada do que ela já dizia, rode `guardar ... --acrescimo` e edite: fica a cópia de segurança, sem conferente.

## Fila de correções e diário

Se os hooks estiverem instalados (passo 3 do README; são opcionais), três travas automáticas (quatro hooks no `~/.claude/settings.json`, que chamam `scripts/vigia.py`) trabalham sem depender de você lembrar. Sem eles, a fila fica vazia e só o banco de recuperação funciona:

- **Fala do dono na hora.** Três tipos entram na fila, com um aviso no seu contexto:
  - a correção ("errado", "já falei", "não repita", "não entendeu", "de novo" junto com "não"), que vence quando há mais de um tipo;
  - o pedido para lembrar ("lembre que", "lembre-se:", "não esqueça", "guarde na memória"; "lembre de rodar X" é tarefa, não entra);
  - o acerto confirmado: uma fala curta, sem pergunta e sem "não", que começa com um elogio (por exemplo, "perfeito", "isso mesmo", "era isso", "excelente") ou que diz "ficou bom".

  Num prompt longo colado, só o começo conta.
- **Diário.** Antes de a conversa ser resumida e quando a sessão termina, o diário da sessão vai para `~/.claude/memoria-recuperacao/diario/`. Ele guarda:
  - as falas desses três tipos;
  - as recusas do dono: a ferramenta, o começo do comando, mascarado, e o motivo, se ele deu;
  - os erros de ferramenta, com a data da mensagem (um "Exit code 1" sem causa fica de fora);
  - os arquivos editados.
- **Começo da sessão.** Aparecem avisos:
  - da fila deste projeto;
  - da revisão semanal vencida (uma vez por dia);
  - do `MEMORY.md` grande demais (o Claude Code só lê as 200 primeiras linhas);
  - dos erros que já se repetiram neste projeto nos últimos 30 dias, uma vez por dia por projeto. Os erros de rotina das ferramentas, como "string to replace not found", ficam de fora.

Para tratar a fila, rode o comando que o aviso mostra (`banco.py fila --projeto <projeto>`) e registre o destino de cada item: `banco.py tratada <id> --nota "virou a memória X"`.
- **Pedido para lembrar:** grave a memória já, sem esperar o fim da tarefa.
- **Correção:** passe pelo ciclo do Observador. Se ela contradiz uma regra que já existe numa memória ou skill, ela vem primeiro: a regra em prosa falhou, então suba para a forma mais forte.
- **Acerto:** vira memória `feedback` só se for um jeito de fazer que vale repetir e que não é óbvio.
- **Recusa do dono no diário:** trate como correção.

A fila tem alarme falso: "não era correção" é uma nota válida. A fila de outra aba se trata na aba dela.

`banco.py repetidos` mostra o mesmo erro de ferramenta em sessões diferentes: é o "duas vezes é padrão" medido pelo computador. Por padrão ele olha os últimos 30 dias, sem as abas de teste (`--projeto`, `--dias`, `--incluir-testes` mudam isso). Com 3 dias diferentes, ele marca FORTE. `banco.py duplicadas` lista os pares de memórias parecidas (nota de 0,45 para cima). Isso é uma suspeita, não um veredito: juntar passa pelo banco e pelo conferente.

A fila e o diário guardam trechos da fala do dono e o começo dos comandos recusados nesta máquina, como as transcrições do Claude Code já guardam. Senha, token, e-mail, CPF, CNPJ e telefone são mascarados, mas nem toda forma de escrever é pega, e nome de pessoa não é. Nunca leve dado pessoal sensível (saúde, paciente, cliente) da fila para uma memória. `banco.py historico` lê as transcrições de todos os projetos dos últimos 30 dias. `banco.py revisao-feita` apaga diário, posições, erros e correções tratadas com mais de 60 dias, e corta o `vigia-erros.log` quando passa de 512 KB.

As travas nunca bloqueiam uma mensagem. Se uma delas falhar, o erro vai para `~/.claude/memoria-recuperacao/vigia-erros.log`.

## Onde o aprendizado mora

| O aprendizado é | Vira |
|---|---|
| Fato sobre o dono, um projeto ou uma preferência, que o código não mostra | Memória (`user`, `project`, `feedback` ou `reference`) com **Por quê** e **Como aplicar** |
| Procedimento que se repete em várias sessões | Skill nova, só se nenhuma outra skill já cuidar desse território; senão, melhoria da skill dona |
| Regra que um programa consegue verificar | Hook, teste, validação ou script. Prosa é o último recurso |
| Algo que o código, o git, o `CLAUDE.md` ou uma skill já registram | Nada. Duplicar faz as cópias divergirem |
| Tropeço de uma sessão só | Nada. Regra feita de um único incidente faz a próxima sessão desviar de um buraco que não existe |

## Regras do que guardar

- Guarde o motivo. Uma regra sem o porquê não sabe quando deixar de valer.
- Diga a fonte e a data: "dito pelo dono em 28/10" pesa mais que "deduzido". O que foi deduzido e ainda não foi confirmado leva "(a confirmar)" na memória, em vez de ficar de fora.
- Memória é registro do passado. Antes de agir por ela, confira se o arquivo, a função, o caminho ou o preço ainda são como estão escritos.
- Uma correção do dono vence a memória antiga. Atualize a memória e mantenha o motivo da mudança.
- Escreva no tom normal. Um motivo convence mais que letra maiúscula.
- Nunca guarde senha, chave, token ou dado pessoal sensível (saúde, paciente, cliente).

## Fechamento de uma tarefa longa

Ao terminar uma tarefa longa, ou quando o dono se despede, rode `banco.py fila` e responda para si três perguntas, uma vez para cada correção da fila:

1. O que eu errei, ou o que o dono corrigiu? (fato)
2. Que história eu contei para mim que não era verdade?
3. Isso já tinha acontecido antes?

Se a resposta 3 for sim, rode os passos 3 a 5 do ciclo. Se não houver nada novo, não escreva nada: memória vazia de novidade é ruído.

## Revisão semanal das memórias

Faça uma vez por semana: quando aparecer o aviso de revisão vencida, quando o dono pedir ("revise suas memórias") ou quando o índice `MEMORY.md` passar de umas 60 linhas. Se você usa a skill task-observer, faça no mesmo dia da revisão dela, para o dono ter um só momento de revisão.

1. Rode `banco.py saude`: ele aponta índice quebrado, memória fora do índice, memória `feedback` ou `project` sem o motivo, data relativa e índice grande demais. Na primeira revisão, rode antes `banco.py historico --dias 30` para o diário ler as sessões antigas (cada erro fica com a data da mensagem original).
2. Leia o índice inteiro e abra as memórias que ele aponta. Para cada uma: ainda é verdade? Alguma outra a contradiz? Ela foi usada? O que ela cita ainda existe? O que estava "(a confirmar)" já foi confirmado?
3. Rode `banco.py duplicadas`, `banco.py repetidos` e `banco.py fila`, e leia os diários da semana em `~/.claude/memoria-recuperacao/diario/`. Um erro que aparece em duas sessões é padrão: passe pelo ciclo. Um FORTE vira hook, script ou teste.
4. Junte as duplicadas, corrija as erradas e leve para uma skill o que virou procedimento, sempre pelo banco de recuperação.
5. Rode `banco.py listar --status conferir-dono` e leve esses itens ao dono. Olhe também o `vigia-erros.log`.
6. Rode `banco.py revisao-feita --resumo "..."` com o que mudou (fica em `revisoes.md`) e conte ao dono em até cinco linhas: o que mudou, o que está no banco e o que só ele pode decidir.

Edite só a pasta de memória da sessão atual. Memória de outro projeto, ou configuração do usuário inteiro, só com o dono pedindo.
