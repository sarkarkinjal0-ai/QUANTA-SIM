# QUANTA-SIM — Integrated Photonic Quantum Simulator

QUANTA-SIM is an educational Streamlit application for constructing small optical circuits, simulating single- and two-photon behavior, exploring imperfections, and comparing optical probabilities with Qiskit Aer.

## Team contributions integrated

- **Member 1 — Core Physics & Mathematics:** `core_engine.py` provides quantum state vectors, unitary evolution, beam-splitter/phase-shifter mathematics, and Born-rule probabilities.
- **Member 2 — Optical Components & Optical Builder:** `optical_builder/` contains the integrated optical circuit builder, circuit schematic, component controls, unitary display, and single-/two-photon simulation controls. Note: the separate original Member 2 source archive was not included in the uploaded deliverables; this package was included in Member 4's integrated submission.
- **Member 3 — Interferometry & Experiments:** `physics_experiments.py` orchestrates MZI sweeps and HOM analyses.
- **Member 4 — Photon & Noise Engine:** `photon_noise_engine.py` handles photon evolution, two-photon/Fock-state outputs, phase/reflectivity imperfections, and finite-shot sampling.
- **Member 5 — Qiskit Integration:** `qiskitintegration/` provides optical-to-circuit conversion, circuit construction, Aer simulation, benchmarks, and plots.
- **Member 6 — UI, Visualization & Integration:** `app.py` connects the modules in a four-tab Streamlit interface.

The original uploaded ZIPs for Members 1, 3, 4, and 5 are preserved under `team_submissions/` for traceability. They are not imported by the application.

## Features

1. **Circuit Builder** — 2–4 modes, beam splitters, phase shifters, MZI preset, circuit schematic, total unitary and heatmap, single-photon and Fock-state outputs.
2. **Experiments & Noise** — MZI interference sweeps, phase/reflectivity noise controls, visibility metric, HOM probabilities and finite-shot counts.
3. **Qiskit Comparison** — Qiskit Aer shot-based benchmark, optical-vs-digital probabilities, TVD, classical fidelity, Hellinger distance, circuit diagram and gate breakdown.
4. **About & Validation** — architecture overview and integration smoke-test runner.

## Your original project is preserved

The code from your uploaded `QUANTA-SIM` folder is also included: `core/`, `experiments/`, `optics/`, `quantum/`, `visualization/`, and `tests/`. Your original Streamlit dashboard is preserved as `app_original.py` so the integrated six-member dashboard can use `app.py` without deleting or overwriting your version. See `ORIGINAL_PROJECT_PRESERVATION.md` for details. The original project can be launched with `streamlit run app_original.py`. Environment folders and generated caches are intentionally excluded.

## Run locally (Windows PowerShell)

From the project root, create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python test_integration.py
python -m pytest -q
streamlit run app.py
```

If PowerShell blocks environment activation, run the commands from Command Prompt or use `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe -m streamlit run app.py`.

## Deploy on Streamlit Community Cloud

1. Push this project folder to a GitHub repository.
2. Open Streamlit Community Cloud and create a new app from that repository.
3. Set the main file path to `app.py`.
4. Deploy. Streamlit installs dependencies from the root `requirements.txt`.
5. Test Circuit Builder, MZI/HOM experiments, and the **Run Qiskit benchmark** button on the deployed URL.

The app is a single Streamlit process; it does not require a separate frontend/backend service. No credentials or API secrets are needed by the current code.

## Tests

```powershell
python test_integration.py
python -m pytest -q
```

The current integration smoke test and root pytest suite passed in the assembly environment. Qiskit runtime execution and the full browser UI must still be verified in an environment with dependencies installed.

## Important scientific note

Probability comparisons are meaningful only when the optical and Qiskit simulations use the same physical transformation, mode labels, and phase convention. The Qiskit bridge uses the imaginary-symmetric beam-splitter convention for the MZI benchmark. Shot-based Qiskit probabilities fluctuate statistically; a nonzero TVD is expected at finite shot counts.

## Repository hygiene

- Do not commit `.venv/`, `venv/`, `__pycache__/`, `.pytest_cache/`, local `.env` files, or Streamlit secrets.
- Keep generated artifacts only if they are useful for documentation; they are not required for the app to run.
- Member 2's separate original source archive should be added when available and compared with `optical_builder/` before any replacement.
