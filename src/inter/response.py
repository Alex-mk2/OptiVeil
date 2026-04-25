import datetime

class RuleGenerator:
    def __init__(self, findings):
        self.findings = findings


    def generate_yara_rule(self):
        """Genera una regla YARA basada en los banners detectados."""
        rules = []
        for item in self.findings.get("ports", []):
            service = item.get("service", "unknown")
            banner = item.get("banner", "")
            
            if not banner: continue

            rule_name = f"Detect_{service}_{item['port']}"
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
            
            rule = f"""rule {rule_name} {{
    meta:
        description = "Deteccion automatica de servicio identificado por OptiVeil"
        author = "OptiVeil AI - Variacion B"
        date = "{timestamp}"
        target_port = {item['port']}
        banner_info = "{banner}"

    strings:
        $service_banner = "{banner}"

    condition:
        $service_banner
}}
"""
            rules.append(rule)
        return "\n".join(rules)