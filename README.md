# 🧠 Totem Inteligente Inclusivo — Cultura para Todos  
**Desenvolvido por:** Matheus Iembo Meissner  

## 🏫 FIAP – Challenge FlexMedia  
### 🧩 Sprint 1 – Proposta Técnica (Planejamento e Arquitetura)

---

## 🧠 1. Introdução e Justificativa  

O projeto **Totem Inteligente Inclusivo – Cultura para Todos** tem como objetivo desenvolver uma solução inovadora para **centros culturais e bibliotecas**, promovendo **acessibilidade, inclusão digital e engajamento sociocultural**.

A proposta visa criar um **totem interativo com Inteligência Artificial**, capaz de auxiliar visitantes — incluindo pessoas com deficiência visual, auditiva e motora — a **encontrar livros, eventos, oficinas e exposições** de acordo com seus interesses pessoais.

A motivação surge da necessidade crescente de **democratizar o acesso à cultura e à informação**, garantindo que todos os públicos possam usufruir de experiências tecnológicas personalizadas e acessíveis.

---

## 🎯 2. Objetivos  

- Promover **acessibilidade** em espaços culturais e bibliotecas, com comandos de voz, tradução em Libras e texto ampliado.  
- Oferecer **recomendações personalizadas** de livros, eventos e oficinas, com base em preferências e perfil do visitante.  
- Garantir **privacidade e segurança** no tratamento dos dados coletados.  
- Integrar **sensores e interfaces inteligentes** para interações multissensoriais (voz, toque e presença).  
- Criar uma **arquitetura escalável**, integrando hardware (ESP32 e sensores) com serviços em nuvem e IA.  

---

## 🧩 3. Descrição da Solução  

O **Totem Inteligente Inclusivo** combina sensores físicos, reconhecimento de voz, análise de preferências e assistência visual e sonora para oferecer uma experiência imersiva.

Quando um visitante se aproxima, o sistema detecta sua presença e inicia uma interação adaptada às suas necessidades.  
O visitante pode:

- Falar com o totem (comando de voz);  
- Escolher a tradução automática em Libras (via avatar digital);  
- Aumentar o tamanho da fonte no display;  
- Receber recomendações de livros, eventos e oficinas com base em seu perfil.  

---

## 🧱 4. Arquitetura Técnica  

A arquitetura é dividida em três camadas principais:

### 🔹 4.1 Hardware  
- **ESP32 / ESP32-CAM:** controle de sensores e captura de imagens.  
- **Sensores de presença (PIR):** iniciam a interação automaticamente.  
- **Microfone e alto-falante:** reconhecimento e resposta por voz.  
- **Display touch:** interface acessível.  
- **Módulo de vibração (opcional):** feedback tátil para acessibilidade motora.  

### 🔹 4.2 Software e IA  
- **Speech-to-Text e Text-to-Speech (Azure Cognitive Services)** para interação por voz.  
- **Tradução em Libras (VLibras API)** para acessibilidade auditiva.  
- **IA de recomendação (Machine Learning)** para sugerir conteúdo.  
- **Interface Web (HTML + JS)** hospedada no **Azure App Service**.  

### 🔹 4.3 Nuvem e Integração  
- **Azure IoT Hub**: comunicação entre sensores e nuvem.  
- **Azure Functions**: processamento e automação de dados.  
- **Azure Cosmos DB**: armazenamento de interações e preferências.  
- **Power BI Dashboard**: análise de engajamento e métricas de acessibilidade.  

---

## 🌐 5. Diagrama da Solução  

Representação do fluxo da arquitetura:
<img width="1474" height="484" alt="diagram-export-10-31-2025-2_31_48-PM" src="https://github.com/user-attachments/assets/8f5ee2e4-b7d8-436b-9745-ab0eb5999c28" />

---

## 🔒 6. Segurança e Privacidade de Dados  

- Dados de voz e interação são **anonimizados**.  
- Comunicação segura com **HTTPS + autenticação via token IoT Hub**.  
- Conformidade com a **LGPD**.  
- Criptografia em repouso (**AES-256**) e em trânsito (**TLS 1.2+**).  

---

## 🚀 7. Estratégia de Desenvolvimento (Plano de Sprints)  

| Sprint | Entregas Principais | Objetivos Técnicos |
|:------:|:--------------------|:-------------------|
| **1** | Planejamento e Arquitetura | Definição do escopo, tecnologias e diagrama da solução. |
| **2** | Protótipo de Interface e Sensores | Simular interação por voz e toque. |
| **3** | IA de Recomendação + Dashboard | Implementar análise de engajamento e relatórios. |
| **4** | Testes de Acessibilidade e Integração | Validação final e ajustes de usabilidade. |

---

## 👥 8. Responsabilidades  

| Membro | Função | Responsabilidades |
|:-------|:--------|:-----------------|
| **Matheus Iembo Meissner** | Desenvolvedor e Arquiteto de Solução | Planejamento técnico, diagramação, definição de tecnologias, documentação e integração. |

---

## 🧰 9. Tecnologias Utilizadas  

| Categoria | Tecnologias |
|:-----------|:-------------|
| **Hardware** | ESP32, ESP32-CAM, sensores PIR, microfone e display touch |
| **IA e Voz** | Azure Cognitive Services (Speech + Translator + VLibras) |
| **Backend/Nuvem** | Azure Functions, Azure IoT Hub, Azure Cosmos DB |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Análise de Dados** | Power BI, Azure Monitor |
| **Documentação** | GitHub (README), Draw.io |

---

## 🧾 10. Estrutura do Repositório  
```
📦 inclusive_culture_totem
┣ 📁 docs
┃ ┗ 🧠 arquitetura-diagrama.png
┣ 📁 assets
┃ ┗ 🗣️ mockups-interacao/
┣ 📄 README.md
┣ 📄 plano_de_desenvolvimento.md
┣ 📄 arquitetura_tecnica.md
┗ 📄 tecnologias_utilizadas.md
```

---

## 🏁 11. Conclusão  

O **Totem Inteligente Inclusivo – Cultura para Todos** representa uma proposta tecnicamente viável e socialmente relevante, unindo **Inteligência Artificial, sensores e acessibilidade digital** para democratizar o acesso à cultura.
