#!/usr/bin/env bash

# ===== Config & paths =====
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="$APP_DIR/logs"
RUN_DIR="$APP_DIR/run"
LOG_FILE="$LOG_DIR/manager.log"
DJANGO_PORT="${DJANGO_PORT:-7000}"
STATIC_DIR="$APP_DIR/static"
COMPOSE_FILE="$APP_DIR/docker-compose.yml"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-core.settings}"

# ===== Colors =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

timestamp() { date +"[%Y-%m-%d %H:%M:%S]"; }
log() { echo -e "$(timestamp) $*" | tee -a "$LOG_FILE"; }

# ===== Prepare dirs & logs =====
mkdir -p "$LOG_DIR" "$RUN_DIR"
chmod 775 "$LOG_DIR" || true
touch "$LOG_FILE" && chmod 664 "$LOG_FILE" || true

# ===== OS helpers =====
is_windows() {
  case "$(uname -s | tr '[:upper:]' '[:lower:]')" in
    *mingw*|*cygwin*|*msys*) return 0 ;;
    *) return 1 ;;
  esac
}

# ===== Celery pool (Windows precisa de solo) =====
if is_windows; then
  CELERY_POOL="solo"
else
  CELERY_POOL="${CELERY_POOL:-prefork}"
fi

# ===== Virtualenv (Linux/Windows) =====
activate_venv() {
  log "Ativando ambiente virtual em $VENV_DIR..."
  if [ -f "$VENV_DIR/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    PYTHON_EXEC="$VENV_DIR/bin/python"
  elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/Scripts/activate"
    PYTHON_EXEC="$VENV_DIR/Scripts/python.exe"
  else
    echo -e "${RED}Erro: Virtualenv não encontrado em $VENV_DIR${NC}"
    log "Erro: Virtualenv não encontrado em $VENV_DIR"
    exit 1
  fi
  if [ ! -f "$PYTHON_EXEC" ] || [ ! -x "$PYTHON_EXEC" ]; then
    echo -e "${RED}Erro: Python executável não encontrado em $PYTHON_EXEC${NC}"
    log "Erro: Python executável não encontrado em $PYTHON_EXEC"
    exit 1
  fi
  PYTHON_VERSION=$("$PYTHON_EXEC" --version 2>&1)
  log "Ambiente virtual ativado. Python: $PYTHON_EXEC ($PYTHON_VERSION)"
  if "$PYTHON_EXEC" -c "import django" >/dev/null 2>&1; then
    DJANGO_VERSION=$("$PYTHON_EXEC" -c "import django; print(django.__version__)")
    log "Django encontrado: versão $DJANGO_VERSION"
  else
    log "Django não encontrado no ambiente virtual"
  fi
}

# ===== Check and install dependencies =====
check_dependencies() {
  log "Verificando dependências..."
  if ! "$PYTHON_EXEC" -m pip --version >/dev/null 2>&1; then
    echo -e "${RED}Erro: pip não encontrado no ambiente virtual${NC}"
    log "Erro: pip não encontrado no ambiente virtual"
    exit 1
  fi
  PIP_VERSION=$("$PYTHON_EXEC" -m pip --version)
  log "pip encontrado: $PIP_VERSION"

  # Django
  if ! "$PYTHON_EXEC" -c "import django" >/dev/null 2>&1; then
    echo -e "${YELLOW}Django não encontrado. Instalando dependências...${NC}"
    log "Django não encontrado. Instalando dependências..."
    if [ -f "$APP_DIR/requirements.txt" ]; then
      "$PYTHON_EXEC" -m pip install -r "$APP_DIR/requirements.txt" >> "$LOG_FILE" 2>&1 || {
        echo -e "${RED}Erro ao instalar dependências. Verifique $LOG_FILE${NC}"
        log "Erro ao instalar dependências"
        exit 1
      }
    else
      "$PYTHON_EXEC" -m pip install "django>=3.2" >> "$LOG_FILE" 2>&1 || {
        echo -e "${RED}Erro ao instalar Django. Verifique $LOG_FILE${NC}"
        log "Erro ao instalar Django"
        exit 1
      }
    fi
  fi

  # Celery + backend Redis (apenas se usar Celery local)
  if [ "${USE_DOCKER_CELERY:-0}" != "1" ]; then
    if ! "$PYTHON_EXEC" -c "import celery" >/dev/null 2>&1; then
      echo -e "${YELLOW}Celery não encontrado. Instalando...${NC}"
      log "Celery não encontrado. Instalando..."
      "$PYTHON_EXEC" -m pip install "celery[redis]>=5" >> "$LOG_FILE" 2>&1 || {
        echo -e "${RED}Erro ao instalar Celery. Verifique $LOG_FILE${NC}"
        log "Erro ao instalar Celery"
        exit 1
      }
    fi
    "$PYTHON_EXEC" -m pip show redis >/dev/null 2>&1 || \
      "$PYTHON_EXEC" -m pip install "redis>=5" >> "$LOG_FILE" 2>&1
  fi

  # Mostrar versões (Celery só se local)
  DJANGO_VERSION=$("$PYTHON_EXEC" -c "import django; print(django.__version__)")
  if [ "${USE_DOCKER_CELERY:-0}" != "1" ]; then
    CELERY_VERSION=$("$PYTHON_EXEC" -c "import celery; print(celery.__version__)" 2>/dev/null || echo "N/A")
    echo -e "${GREEN}Django: $DJANGO_VERSION | Celery(local): $CELERY_VERSION${NC}"
    log "Django: $DJANGO_VERSION | Celery(local): $CELERY_VERSION"
  else
    echo -e "${GREEN}Django: $DJANGO_VERSION | Celery(docker): enabled${NC}"
    log "Django: $DJANGO_VERSION | Celery(docker): enabled"
  fi
}

# ===== Optional .env loader =====
load_dotenv() {
  local dotenv="$APP_DIR/.env"
  [ -f "$dotenv" ] || { log "Arquivo .env não encontrado, pulando..."; return 0; }
  log "Carregando variáveis de $dotenv..."
  while IFS='=' read -r key value; do
    # Skip empty lines, comments, and invalid lines
    [[ -z "$key" || "$key" =~ ^# || "$key" =~ ^[[:space:]]*$ ]] && continue
    # Remove quotes and export
    value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
    export "$key=$value"
    log "Exportada: $key=$value"
  done < "$dotenv"
}

# ===== Docker helpers =====
check_docker() {
  log "Verificando Docker..."
  if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}Docker não está instalado.${NC}"
    log "Docker não está instalado"
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Docker não está rodando.${NC}"
    log "Docker não está rodando"
    exit 1
  fi
  log "Docker verificado com sucesso"
}

get_compose_cmd() {
  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  elif docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  else
    echo -e "${RED}Erro: docker-compose ou docker compose não encontrado.${NC}"
    log "Erro: docker-compose ou docker compose não encontrado"
    exit 1
  fi
}

start_docker_services() {
  local COMPOSE_CMD; COMPOSE_CMD="$(get_compose_cmd)"
  log "Verificando containers Redis/Flower/Celery..."
  local names="redis|flower|celery_worker"
  if docker ps --format '{{.Names}}' | grep -Eq "$names"; then
    echo -e "${GREEN}Alguns containers já em execução.${NC}"
    log "Containers detectados: $names"
  else
    log "Iniciando containers com $COMPOSE_CMD..."
    log "Construindo imagens Docker..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache >> "$LOG_FILE" 2>&1 || {
      echo -e "${RED}Erro ao construir imagens Docker. Verifique $LOG_FILE para detalhes.${NC}"
      log "Erro ao construir imagens Docker. Detalhes:"
      tail -n 20 "$LOG_FILE"
      exit 1
    }
    log "Imagens Docker construídas com sucesso"
    log "Iniciando containers..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d >> "$LOG_FILE" 2>&1 || {
      echo -e "${RED}Erro ao iniciar containers. Verifique $LOG_FILE para detalhes.${NC}"
      log "Erro ao iniciar containers. Detalhes:"
      tail -n 20 "$LOG_FILE"
      exit 1
    }
    # Verify containers are running
    sleep 5
    if ! docker ps --format '{{.Names}}' | grep -Eq "$names"; then
      echo -e "${RED}Erro: Containers não iniciaram corretamente. Verifique $LOG_FILE e logs do Docker.${NC}"
      log "Erro: Containers não iniciaram corretamente"
      log "Logs do Docker:"
      $COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail=20 >> "$LOG_FILE" 2>&1
      tail -n 20 "$LOG_FILE"
      exit 1
    fi
    log "Containers iniciados com sucesso"
  fi
}

# ===== Port check =====
check_port() {
  log "Verificando porta $DJANGO_PORT..."
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "( sport = :$DJANGO_PORT )" | awk 'NR>1{print $4}' | grep -q ":$DJANGO_PORT$" && {
      echo -e "${RED}Porta $DJANGO_PORT já está em uso.${NC}"
      log "Porta $DJANGO_PORT já está em uso"
      exit 1
    }
  else
    if is_windows; then
      netstat -ano | tr -d '\r' | grep -E "LISTENING" | grep -q ":$DJANGO_PORT " && {
        echo -e "${RED}Porta $DJANGO_PORT já está em uso.${NC}"
        log "Porta $DJANGO_PORT já está em uso"
        exit 1
      }
    else
      netstat -tuln | grep -q ":$DJANGO_PORT " && {
        echo -e "${RED}Porta $DJANGO_PORT já está em uso.${NC}"
        log "Porta $DJANGO_PORT já está em uso"
        exit 1
      }
    fi
  fi
  log "Porta $DJANGO_PORT está livre"
}

# ===== Process helpers (portáveis) =====
proc_exists() {
  ps -ef 2>/dev/null | grep -i "$1" | grep -v grep >/dev/null
}

kill_by_pattern() {
  local pattern="$1" name="$2"
  local pids
  pids=$(ps -ef 2>/dev/null | grep -i "$pattern" | grep -v grep | awk '{print $2}')
  if [ -z "$pids" ]; then
    echo "$name já está parado."
    log "$name já está parado"
    return
  fi
  log "Parando $name..."
  kill $pids 2>/dev/null || true
  sleep 1
  pids=$(ps -ef 2>/dev/null | grep -i "$pattern" | grep -v grep | awk '{print $2}')
  if [ -n "$pids" ]; then
    echo -e "${YELLOW}Forçando parada de $name...${NC}"
    kill -9 $pids 2>/dev/null || true
  fi
}

# ===== Paths de pid/log do Django/Celery =====
DJANGO_PID="$RUN_DIR/django.pid"
CELERY_WORKER_LOG="$LOG_DIR/celery_worker.log"
CELERY_WORKER_PID="$RUN_DIR/celery_worker.pid"

# ===== Django settings lookup =====
django_get_setting() {
  local setting_name="$1"
  "$PYTHON_EXEC" - <<PYCODE 2>/dev/null
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE","core.settings"))
try:
    import django
    django.setup()
    from django.conf import settings
    val = getattr(settings, "$setting_name", "")
    print(val or "")
except Exception:
    print("")
PYCODE
}

# ===== Steps =====
prepare_static() {
  log "Executando collectstatic..."
  STATIC_ROOT_VAL="$(django_get_setting STATIC_ROOT)"
  if [ -z "$STATIC_ROOT_VAL" ]; then
    echo "STATIC_ROOT não está definido no settings. Pulando collectstatic."
    log "STATIC_ROOT ausente. collectstatic pulado para não quebrar o start."
    return 0
  fi
  mkdir -p "$STATIC_ROOT_VAL" 2>/dev/null || true
  "$PYTHON_EXEC" manage.py collectstatic --noinput >> "$LOG_FILE" 2>&1
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Static files coletados com sucesso em $STATIC_ROOT_VAL.${NC}"
    log "collectstatic OK → $STATIC_ROOT_VAL"
  else
    echo -e "${RED}Erro no collectstatic. Verifique $LOG_FILE${NC}"
    log "Erro no collectstatic"
    exit 1
  fi
}

start() {
  log "Iniciando aplicação..."
  cd "$APP_DIR" || { echo -e "${RED}Erro: Não foi possível acessar $APP_DIR${NC}"; log "Erro: Não foi possível acessar $APP_DIR"; exit 1; }
  load_dotenv
  activate_venv
  check_dependencies
  check_docker
  start_docker_services
  check_port
  prepare_static

  # Django (runserver)
  if proc_exists "manage.py runserver 0.0.0.0:$DJANGO_PORT"; then
    echo -e "${GREEN}Django já em execução na porta $DJANGO_PORT${NC}"
    log "Django já em execução na porta $DJANGO_PORT"
  else
    nohup "$PYTHON_EXEC" manage.py runserver "0.0.0.0:$DJANGO_PORT" >> "$LOG_FILE" 2>&1 &
    echo $! > "$DJANGO_PID"
    echo -e "${GREEN}Django iniciado na porta $DJANGO_PORT (PID $(cat "$DJANGO_PID"))${NC}"
    log "Django iniciado na porta $DJANGO_PORT (PID $(cat "$DJANGO_PID"))"
  fi

  # Celery: local x docker
  if [ "${USE_DOCKER_CELERY:-0}" = "1" ]; then
    log "Celery gerido por Docker. Pulando worker local."
  else
    # Worker local
    if proc_exists "celery -A core worker"; then
      echo -e "${GREEN}Celery Worker já em execução${NC}"
      log "Celery Worker já em execução"
    else
      nohup "$PYTHON_EXEC" -m celery -A core worker \
        --loglevel=info \
        --logfile="$CELERY_WORKER_LOG" \
        --pidfile="$CELERY_WORKER_PID" \
        --pool="$CELERY_POOL" \
        --detach >/dev/null 2>&1
      for i in {1..10}; do
        if [ -f "$CELERY_WORKER_PID" ] && ps -p "$(cat "$CELERY_WORKER_PID" 2>/dev/null)" >/dev/null 2>&1; then
          echo -e "${GREEN}Celery Worker iniciado (PID $(cat "$CELERY_WORKER_PID"))${NC}"
          log "Celery Worker iniciado (PID $(cat "$CELERY_WORKER_PID"))"
          break
        fi
        sleep 1
      done
      if [ ! -f "$CELERY_WORKER_PID" ]; then
        echo -e "${RED}Erro ao iniciar Celery Worker. Verifique $CELERY_WORKER_LOG${NC}"
        log "Erro ao iniciar Celery Worker"
        exit 1
      fi
    fi
  fi
}

stop() {
  log "Parando aplicação..."

  # Para Django (host)
  if [ -f "$DJANGO_PID" ] && ps -p "$(cat "$DJANGO_PID" 2>/dev/null)" >/dev/null 2>&1; then
    kill "$(cat "$DJANGO_PID")" || true
    sleep 1
    ps -p "$(cat "$DJANGO_PID" 2>/dev/null)" >/dev/null 2>&1 && kill -9 "$(cat "$DJANGO_PID")" || true
    rm -f "$DJANGO_PID"
  else
    kill_by_pattern "manage.py runserver 0.0.0.0:$DJANGO_PORT" "Django"
  fi

  # Se Celery é dockerizado, não há processos locais — pula.
  if [ "${USE_DOCKER_CELERY:-0}" != "1" ]; then
    # Worker local
    [ -f "$CELERY_WORKER_PID" ] && ps -p "$(cat "$CELERY_WORKER_PID" 2>/dev/null)" >/dev/null 2>&1 && \
      kill "$(cat "$CELERY_WORKER_PID")" || true
    sleep 1
    [ -f "$CELERY_WORKER_PID" ] && ps -p "$(cat "$CELERY_WORKER_PID" 2>/dev/null)" >/dev/null 2>&1 && \
      kill -9 "$(cat "$CELERY_WORKER_PID")" || true
    rm -f "$CELERY_WORKER_PID" 2>/dev/null || true

    # Beat local
    [ -f "$CELERY_BEAT_PID" ] && ps -p "$(cat "$CELERY_BEAT_PID" 2>/dev/null)" >/dev/null 2>&1 && \
      kill "$(cat "$CELERY_BEAT_PID")" || true
    sleep 1
    [ -f "$CELERY_BEAT_PID" ] && ps -p "$(cat "$CELERY_BEAT_PID" 2>/dev/null)" >/dev/null 2>&1 && \
      kill -9 "$(cat "$CELERY_BEAT_PID")" || true
    rm -f "$CELERY_BEAT_PID" 2>/dev/null || true
  fi

  # Limpeza Docker completa (containers, imagens, volumes, cache)
deep_clean_docker() {
  local COMPOSE_CMD; COMPOSE_CMD="$(get_compose_cmd)"

  log "Limpando containers/volumes/imagens/caches (full prune)..."

  # Derruba e remove TUDO do compose atual
  $COMPOSE_CMD -f "$COMPOSE_FILE" down -v --rmi local --remove-orphans >> "$LOG_FILE" 2>&1 || true

  # Remove imagens e artefatos antigos/dangling
  docker system prune -af --volumes >> "$LOG_FILE" 2>&1 || true
  docker builder prune -af >> "$LOG_FILE" 2>&1 || true

  log "Limpeza Docker concluída."
}


  # Limpa arquivos de estado locais
  rm -f "$RUN_DIR"/*.pid 2>/dev/null || true
  rm -f "$BUILD_FINGERPRINT_FILE" 2>/dev/null || true

  log "Aplicação parada e ambiente limpo."
}


restart() {
  stop
  sleep 2
  start
}

status() {
  echo "$(timestamp) Status da aplicação:"

  if [ -f "$DJANGO_PID" ] && ps -p "$(cat "$DJANGO_PID" 2>/dev/null)" >/dev/null 2>&1; then
    echo -e "${GREEN}Django: OK (PID $(cat "$DJANGO_PID"))${NC}"
  else
    proc_exists "manage.py runserver 0.0.0.0:$DJANGO_PORT" && echo -e "${GREEN}Django: OK${NC}" || echo -e "${RED}Django: OFF${NC}"
  fi

  if [ "${USE_DOCKER_CELERY:-0}" = "1" ]; then
    # status via Docker
    docker ps --format '{{.Names}}' | grep -q celery_worker && echo -e "${GREEN}Celery Worker (docker): OK${NC}" || echo -e "${RED}Celery Worker (docker): OFF${NC}"
  else
    # status local
    if [ -f "$CELERY_WORKER_PID" ] && ps -p "$(cat "$CELERY_WORKER_PID" 2>/dev/null)" >/dev/null 2>&1; then
      echo -e "${GREEN}Celery Worker: OK (PID $(cat "$CELERY_WORKER_PID"))${NC}"
    else
      proc_exists "celery -A core worker" && echo -e "${GREEN}Celery Worker: OK${NC}" || echo -e "${RED}Celery Worker: OFF${NC}"
    fi
  fi

  docker ps | grep -q redis && echo -e "${GREEN}Redis: OK${NC}" || echo -e "${RED}Redis: OFF${NC}"
  docker ps | grep -q flower && echo -e "${GREEN}Flower: OK${NC}" || echo -e "${RED}Flower: OFF${NC}"
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) restart ;;
  status) status ;;
  *)
    echo "Uso: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac