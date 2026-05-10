from src.knowledge_base import RULES
import logging

def get_recommendations(facts: dict, debug: bool = False) -> list[str]:
    """
    Forward chaining reasoning engine.
    Evaluates rules against facts and returns a list of recommendations.
    """
    # Sort rules by priority ascending (1=Critical, 2=Warning, 3=Informational)
    sorted_rules = sorted(RULES, key=lambda r: r['priority'])
    
    recommendations = []
    fired_rule_ids = []
    
    for rule in sorted_rules:
        try:
            # Evaluate the rule's lambda condition
            if rule['condition'](facts):
                recommendations.append(rule['recommendation'])
                fired_rule_ids.append(rule['id'])
                if debug:
                    logging.debug(f"Rule Fired: {rule['id']} - Priority: {rule['priority']}")
        except (KeyError, TypeError) as e:
            # Skip rule silently if required facts are missing or incorrect type
            if debug:
                logging.debug(f"Rule Skipped: {rule['id']} - Error: {e}")
            continue
            
    # Default message if no rules fire
    if not recommendations:
        recommendations.append("[OK] No specific issues detected. Continue regular monitoring.")

    if debug:
        fired_summary = ", ".join(fired_rule_ids) if fired_rule_ids else "None"
        print(f"[DEBUG] Fired rules: {fired_summary}")
        
    return recommendations
