"""Painel externo público da Transforma — somente recorte técnico curado.

Streamlit Community Cloud; medições independentes; não acessa dados internos.
Curvas completas de P15 com quebras explícitas em janelas não observadas.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Transforma | Painel técnico energético", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
ROOT = Path(__file__).resolve().parent
COLORS = {"blue":"#155f7a", "teal":"#13948b", "dark":"#12364d", "grey":"#647c88", "orange":"#c68c35", "purple":"#7b62a3"}
NAV = ["Visão geral", "Análises de energia", "Simulação Bruno + Jaguar", "Entrada em média tensão", "Metodologia"]

@st.cache_data(show_spinner=False)
def load_data() -> dict:
    with (ROOT / "dados.json").open(encoding="utf-8") as f:
        data = json.load(f)
    if not {"elementos", "cenarios", "faturas_mt"}.issubset(data):
        raise ValueError("Recorte técnico incompleto")
    return data

@st.cache_data(show_spinner=False)
def load_series(code: str) -> pd.DataFrame:
    path = ROOT / "series" / f"{code}.csv"
    if path.exists():
        df = pd.read_csv(path, parse_dates=["data"])
    else:
        record = next((x for x in ITEMS if x["codigo"] == code), None)
        df = pd.DataFrame(record.get("curva15", []) if record else [])
        if df.empty:
            return pd.DataFrame()
        df = df.rename(columns={"kw":"p15_kw", "kva":"s15_kva"})
        df["data"] = pd.to_datetime(df["data"])
        # Fallback for previous exports: do not bridge gaps in a sparse sample.
        typical = df["data"].diff().dropna().median()
        if pd.isna(typical): typical = pd.Timedelta(minutes=15)
        out = []
        for i,row in df.iterrows():
            if out and row["data"] - out[-1]["data"] > max(typical * 2, pd.Timedelta(minutes=35)):
                out.append({"data":out[-1]["data"] + pd.Timedelta(minutes=1),"p15_kw":None,"s15_kva":None})
            out.append(row.to_dict())
        df = pd.DataFrame(out)
    df = df.sort_values("data").reset_index(drop=True)
    return df

DATA = load_data()
ITEMS = DATA["elementos"]
BY_CODE = {e["codigo"]: e for e in ITEMS}
BILLS = DATA["faturas_mt"]
SCENARIOS = DATA["cenarios"]


def fmt(value, digits=1):
    try:
        if value is None or pd.isna(value): return "—"
        return f"{float(value):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError): return "—"


def date_br(value):
    return pd.to_datetime(value).strftime("%d/%m/%Y") if value else "—"


def metric(label, value, note=""):
    st.markdown(f'''<div class="metric-box"><div class="metric-label">{html.escape(label)}</div>
        <div class="metric-value">{html.escape(str(value))}</div>
        <div class="metric-foot">{html.escape(note)}</div></div>''',unsafe_allow_html=True)


def section(title, note=""):
    st.subheader(title)
    if note: st.caption(note)


def choose(code, navigate=False):
    st.session_state["focus_code"] = code
    if navigate: st.session_state["nav_page"] = "Análises de energia"


def base_fig(title="", ytitle=""):
    fig = go.Figure()
    fig.update_layout(height=385, margin=dict(l=8,r=12,t=32 if title else 14,b=12),
        title=title or None, plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#29475a", family="Arial", size=12),
        hovermode="x unified", legend=dict(orientation="h", y=1.13, x=0),
        xaxis=dict(showgrid=False), yaxis=dict(title=ytitle,gridcolor="#e5edf0",zeroline=False))
    return fig


def add_line(fig, df, column, label, color, x="data"):
    fig.add_trace(go.Scatter(x=df[x],y=df[column],name=label,mode="lines",
        line=dict(color=color,width=1.9),connectgaps=False,
        hovertemplate="%{x|%d/%m/%Y %H:%M}<br>"+html.escape(label)+": %{y:,.2f}<extra></extra>"))


def glossary():
    with st.expander("Entenda os indicadores: demanda, janelas de 15 minutos e leituras", expanded=False):
        st.markdown('''
        - **P5 (kW):** maior **potência ativa média em 5 minutos**. **P15 (kW):** maior potência ativa média móvel em **15 minutos**, calculada com três leituras consecutivas e completas de cinco minutos. P5 e P15 são duas maneiras de observar a **mesma carga**, e **não devem ser somadas**.
        - **S5 e S15 (kVA):** médias de **potência aparente** em 5 e 15 minutos; ajudam a avaliar o carregamento elétrico. A demanda contratada na Enel é estudada em kW e no ponto de entrega, não diretamente por esses picos em kVA.
        - **Pico dentro de 5 minutos (kVA):** maior potência aparente interna registrada pelo analisador naquele intervalo. Sua duração exata não é conhecida.
        - **Janela de 15 minutos válida:** intervalo calculável com **três registros completos consecutivos de 5 minutos**; não significa uma partida de motor. Janelas móveis se sobrepõem.
        - **Leituras completas (%):** registros com grandezas disponíveis divididos pelo total de registros da coleta. Segundo a operação informada, Bruno e Jaguar deixam de ter grandezas durante paradas da trituração, quando gerador e triturador são desligados. Isso **não mede tempo de produção** nem caracteriza defeito de medição.
        - **P15 — percentil 95 (P95):** em 95% das janelas móveis calculadas, a demanda ficou **até** esse valor; 5% ficaram acima. Não é a maior demanda nem uma potência contratada.
        - **Energia registrada (kWh):** energia dos intervalos com dados disponíveis, sem atribuir consumo zero a lacunas.
        ''')


def asset_buttons(prefix, navigate=False):
    cols = st.columns(5, gap="small")
    for i,e in enumerate(ITEMS):
        with cols[i]:
            selected = st.session_state.get("focus_code", "JAGUAR") == e["codigo"]
            st.button(e["codigo"] if e["codigo"].startswith("TR") else e["codigo"].title(),
                key=f"{prefix}_{e['codigo']}",use_container_width=True,
                type="primary" if selected else "secondary",
                on_click=choose,args=(e["codigo"],navigate))


def selected_dates(df, key):
    if df.empty:return df
    dates=df["data"].dropna()
    lower=dates.min().date(); upper=dates.max().date()
    values=st.date_input("Período exibido",value=(lower,upper),min_value=lower,max_value=upper,key=key)
    if not isinstance(values,(tuple,list)) or len(values)!=2:
        st.caption("Selecione as duas datas para atualizar o gráfico.")
        return df
    left,right=pd.Timestamp(values[0]),pd.Timestamp(values[1])+pd.Timedelta(days=1)
    return df.loc[(df["data"]>=left)&(df["data"]<right)].copy()


def display_point(e, prefix):
    code=e["codigo"]
    st.markdown(f"### {e['nome']}")
    st.write(e["descricao"])
    st.caption(f"{e['tipo']} · {e['tensao']} · Análise de energia: {date_br(e['inicio'])} a {date_br(e['fim'])}")
    c1,c2,c3,c4=st.columns(4)
    with c1:metric("Demanda P15 móvel máxima",f"{fmt(e['p15_max_kw'])} kW","Maior média móvel válida")
    with c2:metric("S15 máxima",f"{fmt(e['s15_max_kva'])} kVA","Aparente média em 15 min")
    with c3:metric("Energia registrada",f"{fmt(e['energia_kwh'],0)} kWh","Intervalos com dados")
    with c4:metric("Leituras completas",f"{fmt(100*e['validos']/e['registros'])}%",f"{e['validos']} de {e['registros']} registros")
    if code in ("BRUNO", "JAGUAR"):
        st.caption("Conforme a operação informada, o gerador a diesel e o triturador são desligados nas paradas de produção. O percentual acima mostra registros completos, NÃO horas de funcionamento.")
    else:
        st.caption("Porcentagem de registros elétricos completos no período da coleta, não fator de utilização do equipamento.")
    glossary()

    section("Curvas históricas — intervalos medidos", "Linhas interrompidas onde não existem três registros completos consecutivos de cinco minutos; não ligamos dados separados por paradas nem assumimos potência zero.")
    if code in ("BRUNO", "JAGUAR"):
        st.info("Contexto operacional informado: quando a trituração para, o gerador e o triturador são desligados. Os espaços em branco representam períodos fora da coleta com grandezas disponíveis, não falhas assumidas de fornecimento.")
    series=load_series(code)
    if series.empty:
        st.warning("Não foram encontradas séries disponíveis para esse ponto.")
        return
    data=selected_dates(series, prefix+"_datas")
    group=st.radio("Grandeza a visualizar",["Demanda ativa P15 · kW", "Potência aparente S15 · kVA", "Tensões entre fases · V", "Relação P/S"],horizontal=True,key=prefix+"_medida")
    specs={
      "Demanda ativa P15 · kW":[("p15_kw","P15 móvel (kW)",COLORS['teal'])],
      "Potência aparente S15 · kVA":[("s15_kva","S15 média (kVA)",COLORS['blue'])],
      "Tensões entre fases · V":[("vab","AB",COLORS['teal']),("vbc","BC",COLORS['orange']),("vca","CA",COLORS['purple'])],
      "Relação P/S":[("fp_ps","P/S (não fiscal)",COLORS['blue'])]
    }
    fig=base_fig(ytitle=group.split("·")[-1].strip())
    for col,label,color in specs[group]:
        if col in data and data[col].notna().any(): add_line(fig,data,col,label,color)
    if not fig.data: st.warning("A série selecionada não possui valores nesse período.")
    else:
        fig.update_layout(height=440)
        st.plotly_chart(fig,use_container_width=True,key=prefix+"_serie")
    if group=="Relação P/S":
        st.caption("P/S foi calculado pela razão entre potências ativa e aparente médias de cada janela; não substitui medições fiscais de fator de potência ou análise harmônica.")
    if group=="Tensões entre fases · V":
        st.caption("Médias de três intervalos de cinco minutos extraídas dos canais de tensão AB, BC e CA do P54. Não há diagnóstico automático de conformidade.")
    st.caption("É possível ampliar ou selecionar trechos do gráfico com as ferramentas interativas no canto superior direito.")

    daily=pd.DataFrame(e.get("dias",[]))
    if not daily.empty:
        daily["data"]=pd.to_datetime(daily["data"])
        daily=daily[(daily["data"]>=data["data"].min().normalize()) & (daily["data"]<=data["data"].max().normalize())] if not data.empty else daily
        section("Energia e atividade por dia", "A energia reflete somente medições válidas; horas em carga usam o limiar de 10 kW para identificar atividade observada.")
        a,b=st.columns(2)
        with a:
            f=base_fig(ytitle="Energia (kWh)")
            f.add_trace(go.Bar(x=daily["data"],y=daily["kwh"],name="Energia registrada",marker_color=COLORS['teal']))
            st.plotly_chart(f,use_container_width=True,key=prefix+"_kwh")
        with b:
            f=base_fig(ytitle="Horas com carga (h)")
            f.add_trace(go.Bar(x=daily["data"],y=daily["h_em_carga"],name="Atividade ≥ 10 kW",marker_color=COLORS['blue']))
            st.plotly_chart(f,use_container_width=True,key=prefix+"_hours")

    valid=data.dropna(subset=["p15_kw"]).copy()
    if not valid.empty:
        section("Distribuição da demanda observada", "Cada janela móvel de 15 minutos é calculada com três registros completos de 5 minutos; ela não equivale a uma partida do equipamento.")
        a,b=st.columns(2)
        with a:
            f=base_fig(ytitle="P15 (kW)")
            y=valid["p15_kw"].sort_values(ascending=False).to_numpy()
            x=[100*i/max(1,len(y)-1) for i in range(len(y))]
            f.add_trace(go.Scatter(x=x,y=y,name="Curva de duração",mode="lines",line=dict(color=COLORS['teal'],width=2)))
            f.update_xaxes(title="Percentual acumulado das janelas analisadas (%)",range=[0,100])
            st.plotly_chart(f,use_container_width=True,key=prefix+"_duracao")
            st.caption("**Curva de duração:** demandas ordenadas da maior para a menor. A posição de 20%, por exemplo, indica uma demanda atingida ou superada em aproximadamente 20% das janelas calculadas. Não representa 20% das horas do período, pois há intervalos sem valores.")
        with b:
            f=base_fig(ytitle="Janelas móveis de 15 minutos (contagem)")
            f.add_trace(go.Histogram(x=valid["p15_kw"],nbinsx=25,name="Distribuição P15",marker_color=COLORS['blue']))
            f.update_xaxes(title="Faixa de demanda P15 (kW)")
            st.plotly_chart(f,use_container_width=True,key=prefix+"_hist")
            st.caption("**Distribuição:** a altura de cada barra indica quantas janelas de 15 minutos calculadas ficaram na faixa de potência do eixo horizontal. Não é a quantidade de vezes que o triturador foi ligado. O limiar de 10 kW é usado apenas no estudo de episódios/horas em carga. Como as janelas móveis se sobrepõem, a contagem não equivale a intervalos independentes.")
        note_map = ("Cada célula contém a média calculada naquela hora. Nos trituradores, espaços em branco são compatíveis com paradas e desligamento do gerador conforme operação informada." if code in ("BRUNO","JAGUAR") else "Cada célula contém a média calculada naquela hora. Espaços em branco significam ausência de janelas calculáveis.")
        section("Mapa de carga por dia e hora", note_map)
        valid["dia"] = valid["data"].dt.strftime("%d/%m")
        valid["hora"] = valid["data"].dt.hour
        horas = list(range(24))
        pivot = valid.pivot_table(index="dia",columns="hora",values="p15_kw",aggfunc="mean",sort=False).reindex(columns=horas)
        f=go.Figure(go.Heatmap(x=[f"{h:02d}h" for h in horas],y=pivot.index,z=pivot.values,
            colorscale=[[0,"#e8f5f2"],[.5,"#2d9a9e"],[1,"#143c59"]],colorbar=dict(title="kW"),
            hovertemplate="Dia %{y} · %{x}<br>Demanda média: %{z:.1f} kW<extra></extra>"))
        f.update_layout(height=max(300,28*len(pivot)+90),margin=dict(l=8,r=8,t=15,b=10),
            xaxis_title="Hora do dia (00h–23h; 24h = 00h do dia seguinte)",yaxis_title="Dia",paper_bgcolor="rgba(0,0,0,0)",font=dict(color="#29475a"))
        f.update_xaxes(type="category",categoryorder="array",categoryarray=[f"{h:02d}h" for h in horas],tickangle=0)
        st.plotly_chart(f,use_container_width=True,key=prefix+"_calor")

    section("Indicadores adicionais")
    more=st.columns(4)
    with more[0]:st.metric("P5 máxima · kW",fmt(e['p5_max_kw']))
    with more[1]:st.metric("S5 máxima · kVA",fmt(e['s5_max_kva']))
    with more[2]:st.metric("Pico aparente intra-5 min · kVA",fmt(e['s_intra_kva']))
    with more[3]:st.metric("P15 — percentil 95 · kW",fmt(e['p15_p95_kw']))
    st.caption("**P95 da demanda de 15 min:** em 95% das janelas calculadas, a demanda foi igual ou inferior a esse valor; somente 5% ultrapassaram esse patamar. Ajuda a caracterizar a carga elevada habitual, mas não representa o maior pico.")
    if code in ("BRUNO","JAGUAR"):
        x,y,z=st.columns(3)
        with x:st.metric("Energia média por dia ativo",f"{fmt(e['energia_media_dia_ativo_kwh'])} kWh")
        with y:st.metric("Energia média por episódio",f"{fmt(e['energia_media_episodio_kwh'])} kWh")
        with z:st.metric("Episódios observados",str(e['episodios']))
        st.caption("Episódios são trechos consecutivos com potência média ≥ 10 kW: esse limiar serve para estimar horas em carga e episódios, NÃO para contar janelas válidas nem determinar a quantidade exata de partidas elétricas.")


st.markdown('''<style>
.stApp{background:#f4f8fa;color:#19374a}
header[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1450px;padding-top:1.6rem;padding-bottom:3.5rem}
[data-testid="stSidebar"]{background:#10283a}
[data-testid="stSidebar"] *{color:#eef6f8!important}
h1,h2,h3{color:#12364d;letter-spacing:-.025em}
h1{font-size:2.0rem!important}
.brand{display:flex;align-items:center;gap:.75rem;margin-bottom:1.0rem}
.brand-mark{background:#12364d;color:#fff;width:50px;height:50px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:25px}
.brand-text{font-weight:800;font-size:20px;letter-spacing:.05em;color:#14364d}
.brand-sub{font-size:11px;letter-spacing:.12em;color:#6e8895}
.metric-box{border:1px solid #dce7ec;background:white;border-radius:13px;padding:17px;min-height:125px;box-shadow:0 3px 18px #0a3b4908}
.metric-label{font-size:12px;color:#698391;font-weight:600;min-height:17px}
.metric-value{font-size:27px;font-weight:760;color:#0b7373;margin-top:6px;letter-spacing:-.025em}
.metric-foot{font-size:11px;color:#698391;margin-top:5px}
.context{padding:16px 20px;background:#e5f2f2;border-left:4px solid #15958d;border-radius:7px;color:#315d65;margin:13px 0 20px}
.asset{padding:16px 18px;background:white;border:1px solid #dce7ec;border-radius:12px;min-height:172px}
.asset strong{display:block;font-size:15px;color:#15455b;padding:6px 0}
.asset .tag{font-size:11px;color:#117c79;font-weight:750}
.asset p{color:#687f8b;font-size:12px;line-height:1.5}
[data-testid="stMetric"]{background:white;border:1px solid #dce7ec;border-radius:12px;padding:14px}
</style>''',unsafe_allow_html=True)
st.markdown('''<div class="brand"><div class="brand-mark">T</div><div><div class="brand-text">TRANSFORMA</div><div class="brand-sub">PAINEL TÉCNICO ENERGÉTICO · MACAÉ / RJ</div></div></div>''',unsafe_allow_html=True)
if "focus_code" not in st.session_state: st.session_state["focus_code"]="JAGUAR"
with st.sidebar:
    st.title("Painel técnico")
    page = st.radio("Navegação",NAV,key="nav_page",label_visibility="collapsed")
    st.divider()
    st.caption("Consulta externa · somente leitura")
    st.caption("Análises de energia · dados revisados em: "+date_br(DATA.get("atualizacao","2026-11-18")))
    st.caption("Recorte de dados técnicos. Acesso público sem autenticação.")

if page=="Visão geral":
    st.title("Infraestrutura e comportamento elétrico")
    st.write("Foram realizadas cinco análises de energia, com coletas em equipamentos distintos. Selecione um ponto para explorar o histórico e os gráficos.")
    st.markdown('<div class="context"><b>Escopo:</b> TR1, TR2 e TR3 recebem energia da rede MT e fornecem 220 V entre fases; Bruno e Jaguar operam em 380 V com geradores a diesel. As cinco coletas ocorreram em datas diferentes e não correspondem à medição simultânea de toda a planta.</div>',unsafe_allow_html=True)
    section("Distribuição funcional das cargas")
    cols=st.columns(3)
    for i,e in enumerate(ITEMS):
        with cols[i%3]:
            st.markdown(f'''<div class="asset"><span class="tag">{html.escape(e['tipo'])} · {html.escape(e['tensao'])}</span>
             <strong>{html.escape(e['nome'])}</strong><p>{html.escape(e['descricao'])}</p>
             <small>Coleta de dados: {date_br(e['inicio'])} a {date_br(e['fim'])}</small></div>''',unsafe_allow_html=True)
            st.button("Explorar medições de "+e['codigo'],key="overview_"+e['codigo'],on_click=choose,args=(e['codigo'],True),use_container_width=True)
            st.write("")
    section("Síntese do conjunto disponível")
    cols=st.columns(4)
    with cols[0]:metric("Pontos instrumentados",str(len(ITEMS)),"3 transformadores + 2 trituradores")
    with cols[1]:metric("Análises de energia",str(len(ITEMS)),"Coletas em datas diferentes")
    with cols[2]:metric("Registros históricos",fmt(sum(x['registros'] for x in ITEMS),0),"Incluindo períodos sem grandezas")
    with cols[3]:metric("Meses com indicadores MT",str(len(BILLS)),"Somente grandezas técnicas")
    st.info("Os trituradores foram analisados individualmente, utilizando geradores a diesel. A energia dessas coletas não integra o histórico de faturamento da Enel apresentado para outros períodos.")

elif page=="Análises de energia":
    st.title("Análises de energia — comparação e detalhamento")
    st.caption("Compare as cinco coletas de dados e selecione o equipamento para ver todas as curvas, demandas de 15 minutos, energia e indicadores. As medições não foram simultâneas.")
    glossary()
    rows=[]
    for e in ITEMS:
        rows.append({"Ponto":e["codigo"],"Período":f"{date_br(e['inicio'])} – {date_br(e['fim'])}",
            "P5 máx. (kW)":e['p5_max_kw'],"P15 máx. (kW)":e['p15_max_kw'],
            "S5 máx. (kVA)":e['s5_max_kva'],"S15 máx. (kVA)":e['s15_max_kva'],
            "Leituras completas (%)":round(100*e['validos']/e['registros'],1)})
    st.caption("Selecione uma linha ou utilize os botões abaixo para abrir o equipamento.")
    event=st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True,
        on_select="rerun",selection_mode="single-row",key="select_campaign",
        column_config={x:st.column_config.NumberColumn(format="%.1f") for x in
           ("P5 máx. (kW)","P15 máx. (kW)","S5 máx. (kVA)","S15 máx. (kVA)","Leituras completas (%)")})
    if event.selection.rows:
        st.session_state["focus_code"]=ITEMS[event.selection.rows[0]]["codigo"]
    st.markdown("**Explorar ponto:**")
    asset_buttons("comparison")
    a,b=st.columns(2)
    names=[e['codigo'] for e in ITEMS]
    with a:
        section("Máximos de potência ativa — kW", "P5 e P15 lado a lado: **não se somam**.")
        fig=base_fig(ytitle="kW")
        fig.add_trace(go.Bar(name="P5 · média 5 min",x=names,y=[e['p5_max_kw'] for e in ITEMS],marker_color=COLORS['blue']))
        fig.add_trace(go.Bar(name="P15 · média móvel 15 min",x=names,y=[e['p15_max_kw'] for e in ITEMS],marker_color=COLORS['teal']))
        fig.update_layout(barmode="group")
        st.plotly_chart(fig,use_container_width=True,key="p5_p15_compare")
    with b:
        section("Máximos de potência aparente — kVA", "S5 e S15 também são médias em intervalos diferentes.")
        fig=base_fig(ytitle="kVA")
        fig.add_trace(go.Bar(name="S5 · média 5 min",x=names,y=[e['s5_max_kva'] for e in ITEMS],marker_color=COLORS['blue']))
        fig.add_trace(go.Bar(name="S15 · média 15 min",x=names,y=[e['s15_max_kva'] for e in ITEMS],marker_color=COLORS['orange']))
        fig.update_layout(barmode="group")
        st.plotly_chart(fig,use_container_width=True,key="s5_s15_compare")
    st.info("**Leituras completas (%):** quantidade de registros elétricos completos dividida pelo total de registros da coleta. Bruno: 872/4.288 (20,3%); Jaguar: 519/3.268 (15,9%). Conforme operação informada, paradas de trituração incluem o desligamento do gerador. Esse percentual não indica falha de medição nem duração efetiva de produção.")
    st.divider()
    section("Gráficos e indicadores do equipamento selecionado — " + BY_CODE[st.session_state["focus_code"]]["nome"])
    display_point(BY_CODE[st.session_state["focus_code"]],"comp_"+st.session_state["focus_code"])

elif page=="Simulação Bruno + Jaguar":
    st.title("Bruno + Jaguar — sobreposição hipotética")
    st.markdown('<div class="context"><b>Simulação, não medição simultânea:</b> Bruno foi instrumentado em 2024 e Jaguar em 2026. Os históricos são artificialmente alinhados segundo duas hipóteses distintas.</div>',unsafe_allow_html=True)
    mode=st.selectbox("Hipótese de alinhamento",["dia_hora","episodios"],format_func=lambda k: "Mesmo horário dos dias ativos equivalentes" if k=="dia_hora" else "Início dos episódios equivalentes")
    s=SCENARIOS[mode]
    cols=st.columns(4)
    with cols[0]:metric("P15 sintética máxima",f"{fmt(s['p15_max_kw'])} kW","Média móvel alinhada")
    with cols[1]:metric("S15 por soma de módulos",f"{fmt(s['s15_soma_aritmetica_max_kva'])} kVA","Envoltória, não soma fasorial")
    with cols[2]:metric("P5 sintética máxima",f"{fmt(s['p5_max_kw'])} kW","Média de 5 min")
    with cols[3]:metric("Janelas pareadas válidas",fmt(s['janelas_pareadas_15min'],0),"Ambos com dados nesse alinhamento")
    section("Perfil sintético por episódio/alinhamento", "As descontinuidades entre grupos são mostradas como quebras, evitando criar uma rampa fictícia entre episódios.")
    df=pd.DataFrame(s['janelas_15min_amostra'])
    if not df.empty:
        df['grupo']=df['marcador'].astype(str).str.split(' · ').str[0]
        fig=base_fig(ytitle="Potência sintética")
        for idx,(name,unit,color) in enumerate([('p15_kw','P15 (kW)',COLORS['teal']),('s15_superior_kva','S15 superior (kVA)',COLORS['orange'])]):
            xx=[];yy=[];custom=[];last_group=None
            for i,row in df.iterrows():
                if last_group is not None and row['grupo']!=last_group:
                    xx.append(i-.5);yy.append(None);custom.append('')
                xx.append(i); yy.append(row[name]);custom.append(row['marcador']); last_group=row['grupo']
            fig.add_trace(go.Scatter(x=xx,y=yy,customdata=custom,mode="lines",name=unit,
                line=dict(color=color,width=1.8),connectgaps=False,hovertemplate="Grupo %{customdata}<br>%{y:.1f}<extra>"+unit+"</extra>"))
        fig.update_xaxes(title="Sequência dos intervalos pareados (posição sintética)")
        st.plotly_chart(fig,use_container_width=True,key="synthetic_trace")
    st.caption(s.get('aviso',''))
    a,b,c=st.columns(3)
    with a:st.metric("P95 da P15 sintética",f"{fmt(s['p15_p95_kw'])} kW")
    with b:st.metric("Maior pico aparente alinhado",f"{fmt(s['s_intra_soma_aritmetica_max_kva'])} kVA")
    with c:st.metric("Soma dos máximos isolados",f"{fmt(s['s_intra_maximos_individuais_soma_kva'])} kVA")
    st.warning("Estes cenários não reproduzem necessariamente partidas simultâneas. Não podem ser tratados como demanda fiscal nem como dimensionamento definitivo de subestação ou transformador.")

elif page=="Entrada em média tensão":
    st.title("Entrada em média tensão — indicadores mensais")
    st.caption("Indicadores transcritos das faturas da Enel (jan.–ago./2026), no ponto de entrega em MT. Os trituradores a diesel não estão incluídos no consumo medido nesses períodos.")
    f=pd.DataFrame(BILLS)
    f['consumo_kwh']=f['energia_ponta_kwh']+f['energia_fora_kwh']
    f['mes_label']=pd.to_datetime(f['mes']).dt.strftime('%m/%Y')
    c=st.columns(4)
    with c[0]:metric("Maior demanda fora de ponta",f"{fmt(f['demanda_fora_kw'].max())} kW","Máximo dos meses fornecidos")
    with c[1]:metric("Demanda contratada",f"{fmt(f['contratada_kw'].iloc[-1])} kW","Último mês disponível")
    with c[2]:metric("Consumo histórico",f"{fmt(f['consumo_kwh'].sum(),0)} kWh","Soma dos períodos")
    with c[3]:metric("Meses disponíveis",str(len(f)),"Jan.–ago./2026")
    section("Demanda fora de ponta por mês")
    fig=base_fig(ytitle="Demanda (kW)")
    fig.add_trace(go.Bar(x=f['mes_label'],y=f['demanda_fora_kw'],name="Registrada",marker_color=COLORS['blue']))
    fig.add_trace(go.Scatter(x=f['mes_label'],y=f['contratada_kw'],mode="lines+markers",name="Contratada",line=dict(color=COLORS['orange'],dash='dash',width=2)))
    st.plotly_chart(fig,use_container_width=True,key="faturamento_demanda")
    section("Consumo mensal na entrada de MT")
    fig=base_fig(ytitle="Energia (kWh)")
    fig.add_trace(go.Bar(x=f['mes_label'],y=f['energia_fora_kwh'],name="Fora ponta",marker_color=COLORS['teal']))
    fig.add_trace(go.Bar(x=f['mes_label'],y=f['energia_ponta_kwh'],name="Ponta",marker_color=COLORS['orange']))
    fig.update_layout(barmode='stack')
    st.plotly_chart(fig,use_container_width=True,key="faturamento_energia")
    view=f[['mes_label','demanda_ponta_kw','demanda_fora_kw','contratada_kw','consumo_kwh']].rename(columns={'mes_label':'Mês','demanda_ponta_kw':'Demanda ponta (kW)','demanda_fora_kw':'Demanda fora ponta (kW)','contratada_kw':'Contratada (kW)','consumo_kwh':'Energia total (kWh)'})
    st.dataframe(view,hide_index=True,use_container_width=True)
    st.info("Valores financeiros, tarifas, créditos e as faturas PDF originais não são publicados neste portal.")

else:
    st.title("Metodologia e limitações")
    glossary()
    st.markdown('''
    **Origem.** Cinco análises de energia obtidas com o analisador em períodos distintos e indicadores técnicos históricos da entrada em média tensão (MT).

    **Janelas de demanda.** P15 é reconstruída de três amostras válidas e consecutivas de cinco minutos. Nenhuma amostra sem grandezas é transformada em zero. A curva é interrompida quando há falta de janelas completas; o zoom do gráfico permite ver a intermitência.

    **Leituras completas (%).** Quantidade de registros elétricos completos dividida pelo total de registros da coleta. Segundo a informação operacional fornecida, Bruno e Jaguar deixam de registrar grandezas quando ocorre parada de produção com desligamento do gerador e do triturador. O percentual não mede tempo de produção; para TR1, TR2 e TR3, lacunas devem ser examinadas separadamente.

    **Comparações.** P5 e P15 (assim como S5 e S15) são medidas em durações diferentes da **mesma carga**: aparecem lado a lado, não somadas. As coletas duraram tempos diferentes; energia total não deve ser tratada como consumo diário comparável. **Janelas móveis de 15 minutos** são médias sobrepostas com dados completos, não partidas elétricas. O histograma conta essas janelas por faixa de kW; a curva de duração as ordena da maior para a menor potência.

    **Relação P/S.** O quociente P15/S15 é indicador descritivo; não substitui fator de potência fiscal, medições de harmônicos ou testes de qualidade de energia.

    **Trituradores.** Bruno (2024) e Jaguar (2026) foram medidos separadamente. O desligamento de geradores e máquinas nas paradas de produção foi informado pela operação. Cenários alinhados são hipóteses de simultaneidade sem medição conjunta; não comprovam demanda real conjunta nem dimensionamento definitivo de 1.000 kVA.

    **Média tensão.** Os dados de fatura são da entrada da distribuidora. Não há sincronismo temporal entre essas faturas e os períodos das cinco análises de energia.

    **Privacidade.** Somente recortes técnicos e séries derivadas foram disponibilizados. Sem senhas e sem função de importar, editar ou consultar arquivos de gestão interna.
    ''')

st.divider()
st.caption("TRANSFORMA · Portal técnico energético · Consulta externa · Revisão 6.0 · Cinco análises de energia independentes")