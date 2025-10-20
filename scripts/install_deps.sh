#!/bin/bash
# Безопасная установка Python зависимостей для CI

set -e  # Остановка при ошибке

echo "🐍 Checking Python version..."
python --version

echo "📦 Upgrading pip and build tools..."
python -m pip install --upgrade pip setuptools wheel

echo "🔍 Installing core dependencies..."
pip install pytest==7.4.3 pytest-timeout==2.2.0 allure-pytest==2.13.2

echo "🐳 Installing system monitoring..."  
pip install psutil==5.9.6 docker==7.0.0

echo "🌐 Installing HTTP and utilities..."
pip install requests==2.31.0 python-dotenv==1.0.0

echo "📊 Installing graphics libraries..."
if pip install --only-binary=all matplotlib==3.7.2 numpy==1.24.4; then
    echo "✅ Successfully installed latest graphics libraries"
else
    echo "⚠️ Fallback to older graphics libraries..."
    pip install matplotlib==3.6.3 numpy==1.23.5 || {
        echo "❌ Failed to install graphics libraries, tests may not generate charts"
        exit 0  # Continue without graphics
    }
fi

echo "✅ All dependencies installed successfully!"
pip list | grep -E "(pytest|matplotlib|numpy|docker|psutil)"