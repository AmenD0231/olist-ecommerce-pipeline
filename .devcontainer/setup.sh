#!/usr/bin/env bash

set -e

PROJECT_DIR="/workspaces/olist-ecommerce-pipeline"

echo "=========================================="
echo " Olist E-Commerce Pipeline Setup"
echo "=========================================="

cd "$PROJECT_DIR"

echo ""
echo "Python version:"
python --version

# --------------------------------------------------
# 1. Create project virtual environment
# --------------------------------------------------

echo ""
echo "Creating project virtual environment..."

if [ ! -d "venv" ]; then
    python -m venv venv
fi

source venv/bin/activate

python -m pip install --upgrade pip

echo ""
echo "Installing project requirements..."

pip install -r requirements.txt

deactivate

# --------------------------------------------------
# 2. Create Airflow virtual environment
# --------------------------------------------------

echo ""
echo "Creating Airflow virtual environment..."

if [ ! -d "venv-airflow" ]; then
    python -m venv venv-airflow
fi

source venv-airflow/bin/activate

python -m pip install --upgrade pip

echo ""
echo "Installing Apache Airflow 3.3.1..."

AIRFLOW_VERSION="3.3.1"
PYTHON_VERSION="3.13"

CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow==${AIRFLOW_VERSION}" \
    --constraint "${CONSTRAINT_URL}"

deactivate

# --------------------------------------------------
# 3. Prepare Airflow directories
# --------------------------------------------------

mkdir -p airflow/dags
mkdir -p airflow/logs

echo ""
echo "=========================================="
echo " Setup completed successfully!"
echo "=========================================="

echo ""
echo "Project Python:"
./venv/bin/python --version

echo ""
echo "Airflow:"
./venv-airflow/bin/airflow version

echo ""
echo "AIRFLOW_HOME:"
echo "$AIRFLOW_HOME"

echo ""
echo "=========================================="
