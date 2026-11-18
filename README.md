# Transforma — Portal Técnico Energético Externo (v6.0)

Dashboard público, sem autenticação, de consulta técnica ao comportamento elétrico da Transforma. Independente do dashboard interno.

## Aplicativo
- URL: https://transforma-energia.streamlit.app/
- Repositório: `MTH-Comercial/transforma-energia-externo`
- Branch: `main`
- Arquivo: `app.py`

## O que há no portal
- **Visão geral:** cinco análises de energia realizadas em TR1, TR2, TR3, triturador Bruno e triturador Jaguar.
- **Análises de energia:** comparação de P5/P15 em kW e S5/S15 em kVA, seleção de equipamento, curvas de potência ativa/aparente, tensões, perfil de demanda, energia diária, horas em carga e mapa de carga sempre de **00h a 23h**.
- **Simulação Bruno + Jaguar:** cenários de sobreposição **hipotética** entre coletas não simultâneas.
- **Entrada em média tensão:** indicadores técnicos históricos da unidade medidos pela Enel.
- **Metodologia:** definições e limites de interpretação para projetistas e público geral.

## Entenda os indicadores
- **P5** = potência ativa média de 5 min (kW); **P15** = média móvel em 15 min calculada com três leituras completas de 5 min. Não se somam.
- **S5/S15** = potência aparente média (kVA) em períodos de 5/15 min.
- **Janelas móveis válidas** = médias calculáveis em três registros completos consecutivos, não acionamentos ou partidas. Janelas móveis se sobrepõem.
- **Histograma de P15:** número de janelas móveis dentro de cada faixa de demanda (kW).
- **Curva de duração de P15:** janelas ordenadas da maior para a menor demanda; o percentual horizontal se refere às janelas com dados, não ao tempo integral de calendário.
- **Percentil 95 (P95):** 95% das janelas calculadas ficaram até esse patamar; não é a demanda máxima.
- **Leituras completas:** registros com dados elétricos disponíveis ÷ registros totais da análise. Nos trituradores, os períodos sem valores são compatíveis com desligamento da máquina e do gerador durante a parada de produção, conforme informado pela operação. Isso não é tempo em carga nem, por si só, defeito de medição.
- **Episódios de carga >= 10 kW:** critério apenas para identificar atividade observada. Não se confunde com janelas válidas.

## Cuidados com os dados
O portal contém somente dados técnicos selecionados, não contém faturas originais, tarifas, valores financeiros, banco administrativo, senhas nem planilhas de medição brutas.

Bruno (2024) e Jaguar (2026) foram medidos separadamente; os cenários de simultaneidade não são medições conjuntas e não autorizam, isoladamente, dimensionamento final da subestação.

Os CSVs em `series/` são séries técnicas derivadas; intervalos sem grandezas ficam em branco, nunca preenchidos automaticamente com zero.

## Executar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Atualização na nuvem
Mudanças na branch `main` geralmente disparam nova implantação do Streamlit Community Cloud. A execução deve ser conferida no site ou nos registros de implantação.