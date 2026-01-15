@echo off
setlocal

echo === Kontrola virtualniho prostredi ===

if not exist .venv (
    echo Vytvarim .venv...
    python -m venv .venv
)

echo Aktivace .venv...
call .venv\Scripts\activate.bat

echo === Kontrola instalace coverage ===
python -c "import coverage" 2>nul
if errorlevel 1 (
    echo Instalace coverage...
    pip install coverage
)

echo === Spoustim testy s coverage ===
coverage run run_test.py

echo === Generuji report ===
coverage report -m

endlocal
