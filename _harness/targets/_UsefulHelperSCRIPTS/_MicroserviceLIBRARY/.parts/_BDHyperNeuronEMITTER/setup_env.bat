@echo off
echo Setting up _BDHyperNeuronEMITTER v2 environment...
python -m venv .venv
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
echo Done. Activate with: .venv\Scripts\activate.bat
