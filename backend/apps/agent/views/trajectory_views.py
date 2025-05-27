"""
Views for working with trajectories in the root directory.
"""

import json
from pathlib import Path

from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from apps.agent.trajectory_utils import trajectory_manager


@require_http_methods(["GET"])
def list_trajectories(request):
    """
    List all trajectories in the root directory.
    
    Returns:
        JsonResponse: A JSON response containing a list of trajectory IDs.
    """
    trajectory_ids = trajectory_manager.list_trajectories()
    return JsonResponse({"trajectories": trajectory_ids})


@require_http_methods(["GET"])
def get_trajectory(request, trajectory_id):
    """
    Get a specific trajectory from the root directory.
    
    Args:
        request: The HTTP request.
        trajectory_id: The ID of the trajectory to get.
        
    Returns:
        JsonResponse: A JSON response containing the trajectory data.
    """
    trajectory = trajectory_manager.load_trajectory(trajectory_id)
    
    if trajectory is None:
        raise Http404(f"Trajectory {trajectory_id} not found")
    
    trajectory_data = []
    for step in trajectory:
        serializable_step = {}
        for key, value in step.items():
            if isinstance(value, dict):
                serializable_step[key] = {
                    k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v
                    for k, v in value.items()
                }
            elif not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                serializable_step[key] = str(value)
            else:
                serializable_step[key] = value
        trajectory_data.append(serializable_step)
    
    return JsonResponse({"trajectory": trajectory_data})


@csrf_exempt
@require_http_methods(["POST"])
def save_trajectory(request):
    """
    Save a trajectory to the root directory.
    
    Args:
        request: The HTTP request containing the trajectory data.
        
    Returns:
        JsonResponse: A JSON response containing the ID of the saved trajectory.
    """
    try:
        data = json.loads(request.body)
        trajectory = data.get("trajectory")
        trajectory_id = data.get("trajectory_id")
        
        if not trajectory:
            return JsonResponse(
                {"error": "No trajectory data provided"}, 
                status=400
            )
        
        saved_id = trajectory_manager.save_trajectory(trajectory, trajectory_id)
        
        return JsonResponse({
            "status": "success",
            "trajectory_id": saved_id
        })
    
    except Exception as e:
        return JsonResponse(
            {"error": f"Failed to save trajectory: {str(e)}"}, 
            status=500
        )


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_trajectory(request, trajectory_id):
    """
    Delete a trajectory from the root directory.
    
    Args:
        request: The HTTP request.
        trajectory_id: The ID of the trajectory to delete.
        
    Returns:
        JsonResponse: A JSON response indicating success or failure.
    """
    success = trajectory_manager.delete_trajectory(trajectory_id)
    
    if not success:
        return JsonResponse(
            {"error": f"Trajectory {trajectory_id} not found"}, 
            status=404
        )
    
    return JsonResponse({"status": "success"})


@require_http_methods(["GET"])
def download_trajectory(request, trajectory_id):
    """
    Download a trajectory as a JSON file.
    
    Args:
        request: The HTTP request.
        trajectory_id: The ID of the trajectory to download.
        
    Returns:
        HttpResponse: A response containing the trajectory JSON file.
    """
    trajectory_path = trajectory_manager.get_trajectory_path(trajectory_id)
    
    if not trajectory_path.exists():
        raise Http404(f"Trajectory {trajectory_id} not found")
    
    with open(trajectory_path, 'r') as f:
        trajectory_data = f.read()
    
    response = HttpResponse(
        trajectory_data, 
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{trajectory_id}.json"'
    
    return response
