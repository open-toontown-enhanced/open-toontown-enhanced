@echo off
title Open Toontown Enhanced - Astron Server
cd ../astron/win32
astrond --loglevel info ../config/astrond.yml
pause
