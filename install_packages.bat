@echo off
for /f "tokens=*" %%i in (requirements.txt) do (
    conda install --yes %%i
)