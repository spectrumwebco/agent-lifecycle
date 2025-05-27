"""
Neovim action handler for the Python agent.
"""

import asyncio
import re
import time

from ..types import StepOutput


def handle_neovim_action(agent, step: StepOutput) -> StepOutput:
    """Handle execution of a Neovim command.

    Args:
        agent: The agent instance
        step: The step containing the Neovim action

    Returns:
        StepOutput: The result of the action
    """
    action = step.action
    command_parts = action.split("\n", 1)
    command_line = command_parts[0]
    command_content = command_parts[1] if len(command_parts) > 1 else ""

    file_path = None
    background = False

    if "--file=" in command_line:
        file_match = re.search(r"--file=([^\s]+)", command_line)
        if file_match:
            file_path = file_match.group(1)
            command_line = command_line.replace(
                file_match.group(0), ""
            ).strip()

    if "--background" in command_line:
        background = True
        command_line = command_line.replace("--background", "").strip()

    if command_line.startswith("neovim "):
        command = command_line[7:].strip()
    else:
        command = command_line.strip()

    if command_content and command_content.strip():
        command = command_content.strip()

    if background:
        result = asyncio.run(
            agent._neovim_executor.execute_background(command, file_path)
        )
        task_id = result.get("task_id", "unknown")
        step.observation = (
            f"Neovim command started in background. Task ID: {task_id}"
        )
        step.execution_time = 0.0
        if "state" not in step.extra_info:
            step.extra_info["state"] = {}
        step.extra_info["state"]["neovim_task_id"] = task_id
    else:
        start_time = time.perf_counter()
        result = asyncio.run(
            agent._neovim_executor.execute(command, file_path)
        )
        step.execution_time = time.perf_counter() - start_time
        step.observation = str(result)

    return step
