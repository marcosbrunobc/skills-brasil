"""Travas automáticas (hooks) do guardiao-da-memoria. Nunca bloqueiam: qualquer erro vai para o log e sai com código 0.

  vigia.py correcao   UserPromptSubmit: anota na fila a fala do dono que é pedido para lembrar, correção ou acerto
  vigia.py diario     PreCompact e SessionEnd: grava o diário da sessão (falas, recusas, erros, arquivos editados)
  vigia.py inicio     SessionStart: avisa da fila, da revisão vencida, do índice grande e dos erros já repetidos

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


def principal():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        bruto = sys.stdin.buffer.read().decode("utf-8", "replace")
        e = json.loads(bruto) if bruto.strip() else {}
        if not isinstance(e, dict):
            raise ValueError("entrada do hook não é um objeto JSON")
        {"correcao": correcao, "diario": diario, "inicio": inicio}[sys.argv[1]](e)
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
