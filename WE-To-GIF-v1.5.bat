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

if "%~1"=="" (
  echo Drag a Wallpaper Engine ZIP, folder, project.json, or video
  echo onto this file.
  echo.
  set /p INPUT=Or paste the path here: 
) else (
  set "INPUT=%~1"
)

echo.
echo ================= WHAT I RECOMMEND =================
echo Length:      10 seconds
echo FPS:         30 FPS
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

set /p DUR=GIF length in seconds [Recommended: 10]: 
if "%DUR%"=="" set DUR=10
set /p FPS=FPS [Recommended: 30]: 
if "%FPS%"=="" set FPS=30
set /p WIDTH=GIF width in pixels [Recommended: 1280, 0 = full size]: 
if "%WIDTH%"=="" set WIDTH=1280
set /p TARGET=Target max GIF size in MB [Recommended: 5, 0 = no limit]: 
if "%TARGET%"=="" set TARGET=5

echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0we_to_gif_v15.py" "%INPUT%" --duration %DUR% --fps %FPS% --gif-width %WIDTH% --target-mb %TARGET%
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3 is missing. Install it first and run this again.
    pause
    exit /b 1
  )
  python "%~dp0we_to_gif_v15.py" "%INPUT%" --duration %DUR% --fps %FPS% --gif-width %WIDTH% --target-mb %TARGET%
)

echo.
echo That's it. Made by snuver.
pause
