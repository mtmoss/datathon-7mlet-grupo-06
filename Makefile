# Atalhos do projeto. Uso: make <alvo>

.PHONY: install pipeline serve examples test lint decide clean

install:        ## instala o pacote e ferramentas de dev
	pip install -e ".[dev]"

pipeline:       ## roda o fluxo ponta a ponta (dados -> bandits -> avaliacao -> politica)
	python -m datathon_offerexp.data_loader
	python -m datathon_offerexp.synthetic
	python -m datathon_offerexp.evaluation
	python -m datathon_offerexp.offline_eval
	python -m datathon_offerexp.policy_store

examples:       ## 5 casos de teste (Etapa 4): oferta recomendada por cliente
	python -m datathon_offerexp.examples

serve:          ## sobe a API de decisao em http://localhost:8000
	uvicorn datathon_offerexp.app:app --reload

test:           ## roda os testes
	pytest

lint:           ## verifica estilo
	ruff check src

decide:         ## exemplo de chamada a API (precisa do 'make serve' rodando em outro terminal)
	curl -s -X POST localhost:8000/decide -H "Content-Type: application/json" \
	  -d '{"segment":"recorrente","channel":"web","base_propensity":0.2}'

clean:          ## remove artefatos locais
	rm -rf src/*.egg-info .pytest_cache reports/decision_log.jsonl
