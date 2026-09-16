"""
Gera o relatório consolidado em PDF a partir dos markdowns da submissão.

Estratégia: markdown -> HTML com CSS de impressão -> PDF via Chromium
headless (Edge, que já vem no Windows). Não depende de WeasyPrint/GTK.

Uso:  python build_pdf.py
Saída: Relatorio_Redesign_Suporte_Emerson_Guimaraes.pdf (nesta pasta)
"""
import re
import subprocess
import shutil
from pathlib import Path

import markdown

AQUI = Path(__file__).resolve().parent
RAIZ_SUBMISSAO = AQUI.parents[1]
HTML_SAIDA = AQUI / "_relatorio_consolidado.html"
PDF_SAIDA = AQUI / "Relatorio_Redesign_Suporte_Emerson_Guimaraes.pdf"

EDGE_CANDIDATOS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def encontrar_edge():
    for c in EDGE_CANDIDATOS:
        if Path(c).exists():
            return c
    achou = shutil.which("msedge") or shutil.which("chrome")
    if achou:
        return achou
    raise RuntimeError("Edge/Chrome não encontrado. Instale um dos dois.")


def md_para_html(caminho, ajuste_titulos=0):
    """Converte um arquivo markdown, promovendo o nível dos títulos se
    ajuste_titulos>0 (para encaixar na hierarquia do documento maior).
    """
    texto = caminho.read_text(encoding="utf-8")
    # Remove o título H1 de cada documento-fonte: o título de seção é
    # inserido manualmente no template, com numeração própria.
    texto = re.sub(r"^#\s+.+\n", "", texto, count=1)
    if ajuste_titulos:
        def rebaixar(m):
            return "#" * min(6, len(m.group(1)) + ajuste_titulos) + " " + m.group(2)
        texto = re.sub(r"^(#{1,6})\s+(.+)$", rebaixar, texto, flags=re.MULTILINE)
    return markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])


# --------------------------------------------------------------- diagramas

DIAGRAMA_ARQUITETURA = """
<svg viewBox="0 0 980 260" xmlns="http://www.w3.org/2000/svg" class="diagrama">
  <defs>
    <marker id="seta" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="#4a5568"/>
    </marker>
  </defs>
  <style>
    .caixa { fill:#f7fafc; stroke:#2d3748; stroke-width:1.5; rx:8; }
    .caixa-alerta { fill:#fff5f5; stroke:#c53030; stroke-width:1.5; rx:8; }
    .caixa-ok { fill:#f0fff4; stroke:#276749; stroke-width:1.5; rx:8; }
    .titulo { font:600 13px 'Segoe UI',sans-serif; fill:#1a202c; }
    .sub { font:11px 'Segoe UI',sans-serif; fill:#4a5568; }
    .liga { stroke:#4a5568; stroke-width:1.5; fill:none; marker-end:url(#seta); }
    .rot { font:10px 'Segoe UI',sans-serif; fill:#718096; }
  </style>

  <rect x="10" y="30" width="150" height="70" class="caixa"/>
  <text x="85" y="55" text-anchor="middle" class="titulo">Dataset 1</text>
  <text x="85" y="72" text-anchor="middle" class="sub">tickets + métricas</text>
  <text x="85" y="87" text-anchor="middle" class="sub">8.469 registros</text>

  <rect x="10" y="150" width="150" height="70" class="caixa"/>
  <text x="85" y="175" text-anchor="middle" class="titulo">Dataset 2</text>
  <text x="85" y="192" text-anchor="middle" class="sub">tickets reais rotulados</text>
  <text x="85" y="207" text-anchor="middle" class="sub">47.837 registros</text>

  <rect x="220" y="30" width="170" height="70" class="caixa-alerta"/>
  <text x="305" y="52" text-anchor="middle" class="titulo">01 · Auditoria</text>
  <text x="305" y="69" text-anchor="middle" class="sub">9 testes de integridade</text>
  <text x="305" y="84" text-anchor="middle" class="sub">8/9 condenam o DS1</text>

  <rect x="220" y="150" width="170" height="70" class="caixa-ok"/>
  <text x="305" y="172" text-anchor="middle" class="titulo">03 · Classificador</text>
  <text x="305" y="189" text-anchor="middle" class="sub">TF-IDF + LogReg</text>
  <text x="305" y="204" text-anchor="middle" class="sub">86,4% de acurácia</text>

  <rect x="460" y="90" width="180" height="70" class="caixa"/>
  <text x="550" y="112" text-anchor="middle" class="titulo">02 · Diagnóstico</text>
  <text x="550" y="129" text-anchor="middle" class="sub">gargalos, CSAT, ROI</text>
  <text x="550" y="144" text-anchor="middle" class="sub">cobertura medida cruzada</text>

  <rect x="710" y="20" width="180" height="70" class="caixa-ok"/>
  <text x="800" y="42" text-anchor="middle" class="titulo">Mesa de Triagem</text>
  <text x="800" y="59" text-anchor="middle" class="sub">app Streamlit</text>
  <text x="800" y="74" text-anchor="middle" class="sub">triagem + lote + ROI</text>

  <rect x="710" y="160" width="180" height="70" class="caixa"/>
  <text x="800" y="182" text-anchor="middle" class="titulo">Relatórios</text>
  <text x="800" y="199" text-anchor="middle" class="sub">diagnóstico, proposta,</text>
  <text x="800" y="214" text-anchor="middle" class="sub">anexo de auditoria</text>

  <path class="liga" d="M160,65 L220,65"/>
  <path class="liga" d="M160,185 L220,185"/>
  <path class="liga" d="M390,65 L470,65 L470,100"/>
  <path class="liga" d="M390,185 L470,185 L470,150"/>
  <path class="liga" d="M640,110 L700,70 L710,55"/>
  <path class="liga" d="M640,140 L700,180 L710,195"/>
  <text x="425" y="55" class="rot">só o real</text>
  <text x="425" y="200" class="rot">cobertura medida</text>
</svg>
"""

DIAGRAMA_FLUXO = """
<svg viewBox="0 0 760 430" xmlns="http://www.w3.org/2000/svg" class="diagrama">
  <defs>
    <marker id="seta2" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="#4a5568"/>
    </marker>
  </defs>
  <style>
    .n1 { fill:#ebf8ff; stroke:#2b6cb0; stroke-width:1.5; }
    .n2 { fill:#fffaf0; stroke:#c05621; stroke-width:1.5; }
    .n3 { fill:#fff5f5; stroke:#c53030; stroke-width:1.5; }
    .n4 { fill:#f0fff4; stroke:#276749; stroke-width:1.5; }
    .tit { font:600 12px 'Segoe UI',sans-serif; fill:#1a202c; }
    .sub2 { font:10.5px 'Segoe UI',sans-serif; fill:#4a5568; }
    .lig { stroke:#4a5568; stroke-width:1.5; fill:none; marker-end:url(#seta2); }
    .lbl { font:10px 'Segoe UI',sans-serif; fill:#718096; }
  </style>

  <rect x="290" y="10" width="180" height="55" rx="8" class="n1"/>
  <text x="380" y="33" text-anchor="middle" class="tit">Ticket entra</text>
  <text x="380" y="49" text-anchor="middle" class="sub2">email · chat · telefone · social</text>

  <rect x="270" y="100" width="220" height="55" rx="8" class="n1"/>
  <text x="380" y="123" text-anchor="middle" class="tit">Classificador</text>
  <text x="380" y="139" text-anchor="middle" class="sub2">categoria + confiança 0-1</text>

  <path class="lig" d="M380,65 L380,100"/>

  <rect x="250" y="190" width="260" height="55" rx="8" class="n2"/>
  <text x="380" y="213" text-anchor="middle" class="tit">Categoria sensível?</text>
  <text x="380" y="229" text-anchor="middle" class="sub2">Administrative rights · Purchase</text>

  <path class="lig" d="M380,155 L380,190"/>

  <rect x="30" y="280" width="240" height="70" rx="8" class="n3"/>
  <text x="150" y="303" text-anchor="middle" class="tit">FILA HUMANA</text>
  <text x="150" y="319" text-anchor="middle" class="sub2">com sugestão + termos</text>
  <text x="150" y="334" text-anchor="middle" class="sub2">que pesaram na decisão</text>

  <rect x="500" y="280" width="220" height="55" rx="8" class="n2"/>
  <text x="610" y="303" text-anchor="middle" class="tit">Confiança ≥ 0,80 ?</text>
  <text x="610" y="319" text-anchor="middle" class="sub2">limiar calibrado</text>

  <path class="lig" d="M250,217 L150,217 L150,280"/>
  <text x="175" y="255" class="lbl">sim (sensível)</text>

  <path class="lig" d="M510,217 L610,217 L610,280"/>
  <text x="530" y="255" class="lbl">não</text>

  <path class="lig" d="M500,307 L270,307"/>
  <text x="380" y="298" class="lbl">não (confiança baixa)</text>

  <rect x="530" y="365" width="200" height="55" rx="8" class="n4"/>
  <text x="630" y="388" text-anchor="middle" class="tit">ROTEAMENTO AUTOMÁTICO</text>
  <text x="630" y="404" text-anchor="middle" class="sub2">97,48% de acerto medido</text>

  <path class="lig" d="M660,335 L660,365"/>
  <text x="668" y="352" class="lbl">sim · 60,11%</text>
</svg>
"""


def montar_capa():
    return f"""
<section class="pagina capa">
  <div class="capa-topo">
    <div class="capa-etiqueta">G4 · AI Master Challenge</div>
    <div class="capa-etiqueta">Challenge 002 — Redesign de Suporte</div>
  </div>
  <div class="capa-centro">
    <h1 class="capa-titulo">Redesign de Suporte<br>com IA</h1>
    <p class="capa-sub">Diagnóstico operacional, proposta de automação<br>
    e protótipo funcional de triagem</p>
  </div>
  <div class="capa-rodape">
    <table class="capa-tabela">
      <tr><td>Autor</td><td>Emerson Guimarães</td></tr>
      <tr><td>Papel</td><td>AI Master — candidato</td></tr>
      <tr><td>Data</td><td>Setembro de 2026</td></tr>
      <tr><td>Repositório</td><td>submissions/emerson-guimaraes</td></tr>
    </table>
  </div>
</section>
"""


def montar_sumario_executivo():
    return """
<section class="pagina">
  <h1 class="pos-sumario"><span class="num">1</span> Sumário Executivo</h1>
  <div class="callout callout-chave">
    <p>Construí um roteador de tickets que <strong>decide sozinho 60,11%
    dos casos com 97,48% de acerto</strong> e sabe quando não sabe. Duas
    categorias ficam <strong>sempre</strong> com humano — mesmo com 100% de
    confiança — porque concessão de privilégio e decisão de gasto têm custo
    de erro assimétrico, e otimizar acurácia média ignora isso.</p>
    <p>Isso recupera <strong>R$ 63.472/ano (0,71 FTE)</strong> de um custo
    de <strong>R$ 90.000/ano em triagem manual</strong> — projeção para os 30
    mil tickets/ano citados no brief; R$ 25.407 e R$ 17.918 sobre os 8.469
    tickets efetivamente entregues. O ganho é líquido: desconta o retrabalho
    dos próprios erros do modelo e soma o tempo poupado nos tickets que ainda
    vão para humano, que chegam com sugestão pronta. Payback estimado em
    <strong>≈ 2,6 meses</strong>.</p>
    <p>Nada disso usa os campos de tempo ou satisfação do Dataset 1:
    <strong>auditei antes de usar e ele não passa</strong> — 8 de 9 testes o
    condenam, incluindo 100% dos e-mails em domínios reservados da RFC 2606 e
    todas as categóricas uniformes. Por isso o peso quantitativo está nos
    47.837 tickets reais do Dataset 2, e as duas perguntas do diagnóstico que
    esses dados não respondem vêm com o teste que prova, em vez de número
    inventado.</p>
  </div>

  <h2>Números que sustentam a entrega</h2>
  <table class="tabela-metricas">
    <tr><th>Achado</th><th>Evidência</th></tr>
    <tr><td>Dataset 1 é gerado artificialmente</td>
        <td>8/9 testes; 100% dos e-mails em <code>example.com/.org/.net</code> (RFC 2606)</td></tr>
    <tr><td>Não há gargalo identificável</td>
        <td>ANOVA por canal p=0,451 · prioridade p=0,569 · tipo p=0,911</td></tr>
    <tr><td>Nada explica a satisfação</td>
        <td>R² de teste = <strong>−0,0525</strong> (pior que chutar a média)</td></tr>
    <tr><td>Classificador funciona</td>
        <td><strong>86,40%</strong> de acurácia vs 28,47% do baseline (+57,93 p.p.), F1 macro 0,865</td></tr>
    <tr><td>TF-IDF venceu embeddings e zero-shot, testado</td>
        <td>86,40% vs. 78,07% (embeddings) vs. <strong>23,75%</strong> (zero-shot) — mesmo split de teste</td></tr>
    <tr><td>Automação viável e medida</td>
        <td>limiar 0,80 → <strong>60,11%</strong> de cobertura a <strong>97,48%</strong> de acurácia</td></tr>
    <tr><td>Ganho financeiro</td>
        <td><strong>R$ 63.472/ano</strong> líquidos (0,71 FTE) — projeção p/ 30 mil tickets;
        R$ 17.918 sobre os 8.469 tickets reais entregues</td></tr>
    <tr><td>Payback do investimento</td>
        <td>≈ <strong>2,6 meses</strong> (integração estimada em R$ 12.000; fase de sombra custa R$ 0)</td></tr>
    <tr><td>Sensibilidade ao custo/hora</td>
        <td>de <strong>R$ 42.315</strong> (R$ 30/h) a <strong>R$ 84.629</strong> (R$ 60/h) —
        R$ 45/h é benchmark, não a folha real da operação</td></tr>
  </table>

  <h2>Arquitetura da solução</h2>
  <p>O pipeline cruza os dois datasets: o Dataset 1 fornece o volume real
  de tickets, o Dataset 2 fornece o sinal real de classificação. A
  auditoria decide o que cada um pode sustentar antes de qualquer número
  ser publicado.</p>
  __DIAGRAMA_ARQUITETURA__

  <h2>Recomendações, em ordem de prioridade</h2>
  <ol class="lista-numerada">
    <li><strong>Implantar triagem automática em três fases</strong>
      (sombra → piloto → expansão). É o único ganho quantificável e
      comprovado.</li>
    <li><strong>Manter decisões de privilégio e de gasto sempre com
      humano</strong>, qualquer confiança.</li>
    <li><strong>Instrumentar a operação</strong> — sem dados temporais e
      de satisfação confiáveis, as perguntas de gargalo e satisfação
      continuarão sem resposta.</li>
    <li><strong>Revisar a taxonomia de filas</strong> antes de esperar
      mais precisão do modelo.</li>
    <li><strong>Não construir resposta automática ao cliente agora</strong>
      — não há base real de resoluções para aprender.</li>
  </ol>
</section>
"""


def montar_sumario(indice):
    linhas = "".join(
        f'<li><span class="num">{n}</span> {t} <span class="pontos"></span></li>'
        for n, t in indice
    )
    return f"""
<section class="sumario">
  <h1>Sumário</h1>
  <ol class="toc">{linhas}</ol>
</section>
"""


TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Redesign de Suporte com IA — Emerson Guimarães</title>
<style>
  @page {{ size: A4; margin: 15mm 15mm 16mm 15mm;
    @bottom-center {{ content: "Challenge 002 — Redesign de Suporte  ·  página " counter(page);
      font-family: 'Segoe UI', sans-serif; font-size: 9px; color: #a0aec0; }} }}
  @page capa {{ size: A4; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', 'Calibri', sans-serif; color:#1a202c;
    font-size: 11.5px; line-height: 1.48; }}
  h1 {{ font-size: 20px; color:#1a202c; border-bottom: 3px solid #2b6cb0;
    padding-bottom: 6px; margin-top: 0; }}
  h1 .num {{ color:#2b6cb0; margin-right: 6px; }}
  h2 {{ font-size: 15px; color:#2d3748; margin-top: 15px;
    margin-bottom: 7px; border-left: 4px solid #2b6cb0; padding-left: 8px; }}
  h3 {{ font-size: 13px; color:#2d3748; margin-top: 11px;
    margin-bottom: 5px; }}
  h4 {{ font-size: 12px; color:#4a5568; }}
  p {{ margin: 6px 0; text-align: justify; }}
  code {{ background:#edf2f7; padding: 1px 5px; border-radius: 3px;
    font-family: 'Consolas', monospace; font-size: 10.5px; color:#c53030; }}
  pre {{ background:#1a202c; color:#e2e8f0; padding: 12px; border-radius: 6px;
    font-size: 10px; overflow-x: auto; white-space: pre-wrap; }}
  pre code {{ background: none; color: inherit; padding: 0; }}
  blockquote {{ border-left: 4px solid #cbd5e0; margin: 8px 0; padding: 3px 13px;
    color:#4a5568; background:#f7fafc; font-style: italic; }}
  table {{ border-collapse: collapse; width: 100%; margin: 8px 0 11px 0;
    font-size: 10.5px; }}
  th, td {{ border: 1px solid #e2e8f0; padding: 4px 7px; text-align: left; }}
  th {{ background:#2b6cb0; color:white; font-weight:600; }}
  tr:nth-child(even) td {{ background:#f7fafc; }}
  strong {{ color:#1a202c; }}
  a {{ color:#2b6cb0; text-decoration:none; }}
  ul, ol {{ padding-left: 22px; }}
  li {{ margin: 2px 0; }}
  .pagina {{ page-break-after: always; }}
  h1.pos-sumario {{ margin-top: 26px; }}
  .pagina:last-child {{ page-break-after: auto; }}

  /* capa: usa a @page nomeada "capa", sem margem, para sangramento total */
  .capa {{ page: capa; box-sizing:border-box; width:210mm; height:297mm;
    display:flex; flex-direction:column; justify-content:space-between;
    background: linear-gradient(160deg,#1a365d 0%,#2b6cb0 100%);
    color:#ffffff; padding: 20mm 18mm; }}
  .capa-etiqueta {{ font-size:11px; letter-spacing:1.5px; text-transform:uppercase;
    color:#bee3f8; margin-bottom:4px; }}
  .capa-centro {{ text-align:left; }}
  .capa-titulo {{ font-size: 40px; font-weight:700; line-height:1.15; margin:0;
    color:#ffffff !important; }}
  .capa-sub {{ font-size: 14px; color:#e2e8f0; margin-top:14px; }}
  .capa-tabela {{ width:100%; font-size:11px; border-collapse:collapse; }}
  .capa-tabela td {{ border:none !important; border-top:1px solid rgba(255,255,255,0.25) !important;
    padding:6px 0; color:#ffffff !important; background:transparent !important; }}
  .capa-tabela tr:nth-child(even) td {{ background:transparent !important; }}
  .capa-tabela td:first-child {{ color:#bee3f8 !important; width:35%; }}

  /* sumario */
  .toc {{ list-style:none; padding:0; font-size:13px; }}
  .toc li {{ display:flex; align-items:baseline; padding:6px 0;
    border-bottom:1px dotted #cbd5e0; }}
  .toc .num {{ color:#2b6cb0; font-weight:700; margin-right:10px; }}

  .callout {{ padding: 14px 16px; border-radius:6px; margin: 12px 0; }}
  .callout-chave {{ background:#ebf8ff; border-left:4px solid #2b6cb0; }}

  .tabela-metricas td:first-child {{ font-weight:600; width:38%; }}
  .diagrama {{ width:100%; height:auto; margin: 10px 0 18px 0; }}
  .lista-numerada li {{ margin-bottom:6px; }}

  .rodape-doc {{ margin-top: 40px; padding-top:10px; border-top:1px solid #e2e8f0;
    font-size:9.5px; color:#a0aec0; text-align:center; }}
</style>
</head>
<body>

{capa}
{sumario}
{sumario_executivo}
{secao2}
{secao3}
{secao4}
{secao5}

<section class="pagina" style="page-break-after:auto;">
  <div class="rodape-doc">
    Relatório gerado a partir dos documentos versionados em
    <code>submissions/emerson-guimaraes/</code> · reprodução completa em
    <code>docs/SETUP.md</code>
  </div>
</section>

</body>
</html>
"""


def main():
    diag = md_para_html(RAIZ_SUBMISSAO / "solution/relatorio/01_diagnostico_operacional.md", 1)
    auto = md_para_html(RAIZ_SUBMISSAO / "solution/relatorio/02_proposta_automacao.md", 1)
    anexo = md_para_html(RAIZ_SUBMISSAO / "solution/relatorio/03_anexo_auditoria_dados.md", 1)
    diario = md_para_html(RAIZ_SUBMISSAO / "docs/DIARIO_DE_BORDO.md", 1)

    indice = [
        ("1", "Sumário Executivo"),
        ("2", "Diagnóstico Operacional"),
        ("3", "Proposta de Automação com IA"),
        ("4", "Anexo — Auditoria de Integridade dos Dados"),
        ("5", "Diário de Bordo e Process Log"),
    ]

    secao2 = f'<section class="pagina"><h1><span class="num">2</span> Diagnóstico Operacional</h1>{diag}</section>'
    secao3 = f'''<section class="pagina"><h1><span class="num">3</span> Proposta de Automação com IA</h1>
    <h2>Fluxo de decisão proposto</h2>{DIAGRAMA_FLUXO}{auto}</section>'''
    secao4 = f'<section class="pagina"><h1><span class="num">4</span> Anexo — Auditoria de Integridade dos Dados</h1>{anexo}</section>'
    secao5 = f'<section class="pagina" style="page-break-after:auto;"><h1><span class="num">5</span> Diário de Bordo e Process Log</h1>{diario}</section>'

    resumo_exec = montar_sumario_executivo().replace(
        "__DIAGRAMA_ARQUITETURA__", DIAGRAMA_ARQUITETURA)

    html = TEMPLATE.format(
        capa=montar_capa(),
        sumario=montar_sumario(indice),
        sumario_executivo=resumo_exec,
        secao2=secao2, secao3=secao3, secao4=secao4, secao5=secao5,
    )
    HTML_SAIDA.write_text(html, encoding="utf-8")
    print(f"HTML gerado: {HTML_SAIDA}")

    edge = encontrar_edge()
    cmd = [
        edge, "--headless=new", "--disable-gpu", "--no-sandbox",
        f"--print-to-pdf={PDF_SAIDA}",
        "--print-to-pdf-no-header",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=15000",
        HTML_SAIDA.as_uri(),
    ]
    print("Renderizando o PDF via Edge headless...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if PDF_SAIDA.exists():
        tam = PDF_SAIDA.stat().st_size / 1024
        print(f"PDF gerado: {PDF_SAIDA} ({tam:.0f} KB)")
    else:
        print("FALHA ao gerar o PDF.")
        print(r.stdout[-2000:], r.stderr[-2000:])


if __name__ == "__main__":
    main()
