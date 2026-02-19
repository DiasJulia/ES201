#!/bin/bash
set -u -o pipefail

# =========== CONFIG ===========
REMOTE_USER="julia-ellen.dias"
REMOTE_JUMP="ssh.ensta.fr"
REMOTE_HOST="salle"
REMOTE_WORK_DIR="tp5_work"
LOCAL_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_RESULTS_DIR="$LOCAL_SCRIPTS_DIR/results_remote"

SCRIPT_RUN="script_run.sh"
SCRIPT_COLLECT="script_collect.sh"

# Verificar se sshpass está disponível
if ! command -v sshpass &> /dev/null; then
  echo "⚠️  sshpass não encontrado. Instalando..."
  sudo apt-get update && sudo apt-get install -y sshpass || {
    echo "❌ Não foi possível instalar sshpass"
    exit 1
  }
fi

# =========== MAIN ===========
echo "📋 Sincronizando scripts para servidor remoto..."
echo "   -> Host: $REMOTE_USER@$REMOTE_HOST"
echo "   -> Jump: $REMOTE_USER@$REMOTE_JUMP"
echo "   -> Dir: $REMOTE_WORK_DIR"

# 1. Copiar scripts
mkdir -p "$LOCAL_RESULTS_DIR"

scp -o StrictHostKeyChecking=no -J "$REMOTE_USER@$REMOTE_JUMP" \
  "$LOCAL_SCRIPTS_DIR/$SCRIPT_RUN" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_WORK_DIR/" || {
  echo "❌ Erro ao copiar $SCRIPT_RUN"
  exit 1
}

scp -o StrictHostKeyChecking=no -J "$REMOTE_USER@$REMOTE_JUMP" \
  "$LOCAL_SCRIPTS_DIR/$SCRIPT_COLLECT" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_WORK_DIR/" || {
  echo "❌ Erro ao copiar $SCRIPT_COLLECT"
  exit 1
}

echo "✅ Scripts copiados com sucesso"

# 2. Executar scripts remotamente
echo ""
echo "🚀 Executando script_run.sh no servidor remoto..."
ssh -o StrictHostKeyChecking=no -J "$REMOTE_USER@$REMOTE_JUMP" "$REMOTE_USER@$REMOTE_HOST" \
  "cd $REMOTE_WORK_DIR && chmod +x $SCRIPT_RUN && ./$SCRIPT_RUN" 

echo ""
echo "📊 Executando script_collect.sh no servidor remoto..."
ssh -o StrictHostKeyChecking=no -J "$REMOTE_USER@$REMOTE_JUMP" "$REMOTE_USER@$REMOTE_HOST" \
  "cd $REMOTE_WORK_DIR && chmod +x $SCRIPT_COLLECT && ./$SCRIPT_COLLECT" 

# 3. Recuperar results.txt
echo ""
echo "📥 Recuperando results.txt..."
scp -o StrictHostKeyChecking=no -J "$REMOTE_USER@$REMOTE_JUMP" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_WORK_DIR/results.txt" \
  "$LOCAL_RESULTS_DIR/" 

scp -o StrictHostKeyChecking=no -J "julia-ellen.dias@$REMOTE_JUMP" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_WORK_DIR/results.txt" \
  "$LOCAL_RESULTS_DIR/"

  

echo "✅ results.txt recuperado em: $LOCAL_RESULTS_DIR/results.txt"

# 4. Copiar para local padrão (onde o extract_results.py espera)
cp "$LOCAL_RESULTS_DIR/results.txt" "$LOCAL_SCRIPTS_DIR/results.txt" && \
  echo "✅ results.txt copiado para: $LOCAL_SCRIPTS_DIR/results.txt"

echo ""
echo "🎉 Processo completo!"
echo "   results.txt: $LOCAL_SCRIPTS_DIR/results.txt"
echo ""
echo "Próximo passo: python extract_results.py"
