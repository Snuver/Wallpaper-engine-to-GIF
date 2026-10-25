@echo off
setlocal
cd /d "%~dp0"
title Wallpaper GIF Converter v1.5 - Made by snuver

echo ==============================================================
echo              WALLPAPER GIF CONVERTER v1.5
echo                     Made by snuver
echo ==============================================================
echo Turns Wallpaper Engine wallpapers into GIFs.
echo Scene or video, just throw it in here and let it do its thing.
echo.

set "SCRIPT=%~dp0WE-To-GIF.py"

if not exist "%SCRIPT%" (
  echo ERROR: I couldn't find WE-To-GIF.py
  echo.
  echo Make sure these two files are in the SAME folder:
  echo   WE-To-GIF.bat
  echo   WE-To-GIF.py
  echo.
  pause
  exit /b 1
)

if "%~1"=="" (
  echo Drag a Wallpaper Engine ZIP, folder, project.json, or video
  echo onto this file.
  echo.
  set /p "INPUT=Or paste the path here: "
) else (
  set "INPUT=%~1"
)

echo.
echo ================= WHAT I RECOMMEND =================
echo Length:      10 seconds
echo FPS:         12 FPS
echo Size:        1280 px wide
echo Target size: 5 MB
echo.
echo It keeps your FPS first, then lowers colors/resolution only if it has to.
echo Press ENTER if you just want the recommended settings.
echo.
echo Your finished GIF goes to:
echo %%USERPROFILE%%\Videos\Wallpaper GIF Converter
echo ====================================================
echo.

set /p "DUR=GIF length in seconds [Recommended: 10]: "
if "%DUR%"=="" set "DUR=10"
set /p "FPS=FPS [Recommended: 12]: "
if "%FPS%"=="" set "FPS=12"
set /p "WIDTH=GIF width in pixels [Recommended: 1280, 0 = full size]: "
if "%WIDTH%"=="" set "WIDTH=1280"
set /p "TARGET=Target max GIF size in MB [Recommended: 5, 0 = no limit]: "
if "%TARGET%"=="" set "TARGET=5"

echo.

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%SCRIPT%" "%INPUT%" --duration %DUR% --fps %FPS% --gif-width %WIDTH% --target-mb %TARGET%
  goto :done
)

where python >nul 2>nul
if not errorlevel 1 (
  python "%SCRIPT%" "%INPUT%" --duration %DUR% --fps %FPS% --gif-width %WIDTH% --target-mb %TARGET%
  goto :done
)

where python3 >nul 2>nul
if not errorlevel 1 (
  python3 "%SCRIPT%" "%INPUT%" --duration %DUR% --fps %FPS% --gif-width %WIDTH% --target-mb %TARGET%
  goto :done
)

echo ERROR: I couldn't find Python 3 on your PC.
echo.
echo Install Python 3 and make sure "Add Python to PATH" is enabled,
echo then open this BAT again.
echo.
pause
exit /b 1

:done
if errorlevel 1 (
  echo.
  echo Something failed above. Scroll up and send me the error if you need help.
  pause
  exit /b 1
)

echo.
echo That's it. Made by snuver.
pause
