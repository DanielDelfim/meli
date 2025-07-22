@echo off
echo ==============================================
echo   UPLOAD DO PROJETO PARA O GITHUB
echo ==============================================
echo.

REM CONFIGURA SEU NOME E EMAIL DO GIT (EDITAR SE PRECISAR)
git config --global user.name "Daniel M. Delfim"
git config --global user.email "daniel@email.com"

REM ENTRA NA PASTA DO PROJETO
cd /d "C:\Users\dmdel\OneDrive\Aplicativos"

REM INICIALIZA O GIT SE AINDA NAO EXISTIR
if not exist ".git" (
    echo Inicializando repositório local...
    git init
)

REM ADICIONA TODOS OS ARQUIVOS
echo Adicionando arquivos ao commit...
git add .

REM CRIA UM COMMIT
echo Criando commit...
git commit -m "Atualizando projeto" || echo Nenhuma alteração para commitar.

REM SINCRONIZA COM REPOSITÓRIO REMOTO
echo Fazendo pull do GitHub (mesclando alterações)...
git pull origin main --allow-unrelated-histories --no-edit

REM DEFINE A BRANCH PRINCIPAL COMO MAIN
git branch -M main

REM ENVIA OS ARQUIVOS PARA O GITHUB
echo Enviando arquivos para o GitHub...
git push -u origin main

echo.
echo ==============================================
echo   UPLOAD CONCLUIDO!
echo ==============================================
pause
