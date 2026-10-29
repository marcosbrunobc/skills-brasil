# skills-brasil

Skills para o Claude Code (e outros agentes com skills) com as regras do Brasil já embutidas. Peça em português do jeito que você fala; a skill certa entra sozinha.

| Skill | Cuida de | Exemplos de pedido |
|---|---|---|
| [`whatsapp-business-br`](skills/whatsapp-business-br) | Mensagens e robôs de WhatsApp Business na API oficial da Meta: modelos (marketing, utility, autenticação), janela de 24 horas, opt-in e opt-out, fluxo do robô com passagem para humano, preço por mensagem. | "crie um lembrete de consulta para o WhatsApp", "meu template foi rejeitado, por quê?" |
| [`lgpd-br`](skills/lgpd-br) | LGPD em apps: política de privacidade, termos de uso, bases legais (arts. 7 e 11), dados de saúde, direitos do titular, incidente com a ANPD, encarregado, formulários Data safety (Google Play) e App Privacy (Apple). | "escreva a política de privacidade do app", "tivemos um vazamento, o que fazer?" |
| [`financas-empresa-br`](skills/financas-empresa-br) | Finanças e impostos de pequena empresa: PF, MEI, Simples Nacional ou Lucro Presumido, Fator R, pró-labore, carnê-leão, NFS-e nacional, reforma tributária (CBS/IBS), fluxo de caixa, DRE simplificada, reserva de imposto. | "MEI ou Simples?", "quanto reservar de imposto por mês?" |
| [`guardiao-da-memoria`](skills/guardiao-da-memoria) | Como o próprio Claude aprende e cuida das memórias. Ele separa o fato da história, transforma em regra o erro que se repete e poda o que ficou velho. Antes de apagar, a skill manda o Claude guardar uma cópia e chamar um conferente. Travas automáticas opcionais anotam as suas correções, mantêm um diário das sessões e bloqueiam apagar memória por fora do banco. Para ela entrar sozinha, precisa de uma linha no `CLAUDE.md`. | "o que você aprendeu hoje?", "revise suas memórias", "não repita esse erro" |

## Uma skill por território

Cada skill tem um assunto só, e a descrição dela diz qual vizinha chamar para o resto (por exemplo: a tela de consentimento é da `tela-bonita`, não da `lgpd-br`). Assim o agente não escolhe a skill errada sem avisar.

Antes de publicar, cada uma passou no teste dos 5 + 5: 5 pedidos que devem acionar a skill e 5 parecidos que não devem. As três primeiras deram 30 de 30, sem nenhum disparo no lugar errado. A `guardiao-da-memoria` só pela descrição não entra sozinha, e com uma linha no `CLAUDE.md` deu 9 de 10. O passo a passo está no [README dela](skills/guardiao-da-memoria/README.md).

## Como instalar

Copie a pasta de cada skill que quiser de `skills/` para `~/.claude/skills/` (vale para todos os projetos) ou para `.claude/skills/` dentro de um projeto. A `guardiao-da-memoria` tem mais dois passos (a linha no `CLAUDE.md` e, se quiser, os hooks), descritos no [README dela](skills/guardiao-da-memoria/README.md).

`whatsapp-business-br`, `lgpd-br` e `financas-empresa-br` são só texto: não instalam programas, não pedem chave e não acessam conta nenhuma. A `guardiao-da-memoria` traz scripts em Python (só a biblioteca padrão, sem internet) e travas automáticas opcionais, ligadas por hooks. Ela também não pede chave nem acessa conta.

## Fontes e avisos

- Cada skill tem um `fontes.md` com as fontes oficiais, a data da consulta e a lista do que ainda não foi confirmado (marcado "CONFERIR" ou "a verificar").
- As regras e os valores mudam todo ano. Confira a fonte antes de decidir.
- A `lgpd-br` não é parecer jurídico, e a `financas-empresa-br` não substitui contador. A `whatsapp-business-br` não substitui as políticas oficiais da Meta.

## Veja também

- [tela-bonita](https://github.com/marcosbrunobc/tela-bonita): design de telas de sites e apps com as regras do Brasil.

## Licença

Apache 2.0. Copyright 2026 Marcos Bruno Araujo (MB Gestão). Veja [LICENSE](LICENSE).
