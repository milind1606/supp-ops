import os
import re

class TopologyDiscoveryEngine:
    def __init__(self):
        self.file_path = os.getenv("TOPOLOGY_FILE_PATH", "topoloy-all-systems/topoloy-all-systems.txt")
        self.mcp_url = os.getenv("MCP_ANALYZER_URL", "http://support-ops-alert-analyzer-mcp:8001/analyze")
        self.mst_url = os.getenv("MST_ANALYZER_URL", "http://support-ops-alert-analyzer-mst:8001/analyze")

    def discover_target(self, alert_text: str, description_text: str) -> dict:
        combined = f"{alert_text} {description_text}".lower()
        
        # Absolute structural path fallback validation
        if not os.path.exists(self.file_path):
            # Check relative traversal if directory path varies during tests
            alt_path = os.path.join("..", self.file_path)
            if os.path.exists(alt_path):
                self.file_path = alt_path
            else:
                return self._apply_heuristic_fallback(combined, f"Topology map file not found at {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        entries = content.split("=== ENTRY ===")
        for entry in entries:
            if not entry.strip():
                continue
            
            host_match = re.search(r"HOSTNAME:([^\|\n]+)", entry, re.IGNORECASE)
            env_match = re.search(r"ENVIRONMENT:([^\|\n]+)", entry, re.IGNORECASE)
            platform_match = re.search(r"PARENT-PLATFORM:([^\|\n\s]+)", entry, re.IGNORECASE)

            if host_match and env_match and platform_match:
                host = host_match.group(1).strip().lower()
                env = env_match.group(1).strip()
                platform = platform_match.group(1).strip().upper()

                if host in combined:
                    target_url = self.mcp_url if platform == "MCP" else self.mst_url
                    return {
                        "parent_platform": platform,
                        "environment": env,
                        "hostname": host_match.group(1).strip(),
                        "analyzer_target_url": target_url
                    }

        return self._apply_heuristic_fallback(combined, "No explicit physical hostname matched topology map strings.")

    def _apply_heuristic_fallback(self, combined_text: str, reasoning: str) -> dict:
        if "mcp" in combined_text:
            return {"parent_platform": "MCP", "environment": "UNKNOWN", "hostname": "UNKNOWN", "analyzer_target_url": self.mcp_url, "notes": reasoning}
        if "mst" in combined_text:
            return {"parent_platform": "MST", "environment": "UNKNOWN", "hostname": "UNKNOWN", "analyzer_target_url": self.mst_url, "notes": reasoning}
        
        # Standard structural fallback target interface
        return {"parent_platform": "MCP", "environment": "UNKNOWN", "hostname": "UNKNOWN", "analyzer_target_url": self.mcp_url, "notes": reasoning}
