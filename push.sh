#!/bin/bash

git remote set-url origin https://github.com/breachcipher/Nexus.git
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/breachcipher/Nexus.git
git push -u -f origin main
