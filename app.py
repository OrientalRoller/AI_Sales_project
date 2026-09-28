import streamlit as st
import requests
import json
from pymongo import MongoClient

HUBSPOT_ACCESS_TOKEN = "YOR HUBSPOT ACCESS TOKEN" 
HUBSPOT_API_URL = "YOUR HUBSPOT API URL"


client = MongoClient("mongodb://localhost:27017/")
db = client["sales_agent"]
leads_collection = db["prospects"]



# Helper Function: HubSpot Integration
def push_prospect_to_hubspot(prospect_data, email_body):
    """
    Pushes a contact to HubSpot CRM using their Contacts API endpoint.
    """
    headers = {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Map local JSON fields to HubSpot's standard contact properties
    payload = {
        "properties": {
            "firstname": prospect_data.get("first_name", ""),
            "lastname": prospect_data.get("last_name", ""),
            "jobtitle": prospect_data.get("current_role", ""),
            "company": prospect_data.get("company_name", ""),
            "message": email_body,
            "email": f"{prospect_data.get('first_name', 'lead').lower()}@{prospect_data.get('company_name', 'domain').lower().replace(' ', '')}.com"
        }
    }
    
    response = requests.post(HUBSPOT_API_URL, headers=headers, json=payload)
    
    if response.status_code in [200, 201]:
        return True, response.json().get("id")
    else:
        return False, response.text


# Streamlit Dashboard Layout
st.set_page_config(page_title="FireLLama Outreach Dashboard", layout="centered")
st.title("FireLLama Outreach Dashboard")
st.markdown("Review, edit, and push locally generated FireLLama outreach straight to HubSpot.")

prospects = list(leads_collection.find({"status": "drafted"}))

if not prospects:
    st.write("**Status:** No drafted emails to review. Run your local scraper.")
else:
    st.subheader(f"{len(prospects)} Profiles Awaiting Sync")
    
    for prospect in prospects:
        first_name = prospect.get('first_name', 'Unknown')
        last_name = prospect.get('last_name', '')
        company = prospect.get('company_name', 'Unknown Company')
        doc_id = prospect['_id']
        
        with st.expander(f"{first_name} {last_name} @ {company}"):
            st.write(f"**Role:** {prospect.get('current_role', 'N/A')}")
            st.write(f"**Achievements:** {', '.join(prospect.get('recent_achievements', []))}")
            st.write(f"**Interests:** {', '.join(prospect.get('inferred_interests', []))}")
            
            # Editable Email Box
            edited_email = st.text_area(
                "Generated Email (Editable):", 
                prospect.get('generated_email', ''), 
                height=150, 
                key=f"text_{doc_id}"
            )
            
            col1, col2 = st.columns(2)
            
            # Approve & Push Button
            with col1:
                if st.button("Approve & Push to HubSpot", key=f"approve_{doc_id}"):
                    with st.spinner("Connecting to HubSpot API..."):
                        success, result = push_prospect_to_hubspot(prospect, edited_email)
                        
                        if success:
                            st.write(f"**Success:** Contact created in HubSpot! (ID: {result})")
                            # Mark as approved in MongoDB
                            leads_collection.update_one(
                                {"_id": doc_id}, 
                                {"$set": {"status": "approved", "generated_email": edited_email, "hubspot_id": result}}
                            )
                            st.rerun()
                        else:
                            st.write(f"**Error:** Failed to push to CRM: {result}")
                            
            # Reject Button
            with col2:
                if st.button("Reject", key=f"reject_{doc_id}"):
                    leads_collection.update_one(
                        {"_id": doc_id}, 
                        {"$set": {"status": "rejected"}}
                    )
                    st.rerun()