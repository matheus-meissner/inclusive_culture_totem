# 🏛️ Tótem Inteligente Inclusivo — Cultura para Todos

**Desenvolvido por:** Matheus Iembo Meissner  
**Instituição:** FIAP — Challenge Flexmedia  
**Projeto:** Tótem Inteligente para espaços culturais (museus, bibliotecas, centros culturais)

---

> ⚠️ **Declaração:** Este projeto **não concorre ao prêmio de melhor projeto Flexmedia** no Festival NEXT.  
> A solução deve ser mantida em sigilo pela equipe de tutores para fins exclusivos de avaliação acadêmica.

---

## 📌 Sobre o Projeto

O **Tótem Inteligente Inclusivo** é uma solução interativa instalada em espaços de visitação cultural, capaz de:

- Detectar a presença de visitantes via sensores e visão computacional
- Interagir por texto, toque e voz
- Recomendar exposições, eventos e conteúdos personalizados
- Gerar métricas de engajamento e comportamento dos visitantes
- Oferecer recursos completos de acessibilidade (Libras, Braille, áudio)

---

## 🗂️ Estrutura do Repositório

```
inclusive_culture_totem/
├── sprint1/          # Planejamento, arquitetura e proposta técnica
├── sprint2/          # Protótipo de sensores e interface
├── sprint3/          # Pipeline de dados, ML e dashboard inicial
└── sprint4/          # IA, chatbot, visão computacional, voz — Entrega Final
```

---

## 🚀 Sprint 4 — Entrega Final (Como Executar)

```bash
# 1. Instalar dependências
cd sprint4/
pip install -r requirements.txt

# 2. Rodar pipeline completo
python main.py all

# 3. Abrir dashboard interativo
streamlit run dashboard/app.py
```

➡️ Documentação completa da Sprint 4: [`sprint4/README_Sprint4.md`](sprint4/README_Sprint4.md)

---

## 🎬 Vídeo de Apresentação

> 🔗 Link YouTube (não listado): https://youtu.be/lpHy-NsB8sE

---

## 📊 Resumo das Sprints

| Sprint | Foco | Principais Entregas |
|:---:|---|---|
| **1** | Arquitetura e Planejamento | Diagrama da solução, stack tecnológica, plano de desenvolvimento |
| **2** | Sensores e Interface | Simulação ESP32, coleta de dados, interface inicial |
| **3** | Dados e ML | Pipeline sensor→SQLite→RandomForest→Dashboard Streamlit |
| **4** | IA Completa | Chatbot NLP, visão computacional, voz, dashboard 5 abas, relatório automático |

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologias |
|---|---|
| Linguagem | Python 3.10+ |
| Banco de dados | SQLite (6 tabelas) |
| Machine Learning | scikit-learn (RandomForest, DummyClassifier) |
| Dashboard | Streamlit |
| Chatbot (NLP) | 100% local — regras + detecção de intenção por keywords |
| Visão computacional | OpenCV (câmera real) / Simulação inteligente |
| Reconhecimento de voz | SpeechRecognition + Whisper (microfone real) / Simulação |
| Análise de dados | pandas, matplotlib |
| Notebook | Jupyter (analysis.ipynb) |

---

## 👤 Equipe

| Membro | RM | Função |
|---|---|---|
| Matheus Iembo Meissner | RM567080 | Desenvolvedor e Arquiteto de Solução |

---

*FIAP — Challenge Flexmedia 2026*
