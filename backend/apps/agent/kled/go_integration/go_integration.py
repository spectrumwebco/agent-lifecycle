"""
Go integration for the Kled agent.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.agent.go_integration import get_go_runtime_integration

logger = logging.getLogger(__name__)

class KledGoRuntime:
    """Go runtime integration for the Kled agent."""
    
    def __init__(self):
        """Initialize the Go runtime integration."""
        self.go_runtime = get_go_runtime_integration()
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to the Go runtime."""
        try:
            self.connected = self.go_runtime.connect()
            return self.connected
        except Exception as e:
            logger.error("Failed to connect to Go runtime: %s", e)
            return False
    
    def register_tools(self) -> bool:
        """Register tools with the Go runtime."""
        import json
        import os
        from pathlib import Path
        
        if not self.connected:
            if not self.connect():
                logger.error("Failed to connect to Go runtime")
                return False
        
        try:
            config_path = Path(os.path.dirname(os.path.dirname(__file__))) / "config" / "kled_tools.json"
            logger.info("Loading tools from %s", config_path)
            
            with open(config_path, 'r') as f:
                tools_config = json.load(f)
                tools = tools_config.get("tools", [])
            
            logger.info("Loaded %d tools from configuration", len(tools))
        except Exception as e:
            logger.error("Failed to load tools configuration: %s", e)
            return False
        
        logger.info("Registering %d tools with Go runtime", len(tools))
        
        for tool in tools:
            try:
                self.go_runtime.publish_event(
                    event_type="tool_registered",
                    data={
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                        "module": tool.get("module", ""),
                        "class": tool.get("class", "")
                    },
                    source="kled",
                    metadata={}
                )
                logger.info("Registered tool: %s", tool['name'])
            except Exception as e:
                logger.error("Failed to register tool %s: %s", tool['name'], e)
                return False
        
        return True
    
    def handle_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool call from the Go runtime."""
        try:
            logger.info("Handling tool call: %s with parameters %s", tool_name, parameters)
            
            config_path = Path(os.path.dirname(os.path.dirname(__file__))) / "config" / "kled_tools.json"
            with open(config_path, 'r') as f:
                tools_config = json.load(f)
                tools = tools_config.get("tools", [])
            
            tool_config = None
            for tool in tools:
                if tool["name"] == tool_name:
                    tool_config = tool
                    break
            
            if not tool_config:
                logger.error("Tool %s not found in configuration", tool_name)
                return {
                    "status": "error",
                    "error": f"Tool {tool_name} not found in configuration"
                }
            
            module_name = tool_config.get("module")
            class_name = tool_config.get("class")
            
            if not module_name or not class_name:
                logger.error("Tool %s has no module or class defined", tool_name)
                return {
                    "status": "error",
                    "error": f"Tool {tool_name} has no module or class defined"
                }
            
            try:
                module = __import__(module_name, fromlist=[class_name])
                tool_class = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                logger.error("Failed to import tool %s: %s", tool_name, e)
                return {
                    "status": "error",
                    "error": f"Failed to import tool {tool_name}: {str(e)}"
                }
            
            tool_instance = tool_class()
            result = tool_instance.execute(**parameters)
            
            return {
                "status": "success",
                "result": result
            }
        
        except Exception as e:
            logger.error("Error handling tool call %s: %s", tool_name, e)
            import traceback
            return {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def publish_event(self, event_type: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Publish an event to the Go runtime."""
        if not self.connected:
            if not self.connect():
                logger.error("Failed to connect to Go runtime")
                return False
        
        try:
            self.go_runtime.publish_event(
                event_type=event_type,
                data=data,
                source="kled",
                metadata=metadata or {}
            )
            return True
        except Exception as e:
            logger.error("Failed to publish event %s: %s", event_type, e)
            return False


def get_kled_go_runtime() -> KledGoRuntime:
    """Get the Kled Go runtime integration."""
    return KledGoRuntime()
