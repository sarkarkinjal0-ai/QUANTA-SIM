# Original QUANTA-SIM Project Preservation

The first uploaded `QUANTA-SIM` project has been retained inside this integrated project.

## Preserved from your original folder

- `core/` — photon/Fock/state/probability/unitary engine and its tests
- `experiments/` — MZI, HOM, noise simulations and experiment tests
- `optics/` — beam splitter, phase shifter, optical circuit, mode network and tests
- `quantum/` — original Qiskit MZI/comparison modules and tests
- `visualization/` — original plots and visualization tests
- `tests/` — original test package marker
- `app_original.py` — your original Streamlit app, preserved under a different filename so it does not overwrite the integrated `app.py`

These source files were copied from the uploaded archive. Python bytecode (`__pycache__`), pytest cache (`.pytest_cache`), and virtual-environment/dependency files were not copied; those are generated/environment-specific files and should not be committed to GitHub. The new integrated app remains `app.py`.

## Running the original app

From this project's root, install `requirements.txt`, then run:

```powershell
streamlit run app_original.py
```

## Running the integrated app

```powershell
streamlit run app.py
```
