# Neovim Plugins for agent_runtime

This directory contains the Neovim plugin configuration for the agent_runtime system, enabling parallel workflow capabilities with Terraform and HCL support.

## Plugins

### Core Plugins

- **tmux.nvim**: Seamless integration between Neovim and tmux for terminal multiplexing
- **fzf-lua**: Fuzzy finder for efficient file navigation
- **molten-nvim**: Interactive code execution with Jupyter kernel integration
- **coc.nvim**: Intelligent completion engine with LSP support
- **tokyonight.nvim**: Clean, dark theme with extensive plugin support
- **markdown-preview.nvim**: Real-time Markdown preview with synchronized scrolling

### Terraform and HCL Plugins

- **vim-terraform**: Basic Vim/Terraform integration with syntax highlighting and formatting
- **vim-terraform-completion**: Autocompletion and linting for Terraform
- **vim-hcl**: Syntax highlighting for HashiCorp Configuration Language (HCL)

## Installation

The plugins can be installed using the provided `install.sh` script:

```bash
./install.sh
```

This script will:
1. Install packer.nvim if not already installed
2. Copy the init.lua configuration to the Neovim config directory
3. Install all required plugins
4. Configure coc.nvim for TypeScript and Terraform support

## Configuration

The plugins are configured in `init.lua` with the following features:

### Terraform and HCL Configuration

- Syntax highlighting for Terraform and HCL files
- Automatic formatting on save
- Terraform command integration
- Autocompletion for Terraform resources and modules
- Linting for Terraform configurations

### Key Mappings

- `<leader>ti`: Format Terraform file
- `<leader>tv`: Validate Terraform configuration
- `<leader>tp`: Run Terraform plan
- `<leader>ta`: Run Terraform apply

## Plugin Management

The `plugin_manager.py` module provides functionality for managing Neovim plugins:

- Installing plugins
- Verifying plugin installation
- Updating plugins
- Configuring Terraform plugins

## Usage

To use the Neovim plugins in the agent_runtime system:

1. Ensure the plugins are installed using the installation script
2. Start a Neovim instance through the agent_runtime API
3. Execute Terraform commands using the provided key mappings

## Dependencies

- Neovim 0.5.0 or later
- Git
- Node.js and npm (for coc.nvim)
- Terraform and terraform-ls (for Terraform language server)
