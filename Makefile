# MerchantDNA pipeline. `make all` = data -> features -> train -> eval.
PY := .venv/bin/python
SMALL ?=
export PYTHONPATH := $(CURDIR)

.PHONY: setup data features train eval all app test demo guide clean

setup:
	uv venv --python 3.11 .venv
	uv pip install --python $(PY) -r requirements.txt

data:
	$(PY) -m merchantdna.sim.run $(if $(SMALL),--small,)

features:
	$(PY) -m merchantdna.features.build

train:
	$(PY) -m merchantdna.models.train

eval:
	$(PY) -m merchantdna.eval.run

all: data features train eval

app:
	$(PY) -m streamlit run app/Home.py --server.headless true

test:
	$(PY) -m pytest -q tests

demo: all app

guide:
	$(PY) tools/build_code_guide.py

clean:
	rm -rf data/*.parquet artifacts/* reports/*.json reports/*.png reports/sim
