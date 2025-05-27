# Shared Application State Documentation

This document describes the shared application state implementation between the React frontend and Go/Python backend in the agent_runtime system.

## Overview

The shared application state system enables real-time, bidirectional communication between the frontend and backend components of the agent_runtime system. It leverages WebSockets for real-time updates and uses Go as a high-performance intermediary layer between the React frontend and Django backend.

## Architecture

The shared state system consists of the following components:

1. **Go State Manager**: A high-performance state manager implemented in Go that handles state persistence, retrieval, and real-time updates.

2. **Django WebSocket Consumer**: A Django Channels consumer that connects to the Go state manager and provides WebSocket endpoints for the frontend.

3. **React Hooks and Components**: React hooks and components that connect to the WebSocket endpoints and provide a simple API for using shared state in the frontend.

4. **gRPC Bridge**: A bridge between Django and Go that enables communication between the two components.

## Go State Manager

The Go state manager is implemented in the `internal/statemanager/websocket/websocket_state_manager.go` file. It provides the following functionality:

- State persistence and retrieval
- Real-time state updates via WebSockets
- Support for different state types (task, agent, lifecycle, shared)
- Integration with Supabase for persistent storage

## Django WebSocket Consumer

The Django WebSocket consumer is implemented in the `api/websocket_state.py` file. It provides the following functionality:

- WebSocket endpoints for the frontend
- Connection to the Go state manager via gRPC
- Real-time state updates to connected clients
- Support for different state types

## React Hooks and Components

The React hooks and components are implemented in the `frontend/src/hooks/useSharedState.ts` and `frontend/src/components/SharedState.tsx` files. They provide the following functionality:

- Simple API for using shared state in React components
- Real-time state updates via WebSockets
- Support for different state types
- Error handling and connection status

## Usage

### Backend (Django)

```python
from api.websocket_state import update_shared_state, get_shared_state

# Get shared state
state = await get_shared_state(state_id='example')

# Update shared state
success = await update_shared_state(
    state_id='example',
    data={'messages': ['Hello, world!'], 'count': 1}
)
```

### Frontend (React)

```tsx
import useSharedState from '../hooks/useSharedState';

const MyComponent = () => {
  const { state, updateState, connected, error } = useSharedState({
    stateType: 'shared',
    stateId: 'example',
    initialState: {
      messages: [],
      count: 0
    }
  });

  // Use state and updateState in your component
  return (
    <div>
      <p>Connected: {connected ? 'Yes' : 'No'}</p>
      <p>Message count: {state.count}</p>
      <button onClick={() => updateState({
        ...state,
        count: state.count + 1
      })}>
        Increment count
      </button>
    </div>
  );
};
```

## Integration with CoPilotKit CoAgents SDK

The shared state system is designed to integrate with the CoPilotKit CoAgents SDK for creating a more engaging UI experience. This integration enables:

1. Configuring AI components in both the React frontend and Go/Python backend
2. Two-way communication between components
3. Autonomous operation without human-in-the-loop requirements
4. Real-time state updates via WebSockets

## Performance Considerations

The shared state system uses Go as a high-performance intermediary layer between the React frontend and Django backend. This approach provides several benefits:

1. **Reduced latency**: Go's efficient concurrency model enables handling many concurrent WebSocket connections with minimal overhead.

2. **Scalability**: The Go state manager can handle thousands of concurrent connections, making it suitable for large-scale deployments.

3. **Reliability**: The system includes error handling and reconnection logic to ensure reliable communication between components.

## Security Considerations

The shared state system includes several security features:

1. **Authentication**: WebSocket connections require authentication via Django's authentication system.

2. **Authorization**: Access to state is controlled based on the user's permissions.

3. **Data validation**: All state updates are validated before being applied.

## Future Improvements

Planned improvements to the shared state system include:

1. **State versioning**: Track changes to state over time and support rollback to previous versions.

2. **Conflict resolution**: Implement strategies for resolving conflicts when multiple clients update the same state simultaneously.

3. **Offline support**: Enable offline operation with state synchronization when the client reconnects.

4. **Performance optimizations**: Further optimize the performance of the state manager for large-scale deployments.
