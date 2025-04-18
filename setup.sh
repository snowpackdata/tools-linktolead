#!/bin/bash
# setup.sh - Script to setup the linktolead project

set -e  # Exit on error

echo "🚀 Setting up linktolead..."

# Check if uv is installed
if command -v uv >/dev/null 2>&1; then
    echo "✅ uv is already installed"
else
    echo "⚙️ Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed successfully"
fi

# Run uv sync to install dependencies
echo "⚙️ Installing dependencies..."
uv sync
echo "✅ Dependencies installed"

# Install Playwright browsers
echo "⚙️ Installing Playwright browsers..."
if [[ -f .venv/bin/playwright ]]; then
    .venv/bin/playwright install --with-deps
else
    echo "⚠️ Playwright executable not found in virtual environment"
    echo "   Trying with uv run..."
    uv run playwright install --with-deps
fi
echo "✅ Playwright browsers installed"

# Check if .env file exists, create if not
if [[ ! -f .env ]]; then
    echo "⚙️ Creating .env file template..."
    cp .env.example .env
    echo "✅ Created .env file template. Please edit it with your credentials."
    echo "⚠️ You must edit .env with your LinkedIn and HubSpot credentials before using the tool."
else
    echo "✅ .env file already exists"
fi

# Check if config yaml exists, create if not
if [[ ! -f .linktolead_config.yaml ]]; then
    echo "⚙️ Creating config file template..."
    cp .linktolead_config.yaml.example .linktolead_config.yaml
    echo "✅ Created config file template."
else
    echo "✅ Config file already exists"
fi

# Install the package in development mode
echo "⚙️ Installing linktolead in development mode..."
uv pip install -e .
echo "✅ Package installed in development mode"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your LinkedIn and HubSpot credentials"
echo "2. Open and edit .linktolead_config.yaml to customize settings"
echo "3. Run the tool with: linktolead <linkedin_job_url> <linkedin_company_url>"
echo ""
echo "For more information, see README.md"
echo ""

# Check if LLM dependencies are requested
read -p "Would you like to install optional LLM dependencies? (y/N): " install_llm
if [[ $install_llm == "y" || $install_llm == "Y" ]]; then
    echo "⚙️ Installing LLM dependencies..."
    uv pip install -e ".[llm]"
    echo "✅ LLM dependencies installed"
    echo ""
    echo "⚠️ Remember to update .linktolead_config.yaml to enable LLM processing:"
    echo "llm_enabled: true"
    echo ""
fi 