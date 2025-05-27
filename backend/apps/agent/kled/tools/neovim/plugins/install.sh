
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
NVIM_CONFIG_DIR="${HOME}/.config/nvim"
NVIM_DATA_DIR="${HOME}/.local/share/nvim"
PLUGIN_DIR="${NVIM_DATA_DIR}/site/pack/packer/start"

mkdir -p "${NVIM_CONFIG_DIR}"
mkdir -p "${PLUGIN_DIR}"

if [ ! -d "${PLUGIN_DIR}/packer.nvim" ]; then
  echo "Installing packer.nvim..."
  git clone --depth 1 https://github.com/wbthomason/packer.nvim "${PLUGIN_DIR}/packer.nvim"
fi

echo "Copying init.lua to ${NVIM_CONFIG_DIR}..."
cp "${SCRIPT_DIR}/init.lua" "${NVIM_CONFIG_DIR}/init.lua"

echo "Installing core plugins..."
if [ ! -d "${PLUGIN_DIR}/tmux.nvim" ]; then
  git clone --depth 1 https://github.com/aserowy/tmux.nvim "${PLUGIN_DIR}/tmux.nvim"
fi

if [ ! -d "${PLUGIN_DIR}/fzf-lua" ]; then
  git clone --depth 1 https://github.com/ibhagwan/fzf-lua "${PLUGIN_DIR}/fzf-lua"
fi

if [ ! -d "${PLUGIN_DIR}/molten-nvim" ]; then
  git clone --depth 1 https://github.com/benlubas/molten-nvim "${PLUGIN_DIR}/molten-nvim"
fi

echo "Installing Terraform and HCL plugins..."
if [ ! -d "${PLUGIN_DIR}/vim-terraform" ]; then
  git clone --depth 1 https://github.com/hashivim/vim-terraform "${PLUGIN_DIR}/vim-terraform"
fi

if [ ! -d "${PLUGIN_DIR}/vim-terraform-completion" ]; then
  git clone --depth 1 https://github.com/juliosueiras/vim-terraform-completion "${PLUGIN_DIR}/vim-terraform-completion"
fi

if [ ! -d "${PLUGIN_DIR}/vim-hcl" ]; then
  git clone --depth 1 https://github.com/jvirtanen/vim-hcl "${PLUGIN_DIR}/vim-hcl"
fi

echo "Installing TypeScript support..."
if [ ! -d "${PLUGIN_DIR}/coc.nvim" ]; then
  git clone --depth 1 --branch release https://github.com/neoclide/coc.nvim "${PLUGIN_DIR}/coc.nvim"
fi

echo "Installing theme..."
if [ ! -d "${PLUGIN_DIR}/tokyonight.nvim" ]; then
  git clone --depth 1 https://github.com/folke/tokyonight.nvim "${PLUGIN_DIR}/tokyonight.nvim"
fi

echo "Installing Markdown support..."
if [ ! -d "${PLUGIN_DIR}/markdown-preview.nvim" ]; then
  git clone --depth 1 https://github.com/iamcco/markdown-preview.nvim "${PLUGIN_DIR}/markdown-preview.nvim"
  cd "${PLUGIN_DIR}/markdown-preview.nvim"
  yarn install
  yarn build
fi

echo "Creating coc-settings.json..."
cat > "${NVIM_CONFIG_DIR}/coc-settings.json" << 'EOF'
{
  "suggest.noselect": false,
  "suggest.enablePreselect": false,
  "suggest.triggerAfterInsertEnter": true,
  "suggest.timeout": 5000,
  "suggest.enablePreview": true,
  "suggest.floatEnable": true,
  "suggest.detailField": "preview",
  "suggest.snippetIndicator": "►",
  "diagnostic.errorSign": "✘",
  "diagnostic.warningSign": "⚠",
  "diagnostic.infoSign": "ℹ",
  "diagnostic.hintSign": "➤",
  "diagnostic.virtualText": true,
  "diagnostic.virtualTextPrefix": " ❯❯❯ ",
  "typescript.suggest.completeFunctionCalls": true,
  "typescript.format.enabled": true,
  "typescript.updateImportsOnFileMove.enabled": "always",
  "typescript.preferences.importModuleSpecifier": "shortest",
  "javascript.suggest.autoImports": true,
  "javascript.validate.enable": true,
  "languageserver": {
    "terraform": {
      "command": "terraform-ls",
      "args": ["serve"],
      "filetypes": [
        "terraform",
        "tf"
      ],
      "initializationOptions": {},
      "settings": {}
    }
  }
}
EOF

echo "Installing coc extensions..."
mkdir -p "${HOME}/.config/coc/extensions"
cd "${HOME}/.config/coc/extensions"
if [ ! -f package.json ]; then
  echo '{"dependencies":{}}' > package.json
fi

npm install --global-style --ignore-scripts --no-bin-links --no-package-lock --only=prod \
  coc-tsserver \
  coc-json

echo "Neovim plugins installation complete!"
