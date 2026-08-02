# agents/diff_detector.py

import json
from dataclasses import dataclass, field
from typing import List, Dict
from llm_config import get_llm_response
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from pydantic import SecretStr

load_dotenv()


# ═══════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════

@dataclass
class ChangeItem:
    change_type: str    # "removed" / "added" / "modified"
    endpoint: str       # "/users" ya "GLOBAL"
    description: str    # Kya badla
    impact: str         # "BREAKING" / "NON-BREAKING" / "NEW"
    migration_hint: str # Kaise fix karein


@dataclass
class DiffReport:
    api_name: str
    v1_label: str
    v2_label: str
    breaking_changes: List[ChangeItem]
    non_breaking_changes: List[ChangeItem]
    new_features: List[ChangeItem]
    migration_guide: str
    total_changes: int


# ═══════════════════════════════════════════
# DIFF DETECTOR AGENT
# ═══════════════════════════════════════════

class DiffDetectorAgent:
    """
    Do APISchema objects compare karo.
    Breaking changes automatically detect karo.

    Use case:
    "API v2 se v3 migrate karna hai.
     Mera code tootega kya?"

    Hermes: "Haan — 3 endpoints remove hue,
             2 ke required params badal gaye,
             auth method change hua"
    """

    # LLM sirf small APIs ke liye zaroorat hai
    # Direct comparison zyada reliable hai
    def __init__(self):
        # self.llm = ChatGroq(
        #     # model="llama-3.3-70b-versatile",
        #     # # Adversarial testing ke liye gpt-4o-mini enough hai
        #     # # Code analysis = pattern matching
        #     # # gpt-4o ki zaroorat nahi
        #     # temperature=0,
        #     # api_key=SecretStr(os.getenv("GROQ_API_KEY") or "")


        # )
        pass

    # ─────────────────────────────────────
    # MAIN: Two schemas compare karo
    # ─────────────────────────────────────

    def compare(
        self,
        schema_v1,
        schema_v2,
        v1_label: str = "v1",
        v2_label: str = "v2"
    ) -> DiffReport:

        print(f"\n🔄 Comparing {v1_label} vs {v2_label}...")

        breaking = []
        non_breaking = []
        new_features = []

        # Maps banao: "METHOD:path" → endpoint object
        # Kyun METHOD include kiya?
        # GET /users aur POST /users = alag endpoints
        # Sirf path se compare = wrong
        v1_map = {
            f"{ep.method}:{ep.path}": ep
            for ep in schema_v1.endpoints
        }
        v2_map = {
            f"{ep.method}:{ep.path}": ep
            for ep in schema_v2.endpoints
        }

        v1_keys = set(v1_map.keys())
        v2_keys = set(v2_map.keys())

        # ── Removed endpoints (BREAKING) ──
        removed = v1_keys - v2_keys
        # Set difference: v1 mein tha, v2 mein nahi

        for key in removed:
            ep = v1_map[key]
            breaking.append(ChangeItem(
                change_type="removed",
                endpoint=f"{ep.method} {ep.path}",
                description=(
                    f"Endpoint removed in {v2_label}"
                ),
                impact="BREAKING",
                migration_hint=(
                    f"Remove or replace calls to {ep.path}. "
                    f"Check {v2_label} docs for alternative."
                )
            ))

        # ── New endpoints (NON-BREAKING) ──
        added = v2_keys - v1_keys

        for key in added:
            ep = v2_map[key]
            new_features.append(ChangeItem(
                change_type="added",
                endpoint=f"{ep.method} {ep.path}",
                description=f"New endpoint in {v2_label}",
                impact="NEW",
                migration_hint="Optional — use if needed"
            ))

        # ── Changed endpoints ──
        common = v1_keys & v2_keys
        # Set intersection: dono mein hain

        for key in common:
            ep_v1 = v1_map[key]
            ep_v2 = v2_map[key]

            changes = self._compare_single_endpoint(
                ep_v1, ep_v2, v1_label, v2_label
            )

            for change in changes:
                if change.impact == "BREAKING":
                    breaking.append(change)
                else:
                    non_breaking.append(change)

        # ── Global changes ──

        # Auth method changed?
        if schema_v1.auth_method != schema_v2.auth_method:
            breaking.append(ChangeItem(
                change_type="modified",
                endpoint="GLOBAL",
                description=(
                    f"Auth changed: {schema_v1.auth_method} "
                    f"→ {schema_v2.auth_method}"
                ),
                impact="BREAKING",
                migration_hint=(
                    f"Update all requests to use "
                    f"{schema_v2.auth_method}. "
                    f"Update .env credentials."
                )
            ))

        # Base URL changed?
        if schema_v1.base_url != schema_v2.base_url:
            breaking.append(ChangeItem(
                change_type="modified",
                endpoint="GLOBAL",
                description=(
                    f"Base URL changed: "
                    f"{schema_v1.base_url} → {schema_v2.base_url}"
                ),
                impact="BREAKING",
                migration_hint=(
                    f"Update BASE_URL to: {schema_v2.base_url}"
                )
            ))

        # Migration guide
        guide = self._build_migration_guide(
            breaking, non_breaking, new_features,
            v1_label, v2_label
        )

        total = len(breaking) + len(non_breaking) + len(new_features)

        print(f"✅ Diff done!")
        print(f"   🔴 Breaking:     {len(breaking)}")
        print(f"   🟡 Non-breaking: {len(non_breaking)}")
        print(f"   🟢 New:          {len(new_features)}")

        return DiffReport(
            api_name=schema_v1.api_name,
            v1_label=v1_label,
            v2_label=v2_label,
            breaking_changes=breaking,
            non_breaking_changes=non_breaking,
            new_features=new_features,
            migration_guide=guide,
            total_changes=total
        )

    # ─────────────────────────────────────
    # Single endpoint compare
    # ─────────────────────────────────────

    def _compare_single_endpoint(
        self,
        ep_v1,
        ep_v2,
        v1_label: str,
        v2_label: str
    ) -> List[ChangeItem]:

        changes = []
        label = f"{ep_v1.method} {ep_v1.path}"

        # New required params added? → BREAKING
        new_required = (
            set(ep_v2.required_params) -
            set(ep_v1.required_params)
        )
        if new_required:
            changes.append(ChangeItem(
                change_type="modified",
                endpoint=label,
                description=(
                    f"New required params: {list(new_required)}"
                ),
                impact="BREAKING",
                migration_hint=(
                    f"Add to all calls: {list(new_required)}"
                )
            ))

        # Required params removed? → NON-BREAKING
        removed_required = (
            set(ep_v1.required_params) -
            set(ep_v2.required_params)
        )
        if removed_required:
            changes.append(ChangeItem(
                change_type="modified",
                endpoint=label,
                description=(
                    f"Params now optional: {list(removed_required)}"
                ),
                impact="NON-BREAKING",
                migration_hint=(
                    f"These params optional now — "
                    f"can keep sending them"
                )
            ))

        # New optional params? → NON-BREAKING
        new_optional = (
            set(ep_v2.optional_params) -
            set(ep_v1.optional_params)
        )
        if new_optional:
            changes.append(ChangeItem(
                change_type="modified",
                endpoint=label,
                description=(
                    f"New optional params: {list(new_optional)}"
                ),
                impact="NON-BREAKING",
                migration_hint=(
                    f"Can optionally use: {list(new_optional)}"
                )
            ))

        # Auth requirement changed?
        if ep_v1.auth_required != ep_v2.auth_required:
            if ep_v2.auth_required:
                # Auth add hua → BREAKING
                changes.append(ChangeItem(
                    change_type="modified",
                    endpoint=label,
                    description="Endpoint now requires auth",
                    impact="BREAKING",
                    migration_hint=(
                        f"Add auth headers to {ep_v1.path} calls"
                    )
                ))
            else:
                # Auth remove hua → NON-BREAKING
                changes.append(ChangeItem(
                    change_type="modified",
                    endpoint=label,
                    description="Auth no longer required",
                    impact="NON-BREAKING",
                    migration_hint="Auth headers now optional"
                ))

        return changes

    # ─────────────────────────────────────
    # Migration guide banao
    # ─────────────────────────────────────

    def _build_migration_guide(
        self,
        breaking: list,
        non_breaking: list,
        new_features: list,
        v1_label: str,
        v2_label: str
    ) -> str:

        if not breaking and not non_breaking:
            return (
                f"✅ No changes detected between "
                f"{v1_label} and {v2_label}. "
                f"Safe to upgrade."
            )

        if not breaking:
            return (
                f"✅ Migration from {v1_label} to {v2_label} "
                f"is safe — no breaking changes.\n"
                f"Optionally adopt {len(new_features)} "
                f"new features."
            )

        # Breaking changes hain
        lines = [
            f"# Migration: {v1_label} → {v2_label}\n",
            f"⚠️  {len(breaking)} breaking changes "
            f"require code updates.\n",
            "## Required Changes (Breaking)\n"
        ]

        for i, change in enumerate(breaking, 1):
            lines.append(
                f"{i}. **{change.endpoint}**\n"
                f"   What changed: {change.description}\n"
                f"   How to fix: {change.migration_hint}\n"
            )

        if non_breaking:
            lines.append(
                f"\n## Optional Updates (Non-Breaking)\n"
            )
            for change in non_breaking:
                lines.append(
                    f"- {change.endpoint}: {change.description}\n"
                )

        if new_features:
            lines.append(f"\n## New Features Available\n")
            for feature in new_features:
                lines.append(
                    f"- `{feature.endpoint}`: "
                    f"{feature.description}\n"
                )

        return "\n".join(lines)