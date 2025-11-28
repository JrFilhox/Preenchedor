import os
import sys
import time
import shutil
import logging
import random
from pathlib import Path
from typing import Optional, List, Dict
from playwright.sync_api import sync_playwright, Page

# ANSI cores
class Cor:
    VERMELHO = '\033[91m'
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    AZUL = '\033[94m'
    ROSA = '\033[95m'
    CIANO = '\033[96m'
    BRANCO = '\033[97m'
    RESET = '\033[0m'

def menu_inicial():
    print(f"""
{Cor.VERMELHO}                      :::!~!!!!!:.
                  .xUHWH!! !!?M88WHX:.
                .X*#M@$!!  !X!M$$$$$$WWx:.
               :!!!!!!?H! :!$!$$$$$$$$$$8X:
              !!~  ~:~!! :~!$!#$$$$$$$$$$8X:
             :!~::!H!<   ~.U$X!?R$$$$$$$$MM!
             ~!~!!!!~~ .:XW$$$U!!?$$$$$$RMM!
               !:~~~ .:!M"T#$$$$WX??#MRRMMM!
               ~?WuxiW*`   `"#$$$$8!!!!??!!!
             :X- M$$$$       `"T#$T~!8$WUXU~
            :%`  ~#$$$m:        ~!~ ?$$$$$$
          :!`.-   ~T$$$$8xx.  .xWW- ~""##*"
.....   -~~:<` !    ~?T#$$@@W@*?$$      /`
W$@@M!!! .!~~ !!     .:XUW$W!~ `"~:    :
#"~~`.:x%`!!  !H:   !WM$$$$Ti.: .!WUn+!`
:::~:!!`:X~ .: ?H.!u "$$$B$$$!W:U!T$$M~
.~~   :X@!.-~   ?@WTWo("*$$$W$TH$! `
Wi.~!X$?!-~    : ?$$$B$Wu("**$RM!
$R@i.~~ !     :   ~$$$$$B$$en:``
?MXT@Wx.~    :     ~"##*$$$$M~{Cor.RESET}
{Cor.CIANO}      C A V E I R A{Cor.RESET}
  ╔═══════════════════════╗
  ║ {Cor.VERDE}1{Cor.RESET}  PARA INICIAR       ║
  ║ {Cor.VERMELHO}2{Cor.RESET}  PARA SAIR          ║
  ║ {Cor.AZUL}3{Cor.RESET}  PARA TUTORIAL      ║
  ╚═══════════════════════╝
    """)
    return input("Opção: ")

def exibir_tutorial() -> str:
    print(f"\n{Cor.CIANO}{'='*40}{Cor.RESET}")
    print(f"{Cor.AMARELO}{'           TUTORIAL DE UTILIZAÇÃO'}{Cor.RESET}")
    print(f"{Cor.CIANO}{'='*40}{Cor.RESET}\n")

    print(f"{Cor.VERDE}1. ORGANIZAÇÃO DOS ARQUIVOS:{Cor.RESET}")
    print(f"   - {Cor.AZUL}ips.txt{Cor.RESET}: Cada linha deve conter o IP seguido pelo path (se houver), um espaço, e o reverso do IP.")
    print(f"     Exemplo:")
    print(f"       {Cor.AMARELO}51.195.253.167/blackrock.php vps-ae59c8bf.vps.ovh.net{Cor.RESET}")
    print(f"       {Cor.AMARELO}198.244.150.73 vps-0480c372.vps.ovh.net{Cor.RESET}")
    print(f"   - {Cor.AZUL}sender_emails.txt{Cor.RESET}: Cada linha deve conter a parte do email {Cor.VERMELHO}ANTES{Cor.RESET} do '@'.")
    print(f"     Exemplo:")
    print(f"       {Cor.AMARELO}fernando{Cor.RESET}")
    print(f"       {Cor.AMARELO}notificacoesoficiais{Cor.RESET}")
    print(f"   - {Cor.AZUL}sender_nomes.txt{Cor.RESET}: Cada linha deve conter o nome do remetente.")
    print(f"   - {Cor.AZUL}assuntos.txt{Cor.RESET}: Cada linha deve conter o assunto do email.")
    print(f"   - {Cor.AZUL}html/{Cor.RESET} (pasta): Deve conter arquivos HTML com o corpo do email.")
    print(f"   - {Cor.AZUL}emails/{Cor.RESET} (pasta): Contém arquivos .txt, cada um com a lista de emails de destino (um por linha).\n")

    print(f"{Cor.VERDE}2. CONCATENAÇÃO DO EMAIL DO REMETENTE:{Cor.RESET}")
    print(f"   O programa gera o '{Cor.AZUL}Sender Email Address{Cor.RESET}' da seguinte forma:")
    print(f"   - Escolhe aleatoriamente uma entrada do arquivo '{Cor.AZUL}sender_emails.txt{Cor.RESET}'.")
    print(f"   - Adiciona o símbolo '{Cor.VERMELHO}@{Cor.RESET}'.")
    print(f"   - Adiciona o reverso do IP {Cor.VERDE}CORRESPONDENTE{Cor.RESET} à aba que está sendo processada.")
    print(f"   Exemplo, para o IP '{Cor.AMARELO}51.195.253.167{Cor.RESET}' com reverso '{Cor.AMARELO}vps-ae59c8bf.vps.ovh.net{Cor.RESET}',")
    print(f"   um '{Cor.AZUL}Sender Email Address{Cor.RESET}' possível seria: '{Cor.AMARELO}fernando@vps-ae59c8bf.vps.ovh.net{Cor.RESET}'.\n")

    print(f"{Cor.VERDE}3. COMO INICIAR O PROGRAMA:{Cor.RESET}")
    print(f"   - Certifique-se de que todos os arquivos estejam criados e organizados corretamente na mesma pasta do script.")
    print(f"   - Execute o script Python.")
    print(f"   - No menu que aparecer, digite '{Cor.VERDE}1{Cor.RESET}' e pressione Enter para iniciar a automação.\n")

    print(f"{Cor.VERMELHO}4. SAIR DO PROGRAMA:{Cor.RESET}")
    print(f"   - No menu, digite '{Cor.VERMELHO}2{Cor.RESET}' e pressione Enter para encerrar o programa.\n")

    print(f"{Cor.CIANO}{'='*40}{Cor.RESET}\n")
    input(f"{Cor.AMARELO}Pressione Enter para voltar ao menu principal...{Cor.RESET}")
    return menu_inicial()

def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler("execucao.log", encoding='utf-8'),
                        ])

def preparar_estrutura_padrao():
    Path("emails/processados").mkdir(parents=True, exist_ok=True)
    Path("html").mkdir(parents=True, exist_ok=True)

    arquivos = {
        "ips.txt": ["127.0.0.1 example.com"],
        "sender_emails.txt": ["contato"],
        "sender_nomes.txt": ["Central de negociacao"],
        "assuntos.txt": ["Atualização de Cadastro"]
    }
    for arquivo, linhas in arquivos.items():
        if not Path(arquivo).exists():
            Path(arquivo).write_text("\n".join(linhas), encoding='utf-8')
            logging.info(f"Arquivo criado: {arquivo}")

    html_exemplo = Path("html/mensagem_exemplo.html")
    if not html_exemplo.exists():
        html_exemplo.write_text("""
        <html>
            <body>
                <h1>Mensagem de Teste</h1>
                <p>Este é um conteúdo HTML de exemplo.</p>
            </body>
        </html>
        """.strip(), encoding='utf-8')
        logging.info("Arquivo de exemplo HTML criado: html/mensagem_exemplo.html")

def ler_arquivo_linhas(caminho: str) -> List[str]:
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return [l.strip() for l in f if l.strip()]
    except Exception as e:
        logging.error(f"Erro lendo {caminho}: {e}")
        return []

def ler_arquivo_conteudo(caminho: str) -> str:
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Erro lendo {caminho}: {e}")
        return ""

def ler_links() -> List[str]:
    """Lê todos os links do arquivo links.txt"""
    try:
        with open("links.txt", "r", encoding="utf-8") as f:
            links = [linha.strip() for linha in f.readlines() if linha.strip() and not linha.strip().startswith('#')]
        return links
    except FileNotFoundError:
        logging.error("Arquivo links.txt não encontrado!")
        print(f"{Cor.VERMELHO}[ERRO] Arquivo links.txt não encontrado!{Cor.RESET}")
        return []
    except Exception as e:
        logging.error(f"Erro ao ler links.txt: {e}")
        print(f"{Cor.VERMELHO}[ERRO] Erro ao ler arquivo de links: {e}{Cor.RESET}")
        return []

def listar_arquivos_txt(pasta: str) -> List[Path]:
    p = Path(pasta)
    return sorted([f for f in p.iterdir() if f.is_file() and f.suffix == '.txt'])

def listar_arquivos_html(pasta: str) -> List[Path]:
    p = Path(pasta)
    return sorted([f for f in p.iterdir() if f.is_file() and f.suffix == '.html'])

def mover_para_processados(arquivo: Path):
    destino = Path("emails/processados") / arquivo.name
    try:
        shutil.move(str(arquivo), str(destino))
        logging.info(f"Arquivo movido para processados: {arquivo.name}")
    except Exception as e:
        logging.error(f"Erro ao mover {arquivo.name}: {e}")

def barra_progresso(total: int, atual: int):
    percentual = (atual / total) * 100
    barra = '#' * int(percentual // 5) + '-' * (20 - int(percentual // 5))
    print(f"\r[{barra}] {percentual:.1f}%", end='')

def preencher_formulario(page: Page, dados: Dict[str, str], locs: Dict[str, str], emails: str, botao: str, clicar_enviar: bool, link_atual: str = ""):
    try:
        time.sleep(1)
        if dados.get('sender_email'):
            page.fill('//*[@id="senderEmail"]', dados['sender_email'])
            time.sleep(1)
        if dados.get('sender_name'):
            page.fill('//*[@id="senderName"]', dados['sender_name'])
            time.sleep(1)
        if dados.get('subject'):
            page.fill('//*[@id="subject"]', dados['subject'])
            time.sleep(1)
        if dados.get('html'):
            # Substitui a variável [LINK] no conteúdo HTML pelo link atual
            html_content = dados['html'].replace('[LINK]', link_atual)
            page.fill('//*[@id="messageLetter"]', html_content)
            time.sleep(1)
        if emails:
            page.focus("#emailList")
            page.evaluate("""
                (emails) => {
                    const textarea = document.querySelector("#emailList");
                    textarea.value = emails;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                }
            """, emails)
            time.sleep(2)
        if clicar_enviar:
            time.sleep(2)
            page.click('//*[@id="form"]/font/button')
            time.sleep(7)
    except Exception as e:
        logging.error(f"Erro ao preencher a aba: {e}")
        print("\n[ERRO] Ocorreu uma falha ao preencher uma aba. Veja detalhes no execucao.log")

def main():
    setup_logging()
    preparar_estrutura_padrao()

    clicar_enviar = input("Deseja que o programa envie automaticamente? (s/n): ").strip().lower() == 's'

    # Carrega os links do arquivo links.txt
    links = ler_links()
    link_index = 0  # Índice para controlar a sequência dos links

    ips = ler_arquivo_linhas("ips.txt")
    nomes = ler_arquivo_linhas("sender_nomes.txt")
    prefixos = ler_arquivo_linhas("sender_emails.txt")
    assuntos = ler_arquivo_linhas("assuntos.txt")
    arquivos_html = listar_arquivos_html("html")
    listas = listar_arquivos_txt("emails")

    locs = {
        'sender_email': "#sender_email",
        'sender_name': "input[name='sender_name']",
        'subject': "input[name='subject']",
        'html': "textarea#html_content",
        'emails': ".email-list-textarea"
    }
    botao_enviar = "button.submit-button"

    with sync_playwright() as p:
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

                # Obtém o próximo link da sequência
                link_atual = ""
                if links:
                    link_atual = links[link_index % len(links)]
                    link_index += 1
                    print(f"{Cor.VERDE}[LINK] Usando link {link_index}/{len(links)}: {link_atual}{Cor.RESET}")
                    logging.info(f"Link usado (posição {link_index}): {link_atual}")

                dados = {
                    'sender_email': f"{random.choice(prefixos)}@{reverso}",
                    'sender_name': random.choice(nomes),
                    'subject': random.choice(assuntos),
                    'html': html_content
                }

                arquivo_lista = listas[i % len(listas)]
                emails = ler_arquivo_conteudo(str(arquivo_lista))
                preencher_formulario(page, dados, locs, emails, botao_enviar, clicar_enviar, link_atual)
                mover_para_processados(arquivo_lista)
                barra_progresso(len(ips), i + 1)

            except Exception as e:
                logging.error(f"Erro no IP {linha}: {e}")
                print(f"\n{Cor.VERMELHO}[ERRO] Ocorreu um erro ao processar um dos IPs. Veja detalhes no execucao.log{Cor.RESET}")

        print(f"\n{Cor.VERDE}Execução encerrada. Você pode interagir com as abas manualmente.{Cor.RESET}")
        input(f"{Cor.AZUL}Pressione Enter para encerrar o programa.{Cor.RESET}")

if __name__ == "__main__":
    opcao = menu_inicial()
    if opcao == '1':
        main()
    elif opcao == '3':
        nova_opcao = exibir_tutorial()
        if nova_opcao == '1':
            main()
    else:
        print(f"{Cor.VERMELHO}Saindo...{Cor.RESET}")
        sys.exit()
