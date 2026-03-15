from typing import Dict

import pandas as pd


def suggest_root_cause(category: str, message: str) -> str:
    """
    Simple rule-based mapping from category / keywords to possible root cause.
    This can be extended or replaced with an LLM call.
    """
    msg = (message or "").lower()
    if category == "timeout error" or "timeout" in msg:
        return "Possible cause: handshake or ready/valid signal not asserted, or downstream module stalled."
    if category == "protocol violation" or "protocol" in msg:
        return "Possible cause: protocol handshake ordering violated; check FSM and interface timing."
    if category == "data mismatch" or "mismatch" in msg or "compare fail" in msg:
        return "Possible cause: scoreboard expectation mismatch or incorrect reference model behavior."
    if category == "memory error" or "ecc" in msg or "parity" in msg:
        return "Possible cause: memory initialization or ECC/parity generation logic issue."
    if category == "assertion failure" or "assert" in msg:
        return "Possible cause: violated design assumption captured by assertion; inspect surrounding signals."
    return "Possible cause: unknown; inspect waveform around failure and check recent RTL changes."


def suggest_debug_actions(category: str, module: str, message: str) -> str:
    """
    Recommend concrete debugging steps based on category and module.
    """
    actions = []
    if category in ("protocol violation", "timeout error"):
        actions.append("verify protocol handshake signals and timing")
    if category in ("data mismatch", "memory error"):
        actions.append("check scoreboard expectations and memory transactions")
    if category == "assertion failure":
        actions.append("inspect assertion conditions and triggering signals")

    if "axi" in module.lower() or "axi" in (message or "").lower():
        actions.append("validate AXI channel ordering and ready/valid behavior")
    if "memory" in module.lower():
        actions.append("inspect memory interface, address alignment, and ECC/parity flags")

    if not actions:
        actions.append("inspect module signals around failure timestamp")

    return "; ".join(actions)


def add_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["root_cause_suggestion"] = df.apply(
        lambda row: suggest_root_cause(row.get("category", ""), row.get("message", "")),
        axis=1,
    )
    df["debug_actions"] = df.apply(
        lambda row: suggest_debug_actions(
            row.get("category", ""), str(row.get("module", "")), row.get("message", "")
        ),
        axis=1,
    )
    return df


if __name__ == "__main__":
    sample = pd.DataFrame(
        {
            "category": ["timeout error", "data mismatch"],
            "module": ["AXI_INTERFACE", "MEMORY_CTRL"],
            "message": ["AXI timeout on read", "Data mismatch detected"],
        }
    )
    out = add_recommendations(sample)
    print(out[["category", "root_cause_suggestion", "debug_actions"]])

