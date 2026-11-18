# Portal técnico energético — Transforma

Dashboard externo **público e sem senha**, desenvolvido em Streamlit para consulta técnica de TR1, TR2, TR3 e trituradores Bruno/Jaguar. Projeto independente do dashboard administrativo.

## Publicação no Streamlit Community Cloud

- Repositório: `MTH-Comercial/transforma-energia-externo`
- Branch: `main`
- Arquivo principal: `app.py`
- Acesso: **Public** (não exige senha)

Acesse https://share.streamlit.io/, conecte sua conta GitHub, selecione **Create app**, este repositório, branch `main` e arquivo `app.py`. Confirme a publicação na sua conta Streamlit.

## Conteúdo e limites

Este repositório contém **somente o recorte técnico para apresentação externa** (`dados.json`), sem faturas digitalizadas, custos, planilhas brutas, senhas ou base administrativa. Os indicadores de média tensão são históricos; as curvas amostradas não devem ser confundidas com medições simultâneas. Os cenários Bruno/Jaguar sobrepõem artificialmente campanhas de 2024 e 2026 e **não são demanda conjunta medida**.

## Executar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Atualização dos dados

Atualize `dados.json` somente após revisar e aprovar o recorte de apresentação externa. Não copie arquivos do sistema interno para este repositório.
