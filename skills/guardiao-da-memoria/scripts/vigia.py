"""Travas automáticas (hooks) do guardiao-da-memoria.

  vigia.py correcao   UserPromptSubmit: anota na fila a fala do dono que é pedido para lembrar, correção ou acerto
  vigia.py diario     PreCompact e SessionEnd: grava o diário da sessão (falas, recusas, erros, arquivos editados)
  vigia.py inicio     SessionStart: avisa da fila, da revisão vencida, do índice grande e dos erros já repetidos
  vigia.py trava      PreToolUse: bloqueia (código 2) apagar, mover ou reescrever memória por fora do banco

Erro interno nunca bloqueia: vai para o log e sai com código 0. Só a trava sai com 2, e só quando a regra é quebrada.

Tudo fica em ~/.claude/memoria-recuperacao (para testes: $BANCO_CLAUDE_HOME/memoria-recuperacao).
O banco.py importa este arquivo para ler a fila e o diário.
"""
import datetime
import json
import os
import re
import sys
import time
import traceback

CLAUDE = os.environ.get("BANCO_CLAUDE_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
BANCO = os.path.join(CLAUDE, "memoria-recuperacao")
FILA = os.path.join(BANCO, "correcoes.jsonl")
TRATADAS = os.path.join(BANCO, "correcoes-tratadas.jsonl")
DIARIO = os.path.join(BANCO, "diario")
ERROS = os.path.join(DIARIO, "erros.jsonl")
POSICOES = os.path.join(DIARIO, "posicao")  # um arquivo por sessão: abas simultâneas não se atropelam
REVISAO = os.path.join(BANCO, "ultima-revisao.txt")
AVISO = os.path.join(BANCO, "ultimo-aviso-revisao.txt")
AVISOS_ERROS = os.path.join(BANCO, "avisos")  # lembrete de erros: um por dia em cada projeto
LOG = os.path.join(BANCO, "vigia-erros.log")
DIAS_REVISAO = 7
TRECHO = 300  # caracteres guardados de cada fala do dono
LIMITE_INDICE = 150  # o Claude Code carrega só as 200 primeiras linhas do MEMORY.md

# sinais fortes de correção; "de novo" e "outra vez" só contam junto com um "não"
FORTES = re.compile(
    r"\b(errad[oa]s?|errou|n[aã]o (era|[eé]) (isso|assim)|isso n[aã]o [eé] o que|n[aã]o foi isso"
    r"|n[aã]o,? (eu )?queria|n[aã]o entendeu|j[aá] (te )?(falei|disse|pedi|expliquei)"
    r"|eu (te )?(disse|falei|pedi)|n[aã]o (te )?pedi|n[aã]o mandei|n[aã]o repita|pare de"
    r"|n[aã]o fa[cç]a (mais )?isso|esqueceu|n[aã]o funcionou|n[aã]o (est[aá]|t[aá]) (certo|funcionando))\b",
    re.I,
)
REPETICAO = re.compile(r"\b(de novo|outra vez)\b", re.I)
NEGACAO = re.compile(r"\bn[aã]o\b", re.I)
# pedido explícito para guardar (ideia do "remember:" do claude-reflect); "lembre de rodar X" é tarefa, não memória
LEMBRAR = re.compile(r"\blembre(-se)?(\s*:|,? (sempre )?(de )?que\b| disso\b)|\b(n[aã]o|nunca) esque[cç][ae]\b"
                     r"|\b(anot|guard|grav)[ae] (isso )?(na|em) (sua )?mem[oó]ria|\bremember\b", re.I)
NAO_LEMBRAR = re.compile(r"\b(n[aã]o|nunca) (me )?lembr", re.I)
# acerto: fala curta, sem pergunta e sem "não", que começa elogiando ou diz que ficou bom
ACERTO_INICIO = re.compile(r"^\W*(perfeito|isso mesmo|exatamente( isso)?|era isso( mesmo)?|mandou bem|show de bola|excelente)\b", re.I)
ACERTO_FICOU = re.compile(r"\bficou (muito )?(bom|[oó]timo|show|lindo|perfeito)\b", re.I)
AVISOS = {
    "correcao": "a mensagem do dono parece uma correção",
    "lembrar": "o dono pediu para lembrar algo",
    "acerto": "o dono aprovou um jeito de fazer",
}
# blocos que o próprio Claude Code põe na mensagem (lembretes, texto colado, seleção do editor)
TAGS = r"system-reminder|pasted_content|ide_[a-z_]+|command-[a-z]+|local-command-[a-z]+|task-notification|agent-message|user-prompt-submit-hook"
ABRE = re.compile(rf"<({TAGS})\b[^>]{{0,200}}>")
SEGREDOS = [
    (re.compile(r"\b[\w-]*?(token|secret|passw\w*|senha|api[_-]?key|access[_-]?key)(\s*[:=]\s*|\s+(?:é|e|era|is|was)\s+)\S+", re.I),
     r"\1: [oculto]"),
    (re.compile(r"--(password|passwd|pass|token|secret|api-key)\s+\S+", re.I), r"--\1 [oculto]"),
    (re.compile(r"(\s-u\s+)\S+:\S+"), r"\1[oculto]"),  # curl -u usuario:senha
    (re.compile(r"\b(bearer|basic)\s+\S+", re.I), r"\1 [oculto]"),
    (re.compile(r"://[^/\s:@]+:[^@\s]+@"), "://[oculto]@"),
    (re.compile(r"[\w.+-]{1,64}@[\w-]{1,64}\.[\w.]{1,64}"), "[email]"),
    (re.compile(r"\b(?:sk|rk|pk)[-_][\w-]{8,}|\b(?:ghp|gho|ghs|github_pat)_\w{8,}|\bxox[abp]-[\w-]{8,}|\bAKIA[0-9A-Z]{12,}"), "[token]"),
    (re.compile(r"[A-Za-z0-9_\-]{32,}"), "[token]"),
    # CPF, CNPJ e telefone, também escritos com espaço
    (re.compile(r"\b\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-.\s]?\d{2}\b"), "[numero]"),
    (re.compile(r"\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2}\b"), "[numero]"),
    (re.compile(r"(\(?\b\d{2}\)?[\s-]?)?\b9?\d{4}[\s-]\d{4}\b"), "[numero]"),
]
NUMERO = re.compile(r"\d[\d.\-/]{7,}\d")  # sem espaço: data e hora ficam, números longos saem
RECUSA = re.compile(r"user doesn't want to proceed|user rejected|the user denied", re.I)
MOTIVO_RECUSA = re.compile(r"(?:reason for the rejection|the user said)\W*(.+)", re.I | re.S)
# interrupção do dono e bloqueios do próprio Claude Code não são erro de ferramenta
IGNORAR_ERRO = re.compile(r"interrupted by user|request interrupted|tool call interrupted|denied by the claude code"
                          r"|requested permissions|auto mode|permission for this", re.I)
CAUSA = re.compile(r"error|erro|exception|fail|falh|denied|not found|no such|cannot|can't|invalid|traceback|fatal"
                   r"|refused|missing|unexpected|timed? ?out", re.I)
# no lembrete do começo da sessão ficam de fora os projetos de teste e os erros de rotina das ferramentas
PROJETO_TESTE = re.compile(r"(^|-)(temp|tmp|scratch\w*|tests?|testes?|sandbox|sbx)(-|$)", re.I)  # pasta inteira: "template" fica
ROTINA = re.compile(r"string to replace|file does not exist|file has been modified|has not been read yet|no changes to make"
                    r"|inputvalidationerror|^#+ error", re.I)


def projeto(cwd):
    """Nome da pasta do projeto em ~/.claude/projects, como o Claude Code monta a partir do cwd."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd or "")


def projeto_de(e):
    """A pasta da transcrição é o nome exato do projeto; sem ela, monta a partir do cwd."""
    tp = e.get("transcript_path")
    return os.path.basename(os.path.dirname(tp)) if tp else projeto(e.get("cwd"))


def mesmo_projeto(a, b):
    return (a or "").lower() == (b or "").lower()  # o Claude Code grava c-- e C-- para a mesma pasta


def automacao():
    return os.environ.get("CLAUDE_CODE_ENTRYPOINT", "").startswith("sdk")  # claude -p e rotinas, não o dono


def texto_do_dono(t):
    """Tira os blocos do Claude Code numa passada só (sem regex que volta atrás em texto colado)."""
    t = t or ""
    partes, i = [], 0
    while True:
        m = ABRE.search(t, i)
        if not m:
            partes.append(t[i:])
            break
        partes.append(t[i:m.start()])
        fim = t.find(f"</{m.group(1)}>", m.end())
        # bloco sem fechamento: tira só a tag e segue lendo
        i = m.end() if fim < 0 else fim + len(m.group(1)) + 3
    return " ".join(partes)


def parece_correcao(t):
    t = texto_do_dono(t)[:2000]
    return bool(FORTES.search(t) or (REPETICAO.search(t) and NEGACAO.search(t)))


def tipo_da_fala(t):
    """correcao > lembrar > acerto; None quando a fala não tem nada para aprender."""
    limpo = texto_do_dono(t).strip()
    curto = limpo if len(limpo) <= 600 else limpo[:300]  # prompt longo colado: só o começo é fala sobre o trabalho
    if parece_correcao(curto):
        return "correcao"
    if LEMBRAR.search(curto) and not NAO_LEMBRAR.search(curto):
        return "lembrar"
    if (len(limpo) <= 120 and "?" not in limpo and not NEGACAO.search(limpo)
            and (ACERTO_INICIO.search(limpo) or ACERTO_FICOU.search(limpo))):
        return "acerto"
    return None


def _numero(m):
    return "[numero]" if sum(c.isdigit() for c in m.group(0)) >= 9 else m.group(0)


def mascarar(t):
    """Tira senha, token, e-mail e números longos (CPF, telefone) antes de gravar. Nome de pessoa não sai."""
    for padrao, troca in SEGREDOS:
        t = padrao.sub(troca, t)
    t = NUMERO.sub(_numero, t)
    return " ".join(t.split())


def trecho(t, n=TRECHO):
    """Corta com folga, mascara e só então corta no tamanho final (um token cortado antes escaparia da máscara)."""
    return mascarar(t[:n * 4])[:n]


def assinatura(t):
    """Forma normalizada de um erro, para achar o mesmo erro em sessões diferentes."""
    s = t.lower()
    # caminho até a aspa, o ": " ou o fim da linha (aceita espaço no meio); a mensagem depois dele fica
    s = re.sub(r"([a-z]:)?[\\/](?:[^'\"\n:]|:(?! ))*", "<p>", s)
    s = re.sub(r"\d+", "#", s)
    return " ".join(s.split())[:120]


def trocar(tmp, caminho):
    """os.replace com novas tentativas: no Windows ele falha se outra aba estiver com o arquivo aberto."""
    for tentativa in range(5):
        try:
            os.replace(tmp, caminho)
            return
        except PermissionError:
            time.sleep(0.05 * (tentativa + 1))
    os.replace(tmp, caminho)


def anexar(caminho, obj):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "a", encoding="utf-8") as f:
        # ensure_ascii: U+2028 e afins escapados, para uma linha nunca virar duas
        f.write(json.dumps(obj, ensure_ascii=True) + "\n")


def ler_jsonl(caminho):
    if not os.path.exists(caminho):
        return []
    saida = []
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            try:
                saida.append(json.loads(linha))
            except ValueError:
                continue
    return saida


def ler_texto(caminho):
    if not os.path.exists(caminho):
        return None
    with open(caminho, encoding="utf-8") as f:
        return f.read().strip() or None


def escrever_texto(caminho, texto):
    """Grava por arquivo temporário próprio e troca."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    tmp = f"{caminho}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(texto + "\n")
    trocar(tmp, caminho)


def pendentes(proj=None):
    """Itens da fila ainda não tratados; com proj, só os daquele projeto."""
    feitas = {r.get("id") for r in ler_jsonl(TRATADAS)}
    return [c for c in ler_jsonl(FILA) if c.get("id") not in feitas and (proj is None or mesmo_projeto(c.get("projeto"), proj))]


def correcao(e):
    if automacao():
        return
    texto = e.get("prompt") or ""
    tipo = tipo_da_fala(texto)
    if not tipo:
        return
    agora = datetime.datetime.now()
    proj = projeto_de(e)
    anexar(FILA, {
        "id": agora.strftime("%Y%m%d-%H%M%S-%f"),
        "data": agora.strftime("%Y-%m-%d %H:%M"),
        "projeto": proj,
        "sessao": (e.get("session_id") or "")[:8],
        "origem": os.environ.get("CLAUDE_CODE_ENTRYPOINT", ""),
        "tipo": tipo,
        "texto": trecho(texto_do_dono(texto)),
    })
    quando = "Agora" if tipo == "lembrar" else "No fim da tarefa"
    print(f"guardiao-da-memoria: {AVISOS[tipo]}; anotado na fila (banco.py fila --projeto {proj}). "
          f"{quando}, carregue a skill guardiao-da-memoria e trate a fila.")


def _textos(conteudo):
    if isinstance(conteudo, str):
        return [conteudo]
    if isinstance(conteudo, list):
        return [b.get("text", "") for b in conteudo if isinstance(b, dict) and b.get("type") == "text"]
    return []


def _data(r):
    """Data da mensagem na transcrição (o historico lê sessões antigas); sem ela, agora."""
    ts = str(r.get("timestamp") or "")
    return f"{ts[:10]} {ts[11:16]}" if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", ts) else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _chamadas(conteudo, chamadas, arquivos=None):
    for b in conteudo if isinstance(conteudo, list) else []:
        if not (isinstance(b, dict) and b.get("type") == "tool_use"):
            continue
        entrada = b.get("input") or {}
        resumo = entrada.get("command") or entrada.get("file_path") or entrada.get("url") or entrada.get("pattern") or ""
        chamadas[b.get("id")] = f"{b.get('name')}: {trecho(str(resumo), 80)}"
        if arquivos is not None and b.get("name") in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            alvo = entrada.get("file_path") or entrada.get("notebook_path")
            # rascunho da sessão não interessa ao diário
            if alvo and alvo not in arquivos and "scratchpad" not in alvo.replace("\\", "/").lower():
                arquivos.append(alvo)


def _erro(bruto):
    """Texto curto do erro de ferramenta, ou None quando é rotina sem causa ("Exit code 1" de um teste que falhou de propósito)."""
    linhas = [l.strip() for l in bruto.splitlines() if l.strip()]
    if linhas and re.fullmatch(r"#+\s*error:?", linhas[0], re.I):
        linhas = linhas[1:]  # "### Error" é só o título; o erro está na linha seguinte
    if not linhas or IGNORAR_ERRO.search(linhas[0]):
        return None
    texto = linhas[0]
    if re.fullmatch(r"exit code \d+", texto, re.I):
        # "Exit code 1" sozinho não diz nada: procura a causa nas últimas linhas
        causa = next((l for l in reversed(linhas[-5:]) if CAUSA.search(l)), None)
        if not causa:
            return None
        texto = f"{texto}: {causa}"
    return trecho(texto, 200)


def diario(e):
    caminho = e.get("transcript_path")
    sessao = e.get("session_id") or "sem-id"
    if not caminho or not os.path.isfile(caminho):
        return
    arq_pos = os.path.join(POSICOES, re.sub(r"[^\w-]", "_", sessao)[:80] + ".txt")
    try:
        inicio = int(ler_texto(arq_pos) or 0)
    except ValueError:
        inicio = 0
    falas = {"correcao": [], "lembrar": [], "acerto": []}
    erros, arquivos, recusas, chamadas = {}, [], [], {}
    n = inicio
    with open(caminho, encoding="utf-8", errors="replace") as f:
        for i, linha in enumerate(f, 1):
            if i <= inicio:
                # já lido: só remonta o nome das ferramentas chamadas pouco antes (a recusa pode vir depois)
                if i > inicio - 400 and '"tool_use"' in linha:
                    try:
                        _chamadas(((json.loads(linha).get("message") or {}).get("content")), chamadas)
                    except (ValueError, AttributeError):
                        pass
                continue
            if not linha.endswith("\n"):
                break  # linha ainda sendo gravada: fica para a próxima vez
            n = i
            try:
                r = json.loads(linha)
            except ValueError:
                continue
            if str(r.get("entrypoint", "")).startswith("sdk"):
                continue  # claude -p e automações: não é o dono
            msg = r.get("message") if isinstance(r.get("message"), dict) else {}
            conteudo = msg.get("content")
            if r.get("type") == "user" and not r.get("isMeta") and not r.get("isCompactSummary"):
                for t in _textos(conteudo):
                    tipo = tipo_da_fala(t)
                    if tipo:
                        falas[tipo].append(trecho(texto_do_dono(t)))
                for b in conteudo if isinstance(conteudo, list) else []:
                    if not (isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error")):
                        continue
                    bruto = re.sub(r"</?[a-zA-Z_-]+>", " ", " ".join(_textos(b.get("content"))))
                    if RECUSA.search(bruto[:300]):
                        # recusa do dono mostra preferência (ideia do claude-reflect): vai para o diário, não para erros
                        motivo = MOTIVO_RECUSA.search(bruto)
                        recusas.append(chamadas.get(b.get("tool_use_id"), "ferramenta")
                                       + (f" | motivo: {trecho(motivo.group(1).strip(), 200)}" if motivo else ""))
                        continue
                    texto = _erro(bruto)
                    if texto:
                        erros[assinatura(texto)] = (texto, _data(r))
            elif r.get("type") == "assistant":
                _chamadas(conteudo, chamadas, arquivos)
    secoes = (("Possíveis correções do dono", falas["correcao"]), ("Pedidos para lembrar", falas["lembrar"]),
              ("Acertos confirmados pelo dono", falas["acerto"]), ("Recusas do dono", recusas),
              ("Erros de ferramenta", [t for t, _ in erros.values()]), ("Arquivos editados", arquivos[:40]))
    if any(itens for _, itens in secoes):
        agora = datetime.datetime.now()
        proj = projeto_de(e)
        partes = [f"# Diário {agora:%Y-%m-%d %H:%M} (sessão {sessao[:8]}, {e.get('hook_event_name', '?')})", "", f"Projeto: {proj}", ""]
        for titulo, itens in secoes:
            if itens:
                partes += [f"## {titulo}", ""] + [f"- {i}" for i in itens] + [""]
        os.makedirs(DIARIO, exist_ok=True)
        with open(os.path.join(DIARIO, f"{agora:%Y-%m-%d-%H%M%S}-{sessao[:8]}-{os.getpid()}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(partes))
        for ass, (texto, data) in erros.items():
            anexar(ERROS, {"data": data, "sessao": sessao[:8], "projeto": proj, "assinatura": ass, "texto": texto})
    escrever_texto(arq_pos, str(n))  # só depois de gravar o diário


def erros_repetidos(proj=None, min_sessoes=2, dias=30, limite=3, rotina=False, testes=False):
    """Erros de ferramenta que já apareceram em várias sessões recentes: [(sessões, dias, texto, último registro)]."""
    corte = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
    grupos = {}
    for r in ler_jsonl(ERROS):
        p, t = r.get("projeto") or "", r.get("texto") or ""
        if (r.get("data") or "") < corte or (proj and not mesmo_projeto(p, proj)):
            continue
        # projeto de teste só sai da conta geral; quem pede o próprio projeto vê os erros dele
        if (not testes and not proj and PROJETO_TESTE.search(p)) or (not rotina and ROTINA.search(t)):
            continue
        g = grupos.setdefault(r.get("assinatura", ""), [set(), set(), r])
        g[0].add(r.get("sessao"))
        g[1].add((r.get("data") or "")[:10])
        g[2] = r
    achados = sorted(((len(s), len(d), r.get("texto", ""), r) for s, d, r in grupos.values() if len(s) >= min_sessoes),
                     key=lambda x: (-x[1], -x[0]))
    return achados[:limite] if limite else achados


def inicio(e):
    if automacao():
        return  # a rotina não gasta o aviso do dia
    linhas = []
    proj = projeto_de(e)
    n = len(pendentes(proj))
    if n:
        linhas.append(f"guardiao-da-memoria: {n} item(ns) na fila deste projeto (correções, pedidos para lembrar, acertos) "
                      f"(banco.py fila --projeto {proj}). Trate no fim da primeira tarefa.")
    indice = os.path.join(CLAUDE, "projects", proj, "memory", "MEMORY.md")
    if os.path.exists(indice):
        with open(indice, encoding="utf-8", errors="replace") as f:
            total = sum(1 for _ in f)
        if total >= LIMITE_INDICE:
            linhas.append(f"guardiao-da-memoria: o MEMORY.md tem {total} linhas e o Claude Code só lê as 200 primeiras. "
                          "Junte ou mova memórias pelo banco antes de criar outra.")
    hoje = datetime.date.today().isoformat()
    ultima = ler_texto(REVISAO)
    try:
        vencida = ultima is None or (datetime.date.today() - datetime.date.fromisoformat(ultima)).days >= DIAS_REVISAO
    except ValueError:
        vencida = True
    if vencida and ler_texto(AVISO) != hoje:
        escrever_texto(AVISO, hoje)  # um aviso por dia, em qualquer aba
        linhas.append(f"guardiao-da-memoria: a revisão semanal das memórias está vencida (última: {ultima or 'nunca'}). "
                      "Ofereça ao dono em uma linha (se ele usa a task-observer, faça junto com a revisão dela).")
    aviso_erros = os.path.join(AVISOS_ERROS, re.sub(r"[^\w-]", "_", proj.lower())[:120] + ".txt")
    if e.get("source") in (None, "startup") and ler_texto(aviso_erros) != hoje:
        repetidos = erros_repetidos(proj)
        if repetidos:
            # ideia do memory-engine: lembrar os erros antes da tarefa, não só na revisão
            escrever_texto(aviso_erros, hoje)
            linhas.append("guardiao-da-memoria: erros que já se repetiram neste projeto (evite):")
            linhas += [f"- {t[:140]} ({s} sessões)" for s, _, t, _ in repetidos]
    if linhas:
        print("\n".join(linhas))


REGISTRO = os.path.join(BANCO, "registro.json")
HORAS_VEREDITO = 3  # o veredito REMOVER libera reescrever aquela memória por algumas horas
LIMITE_COMANDO = 500_000  # comando maior: analisa os primeiros 400 KB e os últimos 100 KB (o hook tem 10 s)
LINK_INDICE = re.compile(r"\]\(([^)\s]{1,300}\.md)\)")
CASA = os.path.expanduser("~")
APAGAM = {"rm", "rmdir", "del", "erase", "rd", "unlink", "shred", "truncate", "remove-item", "ri", "clear-content", "clc"}
MOVEM = {"mv", "move", "move-item", "mi", "ren", "rename", "rename-item", "rni"}
COPIAM = {"cp", "copy", "copy-item", "cpi", "install", "ln", "rsync"}
GRAVAM = {"set-content", "sc", "out-file", "new-item", "ni"}
DESCOMPACTAM = {"tar", "unzip", "expand-archive"}
LISTAM = {"ls", "dir", "gci", "get-childitem", "find", "fd", "rg", "grep"}
MUDAM_DIR = {"cd", "pushd", "chdir", "set-location", "sl", "push-location"}
PREFIXOS = {"sudo", "command", "builtin", "nohup", "time", "exec", "env", "&", "then", "do", "else", "elif", "!", "if",
            "while", "until", "try", "catch", "finally", "elseif", "setsid"}
ENVOLVEM = {"timeout", "nice", "ionice", "stdbuf", "busybox", "watch"}  # rodam outro comando: pula opções e números
LACOS = {"foreach", "foreach-object", "%", "where-object", "?"}
INTERPRETES = {"python", "python3", "py", "node", "perl", "ruby"}
GIT_REESCREVE = {"checkout", "restore", "clean", "rm", "mv", "reset", "stash", "switch"}
NOMEADOS = {"-path", "-literalpath", "-destination", "-destinationpath", "-t", "--target-directory", "-o", "--output",
            "-filepath", "-value", "-c", "-d"}
NET = re.compile(r"\[(?:system\.)?io\.(?:file|directory)\]::(?:delete|move|replace|copy|writeall\w{0,20})", re.I)
PY_APAGA = re.compile(r"os\.(?:remove|unlink|rename|replace|rmdir)|shutil\.(?:move|rmtree|copy\w{0,10})|\.write_text|\.unlink\("
                      r"|open\([^)\n]{0,200}['\"][wx]", re.I)
JS_APAGA = re.compile(r"\b(?:unlink|rm|rmdir|rename|writeFile|copyFile)(?:Sync)?\(", re.I)
VERBO_APAGA = re.compile(r"(?<![\w-])(remove-item|ri|rm|del|erase|move-item|mi|mv|set-content|clear-content|out-file)(?![\w-])", re.I)
CITA_CLAUDE = re.compile(r"\.claude[\\/]+projects", re.I)
PODE_TOCAR = re.compile(r"\.claude|projects|memory|users|\$home|\$\{home|\$userprofile|\$env:|%userprofile%|claude_config|~", re.I)
NOME_MD = re.compile(r"\.md['\"]?$|^['\"]?\*['\"]?$|^['\"]?\*\.\*['\"]?$", re.I)  # filtro de find que pode pegar memória


def _log(msg):
    try:
        os.makedirs(BANCO, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} trava: {msg}\n")
    except OSError:
        pass


def _normal(p):
    p = re.sub(r"^\\\\\?\\", "", str(p))  # \\?\C:\... é o mesmo caminho
    return os.path.normcase(os.path.normpath(p))


def _memoria(caminho):
    """(é memória, é o índice) para um caminho de arquivo, pela pasta real de memória do Claude Code."""
    try:
        caminho = re.sub(r"^\\\\\?\\", "", str(caminho))
        real = os.path.normcase(os.path.realpath(caminho))
        raiz = os.path.normcase(os.path.realpath(os.path.join(CLAUDE, "projects")))
        partes = os.path.relpath(real, raiz).split(os.sep)
    except (ValueError, TypeError):  # outro drive, caminho inválido
        return False, False
    if len(partes) != 3 or partes[0] == ".." or partes[1] != "memory" or not real.endswith(".md"):
        return False, False
    return True, partes[2] == os.path.normcase("MEMORY.md")


def _cita_projects(texto):
    """O texto cita a pasta projects do Claude Code (por ~/.claude/projects ou pelo caminho real)?"""
    if CITA_CLAUDE.search(texto):
        return True
    raiz = _normal(os.path.join(CLAUDE, "projects")).replace("\\", "/")
    return raiz in os.path.normcase(texto).replace("\\", "/").replace("//", "/")


def _expandir(tok, cwd, vars_=None):
    """Caminho absoluto normalizado de um argumento (~, $HOME, variáveis, /c/ do Git Bash, relativo ao cwd).

    Termina em os.sep quando o argumento terminava em barra (pasta). None quando não dá para resolver."""
    bruto = (tok or "").strip().strip("@(){};").strip("\"'")
    bruto = re.sub(r"^\\\\\?\\", "", bruto)
    if not bruto or bruto.startswith("-") or len(bruto) > 1000 or "\n" in bruto:
        return None
    t = bruto
    for _ in range(3):  # $m pode valer "$HOME\..."; resolve em camadas
        m = re.match(r"^(?:\$env:(\w+)|\$\{(\w+)\}|\$(\w+)|%(\w+)%)", t, re.I)
        if not m:
            break
        nome = next(g for g in m.groups() if g)
        if nome.lower() in ("_", "psitem"):
            return None  # $_ do PowerShell é o item do pipeline, não variável de ambiente
        if vars_ and nome in vars_:
            valor = vars_[nome]
        elif nome.upper() in ("HOME", "USERPROFILE"):
            valor = CASA
        else:
            valor = os.environ.get(nome)
        if valor is None:
            return None  # variável que não sei resolver
        t = valor + t[m.end():]
    t = re.sub(r"^~(?=$|[\\/])", lambda m: CASA, t)
    m = re.match(r"^/([a-zA-Z])(?=/|$)", t)
    if m and os.name == "nt":
        t = m.group(1) + ":" + t[2:]
    if not os.path.isabs(t):
        t = os.path.join(cwd, t)
    pasta = re.search(r"[\\/]\.?$", bruto) is not None
    return _normal(t) + (os.sep if pasta else "")


def _partes(p):
    """Partes do caminho dentro de CLAUDE/projects, ou None se estiver fora."""
    raiz = _normal(os.path.join(CLAUDE, "projects"))
    p = (p or "").rstrip("\\/")
    if not p.startswith(raiz + os.sep):
        return None
    return p[len(raiz) + 1:].split(os.sep)


def _toca_memoria(p):
    """É uma memória, uma pasta de memória, um projeto inteiro, a pasta projects ou algo acima dela?"""
    if not p:
        return False
    raiz = _normal(os.path.join(CLAUDE, "projects"))
    if (raiz + os.sep).startswith(p.rstrip("\\/") + os.sep):
        return True  # apagar projects, ~/.claude ou acima leva as memórias junto
    partes = _partes(p)
    return partes is not None and (len(partes) == 1 or partes[1] == "memory")


def _dentro_da_memoria(p):
    """Está na pasta de memória de um projeto (ou dentro dela)? Não conta as pastas acima."""
    partes = _partes(p)
    return partes is not None and len(partes) >= 2 and partes[1] == "memory"


def _existe(p):
    try:
        return os.path.exists(p)
    except (OSError, ValueError):
        return False


def _sobrescreve(alvo, fontes):
    """Gravar em alvo apaga uma memória que já existe? Memória nova é livre."""
    if not alvo or not _toca_memoria(alvo):
        return False
    if alvo.endswith(os.sep) or os.path.isdir(alvo):
        if not fontes:
            return True
        for f in fontes:
            if not f:
                continue
            if "*" in f or "?" in f or f.endswith(os.sep) or os.path.isdir(f) or os.path.basename(f) in (".", ""):
                return True  # pasta ou glob copiada por cima pode trocar memórias que já existem
            if _existe(os.path.join(alvo, os.path.basename(f))):
                return True
        return False
    return _existe(alvo) or "*" in alvo


def _sem_heredoc(texto):
    """(texto sem o corpo de heredoc e de here-string, [(linha que abriu, corpo)]). O corpo é dado, não comando."""
    saida, corpos, fim, abertura, corpo = [], [], None, "", []
    for linha in texto.split("\n"):
        if fim is not None:
            if (fim in ("'@", '"@') and linha.lstrip().startswith(fim)) or linha.strip() == fim:
                corpos.append((abertura, "\n".join(corpo)))
                if fim in ("'@", '"@'):
                    saida.append(linha.lstrip()[2:])  # o que vem depois do '@ ainda é comando
                fim, corpo = None, []
            else:
                corpo.append(linha)
            continue
        saida.append(linha)
        m = re.search(r"(?<!<)<<(?!<)-?\s*['\"]?([A-Za-z_][\w-]{0,40})['\"]?", linha)
        if m:
            fim, abertura = m.group(1), linha
        elif re.search(r"@'\s*$", linha):
            fim, abertura = "'@", linha
        elif re.search(r'@"\s*$', linha):
            fim, abertura = '"@', linha
    if fim is not None:
        corpos.append((abertura, "\n".join(corpo)))
    return "\n".join(saida), corpos


def _trechos(texto, bash):
    """[[comando do pipeline, ...], ...]: separa por ; && || e quebra de linha, e o pipeline por |, fora de aspas.

    No PowerShell, { e } também separam comandos, mas no mesmo pipeline (o bloco de um ForEach-Object segue a lista)."""
    seqs, pipe, atual, aspas, i = [], [], [], None, 0
    while i < len(texto):
        c = texto[i]
        if bash and c == "\\" and aspas != "'" and i + 1 < len(texto):
            atual.append(texto[i:i + 2])  # caractere escapado no bash não abre aspas nem separa
            i += 2
            continue
        if aspas:
            aspas = None if c == aspas else aspas
        elif c in "\"'":
            aspas = c
        elif texto.startswith(("&&", "||"), i) or c in ";\n":
            pipe.append("".join(atual))
            seqs.append(pipe)
            pipe, atual = [], []
            i += 2 if texto.startswith(("&&", "||"), i) else 1
            continue
        elif (c == "|" and not (i and texto[i - 1] == ">")) or (not bash and c in "{}"):  # >| é redirecionamento
            pipe.append("".join(atual))
            atual = []
            i += 1
            continue
        atual.append(c)
        i += 1
    pipe.append("".join(atual))
    seqs.append(pipe)
    return seqs


def _brutas(trecho):
    return re.findall(r"\"[^\"]*\"|'[^']*'|[^\s\"']+(?:\"[^\"]*\"|'[^']*')?", trecho)


def _palavras(trecho):
    """Palavras do comando, sem aspas, parênteses e chaves das pontas, e sem os redirecionamentos."""
    saida, pular = [], False
    for w in _brutas(trecho):
        if pular:
            pular = False
            continue
        if re.fullmatch(r"(\d|&|\*)?>>?\|?|<", w):
            pular = True
            continue
        if re.match(r"^((\d|&|\*)?>>?|<)", w):
            continue
        w = w.strip("@(){};")
        if len(w) > 1 and w[0] == w[-1] and w[0] in "\"'":
            w = w[1:-1]
        if w:
            saida.append(w)
    return saida


def _redirecionados(trecho):
    """Alvos de > (e >|, &>, *>) fora de aspas; >> acrescenta e fica livre."""
    toks = re.findall(r"\"[^\"]*\"|'[^']*'|[^\s\"']+", trecho)
    for k, tok in enumerate(toks):
        if tok[:1] in "\"'":
            continue
        m = re.search(r"(?<!>)(\d|&|\*)?>(?![>&])\|?(.*)$", tok)
        if not m or (m.group(1) or "") not in ("", "1", "&", "*"):
            continue
        yield m.group(2) or (toks[k + 1] if k + 1 < len(toks) else "")


def _verbo(palavra):
    v = os.path.basename(palavra.replace("\\", "/")).lower()
    return v[:-4] if v.endswith(".exe") else v


def _origem_destino(resto, ex):
    """(fontes, alvo, nomeados) de cp, mv, Copy-Item, Move-Item, dd, curl, tar e unzip."""
    nomeados, pos, i = {}, [], 0
    while i < len(resto):
        a = resto[i]
        al = a.lower()
        if al in NOMEADOS:
            if i + 1 < len(resto):
                nomeados[al] = resto[i + 1]
            i += 2
            continue
        if al.startswith("--target-directory="):
            nomeados["-t"] = a.split("=", 1)[1]
        elif al.startswith("of="):
            nomeados["of"] = a[3:]
        elif not a.startswith("-"):
            pos.append(a)
        i += 1
    alvo = next((nomeados[k] for k in ("-destination", "-destinationpath", "-t", "--target-directory", "of", "-o",
                                       "--output") if k in nomeados), None)
    fontes = [nomeados[k] for k in ("-path", "-literalpath") if k in nomeados] + pos
    if not alvo and len(fontes) >= 2:
        alvo = fontes.pop()
    return [ex(f) for f in fontes], (ex(alvo) if alvo else None), nomeados


def _atribuicao(trecho, cwd, estado):
    """D=valor (bash) ou $f = valor (PowerShell): guarda o valor. True se o trecho só atribui."""
    m = re.match(r"^\s*\$(\w+)\s*=\s*(.+?)\s*$", trecho)  # PowerShell
    pares = [(m.group(1), m.group(2))] if m else []
    palavras = _brutas(trecho)
    k = 0
    while k < len(palavras) and re.match(r"^\w+=", palavras[k]):  # bash: só as atribuições do começo
        pares.append(tuple(palavras[k].split("=", 1)))
        k += 1
    for nome, valor in pares:
        limpo = valor.strip().strip("\"'")
        if " " not in limpo and not limpo.startswith(("(", "$(")):
            estado["vars"][nome] = limpo  # caminho literal: resolvido depois em $nome
        elif any(_toca_memoria(_expandir(x, cwd, estado["vars"])) for x in _palavras(valor)):
            estado["listas"].add(nome)  # $f = Get-ChildItem <memória>: a variável carrega memórias
    return bool(m) or bool(palavras and k == len(palavras))


def _comando(trecho, cwd, estado, lista_memoria, nivel, bash):
    """(bloqueia, cwd depois do comando, o comando lista ou cita memória) para um comando simples."""
    so_atribui = _atribuicao(trecho, cwd, estado)
    var = estado["var_memoria"]

    def ex(a):
        return _expandir(a, cwd, estado["vars"])

    for alvo in _redirecionados(trecho):
        if _sobrescreve(ex(alvo), []) or ("$" in alvo and var):
            return True, cwd, False
    if so_atribui:
        return False, cwd, False
    args = _palavras(trecho)
    while args:
        primeiro = args[0].lower()
        if primeiro in PREFIXOS or re.match(r"^\w+=", args[0]):
            args = args[1:]
        elif _verbo(args[0]) in ENVOLVEM:
            args = args[1:]
            while args and (args[0].startswith("-") or re.fullmatch(r"\d+[smhd]?", args[0])):
                args = args[1:]
        else:
            break
    if not args:
        return False, cwd, False
    if args[0].startswith("$") and args[0].lstrip("$").split(".")[0] in estado["listas"]:
        return False, cwd, True  # $f | Remove-Item: $f carrega memórias
    verbo = _verbo(args[0])
    resto = args[1:]
    caminhos = [p for p in (ex(a) for a in resto) if p]
    cita = any(_toca_memoria(p) for p in caminhos)
    usa_var = var and any("$" in a for a in resto)
    posicionais = [a for a in resto if not a.startswith("-")]
    if verbo in MUDAM_DIR:
        destino = ex(posicionais[0]) if posicionais else _normal(CASA)
        if verbo in ("pushd", "push-location"):
            estado["pilha"].append(cwd)
        return False, (destino or cwd).rstrip("\\/") or cwd, False
    if verbo in ("popd", "pop-location"):
        return False, (estado["pilha"].pop() if estado["pilha"] else cwd), False
    if verbo == "eval" and nivel < 3:
        return bool(_analisa(" ".join(resto), cwd, nivel + 1, bash, estado)), cwd, cita
    if verbo == "for":  # bash: for f in <memória>; do rm $f; done
        if "in" in resto and any(_toca_memoria(ex(a)) for a in resto[resto.index("in") + 1:]):
            estado["var_memoria"] = True
        return False, cwd, False
    if verbo == "read" or (verbo == "while" and "read" in resto):
        if lista_memoria:
            estado["var_memoria"] = True  # ls <memória> | while read f; do rm "$f"
        return False, cwd, False
    if verbo in LACOS:
        de_lista = any(a.lstrip("$").split(".")[0] in estado["listas"] for a in resto if a.startswith("$"))
        if cita or de_lista or (lista_memoria and verbo == "foreach"):
            estado["var_memoria"] = True  # foreach ($f in <memória>) { Remove-Item $f }: $f carrega memórias
        return (lista_memoria or cita or var or de_lista) and bool(VERBO_APAGA.search(trecho)), cwd, cita or lista_memoria or de_lista
    if (verbo in INTERPRETES or verbo.startswith("python3.")) and verbo not in ("perl", "ruby"):  # -i deles é com o sed
        if verbo.startswith("py") and posicionais and _verbo(posicionais[0]) == "banco.py":
            return False, cwd, False  # o banco é o caminho certo
        codigo = any(a in ("-c", "-e") for a in resto)
        cita_codigo = _cita_projects(trecho) or _dentro_da_memoria(cwd)
        apaga = PY_APAGA.search(trecho[:20000]) or JS_APAGA.search(trecho[:20000])
        return codigo and cita_codigo and bool(apaga), cwd, cita
    if verbo in ("cmd", "bash", "sh", "zsh", "powershell", "pwsh") and nivel < 3:
        interno_bash = verbo in ("bash", "sh", "zsh")
        for j, a in enumerate(resto):
            if a.lower() in ("/c", "-c", "-command") and j + 1 < len(resto):
                return bool(_analisa(" ".join(resto[j + 1:]), cwd, nivel + 1, interno_bash)), cwd, cita
        if verbo in ("powershell", "pwsh"):  # powershell Remove-Item X, sem -Command
            sobra, j = [], 0
            while j < len(resto):
                if resto[j].lower() in ("-executionpolicy", "-windowstyle", "-file", "-encodedcommand"):
                    j += 2
                    continue
                if not resto[j].startswith("-"):
                    sobra.append(resto[j])
                j += 1
            return bool(sobra and _analisa(" ".join(sobra), cwd, nivel + 1, False)), cwd, cita
        return False, cwd, cita
    if NET.search(trecho) and (_cita_projects(trecho) or _dentro_da_memoria(cwd)):
        return True, cwd, False
    if verbo == "xargs":
        sub = [a.lower() for a in posicionais]
        no_lugar = any(re.match(r"^-[a-zA-Z]*i", a) or a.startswith("--in-place") for a in resto)
        apaga = bool(sub) and (sub[0] in APAGAM | MOVEM or (sub[0] in ("sed", "perl") and no_lugar))
        return apaga and lista_memoria, cwd, cita
    if verbo == "find":
        inicio = [ex(a) for a in resto[:next((k for k, a in enumerate(resto) if a.startswith(("-", "(", "!"))), len(resto))]]
        inicio = [p for p in inicio if p] or [cwd]
        negado = {k + 1 for k, a in enumerate(resto) if a in ("-not", "!")}
        nomes = [resto[k + 1] for k, a in enumerate(resto) if a in ("-name", "-iname") and k + 1 < len(resto) and k not in negado]
        # só um filtro positivo com extensão fixa que não é .md (*.jsonl, *.pyc) deixa a memória de fora
        def seguro(n):
            ext = re.search(r"\.([A-Za-z0-9]{1,10})['\"]?$", n)
            return bool(ext) and ext.group(1).lower() != "md" and "*" not in n.split(".")[-1]
        tem_ou = any(a in ("-o", "-or") for a in resto)
        nome_negado = any(resto[k] in ("-name", "-iname") for k in negado if k < len(resto))
        pode_ter_md = not nomes or tem_ou or nome_negado or not all(seguro(n) for n in nomes)
        so_pastas_vazias = "-empty" in resto and "d" in [resto[k + 1] for k, a in enumerate(resto) if a == "-type" and k + 1 < len(resto)]
        exclui = (any(a in ("-not", "!") and k + 2 < len(resto) and "memory" in resto[k + 2] for k, a in enumerate(resto))
                  and not tem_ou) or so_pastas_vazias
        profundidade = next((int(resto[k + 1]) for k, a in enumerate(resto) if a == "-maxdepth" and k + 1 < len(resto)
                             and resto[k + 1].isdigit()), None)
        raiz = _normal(os.path.join(CLAUDE, "projects"))

        def ao_alcance(p):
            if profundidade is None or not _toca_memoria(p):
                return True
            partes = _partes(p)
            if partes is not None:
                falta = 3 - len(partes)
            else:
                rel = os.path.relpath(raiz, p.rstrip("\\/") or os.sep)
                falta = (0 if rel == "." else len(rel.split(os.sep))) + 3
            return profundidade >= falta  # memória fica em projects/<projeto>/memory/<arquivo>
        # pasta acima da memória (a home, projects): só conta se o filtro pode pegar um .md da memória
        alcanca = any(_dentro_da_memoria(p) for p in inicio) or (
            any(_toca_memoria(p) and ao_alcance(p) for p in inicio) and pode_ter_md and not exclui)
        apaga = "-delete" in resto
        for k, a in enumerate(resto):
            if a in ("-exec", "-execdir") and k + 1 < len(resto):
                sub = _verbo(resto[k + 1])
                no_lugar = any(re.match(r"^-[a-zA-Z]*i", x) or x.startswith("--in-place") for x in resto[k + 2:])
                apaga = apaga or sub in APAGAM | MOVEM or (sub in ("sed", "perl") and no_lugar)
        return apaga and alcanca, cwd, alcanca
    if verbo in LISTAM and not caminhos and _dentro_da_memoria(cwd):
        return False, cwd, True  # cd <memória>; ls | xargs rm
    item_do_pipe = any(re.match(r"^\$(_|psitem)\b", a, re.I) for a in resto)
    if verbo in APAGAM:
        return cita or usa_var or (lista_memoria and (not caminhos or item_do_pipe)), cwd, cita
    if verbo in MOVEM:
        fontes, alvo, _ = _origem_destino(resto, ex)
        sai = any(_toca_memoria(f) for f in fontes if f)
        return sai or _sobrescreve(alvo, fontes) or usa_var or (lista_memoria and not fontes), cwd, cita
    if verbo in COPIAM or verbo in ("dd", "curl", "wget", "sort"):
        fontes, alvo, _ = _origem_destino(resto, ex)
        if verbo == "wget" and "-O" in resto and resto.index("-O") + 1 < len(resto):
            alvo = ex(resto[resto.index("-O") + 1])
        if verbo == "sort":
            alvo = ex(next((resto[k + 1] for k, a in enumerate(resto) if a == "-o" and k + 1 < len(resto)), ""))
            fontes = []
        apaga_resto = verbo == "rsync" and any(a.startswith("--delete") for a in resto) and _toca_memoria(alvo)
        alvo_var = usa_var and bool(posicionais) and "$" in posicionais[-1]
        return apaga_resto or alvo_var or _sobrescreve(alvo, fontes), cwd, cita
    if verbo in DESCOMPACTAM:
        _, alvo, nomeados = _origem_destino(resto, ex)
        destino = ex(nomeados.get("-c") or nomeados.get("-d") or nomeados.get("-destinationpath") or "") or cwd
        extrai = verbo != "tar" or any(re.match(r"^-?[a-zA-Z]*x", a) or a == "--extract" for a in resto)
        return extrai and _dentro_da_memoria(destino) or (extrai and destino != cwd and _toca_memoria(destino)), cwd, cita
    if verbo == "tee":
        if any(a in ("-a", "--append") for a in resto):
            return False, cwd, cita
        return usa_var or any(_sobrescreve(p, []) for p in caminhos), cwd, cita
    if verbo in GRAVAM:
        baixo = [a.lower() for a in resto]
        if "-append" in baixo or (verbo in ("new-item", "ni") and "-force" not in baixo):
            return False, cwd, cita
        nomeado = next((resto[k + 1] for k, a in enumerate(baixo) if a in ("-path", "-literalpath", "-filepath") and k + 1 < len(resto)), None)
        alvo_bruto = nomeado or (posicionais[0] if posicionais else "")
        return _sobrescreve(ex(alvo_bruto), []) or ("$" in alvo_bruto and var), cwd, cita
    if verbo in ("sed", "perl", "ruby", "awk", "gawk"):
        no_lugar = (any(re.match(r"^-[a-zA-Z]*i", a) or a.startswith("--in-place") for a in resto)
                    or (verbo in ("awk", "gawk") and "inplace" in resto))
        return no_lugar and (usa_var or any(_sobrescreve(p, []) for p in caminhos)), cwd, cita
    if verbo == "git":
        pasta, j = cwd, 0
        while j < len(resto) and resto[j].startswith("-"):
            if resto[j] == "-C" and j + 1 < len(resto):
                pasta = ex(resto[j + 1]) or cwd
                j += 1
            j += 1
        sub = resto[j].lower() if j < len(resto) else ""
        if sub not in GIT_REESCREVE:
            return False, cwd, cita
        # caminhos do git são relativos à pasta do repositório (-C), não ao cwd
        alvos = [p for p in (_expandir(a, pasta, estado["vars"]) for a in resto[j + 1:] if not a.startswith("-")) if p]
        dentro_do_claude = _normal(pasta).startswith(_normal(CLAUDE))
        # fora do ~/.claude (a home) só conta caminho que cai na memória; dentro dele, qualquer repositório que a contenha
        return (_dentro_da_memoria(pasta) or any(_dentro_da_memoria(p) for p in alvos)
                or (dentro_do_claude and (_toca_memoria(pasta) or any(_toca_memoria(p) for p in alvos)))), cwd, cita
    return False, cwd, cita


def _corpo_apaga(abertura, corpo, cwd, nivel, estado):
    """O corpo de um heredoc dado a um interpretador apaga ou reescreve memória?"""
    palavras = _palavras(abertura)
    while palavras and (palavras[0].lower() in PREFIXOS or re.match(r"^\w+=", palavras[0])):
        palavras = palavras[1:]
    if not palavras or nivel >= 3:
        return False
    verbo = _verbo(palavras[0])
    if verbo in ("bash", "sh", "zsh"):
        return bool(_analisa(corpo, cwd, nivel + 1, True, estado))
    if verbo in ("pwsh", "powershell"):
        return bool(_analisa(corpo, cwd, nivel + 1, False, estado))
    if verbo in INTERPRETES or verbo.startswith("python3."):
        cita = _cita_projects(corpo) or _dentro_da_memoria(cwd)
        return cita and bool(PY_APAGA.search(corpo[:50000]) or JS_APAGA.search(corpo[:50000]))
    return False


def _analisa(texto, cwd, nivel=0, bash=True, estado=None):
    """O trecho do comando que apaga, move ou sobrescreve memória por fora do banco, ou None."""
    if estado is None:
        estado = {"pilha": [], "var_memoria": False, "vars": {}, "listas": set()}
    if len(texto) > LIMITE_COMANDO:
        texto = texto[:400_000] + "\n" + texto[-100_000:]
    texto = texto.replace("\\\n" if bash else "`\n", " ")  # continuação de linha
    texto, corpos = _sem_heredoc(texto)
    for abertura, corpo in corpos:
        if _corpo_apaga(abertura, corpo, cwd, nivel, estado):
            return abertura.strip()[:200] or "heredoc"
    for sub in re.findall(r"<\(([^()]{0,2000})\)", texto):  # done < <(ls <memória>): a lista vem depois do laço
        if any(_toca_memoria(_expandir(a, cwd, estado["vars"])) for a in _palavras(sub)):
            estado["var_memoria"] = True
    if nivel < 3:  # $(...) e crase: comando dentro de comando
        for sub in re.findall(r"\$\(([^()]{0,2000})\)", texto) + (re.findall(r"`([^`\n]{0,2000})`", texto) if bash else []):
            achou = _analisa(sub, cwd, nivel + 1, bash, estado)
            if achou:
                return achou
    for seq in _trechos(texto, bash):
        lista_memoria = False
        for trecho in seq:
            bloqueia, cwd, cita = _comando(trecho, cwd, estado, lista_memoria, nivel, bash)
            if bloqueia:
                return trecho.strip()[:200] or "comando"
            lista_memoria = lista_memoria or cita
    return None


def _comando_apaga_memoria(comando, cwd, bash=True):
    cwd = str(cwd or "") or os.getcwd()
    dentro = _toca_memoria(_normal(cwd)) or _normal(cwd).startswith(_normal(CLAUDE) + os.sep)
    if not dentro and not PODE_TOCAR.search(comando[:LIMITE_COMANDO]):
        return None  # caminho rápido: o comando nem cita a pasta do Claude
    return _analisa(comando, _normal(cwd), 0, bash)


def _veredito_recente(caminho):
    """(há veredito REMOVER recente para este arquivo, o registro do banco está legível)."""
    try:
        with open(REGISTRO, encoding="utf-8") as f:
            reg = json.load(f)
        if not isinstance(reg, dict):
            raise ValueError("registro não é um objeto")
    except FileNotFoundError:
        return False, True
    except (OSError, ValueError) as erro:
        _log(f"registro.json ilegível: {erro}")
        return False, False
    alvo = os.path.normcase(os.path.realpath(caminho))
    limite = (datetime.datetime.now() - datetime.timedelta(hours=HORAS_VEREDITO)).strftime("%Y-%m-%d %H:%M:%S")
    for ent in reg.values():
        if (isinstance(ent, dict) and ent.get("status") == "remover" and ent.get("historico")
                and os.path.normcase(os.path.realpath(ent.get("origem", ""))) == alvo and ent["historico"][-1][0] >= limite):
            return True, True
    return False, True


def _ler(caminho):
    """Texto do arquivo (UTF-8, com ou sem BOM), ou None se não der para ler com segurança."""
    try:
        with open(caminho, "rb") as f:
            return f.read().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def _mantem_linhas(antigo, novo):
    """Toda linha do texto antigo continua no novo, na mesma ordem (pode crescer no fim ou ganhar linhas no meio)."""
    restantes = iter(l.strip() for l in novo.splitlines())
    return all(any(l in n for n in restantes) for l in (x.strip() for x in antigo.splitlines()) if l)


def _so_insere(antigo, novo):
    """O texto novo é o antigo com coisas inseridas em qualquer ponto: nenhum caractere antigo sumiu nem mudou de ordem."""
    resto = iter(novo)
    return all(c in resto for c in antigo)


def _negar(motivo):
    """Código 2 no PreToolUse bloqueia a ferramenta e mostra o stderr ao Claude."""
    sys.stderr.write(
        f"guardiao-da-memoria bloqueou: {motivo}. Para apagar ou reescrever uma memória, use o banco de recuperação: "
        "banco.py guardar <arquivo> --motivo --prova; um conferente novo; banco.py veredito <id> REMOVER --prova "
        "--conferente; então banco.py apagar <id> ou edite. Acrescentar texto sem tirar nada é livre.\n")
    sys.exit(2)


def trava(e):
    """PreToolUse: memória só sai ou muda pelo banco; criar e acrescentar são livres. Em dúvida, deixa passar."""
    ferramenta = e.get("tool_name") or ""
    entrada = e.get("tool_input") or {}
    if not isinstance(entrada, dict):
        return
    if ferramenta in ("Bash", "PowerShell"):
        trecho = _comando_apaga_memoria(str(entrada.get("command") or ""), e.get("cwd"), ferramenta == "Bash")
        if trecho:
            _negar(f"o comando mexe em memória por fora do banco ({trecho[:120]})")
        return
    if ferramenta not in ("Write", "Edit", "MultiEdit"):
        return
    caminho = re.sub(r"^\\\\\?\\", "", str(entrada.get("file_path") or ""))
    eh_memoria, indice = _memoria(caminho)
    if not eh_memoria or not os.path.exists(caminho):
        return  # memória nova não passa pelo banco
    atual = _ler(caminho)
    if atual is None:
        _log(f"não consegui ler {caminho} como UTF-8; deixei passar")
        return
    atual = atual.replace("\r\n", "\n")
    edicoes = [] if ferramenta == "Write" else (entrada.get("edits") or [entrada])
    pares = [(str(ed.get("old_string") or "").replace("\r\n", "\n"), str(ed.get("new_string") or "").replace("\r\n", "\n"))
             for ed in edicoes if isinstance(ed, dict)]
    if indice:
        links_perdidos, novo = False, atual
        if ferramenta == "Write":
            novo = str(entrada.get("content") or "")
        for (velho, troca), ed in zip(pares, edicoes):
            if velho not in novo:  # não achei o trecho: julgo pelos links do próprio trecho
                links_perdidos = links_perdidos or not set(LINK_INDICE.findall(velho)) <= set(LINK_INDICE.findall(troca))
                continue
            novo = novo.replace(velho, troca) if ed.get("replace_all") else novo.replace(velho, troca, 1)
        if links_perdidos or not set(LINK_INDICE.findall(atual)) <= set(LINK_INDICE.findall(novo)):
            _negar("isso tira ou troca um link do MEMORY.md")
        return
    if ferramenta == "Write":
        novo_texto = str(entrada.get("content") or "")
        if _mantem_linhas(atual, novo_texto) or _so_insere(atual, novo_texto.replace("\r\n", "\n")):
            return
    elif pares and all(_so_insere(velho, troca) for velho, troca in pares):
        return  # Edit que só acrescenta: o texto antigo continua inteiro e na ordem dentro do novo
    recente, legivel = _veredito_recente(caminho)
    if recente:
        return
    if not legivel:
        _negar("o registro do banco (registro.json) está ilegível; conserte o banco antes de reescrever memória")
    _negar(f"isso tira ou troca texto de {os.path.basename(caminho)} sem veredito REMOVER recente no banco")


def principal():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        bruto = sys.stdin.buffer.read().decode("utf-8", "replace")
        e = json.loads(bruto) if bruto.strip() else {}
        if not isinstance(e, dict):
            raise ValueError("entrada do hook não é um objeto JSON")
        {"correcao": correcao, "diario": diario, "inicio": inicio, "trava": trava}[sys.argv[1]](e)
    except Exception:
        try:
            os.makedirs(BANCO, exist_ok=True)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {sys.argv[1:]}\n{traceback.format_exc()}\n")
        except OSError:
            pass
    sys.exit(0)


if __name__ == "__main__":
    principal()
