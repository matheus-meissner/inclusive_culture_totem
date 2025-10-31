🎓 Totem Inteligente Inclusivo — Cultura para Todos
Desenvolvido por: Matheus Iembo Meissner

📚 FIAP – Challenge FlexMedia
🗓️ Sprint 1 – Proposta Técnica (Planejamento e Arquitetura)

🧩 1. Introdução e Justificativa

O projeto Totem Inteligente Inclusivo – Cultura para Todos tem como objetivo desenvolver uma solução inovadora para centros culturais e bibliotecas, promovendo acessibilidade, inclusão digital e engajamento sociocultural.

A proposta visa criar um totem interativo com Inteligência Artificial, capaz de auxiliar visitantes — incluindo pessoas com deficiência visual, auditiva e motora — a encontrar livros, eventos, oficinas e exposições de acordo com seus interesses pessoais.

A motivação surge da necessidade crescente de democratizar o acesso à cultura e à informação, garantindo que todos os públicos possam usufruir de experiências tecnológicas personalizadas e acessíveis.

🎯 2. Objetivos

Promover acessibilidade em espaços culturais e bibliotecas, com comandos de voz, tradução em Libras e texto ampliado.

Oferecer recomendações personalizadas de livros, eventos e oficinas, com base em preferências e perfil do visitante.

Garantir privacidade e segurança no tratamento dos dados coletados.

Integrar sensores e interfaces inteligentes para interações multissensoriais (voz, toque, presença).

Criar uma arquitetura escalável, integrando hardware (ESP32 e sensores) com serviços em nuvem e IA.

🧠 3. Descrição da Solução

O Totem Inteligente Inclusivo combina sensores físicos, reconhecimento de voz, análise de preferências e assistência visual e sonora para oferecer uma experiência imersiva.

Quando um visitante se aproxima, o sistema detecta sua presença e inicia uma interação adaptada às suas necessidades.
O visitante pode:

Falar com o totem (comando de voz);

Escolher a tradução automática em Libras (via avatar digital);

Aumentar o tamanho da fonte no display;

Receber recomendações de livros, oficinas e eventos com base em seu perfil.

🧱 4. Arquitetura Técnica

A arquitetura é dividida em três camadas principais:

4.1 Hardware

ESP32 / ESP32-CAM: controle de sensores e captura de imagens (para detecção de presença e expressões).

Sensores de presença (PIR): para iniciar interações automaticamente.

Microfone e alto-falante: reconhecimento e resposta por voz.

Display touch de 10": interface com texto ampliado e opções visuais.

Módulo de vibração (opcional): retorno tátil para acessibilidade motora.

4.2 Software e IA

Speech-to-Text e Text-to-Speech (Azure Cognitive Services) para interação por voz.

Tradução em Libras (plugin de avatar 3D de Libras, ex: VLibras API).

Modelo de recomendação (Machine Learning): sugerir eventos/livros conforme preferências.

Interface Web (HTML + JS) hospedada em Azure App Service.

4.3 Nuvem e Integração

Azure IoT Hub para comunicação entre sensores e nuvem.

Azure Functions para processamento de dados e IA.

Azure Cosmos DB / Blob Storage para armazenamento de interações e estatísticas.

Power BI Dashboard para análise de uso e métricas de acessibilidade.

🌐 5. Diagrama da Solução (descrição para montagem)

<img width="1474" height="484" alt="diagram-export-10-31-2025-2_31_48-PM" src="https://github.com/user-attachments/assets/7f623587-f1a0-4dbf-87b4-9863717f2701" />

🔒 6. Segurança e Privacidade de Dados

Dados de voz e interações são anonimizados e usados apenas para métricas de uso.

Conexões entre o totem e a nuvem usam protocolo HTTPS e autenticação via token IoT Hub.

O sistema segue as diretrizes da LGPD, garantindo consentimento e proteção de dados pessoais.

Logs e dados sensíveis são criptografados em repouso (AES-256) e em trânsito (TLS 1.2+).

🚀 7. Estratégia de Desenvolvimento (Plano de Sprints)
Sprint	Entregas Principais	Objetivos Técnicos
1	Planejamento e Arquitetura	Definir escopo, tecnologias e diagrama de solução.
2	Protótipo de interface e sensores	Simular interação (voz e toque) e coleta de dados.
3	IA de Recomendação + Dashboard	Implementar IA para recomendações e métricas no Power BI.
4	Integração final e testes de acessibilidade	Testes com PCDs e validação de usabilidade.
👥 8. Responsabilidades (Individual – Sprint 1)
Membro	Função	Responsabilidades
Matheus Iembo Meissner	Desenvolvedor e Arquiteto de Solução	Planejamento técnico, diagramação da arquitetura, definição de tecnologias, documentação e estratégia de integração.
🧰 9. Tecnologias e Ferramentas
Categoria	Tecnologias
Hardware	ESP32, ESP32-CAM, sensores PIR, microfone e display touch
IA e Voz	Azure Cognitive Services (Speech + Translator + VLibras)
Backend/Nuvem	Azure Functions, Azure IoT Hub, Azure Cosmos DB
Frontend	HTML5, CSS3, JavaScript, interface web acessível
Análise de Dados	Power BI, Azure Monitor
Documentação	GitHub (README), Draw.io para diagramas
🧾 10. Estrutura do Repositório
📦 TotemInclusivo-CulturaParaTodos
 ┣ 📁 docs
 ┃ ┗ 🧠 arquitetura-diagrama.png
 ┣ 📁 assets
 ┃ ┗ 🗣️ mockups-interacao/
 ┣ 📄 README.md
 ┣ 📄 plano_de_desenvolvimento.md
 ┣ 📄 arquitetura_tecnica.md
 ┗ 📄 tecnologias_utilizadas.md

🏁 11. Conclusão

O Totem Inteligente Inclusivo – Cultura para Todos representa uma proposta real e tecnicamente viável para democratizar o acesso à informação e à cultura.
Unindo IA, sensores e acessibilidade digital, o projeto coloca a inclusão social no centro da inovação tecnológica.
