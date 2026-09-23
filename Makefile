.DEFAULT_GOAL := help
.PHONY: help bootstrap check snapshot secrets-scan portable

REPO := $(shell pwd)
CLAUDE := $(HOME)/.claude

help: ## Mostra os comandos
	@printf "\033[33m%s\033[0m\n" 'Comandos:'
	@awk 'BEGIN{FS=":.*?## "} /^[a-z-]+:.*?## /{printf "  \033[32m%-14s\033[0m %s\n",$$1,$$2}' $(MAKEFILE_LIST)

bootstrap: ## Monta/repara os symlinks e o stub em ~/.claude
	@./bootstrap.sh

check: ## Verifica os symlinks sem escrever nada
	@./bootstrap.sh --check

snapshot: ## Copia o settings.json vivo para o repositório, removendo credenciais
	@python3 -c "import json,re,sys; \
	p='$(CLAUDE)/settings.json'; d=json.load(open(p)); \
	rx=re.compile(r'[0-9a-f]{32,}|X-Amz-(Signature|Credential|Security-Token)|\"password\"\s*:\s*\"(?!\{\{)[^\"]{4,}\"|password=(?!\{\{)[^&\s\x27\"]{4,}',re.I); \
	a=d['permissions']['allow']; k=[e for e in a if not rx.search(e)]; \
	d['permissions']['allow']=k; \
	json.dump(d,open('celesta-microservices/settings/settings.json','w'),indent=2,ensure_ascii=False); \
	print(f'settings.json: {len(a)} -> {len(k)} entradas ({len(a)-len(k)} com credencial, removidas)')"

# Os arquivos do próprio scanner carregam os padrões e casariam consigo mesmos.
SCAN_EXCLUDE := --exclude=Makefile --exclude=pre-commit --exclude-dir=.git

secrets-scan: ## Procura segredo em TODO o histórico, não só no working tree
	@echo "—— working tree"
	@! grep -rnIE 'client_secret[^a-z]{0,4}[=:"[:space:]]+[0-9a-f]{32,}|[0-9a-f]{64,}|GUARD_KEY[[:space:]]*=|X-Amz-Signature=' \
		. $(SCAN_EXCLUDE) 2>/dev/null || (echo "\033[31mACHOU no working tree\033[0m"; exit 1)
	@echo "  limpo"
	@echo "—— histórico completo"
	@if [ -d .git ] && git rev-parse HEAD >/dev/null 2>&1; then \
		if git log -p --all | grep -qE '^\+.*(client_secret[^a-z]{0,4}[=:"[:space:]]+[0-9a-f]{32,}|[0-9a-f]{64,}|GUARD_KEY[[:space:]]*=|-----BEGIN [A-Z ]*PRIVATE KEY-----)'; then \
			echo "\033[31mACHOU no histórico — não basta corrigir o arquivo, tem que reescrever o histórico\033[0m"; exit 1; \
		fi; echo "  limpo"; \
	else echo "  (ainda sem commits)"; fi

portable: ## Testa a promessa do repositório: global/ sobrevive sem celesta-*?
	@tmp=$$(mktemp -d); \
	git archive HEAD 2>/dev/null | tar -x -C $$tmp || { echo "precisa de ao menos um commit"; exit 1; }; \
	rm -rf $$tmp/celesta-microservices $$tmp/celesta-infra; \
	echo "—— links e imports de global/ que deixam de resolver:"; \
	python3 global/scripts/portable-check.py $$tmp; rc=$$?; \
	rm -rf $$tmp; exit $$rc
