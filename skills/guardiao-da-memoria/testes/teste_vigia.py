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

# 10. trava: memória só sai ou muda pelo banco
def travar(entrada, cwd=CWD):
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "vigia.py"), "trava"], capture_output=True, cwd=CWD, timeout=20,
                       input=json.dumps(dict(entrada, cwd=cwd)).encode("utf-8"), env=ENV)
    return r.returncode, r.stderr.decode("utf-8")
alvo = os.path.join(MEM, "alvo.md")
with open(alvo, "w", encoding="utf-8") as f:
    f.write("---\nname: alvo\n---\n\nlinha um\nlinha dois\n")
indice = os.path.join(MEM, "MEMORY.md")
with open(indice, "w", encoding="utf-8") as f:
    f.write("- [Alvo](alvo.md) — gancho\n- [Cor](cor-a.md) — cor\n")
casos = [
    ("Edit que acrescenta", {"tool_name": "Edit", "tool_input": {"file_path": alvo, "old_string": "linha um", "new_string": "linha um\nlinha nova"}}, 0),
    ("Edit que troca texto", {"tool_name": "Edit", "tool_input": {"file_path": alvo, "old_string": "linha um", "new_string": "linha 1"}}, 2),
    ("MultiEdit com uma troca", {"tool_name": "MultiEdit", "tool_input": {"file_path": alvo, "edits": [
        {"old_string": "linha um", "new_string": "linha um!"}, {"old_string": "linha dois", "new_string": "x"}]}}, 2),
    ("Write de memória nova", {"tool_name": "Write", "tool_input": {"file_path": os.path.join(MEM, "nova.md"), "content": "x"}}, 0),
    ("Write que perde linha", {"tool_name": "Write", "tool_input": {"file_path": alvo, "content": "---\nname: alvo\n---\n\nlinha um\n"}}, 2),
    ("Write que só acrescenta", {"tool_name": "Write", "tool_input": {"file_path": alvo, "content": "---\nname: alvo\n---\n\nlinha um\nlinha dois\nlinha três\n"}}, 0),
    ("índice perde link", {"tool_name": "Edit", "tool_input": {"file_path": indice, "old_string": "- [Cor](cor-a.md) — cor\n", "new_string": ""}}, 2),
    ("índice muda texto, mantém link", {"tool_name": "Edit", "tool_input": {"file_path": indice, "old_string": "— cor", "new_string": "— cores da marca"}}, 0),
    ("Edit fora da memória", {"tool_name": "Edit", "tool_input": {"file_path": os.path.join(SBX, "x.md"), "old_string": "a", "new_string": "b"}}, 0),
    ("Read não é com ela", {"tool_name": "Read", "tool_input": {"file_path": alvo}}, 0),
    ("rm na memória", {"tool_name": "Bash", "tool_input": {"command": f'rm "{alvo}"'}}, 2),
    ("rm -rf na pasta", {"tool_name": "Bash", "tool_input": {"command": f'rm -rf "{MEM}"'}}, 2),
    ("mv da memória", {"tool_name": "Bash", "tool_input": {"command": f'mv "{alvo}" /tmp/x.md'}}, 2),
    ("sed -i no índice", {"tool_name": "Bash", "tool_input": {"command": f"sed -i 's/a/b/' \"{indice}\""}}, 2),
    ("> sobrescreve", {"tool_name": "Bash", "tool_input": {"command": f'echo x > "{alvo}"'}}, 2),
    (">> acrescenta", {"tool_name": "Bash", "tool_input": {"command": f'echo x >> "{alvo}"'}}, 0),
    ("find -delete", {"tool_name": "Bash", "tool_input": {"command": f'find "{MEM}" -name "*.md" -delete'}}, 2),
    ("python os.remove", {"tool_name": "Bash", "tool_input": {"command": f"python -c \"import os; os.remove(r'{alvo}')\""}}, 2),
    ("cat para fora", {"tool_name": "Bash", "tool_input": {"command": f'cat "{alvo}" > /tmp/copia.md 2>/dev/null'}}, 0),
    ("grep -ri na memória", {"tool_name": "Bash", "tool_input": {"command": f'grep -ri "linha" "{MEM}" 2>&1 | head'}}, 0),
    ("banco.py apagar", {"tool_name": "Bash", "tool_input": {"command": f'python banco.py guardar "{alvo}" --motivo m --prova p'}}, 0),
    ("banco e rm juntos", {"tool_name": "Bash", "tool_input": {"command": f'python banco.py listar; rm "{alvo}"'}}, 2),
    ("Remove-Item no PowerShell", {"tool_name": "PowerShell", "tool_input": {"command": f'Remove-Item "{alvo}"'}}, 2),
    ("cp por cima da memória", {"tool_name": "Bash", "tool_input": {"command": f'cp /tmp/x.md "{alvo}"'}}, 2),
]
for nome, entrada, esperado in casos:
    rc, err = travar(entrada)
    ok(rc == esperado and (("bloqueou" in err) == (esperado == 2)), f"trava: {nome} -> {esperado} (deu {rc})")
rc, err = travar({"tool_name": "Bash", "tool_input": {"command": "rm alvo.md"}}, cwd=MEM)
ok(rc == 2, "trava: rm relativo de dentro da pasta de memória")
r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "vigia.py"), "trava"], capture_output=True, cwd=CWD, timeout=20, input=b"[1,2]", env=ENV)
ok(r.returncode == 0, "trava: entrada estranha deixa passar")
rc, out = banco("guardar", alvo, "--motivo", "trocar linha um", "--prova", "teste")
ident = out.strip().splitlines()[-1]
banco("veredito", ident, "REMOVER", "--prova", "teste", "--conferente", "haiku")
rc, err = travar({"tool_name": "Edit", "tool_input": {"file_path": alvo, "old_string": "linha um", "new_string": "linha 1"}})
ok(rc == 0, "trava: com veredito REMOVER recente, a troca passa")
t0 = time.time()
travar({"tool_name": "Bash", "tool_input": {"command": "git status"}})
ok(time.time() - t0 < 2, f"trava rápida num comando comum ({time.time() - t0:.2f} s)")

# 11. trava v2: casos da revisão de 29/10 (bloqueio falso tem de passar; brecha comum tem de bloquear)
GB = "/" + MEM[0].lower() + MEM[2:].replace("\\", "/")  # a mesma pasta no formato do Git Bash
PROJ_DIR = os.path.dirname(MEM)
passam = [
    ("echo com rm no texto", "Bash", f'echo "ver {alvo} - rm depois"'),
    ("git commit com mv na mensagem", "Bash", f'git commit -m "docs: mv {alvo} note"'),
    ("grep pela palavra rm", "Bash", f'grep -rn rm "{MEM}"'),
    ("heredoc com rm no corpo", "Bash", f"cat > /tmp/nota.txt <<'EOF'\napague com rm {alvo}\nEOF"),
    ("pasta projects/x/memory fora do Claude", "Bash", "rm -rf /c/dev/projects/app/memory/cache.tmp"),
    ("echo > memória nova", "Bash", f'echo hi > "{MEM}/novo-bash.md"'),
    ("heredoc criando memória nova", "Bash", f"cat > \"{MEM}/novo-heredoc.md\" <<'EOF'\nx\nEOF"),
    ("cp de arquivo novo para a pasta", "Bash", f'cp /tmp/inexistente-xyz.md "{MEM}/"'),
    ("Set-Content em outro lugar lendo a memória", "PowerShell", f'Set-Content -Path C:\\t.txt -Value (Get-Content "{alvo}")'),
    ("banco.py com caminho", "Bash", f'python "C:/x/banco.py" guardar "{alvo}" --motivo m --prova p'),
]
bloqueiam = [
    ("cd na pasta e rm relativo", "Bash", f'cd "{MEM}" && rm alvo.md'),
    ("pushd e rm", "Bash", f'pushd "{MEM}" && rm alvo.md'),
    ("Set-Location e Remove-Item", "PowerShell", f'Set-Location "{MEM}"; Remove-Item alvo.md'),
    ("pipeline Get-ChildItem | Remove-Item", "PowerShell", f'Get-ChildItem "{MEM}" | Remove-Item'),
    ("[IO.File]::Delete", "PowerShell", f'[IO.File]::Delete("{alvo}")'),
    ("Copy-Item -Force por cima", "PowerShell", f'Copy-Item C:\\x.md "{alvo}" -Force'),
    ("Copy-Item -Destination", "PowerShell", f'Copy-Item -Destination "{alvo}" -Path C:\\x.md'),
    ("New-Item -Force", "PowerShell", f'New-Item -Force -Path "{alvo}" -Value x'),
    ("rd -Recurse", "PowerShell", f'rd "{MEM}" -Recurse'),
    ("cmd /c del", "Bash", f'cmd /c "del {alvo}"'),
    ("cp -f no formato Git Bash", "Bash", f"cp -f /tmp/x.md {GB}/alvo.md 2>&1"),
    ("install por cima", "Bash", f'install /tmp/x.md "{alvo}"'),
    ("rsync --delete", "Bash", f'rsync -a --delete /tmp/e/ "{MEM}/"'),
    ("git checkout --", "Bash", f'git -C "{MEM}" checkout -- alvo.md'),
    ("dd of=", "Bash", f'dd if=/tmp/x of="{alvo}"'),
    ("perl -pi", "Bash", f"perl -pi -e 's/a/b/' \"{alvo}\""),
    ("sed --in-place", "Bash", f"sed --in-place 's/a/b/' \"{alvo}\""),
    ("curl -o", "Bash", f'curl -o "{alvo}" https://x.io/a'),
    ("ln -sf", "Bash", f'ln -sf /tmp/x "{alvo}"'),
    ("ls | xargs rm", "Bash", f'ls "{MEM}"/*.md | xargs rm'),
    ("rm do projeto inteiro", "Bash", f'rm -rf "{PROJ_DIR}"'),
    ("rm da pasta projects", "Bash", f'rm -rf "{os.path.dirname(PROJ_DIR)}"'),
    ("barras duplas", "Bash", "rm " + alvo.replace("\\", "\\\\")),
    ("banco.py só no comentário", "Bash", f'rm "{alvo}" # banco.py'),
    ("find -exec rm", "Bash", f'find "{MEM}" -name "*.md" -exec rm {{}} \\;'),
]
for nome, ferramenta, comando in passam:
    rc, err = travar({"tool_name": ferramenta, "tool_input": {"command": comando}})
    ok(rc == 0, f"trava v2 deixa passar: {nome} (deu {rc}) {err[:80]}")
for nome, ferramenta, comando in bloqueiam:
    rc, err = travar({"tool_name": ferramenta, "tool_input": {"command": comando}})
    ok(rc == 2, f"trava v2 bloqueia: {nome} (deu {rc})")
rc, err = travar({"tool_name": "Bash", "tool_input": {"command": "ls > /tmp/lista.txt"}}, cwd=MEM)
ok(rc == 0, "trava v2 deixa passar: ls > fora, de dentro da pasta de memória")
rc, err = travar({"tool_name": "Edit", "tool_input": {"file_path": indice, "old_string": "(alvo.md)", "new_string": "(Alvo2.md)"}})
ok(rc == 2, "trava v2 bloqueia: Edit que troca o destino de um link do índice")
bom = os.path.join(MEM, "bom.md")
with open(bom, "wb") as f:
    f.write("\ufeffumа linha\n".encode("utf-8"))
rc, err = travar({"tool_name": "Write", "tool_input": {"file_path": bom, "content": "umа linha\nmais uma\n"}})
ok(rc == 0, "trava v2: memória com BOM aceita Write que só acrescenta")
lat = os.path.join(MEM, "latin.md")
with open(lat, "wb") as f:
    f.write("ação\n".encode("latin-1"))
rc, err = travar({"tool_name": "Write", "tool_input": {"file_path": lat, "content": "ação\nmais\n"}})
ok(rc == 0, "trava v2: arquivo que não é UTF-8 deixa passar e vai para o log")
t0 = time.time()
rc, err = travar({"tool_name": "Bash", "tool_input": {"command": f"python -c \"x='{alvo}'\" " + "open(" * 40000}})
ok(time.time() - t0 < 3, f"trava v2 rápida com 200 KB de open( ({time.time() - t0:.2f} s)")
t0 = time.time()
travar({"tool_name": "Bash", "tool_input": {"command": f"sed {alvo} " * 20000}})
ok(time.time() - t0 < 3, f"trava v2 rápida com 20000 sed ({time.time() - t0:.2f} s)")

# 12. trava v3: casos da rodada 2 da revisão (29/10)
acres = os.path.join(MEM, "acres.md")
with open(acres, "w", encoding="utf-8", newline="\n") as f:
    f.write("---\nname: acres\n---\n\nlinha um\nlinha dois\n")
for nome, entrada, esperado in [
    ("Edit que cresce o fim da linha", {"tool_name": "Edit", "tool_input": {"file_path": acres, "old_string": "linha um", "new_string": "linha um extra"}}, 0),
    ("Edit no name do frontmatter", {"tool_name": "Edit", "tool_input": {"file_path": acres, "old_string": "name: acres", "new_string": "name: acres b"}}, 0),
    ("Write que cresce uma linha", {"tool_name": "Write", "tool_input": {"file_path": acres, "content": "---\nname: acres\n---\n\nlinha um\nlinha dois extra\n"}}, 0),
    ("Edit que tira texto (controle)", {"tool_name": "Edit", "tool_input": {"file_path": acres, "old_string": "linha dois", "new_string": "linha 2"}}, 2),
]:
    rc, err = travar(entrada)
    ok(rc == esperado, f"trava v3: {nome} -> {esperado} (deu {rc})")
alvo_fwd = alvo.replace("\\", "/")
bloqueiam3 = [
    ("if/then", "Bash", f'if true; then rm "{alvo}"; fi'),
    ("chaves", "Bash", f'{{ rm "{alvo}"; }}'),
    ("subshell", "Bash", f'( rm "{alvo}" )'),
    ("subshell com cd", "Bash", f'( cd "{MEM}" && rm alvo.md )'),
    ("negação", "Bash", f'! rm "{alvo}"'),
    ("while/do", "Bash", f'while true; do rm "{alvo}"; done'),
    ("for na pasta", "Bash", f'for f in "{MEM}"/*.md; do rm $f; done'),
    ("python com heredoc", "Bash", f"python - <<'EOF'\nimport os\nos.remove(r'{alvo}')\nEOF"),
    ("node com heredoc", "Bash", f"node <<'EOF'\nrequire('fs').unlinkSync('{alvo_fwd}')\nEOF"),
    ("bash com heredoc", "Bash", f"bash <<'EOF'\nrm \"{alvo}\"\nEOF"),
    ("cp de glob por cima", "Bash", f'cp /tmp/bkp/*.md "{MEM}/"'),
    ("cp -r de pasta/. por cima", "Bash", f'cp -r /tmp/bkp/. "{MEM}/"'),
    ("rsync de pasta por cima", "Bash", f'rsync -a /tmp/e/ "{MEM}/"'),
    ("tar x na pasta", "Bash", f'tar xzf b.tgz -C "{MEM}"'),
    ("unzip na pasta", "Bash", f'unzip -o b.zip -d "{MEM}"'),
    ("Copy-Item de glob -Force", "PowerShell", f'Copy-Item bkp\\*.md "{MEM}" -Force'),
    ("Expand-Archive na pasta", "PowerShell", f'Expand-Archive b.zip -DestinationPath "{MEM}" -Force'),
    ("$( ) com rm", "Bash", f'echo "$(rm {alvo})"'),
    ("continuação de linha", "Bash", "rm \\\n" + alvo),
    ("here-string <<< antes do rm", "Bash", f'cat <<<"hi"\nrm "{alvo}"'),
    ("aspa escapada antes do rm", "Bash", f"echo l\\'oeil; rm \"{alvo}\""),
    ("variável apontando para a pasta", "Bash", f'D="{MEM}"; echo x > $D/alvo.md'),
    ("variável no PowerShell", "PowerShell", f'$f = "{alvo}"; Remove-Item $f'),
    ("rm depois de 100 KB", "Bash", "echo " + "x" * 110000 + f'\nrm "{alvo}"'),
    ("ForEach-Object Remove-Item", "PowerShell", f'gci "{MEM}" | ForEach-Object {{ Remove-Item $_.FullName }}'),
    ("foreach Remove-Item", "PowerShell", f'foreach ($f in gci "{MEM}") {{ Remove-Item $f.FullName }}'),
    ("Remove-Item -Path @()", "PowerShell", f'Remove-Item -Path @("{alvo}")'),
    ("xargs sed -i", "Bash", f"ls \"{MEM}\"/*.md | xargs sed -i 's/a/b/'"),
    ("find -exec sed -i", "Bash", f"find \"{MEM}\" -name \"*.md\" -exec sed -i 's/a/b/' {{}} \\;"),
    (">| força a sobrescrita", "Bash", f'echo x >| "{alvo}"'),
]
for nome, ferramenta, comando in bloqueiam3:
    rc, err = travar({"tool_name": ferramenta, "tool_input": {"command": comando}})
    ok(rc == 2, f"trava v3 bloqueia: {nome} (deu {rc})")
passam3 = [
    ("> dentro de aspas no echo", "Bash", f'echo "use x > {alvo}"'),
    ("> dentro de aspas no commit", "Bash", f"git commit -m 'a > {alvo}'"),
    ("heredoc que só grava um script em /tmp", "Bash", f"cat > /tmp/x.py <<'EOF'\nimport os\nos.remove(r'{alvo}')\nEOF"),
    ("cp de arquivo novo pelo nome", "Bash", f'cp /tmp/bkp/inexistente-abc.md "{MEM}/inexistente-abc.md"'),
    ("rsync de um arquivo novo", "Bash", f'rsync -a /tmp/inexistente-abc.md "{MEM}/inexistente-abc.md"'),
    ("tar listando", "Bash", f'tar tzf "{MEM}/../b.tgz"'),
]
for nome, ferramenta, comando in passam3:
    rc, err = travar({"tool_name": ferramenta, "tool_input": {"command": comando}})
    ok(rc == 0, f"trava v3 deixa passar: {nome} (deu {rc}) {err[:80]}")

# 13. trava v4: revisão nova de 29/10 (a pasta acima da memória, como a home, não pode travar o trabalho)
ACIMA = SBX  # no teste, SBX faz o papel da home: contém projects/<projeto>/memory
HOME_SIM = os.path.dirname(SBX)  # a home real fica acima de ~/.claude (aqui, acima do SBX)
passam4 = [
    ("git checkout na pasta acima", "Bash", "git checkout main", HOME_SIM),
    ("git stash na pasta acima", "Bash", "git stash", HOME_SIM),
    ("git reset --hard na pasta acima", "Bash", "git reset --hard", HOME_SIM),
    ("git clean -fd na pasta acima", "Bash", "git clean -fd", HOME_SIM),
    ("find .pyc -delete na pasta acima", "Bash", "find . -name '*.pyc' -delete", ACIMA),
    ("find tmp* -delete na pasta acima", "Bash", "find . -maxdepth 1 -name 'tmp*' -delete", ACIMA),
    ("limpar transcrições -exec rm", "Bash", f"find \"{SBX}/projects\" -name '*.jsonl' -mtime +30 -exec rm {{}} \\;", CWD),
    ("limpar transcrições -delete", "Bash", f"find \"{SBX}/projects\" -name '*.jsonl' -delete", CWD),
    ("limpar transcrições | xargs rm", "Bash", f"find \"{SBX}/projects\" -name '*.jsonl' | xargs rm", CWD),
    ("variável do projeto e rm de subagents", "Bash", f'D="{PROJ_DIR}"; rm -rf $D/subagents', CWD),
]
for nome, ferramenta, comando, pasta in passam4:
    rc, err = travar({"tool_name": ferramenta, "tool_input": {"command": comando}}, cwd=pasta)
    ok(rc == 0, f"trava v4 deixa passar: {nome} (deu {rc}) {err[:80]}")
bloqueiam4 = [
    ("find . -delete sem filtro na pasta acima", "Bash", "find . -delete", ACIMA),
    ("find .md -delete na pasta acima", "Bash", "find . -name '*.md' -delete", ACIMA),
    ("if do PowerShell", "PowerShell", f"if ($true) {{ Remove-Item '{alvo}' }}", CWD),
    ("try do PowerShell", "PowerShell", f"try {{ Remove-Item '{alvo}' -ErrorAction Stop }} catch {{}}", CWD),
    ("variável listada no PowerShell", "PowerShell", f'$m="{MEM}"; Get-ChildItem $m | Remove-Item', CWD),
    ("variável com Get-ChildItem", "PowerShell", f"$f=Get-ChildItem '{MEM}'; $f | Remove-Item", CWD),
    ("cd e Get-ChildItem | Remove-Item", "PowerShell", f"cd '{MEM}'; Get-ChildItem | Remove-Item", CWD),
    ("cd e ls | xargs rm", "Bash", f'cd "{MEM}" && ls | xargs rm', CWD),
    ("ls | while read; rm", "Bash", f'ls "{MEM}"/*.md | while read f; do rm "$f"; done', CWD),
    ("while read < <(ls)", "Bash", f'while read f; do rm $f; done < <(ls "{MEM}"/*.md)', CWD),
    ("powershell sem -Command", "Bash", f'powershell Remove-Item "{alvo}"', CWD),
    ("timeout antes do rm", "Bash", f'timeout 5 rm "{alvo}"', CWD),
    ("nice antes do rm", "Bash", f'nice rm "{alvo}"', CWD),
    ("eval com rm", "Bash", f"eval 'rm \"{alvo}\"'", CWD),
    ("python -c relativo de dentro da pasta", "Bash", f'cd "{MEM}" && python -c "import os; os.remove(\'alvo.md\')"', CWD),
    ("sort -o por cima", "Bash", f'sort -o "{alvo}" "{alvo}"', CWD),
    ("ruby -i", "Bash", f'ruby -i -pe x "{alvo}"', CWD),
]
for nome, ferramenta, comando, pasta in bloqueiam4:
    rc, err = travar({"tool_name": ferramenta, "tool_input": {"command": comando}}, cwd=pasta)
    ok(rc == 2, f"trava v4 bloqueia: {nome} (deu {rc})")
rc, err = travar({"tool_name": "Edit", "tool_input": {"file_path": "\\\\?\\" + acres, "old_string": "linha dois", "new_string": "linha 2"}})
ok(rc == 2, "trava v4 bloqueia: caminho \\\\?\\ no Edit")
r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "vigia.py"), "trava"], capture_output=True, cwd=CWD, timeout=20, env=ENV,
                   input=json.dumps({"tool_name": "Bash", "cwd": 123, "tool_input": {"command": f'rm "{alvo}"'}}).encode())
ok(r.returncode == 2, "trava v4: cwd que não é texto não libera o rm")
t0 = time.time()
travar({"tool_name": "Write", "tool_input": {"file_path": indice, "content": "](a" * 50000}})
ok(time.time() - t0 < 3, f"trava v4 rápida com ](a x50000 no índice ({time.time() - t0:.2f} s)")

# 14. trava v4.1: rodada 2 da revisão nova (29/10)
PROJS = os.path.join(SBX, "projects")
bloqueiam5 = [
    ("foreach sobre variável que lista memória", "PowerShell", f"$files = Get-ChildItem '{MEM}'; foreach ($f in $files) {{ Remove-Item $f.FullName }}", CWD),
    ("find ! -name *.jsonl -delete", "Bash", f"find \"{PROJS}\" ! -name '*.jsonl' -delete", CWD),
    ("find -not -name *.jsonl -delete", "Bash", f"find \"{PROJS}\" -not -name '*.jsonl' -delete", CWD),
    ("find -name a* -delete", "Bash", f"find \"{PROJS}\" -name 'a*' -delete", CWD),
    ("find com -o e .md", "Bash", f"find \"{PROJS}\" -not -path '*memory*' -o -name '*.md' -delete", CWD),
    ("git -C projeto checkout -- memory/x", "Bash", f'git -C "{PROJ_DIR}" checkout -- memory/alvo.md', CWD),
    ("git clean no projeto", "Bash", f'cd "{PROJ_DIR}" && git clean -fdx', CWD),
]
for nome, ferramenta, comando, pasta in bloqueiam5:
    rc, err = travar({"tool_name": ferramenta, "tool_input": {"command": comando}}, cwd=pasta)
    ok(rc == 2, f"trava v4.1 bloqueia: {nome} (deu {rc})")
passam5 = [
    ("find de pastas vazias", "Bash", f"find \"{PROJS}\" -type d -empty -delete", CWD),
    ("find *.jsonl com -maxdepth", "Bash", f"find \"{PROJS}\" -maxdepth 2 -name '*.jsonl' -delete", CWD),
    ("find a* com -maxdepth 1 em projects", "Bash", f"find \"{PROJS}\" -maxdepth 1 -name 'a*' -delete", CWD),
    ("git checkout main na pasta acima", "Bash", "git checkout main", HOME_SIM),
]
for nome, ferramenta, comando, pasta in passam5:
    rc, err = travar({"tool_name": ferramenta, "tool_input": {"command": comando}}, cwd=pasta)
    ok(rc == 0, f"trava v4.1 deixa passar: {nome} (deu {rc}) {err[:80]}")
rc, err = travar({"tool_name": "Bash", "tool_input": {"command": f"find \"{PROJS}\" -maxdepth 3 -name 'a*' -delete"}})
ok(rc == 2, "trava v4.1 bloqueia: find a* com -maxdepth 3 em projects (alcança a memória)")
t0 = time.time()
travar({"tool_name": "Bash", "tool_input": {"command": "echo a\n" * 300000}})
ok(time.time() - t0 < 5, f"trava v4.1: 2 MB de comando em menos de 5 s ({time.time() - t0:.2f} s)")

# 15. inserção no meio do trecho é acréscimo (bloqueio falso visto ao vivo em 29/10)
with open(acres, "w", encoding="utf-8", newline="\n") as f:
    f.write("---\nname: acres\n---\n\nantes do ponto. depois do ponto\n")
for nome, entrada, esperado in [
    ("Edit que insere frase no meio do trecho", {"tool_name": "Edit", "tool_input": {"file_path": acres,
        "old_string": "antes do ponto. depois do ponto", "new_string": "antes do ponto. FRASE NOVA. depois do ponto"}}, 0),
    ("Write que insere no meio da linha", {"tool_name": "Write", "tool_input": {"file_path": acres,
        "content": "---\nname: acres\n---\n\nantes do ponto. NOVO. depois do ponto\n"}}, 0),
    ("Edit que tira uma palavra do meio", {"tool_name": "Edit", "tool_input": {"file_path": acres,
        "old_string": "antes do ponto. depois do ponto", "new_string": "antes do ponto. do ponto"}}, 2),
    ("Edit que troca a ordem", {"tool_name": "Edit", "tool_input": {"file_path": acres,
        "old_string": "antes do ponto. depois do ponto", "new_string": "depois do ponto. antes do ponto"}}, 2),
]:
    rc, err = travar(entrada)
    ok(rc == esperado, f"trava v4.2: {nome} -> {esperado} (deu {rc})")

log = os.path.join(B, "vigia-erros.log")
txt_log = open(log, encoding="utf-8").read() if os.path.exists(log) else ""
ok("PermissionError" not in txt_log, "nenhum PermissionError no log")
print("log do vigia:", txt_log or "(vazio)")
shutil.rmtree(SBX)
print("FALHAS:", falhas or "nenhuma")
