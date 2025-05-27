
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.tabstop = 2
vim.opt.shiftwidth = 2
vim.opt.expandtab = true
vim.opt.smartindent = true
vim.opt.wrap = false
vim.opt.swapfile = false
vim.opt.backup = false
vim.opt.undofile = true
vim.opt.undodir = vim.fn.stdpath('data') .. '/undodir'
vim.opt.hlsearch = false
vim.opt.incsearch = true
vim.opt.termguicolors = true
vim.opt.scrolloff = 8
vim.opt.updatetime = 50
vim.opt.colorcolumn = "80"

local install_path = vim.fn.stdpath('data') .. '/site/pack/packer/start/packer.nvim'
if vim.fn.empty(vim.fn.glob(install_path)) > 0 then
  vim.fn.system({'git', 'clone', '--depth', '1', 'https://github.com/wbthomason/packer.nvim', install_path})
  vim.cmd [[packadd packer.nvim]]
end

require('packer').startup(function(use)
  use 'wbthomason/packer.nvim'
  
  use {
    'aserowy/tmux.nvim',
    config = function()
      require('tmux').setup({
        copy_sync = {
          enable = true,
        },
        navigation = {
          enable_default_keybindings = true,
        },
        resize = {
          enable_default_keybindings = true,
        },
      })
    end
  }
  
  use {
    'ibhagwan/fzf-lua',
    requires = { 'nvim-tree/nvim-web-devicons' },
    config = function()
      require('fzf-lua').setup({})
    end
  }
  
  use {
    'iamcco/markdown-preview.nvim',
    run = function() vim.fn['mkdp#util#install']() end,
    ft = {'markdown'}
  }
  
  use {
    'benlubas/molten-nvim',
    run = ':UpdateRemotePlugins',
    config = function()
      vim.g.molten_output_win_max_height = 20
    end
  }
  
  use {
    'folke/tokyonight.nvim',
    config = function()
      vim.cmd[[colorscheme tokyonight]]
    end
  }
  
  use {
    'neoclide/coc.nvim',
    branch = 'release'
  }
  
  use 'hashivim/vim-terraform'
  use 'juliosueiras/vim-terraform-completion'
  use 'jvirtanen/vim-hcl'
  
  use {
    'folke/persistence.nvim',
    config = function()
      require('persistence').setup({
        dir = vim.fn.expand(vim.fn.stdpath('data') .. '/sessions/'),
        options = { 'buffers', 'curdir', 'tabpages', 'winsize' }
      })
    end
  }
  
  use {
    'kristijanhusak/vim-dadbod-ui',
    requires = {
      'tpope/vim-dadbod',
      'kristijanhusak/vim-dadbod-completion'
    }
  }
end)

vim.g.coc_global_extensions = {'coc-tsserver'}

vim.g.terraform_align = 1
vim.g.terraform_fmt_on_save = 1

vim.g.mapleader = " "

vim.keymap.set('n', '<leader>ff', "<cmd>lua require('fzf-lua').files()<CR>")
vim.keymap.set('n', '<leader>fg', "<cmd>lua require('fzf-lua').grep()<CR>")
vim.keymap.set('n', '<leader>fb', "<cmd>lua require('fzf-lua').buffers()<CR>")

vim.keymap.set('n', '<leader>mp', "<cmd>MarkdownPreview<CR>")
vim.keymap.set('n', '<leader>ms', "<cmd>MarkdownPreviewStop<CR>")

vim.keymap.set('n', '<leader>ss', "<cmd>lua require('persistence').load()<CR>")
vim.keymap.set('n', '<leader>sl', "<cmd>lua require('persistence').load({ last = true })<CR>")
vim.keymap.set('n', '<leader>sd', "<cmd>lua require('persistence').stop()<CR>")

vim.keymap.set('n', '<leader>db', "<cmd>DBUIToggle<CR>")
vim.keymap.set('n', '<leader>df', "<cmd>DBUIFindBuffer<CR>")
vim.keymap.set('n', '<leader>dr', "<cmd>DBUIRenameBuffer<CR>")

vim.api.nvim_create_autocmd({"BufWritePost"}, {
  pattern = {"*"},
  callback = function()
    vim.cmd("echo 'Syncing to real-time database...'")
  end,
})

require('neovim.db_integration')
