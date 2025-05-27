
local ensure_packer = function()
  local fn = vim.fn
  local install_path = fn.stdpath('data')..'/site/pack/packer/start/packer.nvim'
  if fn.empty(fn.glob(install_path)) > 0 then
    fn.system({'git', 'clone', '--depth', '1', 'https://github.com/wbthomason/packer.nvim', install_path})
    vim.cmd [[packadd packer.nvim]]
    return true
  end
  return false
end

local packer_bootstrap = ensure_packer()

require('packer').startup(function(use)
  use 'wbthomason/packer.nvim'

  use 'aserowy/tmux.nvim'
  use 'ibhagwan/fzf-lua'
  use 'benlubas/molten-nvim'
  
  use 'hashivim/vim-terraform'
  use 'juliosueiras/vim-terraform-completion'
  use 'jvirtanen/vim-hcl'
  
  use {'neoclide/coc.nvim', branch = 'release'}
  
  use 'folke/tokyonight.nvim'
  
  use({
    'iamcco/markdown-preview.nvim',
    run = function() vim.fn['mkdp#util#install']() end,
  })
  
  if packer_bootstrap then
    require('packer').sync()
  end
end)

require('tmux').setup({
  copy_sync = {
    enable = true,
    sync_registers = true,
    sync_unnamed = true,
  },
  navigation = {
    cycle_navigation = true,
    enable_default_keybindings = true,
  },
  resize = {
    enable_default_keybindings = true,
  },
})

require('fzf-lua').setup({
  winopts = {
    height = 0.85,
    width = 0.80,
    preview = {
      layout = 'flex',
      scrollbar = 'float',
    },
  },
})

vim.g.terraform_align = 1
vim.g.terraform_fmt_on_save = 1

vim.g.terraform_completion_keys = 1
vim.g.terraform_registry_module_completion = 1

vim.g.coc_global_extensions = {
  'coc-tsserver',
  'coc-json',
}

require('tokyonight').setup({
  style = 'night',
  transparent = false,
  terminal_colors = true,
})

vim.cmd[[colorscheme tokyonight]]

vim.api.nvim_set_keymap('n', '<leader>ti', ':call terraform#fmt()<CR>', { noremap = true, silent = true })
vim.api.nvim_set_keymap('n', '<leader>tv', ':call terraform#validate()<CR>', { noremap = true, silent = true })
vim.api.nvim_set_keymap('n', '<leader>tp', ':call terraform#plan()<CR>', { noremap = true, silent = true })
vim.api.nvim_set_keymap('n', '<leader>ta', ':call terraform#apply()<CR>', { noremap = true, silent = true })

vim.cmd([[
  augroup terraform_settings
    autocmd!
    autocmd FileType terraform setlocal commentstring=#%s
    autocmd FileType terraform.tfvars setlocal commentstring=#%s
    autocmd FileType hcl setlocal commentstring=#%s
  augroup END
]])

vim.g.molten_output_win_max_height = 12
vim.g.molten_image_provider = "image.nvim"
vim.api.nvim_set_keymap('n', '<leader>mi', ':MoltenInit<CR>', { noremap = true, silent = true })
vim.api.nvim_set_keymap('n', '<leader>me', ':MoltenEvaluateOperator<CR>', { noremap = true, silent = true })
vim.api.nvim_set_keymap('n', '<leader>ml', ':MoltenEvaluateLine<CR>', { noremap = true, silent = true })
vim.api.nvim_set_keymap('v', '<leader>mr', ':<C-u>MoltenEvaluateVisual<CR>gv', { noremap = true, silent = true })

vim.g.mkdp_auto_start = 0
vim.g.mkdp_auto_close = 1
vim.g.mkdp_refresh_slow = 0
vim.g.mkdp_theme = 'dark'
vim.api.nvim_set_keymap('n', '<C-p>', '<Plug>MarkdownPreviewToggle', {})
