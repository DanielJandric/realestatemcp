@echo off
echo.
echo ========================================
echo INSTALLATION MCP POUR CLAUDE DESKTOP
echo ========================================
echo.

REM Créer le dossier de config s'il n'existe pas
if not exist "%APPDATA%\Claude" mkdir "%APPDATA%\Claude"

REM Copier le fichier de config
copy /Y "claude_desktop_config.json" "%APPDATA%\Claude\claude_desktop_config.json"

if %errorlevel% equ 0 (
    echo.
    echo [OK] Configuration copiee vers:
    echo     %APPDATA%\Claude\claude_desktop_config.json
    echo.
    echo ========================================
    echo PROCHAINES ETAPES:
    echo ========================================
    echo 1. FERMER completement Claude Desktop
    echo 2. ROUVRIR Claude Desktop
    echo 3. Tester: "Liste mes proprietes"
    echo.
    echo Si ca marche, tu verras la liste des proprietes
    echo Si ca ne marche pas, demande "Quels outils as-tu?"
    echo.
) else (
    echo.
    echo [ERREUR] Impossible de copier le fichier
    echo.
)

pause

