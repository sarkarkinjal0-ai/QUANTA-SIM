# Final deployment checklist

* \[ ] Install all dependencies from `requirements.txt` in a clean virtual environment.
* \[x] Python files compile with `python -m compileall -q .`.
* \[x] `python test\_integration.py` passes.
* \[ ] `python -m pytest -q` passes; currently blocked by legacy test import errors.
* \[x] `python -m pytest -q test\_integration.py` passes (5 tests).
* \[x] Open the Streamlit app locally and click through every tab.
* \[ ] Run the Qiskit benchmark with Aer installed; verify no runtime exceptions.
* \[ ] Confirm optical and Qiskit output mode conventions align.
* \[ ] Push the project to GitHub without virtual environments, caches, or secrets.
* \[ ] Deploy `app.py` on Streamlit Community Cloud.
* \[ ] Verify the live app after deployment.

