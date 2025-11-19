@echo off
chcp 65001 > nul
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         SYSTÈME D'ANALYSE IMMOBILIÈRE INTELLIGENTE            ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Choisissez une option:
echo.
echo  1. État général du système
echo  2. Analyse des servitudes
echo  3. Test recherche sémantique
echo  4. Statistiques embeddings
echo  5. Vérifier processus en cours
echo  6. Quitter
echo.
set /p choice="Votre choix (1-6): "

if "%choice%"=="1" goto status
if "%choice%"=="2" goto servitudes
if "%choice%"=="3" goto search
if "%choice%"=="4" goto embeddings
if "%choice%"=="5" goto processus
if "%choice%"=="6" goto end

:status
echo.
echo 📊 Génération rapport d'état...
python final_status_report.py
pause
goto end

:servitudes
echo.
echo 📋 Analyse des servitudes...
python analyze_servitudes.py
pause
goto end

:search
echo.
echo 🔍 Test recherche sémantique...
python test_semantic_search.py
pause
goto end

:embeddings
echo.
echo 📈 Statistiques embeddings...
python check_embedding_progress.py
pause
goto end

:processus
echo.
echo 🔄 Vérification processus...
echo.
echo === LINKING (Terminal 7) ===
powershell -Command "Get-Content 'terminals\7.txt' -Tail 5"
echo.
echo === REGISTRE FONCIER (Terminal 9) ===
powershell -Command "Get-Content 'terminals\9.txt' -Tail 5"
echo.
pause
goto end

:end
echo.
echo ✅ Terminé!
echo.

