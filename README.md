# 📦 Procurement Intelligence Agent (PIA)

**Multi-agent AI system for supply chain risk analysis and procurement strategy generation.**
Built by a procurement professional who has managed supplier contracts for 8 years — this system automates what a strategic sourcing team does when a key supplier starts slipping.

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Tests](https://img.shields.io/badge/tests-6%2F6-brightgreen)
![LLM](https://img.shields.io/badge/LLM-100%25%20local%20(Ollama)-orange)

## 🎥 Demo

![PIA Demo](docs/demo.gif)

## 🧠 Why this exists

Supply chain disruptions cost enterprises **$184B annually** (Gartner, 2024). Most "AI projects"
are chatbots. PIA is a **decision system**: it ingests supplier order data, forecasts delivery
delays, scores risk, and generates quantified, supplier-specific procurement strategies —
dual-sourcing, buffer stock, renegotiation — with an executive-ready report.

Domain logic comes from real procurement practice: lead-time variance analysis, single-source
dependency scoring, and risk-adjusted cost framing.

## 🏗️ Architecture


## 🧪 Tests

```bash
pytest -v        # 6/6 in ~2s — LLM fully mocked, no Ollama required