"""
Complete drug interaction system using RxNorm API with local fallback
This is the ONLY file the agent uses - everything is consolidated here
"""

import requests
from typing import Optional, List, Dict
from langchain_core.tools import tool

# Local interaction database for fallback
LOCAL_INTERACTIONS = {
    'warfarin': {
        'aspirin': {'severity': 'High', 'description': 'Increased bleeding risk'},
        'ibuprofen': {'severity': 'High', 'description': 'Increased bleeding risk'},
        'acetaminophen': {'severity': 'Medium', 'description': 'Monitor INR levels'},
    },
    'aspirin': {
        'warfarin': {'severity': 'High', 'description': 'Increased bleeding risk'},
        'ibuprofen': {'severity': 'Medium', 'description': 'Increased GI bleeding risk'},
    },
    'ibuprofen': {
        'warfarin': {'severity': 'High', 'description': 'Increased bleeding risk'},
        'aspirin': {'severity': 'Medium', 'description': 'Increased GI bleeding risk'},
        'lisinopril': {'severity': 'Medium', 'description': 'Reduced antihypertensive effect'},
    },
    'lisinopril': {
        'ibuprofen': {'severity': 'Medium', 'description': 'Reduced antihypertensive effect'},
    }
}

@tool
def drug_interaction_checker(drug1_rxcui: str, drug2_rxcui: str) -> str:
    """
    Check if two drugs have a known interaction using RxNorm API.
    
    Args:
        drug1_rxcui: RxCUI of the first drug
        drug2_rxcui: RxCUI of the second drug
    
    Returns:
        String describing the interaction or no interaction found
    """
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={drug1_rxcui}+{drug2_rxcui}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for fullInteractionTypeGroup (correct structure)
            if "fullInteractionTypeGroup" in data and data["fullInteractionTypeGroup"]:
                interaction_group = data["fullInteractionTypeGroup"][0]
                if "fullInteractionType" in interaction_group and interaction_group["fullInteractionType"]:
                    interaction_type = interaction_group["fullInteractionType"][0]
                    if "interactionPair" in interaction_type and interaction_type["interactionPair"]:
                        pair = interaction_type["interactionPair"][0]
                        description = pair.get("description", "Interaction found but no description available")
                        severity = pair.get("severity", "Unknown")
                        return f"⚠️ Interaction found ({severity}): {description}"
            
            # Check for older structure as fallback
            elif "interactionTypeGroup" in data and data["interactionTypeGroup"]:
                interaction_group = data["interactionTypeGroup"][0]
                if "interactionType" in interaction_group and interaction_group["interactionType"]:
                    interaction_type = interaction_group["interactionType"][0]
                    if "interactionPair" in interaction_type and interaction_type["interactionPair"]:
                        pair = interaction_type["interactionPair"][0]
                        description = pair.get("description", "Interaction found but no description available")
                        severity = pair.get("severity", "Unknown")
                        return f"⚠️ Interaction found ({severity}): {description}"
            
            return "✅ No known interaction between these drugs."
        else:
            return f"❌ API request failed with status: {response.status_code}"
            
    except Exception as e:
        return f"❌ Error checking interaction: {str(e)}"

@tool
def drug_rxcui_finder(drug_name: str) -> str:
    """
    Find RxCUI for a drug name using RxNorm API.
    
    Args:
        drug_name: Name of the drug to find RxCUI for
    
    Returns:
        RxCUI string if found, or error message
    """
    try:
        from urllib.parse import quote
        
        # Clean and encode drug name
        clean_name = drug_name.strip()
        encoded_name = quote(clean_name)
        
        # Try exact match first
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={encoded_name}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'idGroup' in data and 'rxnormId' in data['idGroup']:
                rxcuis = data['idGroup']['rxnormId']
                if rxcuis:
                    return rxcuis[0]  # Return first match
        
        # If exact match fails, try approximate match
        url = f"https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term={encoded_name}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'approximateGroup' in data and 'candidate' in data['approximateGroup']:
                candidates = data['approximateGroup']['candidate']
                if candidates:
                    return candidates[0].get('rxcui', '')
        
        return f"❌ RxCUI not found for: {drug_name}"
        
    except Exception as e:
        return f"❌ Error finding RxCUI: {str(e)}"

@tool
def multi_drug_interaction_checker(drug_rxcuis: str) -> str:
    """
    Check interactions among multiple drugs using RxNorm API.
    
    Args:
        drug_rxcuis: Comma-separated list of RxCUIs to check for interactions
    
    Returns:
        String describing all interactions found
    """
    try:
        rxcuis = [rxcui.strip() for rxcui in drug_rxcuis.split(',') if rxcui.strip()]
        
        if len(rxcuis) < 2:
            return "❌ Need at least 2 drugs to check interactions"
        
        interactions_found = []
        
        # Check all pairs
        for i, rxcui1 in enumerate(rxcuis):
            for rxcui2 in rxcuis[i+1:]:
                result = drug_interaction_checker(rxcui1, rxcui2)
                if "⚠️ Interaction found" in result:
                    interactions_found.append(f"RxCUI {rxcui1} + RxCUI {rxcui2}: {result}")
        
        if interactions_found:
            return f"Found {len(interactions_found)} interactions:\n" + "\n".join(interactions_found)
        else:
            return "✅ No interactions found among the provided drugs."
            
    except Exception as e:
        return f"❌ Error checking multiple drug interactions: {str(e)}"
def check_all_drug_interactions(new_drugs: List[str], current_medications: List[str] = None) -> str:
    """
    Complete drug interaction checking function - this is what the agent should use
    
    Args:
        new_drugs: List of new drug names to check
        current_medications: List of current medications (optional)
    
    Returns:
        Formatted string with all interaction results
    """
    if current_medications is None:
        current_medications = []
    
    print(f"Checking interactions for new drugs: {new_drugs}")
    print(f"Against current medications: {current_medications}")
    
    interactions_found = []
    drug_rxcuis = {}
    api_working = False
    
    try:
        # Step 1: Get RxCUIs for all drugs
        all_drugs = new_drugs + current_medications
        for drug in all_drugs:
            rxcui = drug_rxcui_finder(drug)
            if not rxcui.startswith('❌'):
                drug_rxcuis[drug] = rxcui
                api_working = True
                print(f"✅ Found RxCUI for {drug}: {rxcui}")
            else:
                print(f"❌ Could not find RxCUI for {drug}")
        
        # Step 2: Check interactions using RxNorm API
        if api_working:
            # Check new drugs vs current medications
            for new_drug in new_drugs:
                if new_drug in drug_rxcuis:
                    for current_drug in current_medications:
                        if current_drug in drug_rxcuis:
                            result = drug_interaction_checker(drug_rxcuis[new_drug], drug_rxcuis[current_drug])
                            if "⚠️ Interaction found" in result:
                                interactions_found.append({
                                    'drug1': new_drug,
                                    'drug2': current_drug,
                                    'result': result,
                                    'source': 'RxNorm API'
                                })
            
            # Check new drugs vs new drugs
            for i, drug1 in enumerate(new_drugs):
                if drug1 in drug_rxcuis:
                    for drug2 in new_drugs[i+1:]:
                        if drug2 in drug_rxcuis:
                            result = drug_interaction_checker(drug_rxcuis[drug1], drug_rxcuis[drug2])
                            if "⚠️ Interaction found" in result:
                                interactions_found.append({
                                    'drug1': drug1,
                                    'drug2': drug2,
                                    'result': result,
                                    'source': 'RxNorm API'
                                })
        
        # Step 3: If no API results, use local database
        if not interactions_found:
            print("No RxNorm API interactions found, checking local database...")
            interactions_found = _check_local_interactions(new_drugs, current_medications)
        
        # Step 4: Format response
        return _format_interaction_response(new_drugs, current_medications, interactions_found, api_working)
        
    except Exception as e:
        print(f"Error in comprehensive drug checking: {e}")
        # Fallback to local database only
        interactions_found = _check_local_interactions(new_drugs, current_medications)
        return _format_interaction_response(new_drugs, current_medications, interactions_found, False)

def _check_local_interactions(new_drugs: List[str], current_medications: List[str]) -> List[Dict]:
    """Check interactions using local database"""
    interactions_found = []
    
    # Check new drugs vs current medications
    for new_drug in new_drugs:
        new_drug_lower = new_drug.lower()
        if new_drug_lower in LOCAL_INTERACTIONS:
            for current_drug in current_medications:
                current_drug_lower = current_drug.lower()
                if current_drug_lower in LOCAL_INTERACTIONS[new_drug_lower]:
                    interaction = LOCAL_INTERACTIONS[new_drug_lower][current_drug_lower]
                    interactions_found.append({
                        'drug1': new_drug,
                        'drug2': current_drug,
                        'result': f"⚠️ Interaction found ({interaction['severity']}): {interaction['description']}",
                        'source': 'Local Database'
                    })
    
    # Check new drugs vs new drugs
    for i, drug1 in enumerate(new_drugs):
        drug1_lower = drug1.lower()
        if drug1_lower in LOCAL_INTERACTIONS:
            for drug2 in new_drugs[i+1:]:
                drug2_lower = drug2.lower()
                if drug2_lower in LOCAL_INTERACTIONS[drug1_lower]:
                    interaction = LOCAL_INTERACTIONS[drug1_lower][drug2_lower]
                    interactions_found.append({
                        'drug1': drug1,
                        'drug2': drug2,
                        'result': f"⚠️ Interaction found ({interaction['severity']}): {interaction['description']}",
                        'source': 'Local Database'
                    })
    
    return interactions_found

def _format_interaction_response(new_drugs: List[str], current_medications: List[str], interactions_found: List[Dict], api_working: bool) -> str:
    """Format the final response"""
    
    source = "RxNorm API" if api_working else "Local Database"
    
    response_parts = [f"💊 **Drug Interaction Check ({source})**\n"]
    
    # Medications being checked
    response_parts.append("**Medications Checked:**")
    response_parts.append(f"- New: {', '.join([d.title() for d in new_drugs])}")
    if current_medications:
        response_parts.append(f"- Current: {', '.join([d.title() for d in current_medications])}")
    else:
        response_parts.append("- Current: None")
    response_parts.append("")
    
    # Interactions found
    if interactions_found:
        response_parts.append("**⚠️ Interactions Detected:**")
        for interaction in interactions_found:
            drug1 = interaction['drug1'].title()
            drug2 = interaction['drug2'].title()
            result = interaction['result']
            
            # Extract severity and description
            if "High" in result:
                emoji = "🔴"
            elif "Medium" in result:
                emoji = "🟡"
            else:
                emoji = "🟠"
            
            response_parts.append(f"{emoji} **{drug1} + {drug2}**")
            response_parts.append(f"   {result}")
        response_parts.append("")
    else:
        response_parts.append("✅ **No Major Interactions Found**")
        response_parts.append(f"Based on {source} analysis.\n")
    
    # Safety footer
    response_parts.extend([
        "**Important Notes:**",
        f"- This check uses the {'NIH RxNorm database' if api_working else 'local drug database'}",
        "- Always consult your pharmacist or doctor",
        "- Report any unusual side effects immediately",
        "- Keep all healthcare providers informed of your medications",
        "",
        f"**Source:** {'National Library of Medicine RxNorm API' if api_working else 'Local Drug Database'}"
    ])
    
    return "\n".join(response_parts)