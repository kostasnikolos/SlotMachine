# Autonomous Execution & Zero-Interruption Rules

## Behavioral Directives:
1. **Auto-Proceed & Zero Interruption**:
   - Never ask the user for confirmation on intermediate steps, plans, or routine operations.
   - Do not stop to ask "Should I proceed?" or use multiple-choice question prompts for standard development decisions.
   - Always choose the best, most robust technical path and execute it immediately to completion.
   - When in planning mode, transition immediately to execution once the plan is established.

2. **Automated Tool Execution**:
   - Always run commands in standard sandbox mode first.
   - Use clean, prefix-matchable command shapes so the execution system can auto-approve commands without prompting the user.
   - For file modifications, execute directly using the appropriate tools without requesting manual approval.
   - Keep background daemons (servers, tunnels) alive and manage them autonomously.

3. **Repeatable Pipelines**:
   - Ensure all generation scripts (such as 3D asset generation and shaders) are 100% self-contained, reproducible, and can be rebooted or re-run on demand without manual intervention.
