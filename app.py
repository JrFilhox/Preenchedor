import logging
import os
import random
import shutil
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Dict, List, Optional

from playwright.sync_api import Page, sync_playwright


# Logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("execucao.log", encoding="utf-8")],
        force=True,
    )


def preparar_estrutura_padrao():
    Path("emails/processados").mkdir(parents=True, exist_ok=True)
    Path("html").mkdir(parents=True, exist_ok=True)

    arquivos = {
        "ips.txt": ["127.0.0.1 example.com"],
        "sender_emails.txt": ["contato"],
        "sender_nomes.txt": ["Central de negociacao"],
        "assuntos.txt": ["Atualização de Cadastro"],
    }
    for arquivo, linhas in arquivos.items():
        if not Path(arquivo).exists():
            Path(arquivo).write_text("\n".join(linhas), encoding="utf-8")
            logging.info(f"Arquivo criado: {arquivo}")

    html_exemplo = Path("html/mensagem_exemplo.html")
    if not html_exemplo.exists():
        html_exemplo.write_text(
            """
        <html>
            <body>
                <h1>Mensagem de Teste</h1>
                <p>Este é um conteúdo HTML de exemplo.</p>
            </body>
        </html>
        """.strip(),
            encoding="utf-8",
        )
        logging.info("Arquivo de exemplo HTML criado: html/mensagem_exemplo.html")


def ler_arquivo_linhas(caminho: str) -> List[str]:
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    except Exception as e:
        logging.error(f"Erro lendo {caminho}: {e}")
        return []


def ler_arquivo_conteudo(caminho: str) -> str:
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logging.error(f"Erro lendo {caminho}: {e}")
        return ""


def ler_links() -> List[str]:
    """Lê todos os links do arquivo links.txt"""
    try:
        with open("links.txt", "r", encoding="utf-8") as f:
            return [linha.strip() for linha in f if linha.strip() and not linha.strip().startswith("#")]
    except FileNotFoundError:
        logging.error("Arquivo links.txt não encontrado!")
        return []
    except Exception as e:
        logging.error(f"Erro ao ler links.txt: {e}")
        return []


def listar_arquivos_txt(pasta: str) -> List[Path]:
    p = Path(pasta)
    return sorted([f for f in p.iterdir() if f.is_file() and f.suffix == ".txt"])


def listar_arquivos_html(pasta: str) -> List[Path]:
    p = Path(pasta)
    return sorted([f for f in p.iterdir() if f.is_file() and f.suffix == ".html"])


def mover_para_processados(arquivo: Path):
    destino = Path("emails/processados") / arquivo.name
    try:
        shutil.move(str(arquivo), str(destino))
        logging.info(f"Arquivo movido para processados: {arquivo.name}")
    except Exception as e:
        logging.error(f"Erro ao mover {arquivo.name}: {e}")


def preencher_formulario(
    page: Page,
    dados: Dict[str, str],
    locs: Dict[str, str],
    emails: str,
    botao: str,
    clicar_enviar: bool,
    link_atual: str = "",
    callback_log: Optional[Callable[[str], None]] = None,
):
    try:
        time.sleep(1)
        if dados.get("sender_email"):
            page.fill('//*[@id="senderEmail"]', dados["sender_email"])
            time.sleep(1)
        if dados.get("sender_name"):
            page.fill('//*[@id="senderName"]', dados["sender_name"])
            time.sleep(1)
        if dados.get("subject"):
            page.fill('//*[@id="subject"]', dados["subject"])
            time.sleep(1)
        if dados.get("html"):
            html_content = dados["html"].replace("[LINK]", link_atual)
            page.fill('//*[@id="messageLetter"]', html_content)
            time.sleep(1)
        if emails:
            page.focus("#emailList")
            page.evaluate(
                """
                (emails) => {
                    const textarea = document.querySelector("#emailList");
                    textarea.value = emails;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                }
            """,
                emails,
            )
            time.sleep(2)
        if clicar_enviar:
            if callback_log:
                callback_log("Envio automático desativado. Botão de envio não será clicado.")
    except Exception as e:
        logging.error(f"Erro ao preencher a aba: {e}")
        if callback_log:
            callback_log("[ERRO] Ocorreu uma falha ao preencher uma aba. Veja detalhes no execucao.log")


def rodar_automacao(
    clicar_enviar: bool = False,
    callback_progresso: Optional[Callable[[int, int], None]] = None,
    callback_log: Optional[Callable[[str], None]] = None,
    callback_status: Optional[Callable[[str], None]] = None,
):
    links = ler_links()
    link_index = 0

    ips = ler_arquivo_linhas("ips.txt")
    nomes = ler_arquivo_linhas("sender_nomes.txt")
    prefixos = ler_arquivo_linhas("sender_emails.txt")
    assuntos = ler_arquivo_linhas("assuntos.txt")
    arquivos_html = listar_arquivos_html("html")
    listas = listar_arquivos_txt("emails")

    locs = {
        "sender_email": "#sender_email",
        "sender_name": "input[name='sender_name']",
        "subject": "input[name='subject']",
        "html": "textarea#html_content",
        "emails": ".email-list-textarea",
    }
    botao_enviar = "button.submit-button"

    if not ips:
        if callback_log:
            callback_log("Nenhum IP encontrado em ips.txt.")
        return

    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()

    for i, linha in enumerate(ips):
        try:
            ip_path, reverso = linha.split()
            url = f"http://{ip_path}"
            page = context.new_page()
            page.goto(url)

            html_path = random.choice(arquivos_html)
            html_content = ler_arquivo_conteudo(str(html_path))

            link_atual = ""
            if links:
                link_atual = links[link_index % len(links)]
                link_index += 1
                logging.info(f"Link usado (posição {link_index}): {link_atual}")
                if callback_log:
                    callback_log(f"[LINK] Usando link {link_index}/{len(links)}: {link_atual}")

            dados = {
                "sender_email": f"{random.choice(prefixos)}@{reverso}",
                "sender_name": random.choice(nomes),
                "subject": random.choice(assuntos),
                "html": html_content,
            }

            arquivo_lista = listas[i % len(listas)]
            emails = ler_arquivo_conteudo(str(arquivo_lista))
            preencher_formulario(
                page,
                dados,
                locs,
                emails,
                botao_enviar,
                clicar_enviar,
                link_atual,
                callback_log,
            )
            mover_para_processados(arquivo_lista)

            if callback_progresso:
                callback_progresso(len(ips), i + 1)
            if callback_status:
                callback_status(f"Processando IP {i + 1} de {len(ips)}: {linha}")
        except Exception as e:
            logging.error(f"Erro no IP {linha}: {e}")
            if callback_log:
                callback_log("[ERRO] Ocorreu um erro ao processar um dos IPs. Veja detalhes no execucao.log")

    if callback_log:
        callback_log("Execução encerrada. O navegador permanecerá aberto para ações manuais.")
    if callback_status:
        callback_status("Execução concluída. Navegador aberto.")


class CaveiraMailerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caveira Mailer – Painel")
        self.geometry("900x600")
        self.configure(bg="#f2f2f2")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#f2f2f2")
        self.style.configure("TLabel", background="#f2f2f2", font=("Segoe UI", 9))
        self.style.configure("TButton", font=("Segoe UI", 9))
        self.style.configure("Heading.TLabel", font=("Segoe UI", 10, "bold"))

        self.tab_buttons = {}
        self.frames: Dict[str, ttk.Frame] = {}

        self._montar_layout()
        self.show_tab("IPs")

    def _montar_layout(self):
        top_bar = ttk.Frame(self)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        tabs = [
            "IPs",
            "Remetentes – Prefixos",
            "Remetentes – Nomes",
            "Assuntos",
            "Links",
            "HTML",
            "Listas de e-mails",
            "Execução & Log",
        ]

        for tab in tabs:
            btn = ttk.Button(top_bar, text=tab, command=lambda t=tab: self.show_tab(t))
            btn.pack(side=tk.LEFT, padx=3)
            self.tab_buttons[tab] = btn

        self.content = ttk.Frame(self)
        self.content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.status_var = tk.StringVar(value="Pronto.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.frames["IPs"] = self._criar_editor_simples("ips.txt", "IPs")
        self.frames["Remetentes – Prefixos"] = self._criar_editor_simples("sender_emails.txt", "Remetentes – Prefixos")
        self.frames["Remetentes – Nomes"] = self._criar_editor_simples("sender_nomes.txt", "Remetentes – Nomes")
        self.frames["Assuntos"] = self._criar_editor_simples("assuntos.txt", "Assuntos")
        self.frames["Links"] = self._criar_editor_simples("links.txt", "Links")
        self.frames["HTML"] = self._criar_aba_html()
        self.frames["Listas de e-mails"] = self._criar_aba_listas()
        self.frames["Execução & Log"] = self._criar_aba_execucao()

    def _criar_editor_simples(self, caminho: str, titulo: str) -> ttk.Frame:
        frame = ttk.Frame(self.content)
        ttk.Label(frame, text=titulo, style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 5))
        text_widget = self._criar_text_widget(frame)
        text_widget.insert("1.0", ler_arquivo_conteudo(caminho))

        def salvar():
            try:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write(text_widget.get("1.0", tk.END).rstrip("\n"))
                self._atualizar_status(f"{caminho} salvo.")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar {caminho}: {e}")

        ttk.Button(frame, text="Salvar", command=salvar).pack(anchor=tk.E, pady=5)
        return frame

    def _criar_aba_html(self) -> ttk.Frame:
        frame = ttk.Frame(self.content)
        ttk.Label(frame, text="Arquivos HTML", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 5))

        container = ttk.Frame(frame)
        container.pack(fill=tk.BOTH, expand=True)

        self.html_listbox = tk.Listbox(container, exportselection=False)
        self.html_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.html_listbox.bind("<<ListboxSelect>>", self._carregar_html_selecionado)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.html_listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.html_listbox.config(yscrollcommand=scrollbar.set)

        self.html_text = self._criar_text_widget(container)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Salvar", command=self._salvar_html).pack(side=tk.RIGHT, padx=3)
        ttk.Button(btn_frame, text="Novo HTML", command=self._novo_html).pack(side=tk.RIGHT)

        self._atualizar_lista_html()
        return frame

    def _criar_aba_listas(self) -> ttk.Frame:
        frame = ttk.Frame(self.content)
        ttk.Label(frame, text="Listas de e-mails", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 5))

        selecao_frame = ttk.Frame(frame)
        selecao_frame.pack(anchor=tk.W, pady=5)

        self.pasta_emails_var = tk.StringVar(value="emails")
        ttk.Radiobutton(selecao_frame, text="Pendentes (emails/)", variable=self.pasta_emails_var, value="emails", command=self._atualizar_lista_emails).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(selecao_frame, text="Processados (emails/processados/)", variable=self.pasta_emails_var, value="emails/processados", command=self._atualizar_lista_emails).pack(side=tk.LEFT, padx=5)

        container = ttk.Frame(frame)
        container.pack(fill=tk.BOTH, expand=True)

        self.emails_listbox = tk.Listbox(container, exportselection=False)
        self.emails_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.emails_listbox.bind("<<ListboxSelect>>", self._carregar_lista_emails)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.emails_listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.emails_listbox.config(yscrollcommand=scrollbar.set)

        self.emails_text = self._criar_text_widget(container)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Salvar", command=self._salvar_lista_emails).pack(side=tk.RIGHT, padx=3)
        ttk.Button(btn_frame, text="Mover para outra pasta", command=self._mover_lista_emails).pack(side=tk.RIGHT)

        self._atualizar_lista_emails()
        return frame

    def _criar_aba_execucao(self) -> ttk.Frame:
        frame = ttk.Frame(self.content)
        ttk.Label(frame, text="Execução & Log", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 5))

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X, pady=5)

        self.iniciar_btn = ttk.Button(controls, text="Iniciar preenchimento", command=self._iniciar_automacao)
        self.iniciar_btn.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, mode="determinate")
        self.progress.pack(fill=tk.X, pady=10)

        self.status_exec_var = tk.StringVar(value="Aguardando execução.")
        ttk.Label(frame, textvariable=self.status_exec_var).pack(anchor=tk.W)

        self.log_text = self._criar_text_widget(frame, height=15)
        self.log_text.config(state=tk.DISABLED)

        return frame

    def _criar_text_widget(self, parent, height: int = 20) -> tk.Text:
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True)
        text_widget = tk.Text(text_frame, wrap=tk.WORD, height=height, font=("Segoe UI", 9))
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)
        return text_widget

    def show_tab(self, tab_name: str):
        for frame in self.frames.values():
            frame.pack_forget()
        frame = self.frames.get(tab_name)
        if frame:
            frame.pack(fill=tk.BOTH, expand=True)
            self._atualizar_status(f"Aba {tab_name} selecionada.")

    def _atualizar_status(self, mensagem: str):
        self.status_var.set(mensagem)

    def _atualizar_lista_html(self):
        self.html_listbox.delete(0, tk.END)
        for arquivo in listar_arquivos_html("html"):
            self.html_listbox.insert(tk.END, arquivo.name)
        if self.html_listbox.size() > 0:
            self.html_listbox.selection_set(0)
            self._carregar_html_selecionado()

    def _carregar_html_selecionado(self, event=None):
        selection = self.html_listbox.curselection()
        if not selection:
            return
        nome_arquivo = self.html_listbox.get(selection[0])
        conteudo = ler_arquivo_conteudo(os.path.join("html", nome_arquivo))
        self.html_text.delete("1.0", tk.END)
        self.html_text.insert("1.0", conteudo)
        self._atualizar_status(f"Editando html/{nome_arquivo}")

    def _salvar_html(self):
        selection = self.html_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um arquivo HTML para salvar.")
            return
        nome_arquivo = self.html_listbox.get(selection[0])
        try:
            with open(os.path.join("html", nome_arquivo), "w", encoding="utf-8") as f:
                f.write(self.html_text.get("1.0", tk.END).rstrip("\n"))
            self._atualizar_status(f"html/{nome_arquivo} salvo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar {nome_arquivo}: {e}")

    def _novo_html(self):
        base_nome = "novo_arquivo"
        indice = 1
        while True:
            nome = f"{base_nome}_{indice}.html"
            caminho = Path("html") / nome
            if not caminho.exists():
                break
            indice += 1
        caminho.write_text("<html>\n  <body>\n    <h1>Título</h1>\n    <p>Conteúdo.</p>\n  </body>\n</html>", encoding="utf-8")
        self._atualizar_lista_html()
        self._atualizar_status(f"Arquivo criado: html/{nome}")

    def _atualizar_lista_emails(self):
        pasta = self.pasta_emails_var.get()
        Path(pasta).mkdir(parents=True, exist_ok=True)
        self.emails_listbox.delete(0, tk.END)
        for arquivo in listar_arquivos_txt(pasta):
            self.emails_listbox.insert(tk.END, arquivo.name)
        if self.emails_listbox.size() > 0:
            self.emails_listbox.selection_set(0)
            self._carregar_lista_emails()
        self.emails_text.delete("1.0", tk.END)

    def _carregar_lista_emails(self, event=None):
        selection = self.emails_listbox.curselection()
        if not selection:
            return
        nome_arquivo = self.emails_listbox.get(selection[0])
        pasta = self.pasta_emails_var.get()
        conteudo = ler_arquivo_conteudo(os.path.join(pasta, nome_arquivo))
        self.emails_text.delete("1.0", tk.END)
        self.emails_text.insert("1.0", conteudo)
        self._atualizar_status(f"Editando {pasta}/{nome_arquivo}")

    def _salvar_lista_emails(self):
        selection = self.emails_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um arquivo de lista para salvar.")
            return
        nome_arquivo = self.emails_listbox.get(selection[0])
        pasta = self.pasta_emails_var.get()
        try:
            with open(os.path.join(pasta, nome_arquivo), "w", encoding="utf-8") as f:
                f.write(self.emails_text.get("1.0", tk.END).rstrip("\n"))
            self._atualizar_status(f"{pasta}/{nome_arquivo} salvo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar {nome_arquivo}: {e}")

    def _mover_lista_emails(self):
        selection = self.emails_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um arquivo para mover.")
            return
        nome_arquivo = self.emails_listbox.get(selection[0])
        pasta_atual = Path(self.pasta_emails_var.get())
        nova_pasta = Path("emails/processados") if pasta_atual == Path("emails") else Path("emails")
        nova_pasta.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(pasta_atual / nome_arquivo), str(nova_pasta / nome_arquivo))
            self._atualizar_status(f"{nome_arquivo} movido para {nova_pasta}.")
            self._atualizar_lista_emails()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível mover {nome_arquivo}: {e}")

    def _iniciar_automacao(self):
        self.iniciar_btn.config(state=tk.DISABLED)
        self.progress.config(value=0, maximum=100)
        self.status_exec_var.set("Iniciando...")
        self._limpar_log()

        thread = threading.Thread(target=self._rodar_automacao_thread, daemon=True)
        thread.start()

    def _rodar_automacao_thread(self):
        try:
            rodar_automacao(
                clicar_enviar=False,
                callback_progresso=self._callback_progresso,
                callback_log=self._callback_log,
                callback_status=self._callback_status,
            )
        finally:
            self.after(0, lambda: self.iniciar_btn.config(state=tk.NORMAL))

    def _callback_progresso(self, total: int, atual: int):
        self.after(0, lambda: self._atualizar_progresso(total, atual))

    def _callback_log(self, mensagem: str):
        self.after(0, lambda: self._registrar_log(mensagem))

    def _callback_status(self, mensagem: str):
        self.after(0, lambda: self.status_exec_var.set(mensagem))

    def _atualizar_progresso(self, total: int, atual: int):
        self.progress.config(maximum=total, value=atual)
        self.status_exec_var.set(f"Processando IP {atual} de {total}.")

    def _registrar_log(self, mensagem: str):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, mensagem + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        logging.info(mensagem)

    def _limpar_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    setup_logging()
    preparar_estrutura_padrao()
    app = CaveiraMailerGUI()
    app.mainloop()
