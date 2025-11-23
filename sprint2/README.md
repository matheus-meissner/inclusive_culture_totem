# 🧠 Totem Inteligente Inclusivo – Sprint 2  
## Challenge Flexmedia – Integração Sensores + SQL + Análise de Dados

Esta sprint implementa a **primeira versão funcional** do fluxo:

> Sensor (simulado) → Banco SQL (SQLite) → Análise em Python → Dashboard (Streamlit)

A proposta é demonstrar como o Totem Flexmedia pode registrar, armazenar e analisar interações de usuários em um fluxo real de dados.

---

## 📂 Estrutura da Sprint 2

```text
sprint2/
 ┣ analysis/
 ┃ ┗ analysis.ipynb         # Notebook com leitura do banco, estatística e ML supervisionado simples
 ┣ dashboard/
 ┃ ┗ app.py                 # Dashboard interativo em Streamlit
 ┣ database/
 ┃ ┗ totem.db               # Banco SQLite gerado automaticamente pelo simulador
 ┣ sensor_simulation/
 ┃ ┗ simulate_sensor.py     # Simulação de sensores (ESP32 / presença / toque / voz)
 ┣ README.md                # Este arquivo
 ┗ video_script.md          # Roteiro sugerido para o vídeo de demonstração
