PYTHON ?= python
QUERY ?= how does approximate nearest neighbour search work

.PHONY: install index search app eval test clean

install:
	$(PYTHON) -m pip install -r requirements.txt

index:
	$(PYTHON) -m noterecall index --chunk-size 128 --chunk-size 256 --chunk-size 512 --rebuild

search:
	$(PYTHON) -m noterecall search "$(QUERY)"

app:
	$(PYTHON) -m streamlit run noterecall/app.py

eval:
	$(PYTHON) -m evaluation.run_eval --chunk-sizes 128 256 512 --top-k 5

test:
	$(PYTHON) -m pytest

clean:
	rm -rf .index .pytest_cache
	rm -f results/metrics.csv results/metrics_by_category.csv results/per_query.csv
	rm -f results/summary.md
	rm -rf results/figures
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
