import asyncio
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

# Attempt to import the Rust extension
try:
    from agent_lifecycle_rust import execute_command_rust_async, CommandOutput as RustCommandOutput
    print("SUCCESS: Rust command executor module loaded.")
except ImportError as e:
    print(f"ERROR: Failed to import Rust command executor: {e}")
    print("Ensure 'maturin develop' was run successfully in the '.venv' environment from '/root/agent-lifecycle'.")
    sys.exit(1)

async def run_test(test_name, command_str, cwd=None, env_vars=None, timeout_seconds=None, stdin_str=None,
                 expected_stdout_contains=None, expected_stderr_contains=None,
                 expected_exit_code=None,
                 expected_exception_type=None, expected_exception_message_contains=None):
    print(f"\n--- Running Test: {test_name} ---")
    print(f"Command: {command_str}")
    if stdin_str:
        print(f"Stdin: {stdin_str[:50]}{'...' if len(stdin_str) > 50 else ''}")
    if timeout_seconds:
        print(f"Timeout: {timeout_seconds}s (Expected Exception: {expected_exception_type.__name__ if expected_exception_type else 'None'})")

    try:
        result: RustCommandOutput = await execute_command_rust_async(
            command_str=command_str,
            cwd=cwd,
            env_vars=env_vars,
            timeout_seconds=timeout_seconds,
            stdin_str=stdin_str
        )

        if expected_exception_type is not None:
            print(f"FAIL: Expected exception {expected_exception_type.__name__} but no exception was raised.")
            print(f"Received instead: Stdout='{result.stdout}', Stderr='{result.stderr}', ExitCode={result.exit_code}")
            return False

        # No exception expected, proceed with normal checks
        print(f"Stdout: {result.stdout.strip()[:200]}{'...' if len(result.stdout.strip()) > 200 else ''}")
        print(f"Stderr: {result.stderr.strip()[:200]}{'...' if len(result.stderr.strip()) > 200 else ''}")
        print(f"Exit Code: {result.exit_code}")

        passed = True
        if expected_stdout_contains is not None and expected_stdout_contains not in result.stdout:
            print(f"FAIL: Expected stdout to contain '{expected_stdout_contains}'")
            passed = False
        if expected_stderr_contains is not None and expected_stderr_contains not in result.stderr:
            print(f"FAIL: Expected stderr to contain '{expected_stderr_contains}'")
            passed = False
        if expected_exit_code is not None and result.exit_code != expected_exit_code:
            print(f"FAIL: Expected exit code {expected_exit_code}, got {result.exit_code}")
            passed = False
        
        if passed:
            print("PASS")
        return passed

    except Exception as e:
        if expected_exception_type is not None:
            if isinstance(e, expected_exception_type):
                print(f"CAUGHT EXPECTED EXCEPTION: {type(e).__name__}: {e}")
                passed = True
                if expected_exception_message_contains is not None:
                    if expected_exception_message_contains.lower() not in str(e).lower():
                        print(f"FAIL: Expected exception message to contain (case-insensitive) '{expected_exception_message_contains}', but got '{str(e)}'")
                        passed = False
                    else:
                        print(f"PASS: Exception message contains expected text (case-insensitive).")
                
                if passed:
                    print("PASS")
                return passed
            else:
                print(f"FAIL: Expected exception {expected_exception_type.__name__} but got {type(e).__name__}: {e}")
                return False
        else: # An unexpected exception occurred
            print(f"PYTHON UNEXPECTED EXCEPTION during test: {type(e).__name__}: {e}")
            print("FAIL")
            return False

async def main():
    test_results = []

    # 1. Simple echo
    test_results.append(await run_test("Simple Echo", "echo hello rust world", 
                                     expected_stdout_contains="hello rust world", expected_exit_code=0))

    # 2. Command with arguments (listing a known, small directory)
    # Using /bin itself as it's small and predictable, focusing on `ls` not its output much
    test_results.append(await run_test("Command with Args", "ls /bin/echo", 
                                     expected_stdout_contains="/bin/echo", expected_exit_code=0))

    # 3. Command producing stderr
    test_results.append(await run_test("Stderr Output", "python3 -c \"import sys; sys.stderr.write('this is an error')\"",
                                     expected_stderr_contains="this is an error", expected_exit_code=0))

    # 4. Command with failing exit code
    test_results.append(await run_test("Failing Exit Code", "python3 -c \"import sys; sys.exit(42)\"",
                                     expected_exit_code=42))
    
    # 5. Command taking stdin
    test_results.append(await run_test("Stdin Handling", "python3 -c \"import sys; data = sys.stdin.read(); print(f'stdin_received: {data.strip()}')\"",
                                     stdin_str="hello from stdin",
                                     expected_stdout_contains="stdin_received: hello from stdin", expected_exit_code=0))

    # 6. Command that times out (sleep 3s, timeout 1s)
    test_results.append(await run_test("Timeout", "sleep 3", 
                                     timeout_seconds=1, 
                                     expected_exception_type=TimeoutError,
                                     expected_exception_message_contains="timed out after 1 seconds"))

    # 7. Non-existent command
    test_results.append(await run_test("Non-existent Command", "hopefullythiscommanddoesnotexist12345",
                                     expected_exception_type=OSError,
                                     expected_exception_message_contains="Failed to spawn command 'hopefullythiscommanddoesnotexist12345'",
                                     # Stderr check might be removed if exception is raised before stderr capture
                                     expected_stderr_contains=None)) # Let's remove stderr check for now as spawn error happens early

    # 8. Empty command string
    test_results.append(await run_test("Empty Command String", "",
                                     expected_exception_type=ValueError,
                                     expected_exception_message_contains="Empty command string provided"))
    
    # 9. Command with environment variables
    test_results.append(await run_test("Environment Variables", "python3 -c \"import os; print(os.getenv('MY_TEST_VAR', 'not_found'))\"",
                                     env_vars={"MY_TEST_VAR": "hello_env"},
                                     expected_stdout_contains="hello_env", expected_exit_code=0))

    # 10. Command in a specific CWD (create a temp dir and file)
    # For simplicity, we'll assume /tmp is writable and use a simple `pwd` or `ls`.
    # A more robust test would create a unique temp dir.
    test_results.append(await run_test("Custom CWD", "pwd", 
                                     cwd="/tmp", 
                                     expected_stdout_contains="/tmp", expected_exit_code=0))

    print("\n--- Test Summary ---")
    if all(test_results):
        print("All tests PASSED!")
    else:
        print(f"{sum(test_results)} out of {len(test_results)} tests PASSED.")
        print("SOME TESTS FAILED!")
        sys.exit(1) # Exit with error code if any test failed

if __name__ == "__main__":
    asyncio.run(main())
