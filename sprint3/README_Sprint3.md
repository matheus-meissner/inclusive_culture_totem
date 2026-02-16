# 🧠 Sprint 3 --- Totem Inteligente Inclusivo

## Integração Profissional: Sensores → Banco → ML → Dashboard → Report → Orquestração

Repositório geral: https://github.com/matheus-meissner/inclusive_culture_totem  
Vídeo da Sprint 2: https://youtu.be/YS9H5aj9bus


**Última atualização:** 2026-02-16 15:25:35 UTC

------------------------------------------------------------------------

# 📌 1. Objetivo da Sprint 3

Consolidar pelo menos **60% dos módulos do sistema** em um fluxo
funcional integrado, garantindo:

-   Coleta de dados simulados (sensor)
-   Persistência estruturada (SQLite)
-   Treinamento de Machine Learning supervisionado
-   Geração de métricas e artifacts
-   Inferência com gravação de previsões
-   Dashboard interativo (Streamlit)
-   Relatório automático em Markdown
-   Orquestração completa via 1 comando

------------------------------------------------------------------------

# 🚀 2. Execução Rápida (Modo Avaliador)

Dentro da pasta `sprint3/`:

``` bash
python main.py all --seconds 60
```

Esse comando executa:

-   init-db
-   ingest
-   train
-   predict
-   report

### 📸 Evidência do pipeline completo

Arquivo esperado:

    ![Report 1](docs/prints/count_predicts.png)

------------------------------------------------------------------------

# 🏗️ 3. Estrutura do Projeto (Sprint 3)

    sprint3/
    │
    ├── main.py
    ├── sensor/
    ├── database/
    ├── ml/
    │   └── artifacts/
    ├── reports/
    ├── dashboard/
    └── docs/prints/

------------------------------------------------------------------------

# 🟦 4. Simulação de Sensores

Arquivo:

    sensor/simulate_sensor.py

Geração contínua:

``` bash
python -m sensor.simulate_sensor
```

Geração em volume (bulk):

``` bash
python -m sensor.simulate_sensor --bulk 5000 --devices 5 --days 7
```

### 📸 Prints relacionados

    <img width="818" height="204" alt="count_predicts" src="https://github.com/user-attachments/assets/b8912f70-7377-4f13-ba45-aa5b4652c7c6" />

------------------------------------------------------------------------

# 🟫 5. Banco de Dados (SQLite)

-   Tabela: `interactions`
-   Tabela: `predictions`
-   Integridade: UNIQUE(device_id, event_timestamp)

### 📸 Evidências

    <img width="818" height="204" alt="count_predicts" src="https://github.com/user-attachments/assets/3663c009-ced7-4a45-a0a5-54883f5ab5e8" />

------------------------------------------------------------------------

# 🟧 6. Machine Learning (Supervisionado)

## Target

-   quick (≤5s)
-   normal (6--20s)
-   engaged (≥21s)

## Modelos

1.  DummyClassifier (baseline)
2.  RandomForest (FULL)
3.  RandomForest (sem duration_s --- sanity check)

## Métricas

-   Accuracy
-   F1-macro
-   Matriz de Confusão

### 📸 Prints ML

    <img width="738" height="782" alt="ml_train1" src="https://github.com/user-attachments/assets/906c87c3-1179-4082-9b99-d4a06d6734c7" />

    <img width="788" height="500" alt="ml_train2" src="https://github.com/user-attachments/assets/50bc649b-dd4c-48f4-8ea7-c6a8b94974bc" />

    <img width="255" height="138" alt="ml_artifacts" src="https://github.com/user-attachments/assets/00e07bcb-2ecf-41d7-9587-21cee661ea0a" />


Artifacts gerados:

    ml/artifacts/model.pkl
    ml/artifacts/metrics.json
    ml/artifacts/confusion_matrix.png
    ml/artifacts/confusion_matrix_no_duration.png

------------------------------------------------------------------------

# 🟨 7. Inferência (Predictions)

Arquivo:

    ml/predict.py

Grava previsões no banco.

### 📸 Evidência

    <img width="752" height="744" alt="ml_predict" src="https://github.com/user-attachments/assets/1be440c4-06ea-48ed-a5e0-c76d59263482" />

------------------------------------------------------------------------

# 🟦 8. Dashboard (Streamlit)

Rodar:

``` bash
streamlit run dashboard/app.py
```

## Abas:

-   Visão Geral
-   Machine Learning
-   Dados

### 📸 Prints Dashboard

    <img width="1677" height="871" alt="streamlit_visao_geral" src="https://github.com/user-attachments/assets/ddf9fc34-0e97-4a88-a08d-b71cd5766dba" />
    <img width="1692" height="906" alt="streamlit_visao_geral2" src="https://github.com/user-attachments/assets/c81ab2f0-0d25-41a0-bb26-74d2bbc9fe96" />
    <img width="1249" height="936" alt="streamlit_ml_visao_geral" src="https://github.com/user-attachments/assets/350773b0-097a-45d5-84d0-8672a03c8720" />
    <img width="926" height="722" alt="streamlit_ml_matriz_confusao" src="https://github.com/user-attachments/assets/1a96c49f-6410-4cf5-869b-bdaebfb3f93e" />
    <img width="927" height="503" alt="streamlit_ml_previsoes_banco" src="https://github.com/user-attachments/assets/360cf358-0a4f-44ba-bfdb-4ff1bb7219bf" />
    <img width="929" height="568" alt="streamlit_ml_ultimas_previsoes" src="https://github.com/user-attachments/assets/1007b3f8-49f5-4cb5-a514-792034f287af" />

------------------------------------------------------------------------

# 🧾 9. Report Automático

Gerado por:

``` bash
python -m reports.generate_report
```

Arquivo:

    reports/report.md

### 📸 Prints do Report

    <img width="1058" height="964" alt="report md_1" src="https://github.com/user-attachments/assets/d6e499b5-c966-46e0-83fb-4334dfa1ac0f" />
    <img width="1033" height="890" alt="report md_2" src="https://github.com/user-attachments/assets/e5cc4cfe-18ac-4e42-8beb-cb339eebbbd7" />
    <img width="1080" height="872" alt="report md_3" src="https://github.com/user-attachments/assets/216bfb70-6df1-461f-9a47-f4f114e9adb7" />
    <img width="1038" height="652" alt="report md_4" src="https://github.com/user-attachments/assets/80fc01f5-665c-48ef-9a90-4b7426040470" />

------------------------------------------------------------------------

# 🏁 10. Conclusão

A Sprint 3 consolida o Totem como um sistema completo, integrado e
validado:

-   Pipeline fim-a-fim funcional
-   ML com baseline + modelo principal + sanity check
-   Persistência estruturada
-   Dashboard interativo
-   Report automático
-   Orquestração profissional

Projeto pronto para documentação final e apresentação em vídeo.
