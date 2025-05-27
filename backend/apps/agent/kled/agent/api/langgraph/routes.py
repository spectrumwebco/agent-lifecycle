from flask import Blueprint, request, jsonify
import json
from agent.api.utils import AttrDict
from agent.agent.problem_statement import problem_statement_from_simplified_input
from agent.environment.repo import repo_from_simplified_input
from agent.run.run_single import RunSingle, RunSingleConfig

langgraph_bp = Blueprint('langgraph', __name__, url_prefix='/api/agent')

@langgraph_bp.route('/plan', methods=['POST'])
def plan():
    """Create a plan based on the input and agent state."""
    data = request.json
    input_text = data.get('input', '')
    agent_state = data.get('state', {})
    
    try:
        config = RunSingleConfig.model_validate(
            problem_statement=problem_statement_from_simplified_input(
                input=input_text,
                type="text"
            ),
            agent={
                "model": {
                    "model_name": "gpt-4",
                }
            },
            environment={
                "repo": repo_from_simplified_input(
                    input="",
                    base_commit="",
                    type="auto"
                )
            }
        )
        
        agent = RunSingle.from_config(config).agent
        plan = agent.create_plan(input_text)
        
        return jsonify({
            "plan": plan,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@langgraph_bp.route('/select_tool', methods=['POST'])
def select_tool():
    """Select a tool based on the input, plan, and available tools."""
    data = request.json
    input_text = data.get('input', '')
    plan = data.get('plan', '')
    tools = data.get('tools', [])
    agent_state = data.get('state', {})
    
    try:
        config = RunSingleConfig.model_validate(
            problem_statement=problem_statement_from_simplified_input(
                input=input_text,
                type="text"
            ),
            agent={
                "model": {
                    "model_name": "gpt-4",
                }
            },
            environment={
                "repo": repo_from_simplified_input(
                    input="",
                    base_commit="",
                    type="auto"
                )
            }
        )
        
        agent = RunSingle.from_config(config).agent
        tool_selection = agent.select_tool(plan, tools)
        
        return jsonify({
            "selected_tool": tool_selection.get("tool", ""),
            "tool_input": tool_selection.get("input", ""),
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@langgraph_bp.route('/execute_tool', methods=['POST'])
def execute_tool():
    """Execute a tool with the provided input."""
    data = request.json
    tool_name = data.get('tool', '')
    tool_input = data.get('input', '')
    agent_state = data.get('state', {})
    
    try:
        config = RunSingleConfig.model_validate(
            problem_statement=problem_statement_from_simplified_input(
                input="",
                type="text"
            ),
            agent={
                "model": {
                    "model_name": "gpt-4",
                }
            },
            environment={
                "repo": repo_from_simplified_input(
                    input="",
                    base_commit="",
                    type="auto"
                )
            }
        )
        
        agent = RunSingle.from_config(config).agent
        tool_output = agent.execute_tool(tool_name, tool_input)
        
        return jsonify({
            "output": tool_output,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@langgraph_bp.route('/reflect', methods=['POST'])
def reflect():
    """Reflect on observations and update the plan."""
    data = request.json
    observations = data.get('observations', [])
    plan = data.get('plan', '')
    agent_state = data.get('state', {})
    
    try:
        config = RunSingleConfig.model_validate(
            problem_statement=problem_statement_from_simplified_input(
                input="",
                type="text"
            ),
            agent={
                "model": {
                    "model_name": "gpt-4",
                }
            },
            environment={
                "repo": repo_from_simplified_input(
                    input="",
                    base_commit="",
                    type="auto"
                )
            }
        )
        
        agent = RunSingle.from_config(config).agent
        reflection = agent.reflect(observations, plan)
        
        return jsonify({
            "reflection": reflection,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@langgraph_bp.route('/decide_action', methods=['POST'])
def decide_action():
    """Decide the next action based on reflection and observations."""
    data = request.json
    reflection = data.get('reflection', '')
    observations = data.get('observations', [])
    agent_state = data.get('state', {})
    
    try:
        config = RunSingleConfig.model_validate(
            problem_statement=problem_statement_from_simplified_input(
                input="",
                type="text"
            ),
            agent={
                "model": {
                    "model_name": "gpt-4",
                }
            },
            environment={
                "repo": repo_from_simplified_input(
                    input="",
                    base_commit="",
                    type="auto"
                )
            }
        )
        
        agent = RunSingle.from_config(config).agent
        action = agent.decide_action(reflection, observations)
        
        return jsonify({
            "action": action,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@langgraph_bp.route('/finalize', methods=['POST'])
def finalize():
    """Finalize the agent workflow and return the output."""
    data = request.json
    observations = data.get('observations', [])
    agent_state = data.get('state', {})
    
    try:
        config = RunSingleConfig.model_validate(
            problem_statement=problem_statement_from_simplified_input(
                input="",
                type="text"
            ),
            agent={
                "model": {
                    "model_name": "gpt-4",
                }
            },
            environment={
                "repo": repo_from_simplified_input(
                    input="",
                    base_commit="",
                    type="auto"
                )
            }
        )
        
        agent = RunSingle.from_config(config).agent
        output = agent.finalize(observations)
        
        return jsonify({
            "output": output,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500
