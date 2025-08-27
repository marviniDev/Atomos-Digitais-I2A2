@echo off
title Controle de VR - Interface Web
echo Iniciando a interface web do Controle de VR...
echo Aguarde alguns segundos até o navegador abrir.

:: Ativar ambiente virtual, se estiver usando um
:: call venv\Scripts\activate

:: Executar o Streamlit
streamlit run vr_web.py

pause
