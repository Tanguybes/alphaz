@echo off
set PYTHONPATH=%cd%;

echo  0 - Flag Def Tool
set /p reponse="Quel batch voulez vous executer ?"

If "%reponse%"=="" goto :sub_error
If /i "%reponse%"=="0" goto :batch0

:batch0
python progs/fdt.py %*
goto :end

:batch12
python IA/selection.py
goto :end

:end
pause