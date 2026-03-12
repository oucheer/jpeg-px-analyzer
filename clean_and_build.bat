@echo off
echo Closing processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul
echo Removing dist folder...
rmdir /s /q "d:\work\AI\AI Use\jpeg analyzer\dist"
echo Done!
pause
