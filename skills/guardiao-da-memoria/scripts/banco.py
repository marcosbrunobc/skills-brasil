"""Banco de recuperação das memórias do Claude.

Nenhuma memória é apagada ou sobrescrita pelo script sem antes ter uma cópia aqui. Uma memória
só sai de vez depois que um conferente registrou REMOVER, com prova.

Uso:
  python banco.py guardar <arquivo-da-memoria> --motivo "..." --prova "..." [--acrescimo]
  python banco.py veredito <id> REMOVER|MANTER|NAO_VERIFICAVEL --prova "..." --conferente haiku|sonnet-high|opus-high|dono
  python banco.py apagar <id>        # só com veredito REMOVER
  python banco.py restaurar <id>     # devolve a cópia ao lugar de origem
  python banco.py listar [--status em-revisao|remover|manter|conferir-dono|apagado|restaurado]

Fila, diário e revisão (as travas automáticas do vigia.py alimentam a fila e o diário):
  python banco.py fila [--todas] [--projeto P]      # correções do dono ainda não tratadas (deste projeto)
  python banco.py tratada <id...>|todas --nota "..." [--projeto P]
  python banco.py duplicadas [--pasta P] [--limite 0.45]   # pares de memórias parecidas
  python banco.py repetidos [--min 2] [--dias 30] [--projeto P] [--incluir-testes]  # o mesmo erro em sessões diferentes
  python banco.py revisao-feita [--resumo "..."]   # registra a revisão semanal e apaga diário com mais de 60 dias
  python banco.py saude [--projeto P]              # índice quebrado, órfãs, sem motivo, data relativa, tamanho
  python banco.py historico [--dias 30]            # passa o diário pelas transcrições antigas

O banco fica em ~/.claude/memoria-recuperacao (para testes: $BANCO_CLAUDE_HOME/memoria-recuperacao).
Só aceita arquivos dentro de ~/.claude/projects/<projeto>/memory/.
"""
import argparse
import datetime
import filecmp
import json
import os
import re
import shutil
import sys
import time

sys.dont_write_bytecode = True  # sem __pycache__ dentro da skill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vigia  # noqa: E402  (caminhos da fila e do diário, compartilhados com as travas automáticas)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
CLAUDE = os.environ.get("BANCO_CLAUDE_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
BANCO = os.path.join(CLAUDE, "memoria-recuperacao")
REGISTRO = os.path.join(BANCO, "registro.json")
STATUS = {"REMOVER": "remover", "MANTER": "manter", "NAO_VERIFICAVEL": "conferir-dono"}
CONFERENTES = ("haiku", "sonnet-high", "opus-high", "sonnet", "opus", "dono")
FINAIS = ("apagado", "restaurado")


def agora():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def carimbo():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def ler():
    if not os.path.exists(REGISTRO):
        return {}
    with open(REGISTRO, encoding="utf-8") as f:
        return json.load(f)


def gravar(reg):
    os.makedirs(BANCO, exist_ok=True)
    tmp = REGISTRO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=1)
    os.replace(tmp, REGISTRO)


def pasta_de_memoria(caminho):
    """Devolve (projeto, pasta) se o arquivo está numa pasta de memória; senão sai com erro."""
    real = os.path.realpath(caminho)
    raiz = os.path.realpath(os.path.join(CLAUDE, "projects"))
    try:
        rel = os.path.relpath(real, raiz)
    except ValueError:  # outro drive
        rel = ".."
    partes = rel.split(os.sep)
    if rel.startswith("..") or len(partes) != 3 or partes[1] != "memory" or not real.endswith(".md"):
        sys.exit(f"recusado: {caminho} não é um arquivo .md de ~/.claude/projects/<projeto>/memory/")
    if os.path.basename(real) == "MEMORY.md":
        sys.exit("recusado: o índice MEMORY.md não entra no banco sozinho; guarde a memória que ele aponta")
    return partes[0], os.path.dirname(real)


def linha_do_indice(pasta, nome):
    indice = os.path.join(pasta, "MEMORY.md")
    if not os.path.exists(indice):
        return None
    with open(indice, encoding="utf-8") as f:
        for linha in f:
            if f"({nome})" in linha:
                return linha.rstrip("\n")
    return None


def guarda_extra(e, rotulo):
    """Copia o estado atual da origem para o banco, se ele difere da cópia guardada."""
    origem = e["origem"]
    if os.path.isfile(origem) and not filecmp.cmp(origem, e["copia"], shallow=False):
        extra = e["copia"][:-3] + f".{rotulo}-{carimbo()}.md"
        shutil.copy2(origem, extra)
        e.setdefault("extras", []).append(extra)
        e["historico"].append([agora(), f"estado atual guardado como {os.path.basename(extra)}"])


def guardar(a):
    if not a.motivo.strip() or not a.prova.strip():
        sys.exit("recusado: --motivo e --prova não podem ficar vazios")
    if not os.path.isfile(a.arquivo):
        sys.exit(f"não existe: {a.arquivo}")
    projeto, pasta = pasta_de_memoria(a.arquivo)
    nome = os.path.basename(a.arquivo)
    reg = ler()
    ident = carimbo() + "-" + nome[:-3]
    destino = os.path.join(BANCO, projeto, ident + ".md")
    if ident in reg or os.path.exists(destino):
        sys.exit("recusado: id já existe; rode de novo")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copy2(a.arquivo, destino)
    reg[ident] = {
        "origem": os.path.realpath(a.arquivo),
        "copia": destino,
        "indice": linha_do_indice(pasta, nome),
        "motivo": a.motivo,
        "prova": a.prova,
        # acréscimo: só cópia de segurança, sem nada a revisar
        "status": "copia" if a.acrescimo else "em-revisao",
        "historico": [[agora(), "guardado (acréscimo)" if a.acrescimo else "guardado"]],
    }
    gravar(reg)
    print(ident)


def pegar(reg, ident):
    if ident not in reg:
        sys.exit(f"id não encontrado: {ident}")
    e = reg[ident]
    pasta_de_memoria(e["origem"])  # não confia no registro: revalida o caminho
    return e


def veredito(a):
    reg = ler()
    e = pegar(reg, a.id)
    if e["status"] in FINAIS:
        sys.exit(f"recusado: a entrada já está '{e['status']}'")
    if not a.prova.strip():
        sys.exit("recusado: veredito sem prova")
    e["status"] = STATUS[a.veredito]
    e["veredito"] = {"resultado": a.veredito, "prova": a.prova, "conferente": a.conferente, "data": agora()}
    e["historico"].append([agora(), f"veredito {a.veredito} por {a.conferente}"])
    gravar(reg)
    print(a.id, e["status"])


def apagar(a):
    reg = ler()
    e = pegar(reg, a.id)
    if e["status"] != "remover":
        sys.exit(f"recusado: status '{e['status']}'. Só apaga com veredito REMOVER de um conferente.")
    if not os.path.isfile(e["copia"]):
        sys.exit("recusado: a cópia no banco sumiu; não apago o original")
    guarda_extra(e, "final")
    origem = e["origem"]
    pasta = os.path.dirname(origem)
    if os.path.exists(origem):
        os.remove(origem)
    indice = os.path.join(pasta, "MEMORY.md")
    if e.get("indice") and os.path.exists(indice):
        shutil.copy2(indice, e["copia"][:-3] + ".MEMORY.md")
        with open(indice, encoding="utf-8") as f:
            linhas = f.read().split("\n")
        with open(indice, "w", encoding="utf-8") as f:
            f.write("\n".join(l for l in linhas if l != e["indice"]))
    e["status"] = "apagado"
    e["historico"].append([agora(), "apagado do lugar de origem (a cópia fica no banco)"])
    gravar(reg)
    print(a.id, "apagado; cópia em", e["copia"])


def restaurar(a):
    reg = ler()
    e = pegar(reg, a.id)
    guarda_extra(e, "antes-de-restaurar")
    shutil.copy2(e["copia"], e["origem"])
    indice = os.path.join(os.path.dirname(e["origem"]), "MEMORY.md")
    if e.get("indice") and os.path.exists(indice):
        with open(indice, encoding="utf-8") as f:
            texto = f.read()
        if e["indice"] not in texto:
            with open(indice, "a", encoding="utf-8") as f:
                f.write(("" if texto.endswith("\n") else "\n") + e["indice"] + "\n")
    e["status"] = "restaurado"
    e["historico"].append([agora(), "restaurado (a linha do índice volta no fim, se faltava)"])
    gravar(reg)
    print(a.id, "restaurado em", e["origem"])


def listar(a):
    for ident, e in sorted(ler().items()):
        if a.status and e["status"] != a.status:
            continue
        print(f"{ident} | {e['status']} | {e['motivo'][:80]}")


def _projeto(a):
    """O projeto vem do aviso do hook (--projeto); sem ele, da pasta atual."""
    return a.projeto or vigia.projeto(os.getcwd())


def fila(a):
    proj = None if a.todas else _projeto(a)
    itens = vigia.pendentes(proj)
    for c in itens:
        print(f"{c['id']} | {c.get('tipo', 'correcao')} | {c['data']} | {c['projeto']} | {c['texto'][:200]}")
    if not itens:
        print("fila vazia" + ("" if a.todas else " neste projeto (use --todas para ver as outras abas)"))


def tratada(a):
    if not a.nota.strip():
        sys.exit("recusado: --nota não pode ficar vazia (diga o que virou: memória, skill, hook ou nada)")
    pend = {c["id"]: c for c in vigia.pendentes()}
    if a.ids == ["todas"]:
        proj = _projeto(a)
        ids = [i for i, c in pend.items() if vigia.mesmo_projeto(c.get("projeto"), proj)]
    else:
        ids = a.ids
    faltam = [i for i in ids if i not in pend]
    if faltam:
        sys.exit("não estão pendentes: " + ", ".join(faltam))
    for i in ids:
        vigia.anexar(vigia.TRATADAS, {"id": i, "data": agora(), "nota": a.nota})
    print(len(ids), "tratada(s)")


VAZIAS = set("""para como mais that this with from have when what before after only into your they them than
sobre quando antes depois porque também então pelo pela isso esse essa este esta onde cada todo toda nunca sempre
ainda está será foram fica ficou pode deve the and""".split())


def _palavras(t):
    return {w for w in re.findall(r"[a-zà-ü0-9]{4,}", t.lower()) if w not in VAZIAS}


def _parecidas(p1, p2):
    """Palavras em comum sobre o total de palavras dos dois (0 a 1)."""
    return len(p1 & p2) / len(p1 | p2) if p1 | p2 else 0


def duplicadas(a):
    pasta = a.pasta or os.path.join(CLAUDE, "projects", _projeto(a), "memory")
    if not os.path.isdir(pasta):
        sys.exit(f"não existe: {pasta}")
    mems = []
    for nome in sorted(os.listdir(pasta)):
        if not nome.endswith(".md") or nome == "MEMORY.md":
            continue
        with open(os.path.join(pasta, nome), encoding="utf-8") as f:
            texto = f.read()
        partes = texto.split("---", 2)
        corpo = partes[2] if texto.startswith("---") and len(partes) == 3 else texto
        achou = re.search(r"^description:\s*(.*)$", texto, re.M)
        desc = achou.group(1).strip("\"' ").lower() if achou else ""
        mems.append((nome, _palavras(desc), _palavras(desc + " " + corpo)))
    pares = []
    for i, (n1, d1, p1) in enumerate(mems):
        for n2, d2, p2 in mems[i + 1:]:
            texto = _parecidas(p1, p2)
            desc = _parecidas(d1, d2)
            if max(texto, desc) >= a.limite:
                pares.append((max(texto, desc), texto, desc, n1, n2))
    for nota, texto, desc, n1, n2 in sorted(pares, reverse=True):
        print(f"{nota:.2f} | texto {texto:.2f} | descrição {desc:.2f} | {n1} + {n2}")
    if not pares:
        print(f"nenhum par com nota {a.limite} ou mais em {pasta}")


def repetidos(a):
    achados = vigia.erros_repetidos(a.projeto, a.min, a.dias, limite=0, rotina=True, testes=a.incluir_testes)
    for sessoes, dias, texto, ex in achados:
        # claude-diary e memory-engine: 3 vezes em dias diferentes pede regra dura, não prosa
        forte = " | FORTE: vire hook, script ou teste" if dias >= 3 else ""
        print(f"{sessoes} sessões em {dias} dia(s){forte} | última: {ex.get('data')} | {ex.get('projeto')} | {texto[:160]}")
    if not achados:
        print(f"nenhum erro em {a.min} sessões ou mais nos últimos {a.dias} dias")


RELATIVAS = re.compile(r"\b(ontem|anteontem|amanh[aã]|semana que vem|pr[oó]xima semana|m[eê]s que vem|semana passada"
                       r"|yesterday|tomorrow|next week|last week)\b(?!'s)", re.I)
DATA_ABSOLUTA = re.compile(r"\d{4}-\d{2}-\d{2}|\b\d{1,2}/\d{1,2}\b")
CITACAO = re.compile(r"\"[^\"]*\"|“[^”]*”|(?<!\w)'[^'\n]{1,80}'(?!\w)")  # o apóstrofo de "today's" não abre citação


def _data_relativa(texto):
    """Primeira data relativa fora de bloco de código, de citação e de linha que já tem a data certa."""
    dentro_de_codigo = False
    for linha in texto.splitlines():
        if linha.strip().startswith("```"):
            dentro_de_codigo = not dentro_de_codigo
            continue
        if dentro_de_codigo or DATA_ABSOLUTA.search(linha):
            continue
        achou = RELATIVAS.search(CITACAO.sub(" ", linha))
        if achou:
            return achou.group(0)
    return None


def saude(a):
    """Exame mecânico da pasta de memória (ideia do /memory-health do memory-engine e dos órfãos do memory-reflect)."""
    pasta = a.pasta or os.path.join(CLAUDE, "projects", _projeto(a), "memory")
    if not os.path.isdir(pasta):
        sys.exit(f"não existe: {pasta}")
    caminho_indice = os.path.join(pasta, "MEMORY.md")
    indice = open(caminho_indice, encoding="utf-8").read() if os.path.exists(caminho_indice) else ""
    linhas = indice.splitlines()
    arquivos = {n for n in os.listdir(pasta) if n.endswith(".md") and n != "MEMORY.md"}
    apontados = set(re.findall(r"\]\(([^)\s]+\.md)\)", indice))
    achados = []
    if len(linhas) >= vigia.LIMITE_INDICE:
        achados.append(f"índice com {len(linhas)} linhas: o Claude Code só lê as 200 primeiras")
    achados += [f"índice aponta para memória que não existe: {n}" for n in sorted(apontados - arquivos)]
    achados += [f"memória fora do índice (órfã): {n}" for n in sorted(arquivos - apontados)]
    achados += [f"linha do índice com {len(l)} caracteres (deixe em uma linha curta): {l[:60]}..." for l in linhas if len(l) > 200]
    for nome in sorted(arquivos):
        with open(os.path.join(pasta, nome), encoding="utf-8") as f:
            texto = f.read()
        tipo = re.search(r"^\s*type:\s*(\w+)", texto, re.M)
        if tipo and tipo.group(1) in ("feedback", "project") and not re.search(r"\*\*(why|por qu[eê])", texto, re.I):
            achados.append(f"{tipo.group(1)} sem o motivo (**Why:** / **Por quê:**): {nome}")
        rel = _data_relativa(texto)
        if rel:
            achados.append(f"data relativa \"{rel}\" (troque pela data): {nome}")
    for item in achados:
        print("-", item)
    print(f"{len(arquivos)} memórias, {len(linhas)} linhas no índice, {len(achados)} achado(s)")


def historico(a):
    """Passa o diário pelas transcrições antigas (ideia do --scan-history do claude-reflect). Não mexe na fila."""
    raiz = os.path.join(CLAUDE, "projects")
    limite = time.time() - a.dias * 86400
    lidas, falhas = 0, []
    for proj in sorted(os.listdir(raiz)):
        pasta = os.path.join(raiz, proj)
        if not os.path.isdir(pasta) or (a.projeto and not vigia.mesmo_projeto(proj, a.projeto)):
            continue
        for nome in sorted(os.listdir(pasta)):
            arq = os.path.join(pasta, nome)
            if nome.endswith(".jsonl") and os.path.getmtime(arq) >= limite:
                try:
                    vigia.diario({"transcript_path": arq, "session_id": nome[:-6], "hook_event_name": "historico"})
                    lidas += 1
                except Exception as erro:  # uma transcrição ruim não para as outras
                    falhas.append(f"{nome}: {erro}")
    print(f"{lidas} transcrição(ões) lidas (as já lidas antes só andam o que é novo). Veja banco.py repetidos e a pasta diario/.")
    for f in falhas:
        print("falhou:", f)


GUARDAR_DIAS = 60  # diário, posições e erros mais velhos que isso saem na revisão


def revisao_feita(a):
    hoje = datetime.date.today()
    vigia.escrever_texto(vigia.REVISAO, hoje.isoformat())
    if a.resumo.strip():
        # registro de cada revisão (ideia do "Reflection (HH:MM)" do memory-reflect)
        with open(os.path.join(BANCO, "revisoes.md"), "a", encoding="utf-8") as f:
            f.write(f"## {datetime.datetime.now():%Y-%m-%d %H:%M}\n\n{a.resumo.strip()}\n\n")
    limite = time.time() - GUARDAR_DIAS * 86400
    podados = 0
    for pasta in (vigia.DIARIO, vigia.POSICOES):
        if os.path.isdir(pasta):
            for nome in os.listdir(pasta):
                caminho = os.path.join(pasta, nome)
                if nome.endswith((".md", ".txt")) and os.path.getmtime(caminho) < limite:
                    os.remove(caminho)
                    podados += 1
    corte = (hoje - datetime.timedelta(days=GUARDAR_DIAS)).isoformat()
    erros = _podar_jsonl(vigia.ERROS, lambda r: (r.get("data") or "") >= corte)
    # correção tratada há mais de 60 dias sai da fila e do registro; pendente nunca sai
    velhas = {r.get("id") for r in vigia.ler_jsonl(vigia.TRATADAS) if (r.get("data") or "") < corte}
    corr = _podar_jsonl(vigia.FILA, lambda r: r.get("id") not in velhas) if velhas else 0
    if velhas:
        _podar_jsonl(vigia.TRATADAS, lambda r: r.get("id") not in velhas)
    if os.path.exists(vigia.LOG) and os.path.getsize(vigia.LOG) > 512 * 1024:
        with open(vigia.LOG, encoding="utf-8", errors="replace") as f:
            fim = f.read().splitlines()[-2000:]
        vigia.escrever_texto(vigia.LOG, "\n".join(fim))
    print(f"revisão semanal registrada em {hoje}; apagados {podados} arquivo(s) de diário, {erros} erro(s) "
          f"e {corr} correção(ões) tratadas, todos com mais de {GUARDAR_DIAS} dias")


def _podar_jsonl(caminho, fica):
    """Reescreve só com as linhas que ficam; o que um hook anexou durante a poda é mantido. Devolve quantas saíram."""
    if not os.path.exists(caminho):
        return 0
    with open(caminho, encoding="utf-8") as f:
        lidas = [l for l in f.read().split("\n") if l]  # split("\n"), não splitlines: U+2028 não quebra registro
    manter = []
    for linha in lidas:
        try:
            if fica(json.loads(linha)):
                manter.append(linha)
        except ValueError:
            continue
    saiu = len(lidas) - len(manter)
    if not saiu:
        return 0
    with open(caminho, encoding="utf-8") as f:
        manter += [l for l in f.read().split("\n") if l][len(lidas):]  # o que um hook anexou durante a poda
    tmp = f"{caminho}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("".join(linha + "\n" for linha in manter))
    vigia.trocar(tmp, caminho)
    return saiu


p = argparse.ArgumentParser()
s = p.add_subparsers(dest="cmd", required=True)
g = s.add_parser("guardar"); g.add_argument("arquivo"); g.add_argument("--motivo", required=True); g.add_argument("--prova", required=True); g.add_argument("--acrescimo", action="store_true"); g.set_defaults(f=guardar)
v = s.add_parser("veredito"); v.add_argument("id"); v.add_argument("veredito", choices=list(STATUS)); v.add_argument("--prova", required=True); v.add_argument("--conferente", required=True, choices=CONFERENTES); v.set_defaults(f=veredito)
d = s.add_parser("apagar"); d.add_argument("id"); d.set_defaults(f=apagar)
r = s.add_parser("restaurar"); r.add_argument("id"); r.set_defaults(f=restaurar)
l = s.add_parser("listar"); l.add_argument("--status"); l.set_defaults(f=listar)
fi = s.add_parser("fila"); fi.add_argument("--todas", action="store_true"); fi.add_argument("--projeto"); fi.set_defaults(f=fila)
t = s.add_parser("tratada"); t.add_argument("ids", nargs="+"); t.add_argument("--nota", required=True); t.add_argument("--projeto"); t.set_defaults(f=tratada)
du = s.add_parser("duplicadas"); du.add_argument("--pasta"); du.add_argument("--projeto"); du.add_argument("--limite", type=float, default=0.45); du.set_defaults(f=duplicadas)
rp = s.add_parser("repetidos"); rp.add_argument("--min", type=int, default=2); rp.add_argument("--dias", type=int, default=30); rp.add_argument("--projeto"); rp.add_argument("--incluir-testes", action="store_true"); rp.set_defaults(f=repetidos)
rv = s.add_parser("revisao-feita"); rv.add_argument("--resumo", default=""); rv.set_defaults(f=revisao_feita)
sa = s.add_parser("saude"); sa.add_argument("--pasta"); sa.add_argument("--projeto"); sa.set_defaults(f=saude)
hi = s.add_parser("historico"); hi.add_argument("--dias", type=int, default=30); hi.add_argument("--projeto"); hi.set_defaults(f=historico)
a = p.parse_args()
a.f(a)
