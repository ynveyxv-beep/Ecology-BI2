# runtime_hook.py
# Выполняется при старте собранного .exe — исправляет рабочую директорию
import os
import sys

if getattr(sys, 'frozen', False):
    # Переключаемся в папку с Ecology-BI.exe,
    # чтобы относительные пути (templates/, resources/) работали
    os.chdir(os.path.dirname(sys.executable))
