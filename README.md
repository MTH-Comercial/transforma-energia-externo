# Transforma — Portal Técnico Energético Externo (v5.0)

Dashboard público de consulta técnica, independente do sistema administrativo e sem autenticação.

## Publicação
- Repositório: `MTH-Comercial/transforma-energia-externo`
- Branch: `main`
- Arquivo: `app.py`
- Endereço: https://transforma-energia.streamlit.app/

## O que mudou
- Seleção interativa de TR1, TR2, TR3, Bruno e Jaguar.
- Séries derivadas completas em `series/*.csv`, com **quebras explícitas nos intervalos sem três medições válidas e consecutivas de 5 minutos**; não se interpola consumo nem se inventam valores zero.
- Curvas de P15 e S15, tensões entre fases, relação P/S, energia diária, horas em carga, distribuição de demanda, curva de duração e mapa horário.
- Comparação de P5 x P15 e S5 x S15 em **barras agrupadas**, não empilhadas.
- Simulações de Bruno e Jaguar continuam identificadas como hipóteses de sobreposição de campanhas independentes.

## Interpretação
**P5** e **S5** são máximos de potência média em cinco minutos. **P15 móvel** e **S15** são médias em janelas consecutivas de quinze minutos. Máximos intra-intervalo não são demanda fiscal.

**Cobertura** corresponde a registros completos ÷ registros totais da campanha, **não** ao percentual de funcionamento. Períodos sem grandezas não são automaticamente motor desligado.

Bruno e Jaguar foram medidos em períodos diferentes. As simulações não são medições simultâneas nem dimensionamento definitivo de subestação.

## Atualização de dados
Publique somente dados técnicos previamente revisados. Nunca inclua planilhas brutas, PDFs de fatura, tarifas, preços, credenciais ou banco de dados administrativo neste repositório público.

## Executar local
```bash
pip install -r requirements.txt
streamlit run app.py
```
