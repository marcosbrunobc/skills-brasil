"""Testa vigia.py e os comandos novos do banco.py numa pasta isolada."""
import json, os, shutil, subprocess, sys, tempfile

sys.stdout.reconfigure(encoding="utf-8")
SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
SBX = tempfile.mkdtemp(prefix="sbx-guardiao-")
ENV = dict(os.environ, BANCO_CLAUDE_HOME=SBX)
CWD = os.path.join(SBX, "Proj A")
os.makedirs(CWD)
PROJ = "".join(c if c.isalnum() else "-" for c in CWD)
MEM = os.path.join(SBX, "projects", PROJ, "memory")
os.makedirs(MEM)
falhas = []


def ok(cond, nome):
    print(("OK   " if cond else "FALHA") + " " + nome)
    if not cond:
        falhas.append(nome)


def hook(cmd, entrada):
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "vigia.py"), cmd], input=json.dumps(entrada).encode("utf-8"),
                       capture_output=True, env=ENV, cwd=CWD, timeout=20)
    return r.returncode, r.stdout.decode("utf-8")


def banco(*args):
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "banco.py"), *args], capture_output=True, env=ENV, cwd=CWD, timeout=20)
    return r.returncode, r.stdout.decode("utf-8") + r.stderr.decode("utf-8")


B = os.path.join(SBX, "memoria-recuperacao")

# 1. correção na hora
for texto, esperado in [("você errou de novo o caminho", True), ("ja falei que é 21h", True), ("nao ta funcionando", True),
                        ("faça de novo o vídeo", False), ("ótimo, ficou bom", True),
                        ("<pasted_content id=x>isso está errado</pasted_content> resuma o texto", False),
                        ("não, faz de novo", True)]:
    rc, out = hook("correcao", {"prompt": texto, "cwd": CWD, "session_id": "sess-111"})
    ok(rc == 0 and (("anotado" in out) == esperado), f"correcao {texto!r} -> {esperado}")
rc, out = hook("correcao", {"prompt": "errado, meu cpf 000.000.000-00 e email a@b.com, chave sk-abcdefghijklmnop, dia 28/10/2026",
                            "cwd": CWD, "session_id": "sess-111"})
ultima = open(os.path.join(B, "correcoes.jsonl"), encoding="utf-8").read().strip().splitlines()[-1]
ok("000.000.000-00" not in ultima and "a@b.com" not in ultima and "sk-abc" not in ultima and "28/10/2026" in ultima, "mascara cpf/email/token, mantém data")
rc, out = hook("correcao", "não é um objeto")  # entrada errada: não pode quebrar
ok(rc == 0, "entrada estranha sai com 0")
rc, out = hook("correcao", {})
ok(rc == 0 and out == "", "entrada vazia não anota")

# 2. fila e tratada
rc, out = banco("fila")
ok(out.count(" | ") >= 5 * 3, "fila lista as 5 correções")
ids = [l.split(" | ")[0] for l in out.splitlines() if " | " in l]
rc, out = banco("tratada", ids[0], "--nota", "")
ok(rc != 0 and "vazia" in out, "tratada recusa nota vazia")
rc, out = banco("tratada", "id-inexistente", "--nota", "x")
ok(rc != 0, "tratada recusa id inexistente")
rc, out = banco("tratada", ids[0], "--nota", "virou memória x")
rc, out = banco("fila")
ok(ids[0] not in out and ids[1] in out, "tratada sai da fila")
rc, out = banco("tratada", "todas", "--nota", "teste")
rc, out = banco("fila")
ok("fila vazia" in out, "tratada todas esvazia a fila do projeto")

# 3. diário
transcript = os.path.join(SBX, "projects", PROJ, "t.jsonl")
linhas = [
    {"type": "user", "message": {"role": "user", "content": "você errou de novo a pasta"}},
    {"type": "user", "isMeta": True, "message": {"role": "user", "content": "errado (meta, ignorar)"}},
    {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Edit", "input": {"file_path": "C:/x/a.py"}},
                                                    {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]}},
    {"type": "user", "message": {"content": [{"type": "tool_result", "is_error": True,
                                               "content": "<tool_use_error>ValueError: dado inválido em C:/x/a.py</tool_use_error>"}]}},
    "linha quebrada {",
]
with open(transcript, "w", encoding="utf-8") as f:
    for l in linhas:
        f.write((l if isinstance(l, str) else json.dumps(l, ensure_ascii=False)) + "\n")
rc, out = hook("diario", {"transcript_path": transcript, "session_id": "sess-AAAA1111", "cwd": CWD, "hook_event_name": "PreCompact"})
D = os.path.join(B, "diario")
md = [n for n in os.listdir(D) if n.endswith(".md")]
ok(rc == 0 and len(md) == 1, "diário gravado")
conteudo = open(os.path.join(D, md[0]), encoding="utf-8").read()
ok("errou de novo" in conteudo and "meta" not in conteudo and "C:/x/a.py" in conteudo and "ValueError: dado inválido" in conteudo,
   "diário tem correção, arquivo e erro; ignora meta")
rc, out = hook("diario", {"transcript_path": transcript, "session_id": "sess-AAAA1111", "cwd": CWD, "hook_event_name": "SessionEnd"})
ok(len([n for n in os.listdir(D) if n.endswith(".md")]) == 1, "segunda chamada sem linha nova não repete o diário")
# mesmo erro, outra sessão e outro arquivo
t2 = os.path.join(SBX, "projects", PROJ, "t2.jsonl")
with open(t2, "w", encoding="utf-8") as f:
    f.write(json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "is_error": True,
            "content": [{"type": "text", "text": "ValueError: dado inválido em D:/outro/b.ts"}]}]}}) + "\n")
hook("diario", {"transcript_path": t2, "session_id": "sess-BBBB2222", "cwd": CWD, "hook_event_name": "PreCompact"})
rc, out = banco("repetidos", "--incluir-testes")
ok("2 sessões" in out and "ValueError: dado inválido" in out, "repetidos acha o mesmo erro em 2 sessões")
rc, out = hook("diario", {"transcript_path": os.path.join(SBX, "nao-existe.jsonl"), "session_id": "s"})
ok(rc == 0, "diário sem transcrição sai com 0")

# 4. início e revisão
hook("correcao", {"prompt": "errado de novo", "cwd": CWD, "session_id": "s3"})
rc, out = hook("inicio", {"cwd": CWD, "source": "startup"})
ok("1 item" in out and "vencida (última: nunca)" in out, "início avisa fila e revisão nunca feita")
ok("já se repetiram" in out and "ValueError: dado inválido" in out, "início lembra os erros já repetidos")
rc, out = hook("inicio", {"cwd": CWD, "source": "startup"})
ok("vencida" not in out and "1 item" in out, "aviso de revisão só uma vez por dia")
rc, out = hook("inicio", {"cwd": os.path.join(SBX, "outro"), "source": "startup"})
ok("item" not in out, "outro projeto não vê a fila deste")
rc, out = hook("inicio", {"cwd": CWD, "source": "compact"})
ok("já se repetiram" not in out, "lembrete de erros só no começo de verdade, não após resumo")
banco("revisao-feita")
os.remove(os.path.join(B, "ultimo-aviso-revisao.txt"))
rc, out = hook("inicio", {"cwd": CWD, "source": "startup"})
ok("vencida" not in out, "revisão feita hoje não avisa")
with open(os.path.join(B, "ultima-revisao.txt"), "w") as f:
    f.write("2026-10-01\n")
rc, out = hook("inicio", {"cwd": CWD, "source": "startup"})
ok("vencida (última: 2026-10-01)" in out, "revisão velha avisa")

# 5. duplicadas
for nome, desc, corpo in [("cor-a.md", "Brand colors purple mint palette", "Palette purple #8B5CF6 mint #5FF0C8 for the Guia app icon"),
                          ("cor-b.md", "Brand colors purple and mint palette", "Guia app icon palette purple #8B5CF6 mint #5FF0C8"),
                          ("aniver.md", "Owner birthday", "Birthday is May 3rd")]:
    with open(os.path.join(MEM, nome), "w", encoding="utf-8") as f:
        f.write(f"---\nname: {nome[:-3]}\ndescription: {desc}\nmetadata:\n  type: user\n---\n\n{corpo}\n")
rc, out = banco("duplicadas")
ok("cor-a.md + cor-b.md" in out and "aniver" not in out, "duplicadas acha o par de cores e não o aniversário")

# 6. achados da revisão de 28/10 (rodados direto nas funções)
sys.path.insert(0, SCRIPTS)
os.environ["BANCO_CLAUDE_HOME"] = SBX
sys.dont_write_bytecode = True
import time
import vigia
for texto, esperado in [("corrija o bug do login", False), ("faltou energia hoje", False),
                        ("tente novamente, não entendi a explicação", False), ("Não, eu queria o azul", True),
                        ("voce nao entendeu", True), ("isso nao e o que pedi", True)]:
    ok(vigia.parece_correcao(texto) == esperado, f"parece_correcao {texto!r} -> {esperado}")
for entrada, some, fica in [("senha: Hunter2abc", "Hunter2abc", "senha"),
                            ("postgres://user:Secret1@localhost:5432/db", "Secret1", "localhost"),
                            ("Bearer abcdef1234567890abcd", "abcdef1234", "Bearer"),
                            ("cpf 000.000.000-00 tel (85) 99999-9999", "99999-9999", "cpf"),
                            ("skills-proprias/x quebrou", "[token]", "skills-proprias/x quebrou"),
                            ("2026-10-28 19:33 e 28/10/2026 29/10/2026", "[numero]", "2026-10-28 19:33 e 28/10/2026 29/10/2026")]:
    m = vigia.mascarar(entrada)
    ok(some not in m and fica in m, f"mascarar {entrada!r} -> {m!r}")
ok(vigia.assinatura(r"falhou em C:\Users\ana\Proj A\x.py") == vigia.assinatura(r"falhou em C:\Users\ana\Proj B\x.py"),
   "assinatura igual com caminho que tem espaço")
for nome, texto in [("<br> x20000", "<br>" * 20000 + " errado"), ("<system-reminder> aberto x5000", "<system-reminder>" * 5000 + " errado")]:
    t0 = time.time()
    rc, out = hook("correcao", {"prompt": texto, "cwd": CWD, "session_id": "perf"})
    ok(rc == 0 and time.time() - t0 < 3, f"correcao rápida com {nome} ({time.time() - t0:.2f} s)")
# caixa do drive: a correção gravada com c-- aparece na fila pedida com C--
pasta_t = os.path.join(SBX, "projects", "c--Caixa-teste")
os.makedirs(pasta_t)
hook("correcao", {"prompt": "errado", "transcript_path": os.path.join(pasta_t, "s.jsonl"), "session_id": "cx"})
rc, out = banco("fila", "--projeto", "C--Caixa-teste")
ok("c--Caixa-teste" in out, "fila ignora a caixa da letra do drive")
rc, out = banco("tratada", "todas", "--nota", "teste", "--projeto", "C--CAIXA-TESTE")
ok(out.startswith("1 "), "tratada todas com --projeto em outra caixa")
# claude -p e automações não entram na fila
r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "vigia.py"), "correcao"], capture_output=True, cwd=CWD, timeout=20,
                   input=json.dumps({"prompt": "errado", "cwd": CWD}).encode(), env=dict(ENV, CLAUDE_CODE_ENTRYPOINT="sdk-cli"))
ok(r.stdout == b"", "claude -p (sdk-cli) não anota")
# recusa do dono não é erro; linha incompleta fica para depois
t3 = os.path.join(SBX, "t3.jsonl")
erro_dono = {"type": "user", "message": {"content": [{"type": "tool_result", "is_error": True, "content": "The user doesn't want to proceed with this tool use."}]}}
erro_real = {"type": "user", "message": {"content": [{"type": "tool_result", "is_error": True, "content": "Exit code 1\nTraceback\nValueError: valor ruim"}]}}
with open(t3, "w", encoding="utf-8") as f:
    f.write(json.dumps(erro_dono) + "\n" + json.dumps(erro_real))  # sem \n no fim: ainda sendo gravada
antes = set(os.listdir(D))
hook("diario", {"transcript_path": t3, "session_id": "sess-CCCC3333", "cwd": CWD, "hook_event_name": "PreCompact"})
novos = [n for n in set(os.listdir(D)) - antes if n.endswith(".md")]
txt = "".join(open(os.path.join(D, n), encoding="utf-8").read() for n in novos)
ok("## Recusas do dono" in txt and "## Erros de ferramenta" not in txt and "valor ruim" not in txt,
   "recusa do dono vai para Recusas, não para erros; linha incompleta não é lida")
with open(t3, "a", encoding="utf-8") as f:
    f.write("\n")
hook("diario", {"transcript_path": t3, "session_id": "sess-CCCC3333", "cwd": CWD, "hook_event_name": "SessionEnd"})
novos = [n for n in set(os.listdir(D)) - antes if n.endswith(".md")]
com_erro = [n for n in novos if "ValueError: valor ruim" in open(os.path.join(D, n), encoding="utf-8").read()]
ok(len(novos) == 2 and len(com_erro) == 1, "linha completada entra no diário seguinte, com a última linha do erro")
# 10 abas ao mesmo tempo
procs, antes = [], {n for n in os.listdir(D) if n.endswith(".md")}
for k in range(10):
    tk = os.path.join(SBX, f"c{k}.jsonl")
    with open(tk, "w", encoding="utf-8") as f:
        for _ in range(3000):
            f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Edit", "input": {"file_path": f"C:/p/{k}.py"}}]}}) + "\n")
    procs.append(subprocess.Popen([sys.executable, os.path.join(SCRIPTS, "vigia.py"), "diario"], stdin=subprocess.PIPE, env=ENV, cwd=CWD))
for k, pr in enumerate(procs):
    pr.communicate(json.dumps({"transcript_path": os.path.join(SBX, f"c{k}.jsonl"), "session_id": f"conc-{k}", "cwd": CWD,
                               "hook_event_name": "PreCompact"}).encode(), timeout=60)
novos = {n for n in os.listdir(D) if n.endswith(".md")} - antes
posicoes = [n for n in os.listdir(os.path.join(D, "posicao")) if n.startswith("conc-")]
ok(len(novos) == 10 and len(posicoes) == 10, f"10 abas ao mesmo tempo: {len(novos)} diários, {len(posicoes)} posições")
# revisão apaga diário velho
velho = os.path.join(D, "2026-01-01-000000-velho.md")
open(velho, "w").close()
os.utime(velho, (time.time() - 90 * 86400,) * 2)
rc, out = banco("revisao-feita")
ok(not os.path.exists(velho) and "apagados 1" in out, "revisao-feita apaga diário com mais de 60 dias")

# rodada 2 da revisão
for entrada, some in [("password is hunter2", "hunter2"), ("a senha é Hunter2", "Hunter2"), ("cpf 123 456 789 09", "789"),
                      ("tel 85 99999 9999", "99999"), ("cnpj 12.345.678/0001-90", "0001")]:
    ok(some not in vigia.mascarar(entrada), f"mascarar {entrada!r}")
ok(vigia.assinatura("cat: /x/y: No such file or directory") != vigia.assinatura("cat: /x/y: Permission denied"),
   "assinatura mantém a mensagem depois do caminho")
ok(vigia.parece_correcao("<system-reminder>sem fechar ... errado"), "tag sem fechamento não apaga o resto")
for nome in ("correcoes.jsonl", "correcoes-tratadas.jsonl"):
    if os.path.exists(os.path.join(B, nome)):
        linhas = open(os.path.join(B, nome), encoding="utf-8").read().splitlines()
        with open(os.path.join(B, nome), "w", encoding="utf-8") as f:
            for l in linhas:
                r = json.loads(l)
                if nome.startswith("correcoes-t"):
                    r["data"] = "2026-01-01 00:00:00"
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
rc, out = banco("revisao-feita")
ok("correção(ões) tratadas" in out and not out.split(" e ")[-1].startswith("0 "), f"revisao-feita poda correções tratadas velhas: {out.strip()}")

# 7. ideias das outras skills
for texto, tipo in [("lembre que meu aniversário é 3 de maio", "lembrar"), ("não esqueça: reunião às 21h", "lembrar"),
                    ("perfeito, era isso", "acerto"), ("ficou ótimo", "acerto"), ("você errou", "correcao"),
                    ("faça o relatório", None)]:
    ok(vigia.tipo_da_fala(texto) == tipo, f"tipo_da_fala {texto!r} -> {tipo}")
rc, out = hook("correcao", {"prompt": "lembre que a fila é às 21h", "cwd": CWD, "session_id": "lm"})
ok("pediu para lembrar" in out, "pedido para lembrar entra na fila com aviso próprio")
rc, out = banco("fila")
ok("| lembrar |" in out, "fila mostra o tipo")
t4 = os.path.join(SBX, "t4.jsonl")
with open(t4, "w", encoding="utf-8") as f:
    for r in [{"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "tu1", "name": "Bash", "input": {"command": "rm -rf build"}}]}},
              {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "tu1", "is_error": True,
               "content": "The user doesn't want to proceed with this tool use. The user provided the following reason for the rejection: nunca apague build"}]}},
              {"type": "user", "entrypoint": "sdk-cli", "message": {"content": "errado, isso veio do claude -p"}}]:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
antes = set(os.listdir(D))
hook("diario", {"transcript_path": t4, "session_id": "sess-DDDD4444", "cwd": CWD, "hook_event_name": "PreCompact"})
novo = [n for n in set(os.listdir(D)) - antes if n.endswith(".md")]
txt = open(os.path.join(D, novo[0]), encoding="utf-8").read() if novo else ""
ok("## Recusas do dono" in txt and "Bash: rm -rf build" in txt and "nunca apague build" in txt and "claude -p" not in txt,
   "diário registra recusa com ferramenta e motivo, ignora sdk")
for k, dia in enumerate(["2026-10-20", "2026-10-22", "2026-10-25"]):
    vigia.anexar(vigia.ERROS, {"data": dia + " 10:00", "sessao": f"f{k}", "projeto": PROJ, "assinatura": "erro forte #", "texto": "erro forte 1"})
rc, out = banco("repetidos", "--incluir-testes")
ok("3 dia(s) | FORTE" in out, "repetidos marca FORTE com 3 dias diferentes")
with open(os.path.join(MEM, "MEMORY.md"), "w", encoding="utf-8") as f:
    f.write("- [Cor](cor-a.md) — cor\n- [Some](sumiu.md) — x\n")
with open(os.path.join(MEM, "proj.md"), "w", encoding="utf-8") as f:
    f.write("---\nname: proj\ndescription: d\nmetadata:\n  type: project\n---\n\nEntrega amanhã.\n")
rc, out = banco("saude")
ok("sumiu.md" in out and "órfã): cor-b.md" in out and "sem o motivo" in out and "amanhã" in out,
   "saude acha índice quebrado, órfã, sem motivo e data relativa")
with open(os.path.join(MEM, "MEMORY.md"), "a", encoding="utf-8") as f:
    f.write("- x\n" * 160)
rc, out = hook("inicio", {"cwd": CWD, "source": "resume"})
ok("só lê as 200 primeiras" in out, "início avisa índice grande")
hist = os.path.join(SBX, "projects", "C--Hist", "h1.jsonl")
os.makedirs(os.path.dirname(hist))
with open(hist, "w", encoding="utf-8") as f:
    f.write(json.dumps({"type": "user", "message": {"content": "não repita isso"}}, ensure_ascii=False) + "\n")
antes = set(os.listdir(D))
rc, out = banco("historico", "--dias", "5", "--projeto", "C--Hist")
novo = [n for n in set(os.listdir(D)) - antes if n.endswith(".md")]
txt = open(os.path.join(D, novo[0]), encoding="utf-8").read() if novo else ""
ok("1 transcrição" in out and "Projeto: C--Hist" in txt and "não repita isso" in txt, "historico passa o diário nas transcrições antigas")
rc, out = banco("historico", "--dias", "5", "--projeto", "C--Hist")
ok(len([n for n in set(os.listdir(D)) - antes if n.endswith(".md")]) == 1, "historico de novo não repete o diário")
rc, out = banco("revisao-feita", "--resumo", "juntei cor-a e cor-b")
ok("juntei cor-a e cor-b" in open(os.path.join(B, "revisoes.md"), encoding="utf-8").read(), "revisao-feita registra o resumo")

# 8. revisão das ideias novas (28/10)
for entrada, some in [("curl https://x.io/a?access_token=secretvalue99", "secretvalue99"), ("mysql --password hunter2", "hunter2"),
                      ("curl -u admin:s3cr3t https://x.io", "s3cr3t"), ("export CLIENT_SECRET=abcd1234", "abcd1234"),
                      ("Authorization: Basic dXNlcjpwYXNzd29yZA==", "dXNlcjpw")]:
    ok(some not in vigia.mascarar(entrada), f"mascarar {entrada!r}")
t0 = time.time()
vigia.trecho("a" * 200000)
ok(time.time() - t0 < 1, f"trecho rápido em texto enorme ({time.time() - t0:.2f} s)")
for texto, tipo in [("lembra de rodar os testes antes de commitar", None), ("guarde isso em C:/docs/x.md", None),
                    ("você não lembra de nada, errou", "correcao"), ("não me lembre disso", None),
                    ("lembre-se: sempre acento", "lembrar"), ("nao esquece", "lembrar"), ("nao ficou bom", None),
                    ("perfeito?", None), ("monte um prompt perfeito para um agente", None), ("não está perfeito", None),
                    ("exatamente isso não", None), ("era isso? não", None),
                    ("Atue como designer de produto. " + "Descreva a tela. " * 40 + "Não pode ficar errado.", None)]:
    ok(vigia.tipo_da_fala(texto) == tipo, f"tipo_da_fala {texto[:50]!r} -> {tipo}")
r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "vigia.py"), "inicio"], capture_output=True, cwd=CWD, timeout=20,
                   input=json.dumps({"cwd": os.path.join(SBX, "sdk"), "source": "startup"}).encode(), env=dict(ENV, CLAUDE_CODE_ENTRYPOINT="sdk-cli"))
ok(r.stdout == b"", "início não avisa nada em claude -p")
# data do erro vem da transcrição; "Exit code 1" sem causa não entra; recusa acha a ferramenta lida antes
t5 = os.path.join(SBX, "t5.jsonl")
with open(t5, "w", encoding="utf-8") as f:
    f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "tu9", "name": "Bash", "input": {"command": "git push --force"}}]}}) + "\n")
    f.write(json.dumps({"type": "user", "timestamp": "2026-10-02T09:15:00.000Z", "message": {"content": [{"type": "tool_result", "is_error": True, "content": "Exit code 1\n3 passed\nok"}]}}) + "\n")
    f.write(json.dumps({"type": "user", "timestamp": "2026-10-03T09:15:00.000Z", "message": {"content": [{"type": "tool_result", "is_error": True, "content": "Exit code 1\nlinha\nModuleNotFoundError: No module named x"}]}}) + "\n")
hook("diario", {"transcript_path": t5, "session_id": "sess-EEEE5555", "cwd": CWD, "hook_event_name": "PreCompact"})
regs = [r for r in vigia.ler_jsonl(vigia.ERROS) if r.get("sessao") == "sess-EEE"]
ok(len(regs) == 1 and regs[0]["data"] == "2026-10-03 09:15" and "ModuleNotFoundError" in regs[0]["texto"],
   "erro com a data da transcrição; Exit code sem causa fica de fora")
with open(t5, "a", encoding="utf-8") as f:
    f.write(json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "tu9", "is_error": True,
            "content": "The user doesn't want to proceed with this tool use."}]}}) + "\n")
antes = set(os.listdir(D))
hook("diario", {"transcript_path": t5, "session_id": "sess-EEEE5555", "cwd": CWD, "hook_event_name": "SessionEnd"})
novo = [n for n in set(os.listdir(D)) - antes if n.endswith(".md")]
ok(novo and "Bash: git push --force" in open(os.path.join(D, novo[0]), encoding="utf-8").read(), "recusa acha a ferramenta chamada antes da posição salva")
# poda não quebra registro com U+2028
vigia.anexar(vigia.ERROS, {"data": "2026-10-27 10:00", "sessao": "u2028", "projeto": PROJ, "assinatura": "x", "texto": "colado\u2028da web"})
vigia.anexar(vigia.ERROS, {"data": "2025-01-01 10:00", "sessao": "velho", "projeto": PROJ, "assinatura": "y", "texto": "velho"})
banco("revisao-feita")
sessoes = {r.get("sessao") for r in vigia.ler_jsonl(vigia.ERROS)}
ok("u2028" in sessoes and "velho" not in sessoes, "poda tira o velho e mantém o registro com U+2028")
# lembrete de erros: só do projeto, uma vez por dia
for k in range(2):
    vigia.anexar(vigia.ERROS, {"data": "2026-10-27 10:00", "sessao": f"outro{k}", "projeto": "C--Outro", "assinatura": "z", "texto": "ZeroDivisionError de outro projeto"})
avisos = os.path.join(B, "avisos")
shutil.rmtree(avisos, ignore_errors=True)
rc, out = hook("inicio", {"cwd": CWD, "source": "startup"})
ok("já se repetiram" in out and "ZeroDivisionError" not in out, "lembrete só com erros deste projeto")
rc, out = hook("inicio", {"cwd": CWD, "source": "startup"})
ok("já se repetiram" not in out, "lembrete de erros uma vez por dia")

# 9. ruídos vistos nos diários reais (28/10)
ok(vigia._erro("### Error\nModuleNotFoundError: No module named x") == "ModuleNotFoundError: No module named x", "### Error pula para o erro de verdade")
ok(vigia._erro("[Tool call interrupted: the session ended before this call's result was recorded]") is None, "sessão encerrada não é erro")
t6 = os.path.join(SBX, "projects", PROJ, "t6.jsonl")
with open(t6, "w", encoding="utf-8") as f:
    f.write(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "a1", "name": "Write", "input": {"file_path": "C:/Temp/claude/x/scratchpad/p1.py"}},
        {"type": "tool_use", "id": "a2", "name": "Write", "input": {"file_path": "C:/proj/app.py"}}]}}) + "\n")
antes = set(os.listdir(D))
hook("diario", {"transcript_path": t6, "session_id": "sess-FFFF6666", "cwd": CWD, "hook_event_name": "SessionEnd"})
novo = [n for n in set(os.listdir(D)) - antes if n.endswith(".md")]
txt = open(os.path.join(D, novo[0]), encoding="utf-8").read() if novo else ""
ok("C:/proj/app.py" in txt and "scratchpad" not in txt, "rascunho da sessão fica fora de Arquivos editados")

log = os.path.join(B, "vigia-erros.log")
txt_log = open(log, encoding="utf-8").read() if os.path.exists(log) else ""
ok("PermissionError" not in txt_log, "nenhum PermissionError no log")
print("log do vigia:", txt_log or "(vazio)")
shutil.rmtree(SBX)
print("FALHAS:", falhas or "nenhuma")
