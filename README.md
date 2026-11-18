# Portal técnico energético — Transforma (externo)

Versão em Streamlit Community Cloud do portal de apresentação técnica.

## Conteúdo
- Distribuição funcional TR1, TR2 e TR3 e trituradores Bruno/Jaguar
- Séries de potência aparente e ativa de 15 minutos (amostras para apresentação)
- Resultados e indicadores das campanhas completas
- Cenários **hipotéticos** de sobreposição dos históricos Bruno (2024) e Jaguar (2026)
- Indicadores técnicos de energia e demanda na entrada em média tensão (jan–ago/2026)

O arquivo `dados.json` contém exclusivamente o recorte técnico destinado à apresentação externa. Não existem senhas, faturas originais, preços, contas, bancos de dados ou planilhas brutas. Este aplicativo é **público e sem autenticação**.

## Rodar local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar no Streamlit Community Cloud
1. Em https://share.streamlit.io, autentique-se usando o GitHub.
2. `Create app` → `Yup, I have an app`.
3. Repositório: `MTH-Comercial/Dashboard-TRF`.
4. Branch: `portal-energia-externo`.
5. Main file path: `portal_energia_externo/app.py`.
6. Defina um subdomínio disponível e clique `Deploy`.
7. Ajuste a visibilidade como **Public** (sem senha).

> Se hospedar em outra branch ou repositório, atualize os campos acima.

## Atualizar dados publicados
Substitua somente `dados.json` com uma exportação revisada do **dashboard interno**. Não envie planilhas XLSX, PDFs de faturas nem banco de dados privado. A publicação em nuvem usa o snapshot do GitHub e não lê automaticamente dados do notebook.

## Limitações
- Os trituradores não foram medidos de forma simultânea.
- As curvas são dados históricos e cenários, não estimativas fiscais definitivas.
- A publicação implica que indicadores técnicos e informações sobre cargas fiquem acessíveis publicamente.