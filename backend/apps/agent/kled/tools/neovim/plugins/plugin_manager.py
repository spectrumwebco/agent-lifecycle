"""
Plugin manager for Neovim in the agent_runtime system.

This module provides functionality for managing Neovim plugins,
including installation, configuration, and verification.
"""

import os
import subprocess
import json
import logging
from typing import Dict, List, Optional, Any, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("neovim-plugin-manager")


class NeovimPluginManager:
    """Manager for Neovim plugins in the agent_runtime system."""

    def __init__(self):
        """Initialize the Neovim plugin manager."""
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.nvim_config_dir = os.path.expanduser("~/.config/nvim")
        self.nvim_data_dir = os.path.expanduser("~/.local/share/nvim")
        self.plugin_dir = os.path.join(
            self.nvim_data_dir, "site", "pack", "packer", "start"
        )
        self.install_script = os.path.join(self.script_dir, "install.sh")
        self.init_lua = os.path.join(self.script_dir, "init.lua")
        
        self.core_plugins = [
            "packer.nvim",
            "tmux.nvim",
            "fzf-lua",
            "molten-nvim",
            "tokyonight.nvim",
            "coc.nvim",
            "markdown-preview.nvim"
        ]
        
        self.terraform_plugins = [
            "vim-terraform",
            "vim-terraform-completion",
            "vim-hcl"
        ]
        
        self.all_plugins = self.core_plugins + self.terraform_plugins

    def install_plugins(self) -> bool:
        """Install all Neovim plugins.
        
        Returns:
            bool: True if installation was successful, False otherwise
        """
        try:
            logger.info("Installing Neovim plugins...")
            result = subprocess.run(
                ["bash", self.install_script],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(result.stdout)
            if result.stderr:
                logger.warning(result.stderr)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error installing plugins: {e}")
            logger.error(f"Stderr: {e.stderr}")
            return False

    def verify_plugins(self) -> Tuple[bool, List[str]]:
        """Verify that all required plugins are installed.
        
        Returns:
            Tuple[bool, List[str]]: (success, missing_plugins)
        """
        missing_plugins = []
        
        for plugin in self.all_plugins:
            plugin_path = os.path.join(self.plugin_dir, plugin)
            if not os.path.exists(plugin_path):
                missing_plugins.append(plugin)
        
        return len(missing_plugins) == 0, missing_plugins

    def verify_terraform_plugins(self) -> Tuple[bool, List[str]]:
        """Verify that all Terraform plugins are installed.
        
        Returns:
            Tuple[bool, List[str]]: (success, missing_plugins)
        """
        missing_plugins = []
        
        for plugin in self.terraform_plugins:
            plugin_path = os.path.join(self.plugin_dir, plugin)
            if not os.path.exists(plugin_path):
                missing_plugins.append(plugin)
        
        return len(missing_plugins) == 0, missing_plugins

    def update_plugins(self) -> bool:
        """Update all Neovim plugins.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            logger.info("Updating Neovim plugins...")
            for plugin in self.all_plugins:
                plugin_path = os.path.join(self.plugin_dir, plugin)
                if os.path.exists(plugin_path):
                    logger.info(f"Updating {plugin}...")
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=plugin_path,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    logger.info(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error updating plugins: {e}")
            return False

    def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about installed plugins.
        
        Returns:
            Dict[str, Any]: Information about installed plugins
        """
        plugin_info = {
            "core_plugins": {},
            "terraform_plugins": {}
        }
        
        for plugin in self.core_plugins:
            plugin_path = os.path.join(self.plugin_dir, plugin)
            plugin_info["core_plugins"][plugin] = os.path.exists(plugin_path)
        
        for plugin in self.terraform_plugins:
            plugin_path = os.path.join(self.plugin_dir, plugin)
            plugin_info["terraform_plugins"][plugin] = os.path.exists(plugin_path)
        
        return plugin_info

    def configure_terraform_plugins(self) -> bool:
        """Configure Terraform plugins.
        
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        try:
            coc_settings_path = os.path.join(self.nvim_config_dir, "coc-settings.json")
            
            if os.path.exists(coc_settings_path):
                with open(coc_settings_path, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            if "languageserver" not in settings:
                settings["languageserver"] = {}
            
            settings["languageserver"]["terraform"] = {
                "command": "terraform-ls",
                "args": ["serve"],
                "filetypes": ["terraform", "tf"],
                "initializationOptions": {},
                "settings": {}
            }
            
            with open(coc_settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info("Terraform plugins configured successfully")
            return True
        except Exception as e:
            logger.error(f"Error configuring Terraform plugins: {e}")
            return False


plugin_manager = NeovimPluginManager()


def install_all_plugins() -> bool:
    """Install all Neovim plugins.
    
    Returns:
        bool: True if installation was successful, False otherwise
    """
    return plugin_manager.install_plugins()


def verify_all_plugins() -> Tuple[bool, List[str]]:
    """Verify that all required plugins are installed.
    
    Returns:
        Tuple[bool, List[str]]: (success, missing_plugins)
    """
    return plugin_manager.verify_plugins()


def verify_terraform_plugins() -> Tuple[bool, List[str]]:
    """Verify that all Terraform plugins are installed.
    
    Returns:
        Tuple[bool, List[str]]: (success, missing_plugins)
    """
    return plugin_manager.verify_terraform_plugins()


def update_all_plugins() -> bool:
    """Update all Neovim plugins.
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    return plugin_manager.update_plugins()


def get_plugin_info() -> Dict[str, Any]:
    """Get information about installed plugins.
    
    Returns:
        Dict[str, Any]: Information about installed plugins
    """
    return plugin_manager.get_plugin_info()


def configure_terraform_plugins() -> bool:
    """Configure Terraform plugins.
    
    Returns:
        bool: True if configuration was successful, False otherwise
    """
    return plugin_manager.configure_terraform_plugins()


if __name__ == "__main__":
    success = install_all_plugins()
    if success:
        logger.info("Plugin installation completed successfully")
    else:
        logger.error("Plugin installation failed")
