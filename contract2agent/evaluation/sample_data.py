from __future__ import annotations

from contract2agent.evaluation.schema import AgentProfile, ToolSurface


def sample_agent_profiles() -> dict[str, AgentProfile]:
    return {
        "coding_agent": AgentProfile(
            agent_id="sample-coding-agent",
            name="Generic repository repair profile",
            description="Synthetic profile for an agent that edits repositories and runs tests.",
            declared_capabilities=["inspect repository", "edit code", "run tests"],
            tools=[
                ToolSurface(name="file_reader", category="filesystem", mode="read"),
                ToolSurface(
                    name="code_editor",
                    category="filesystem",
                    mode="write",
                    side_effect_level="medium",
                ),
                ToolSurface(
                    name="shell",
                    category="execution",
                    mode="command",
                    side_effect_level="medium",
                    requires_approval=True,
                ),
            ],
            tool_permissions=["read_workspace", "write_workspace", "run_tests"],
            data_access=["repository_files"],
            can_read_files=True,
            can_write_files=True,
            can_run_code=True,
            requires_human_approval=True,
            autonomy_level="medium",
            environment="local_workspace",
            sample_tasks=["Fix failing tests with a minimal diff."],
            policy_constraints=["stay inside workspace", "do not run destructive commands"],
            metadata={"synthetic": True},
        ),
        "unknown_agent": AgentProfile(
            agent_id="sample-unknown-agent",
            name="Sparse profile",
            description="Synthetic sparse profile with no tool or task evidence.",
            metadata={"synthetic": True},
        ),
    }
