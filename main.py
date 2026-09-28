import json
import ollama
from pydantic import BaseModel
from typing import List, Optional
from playwright.sync_api import sync_playwright
import csv
import time
import random 
from pymongo import MongoClient

# 1. Define the Fault-Tolerant Schema
class ProspectProfile(BaseModel):
    first_name: Optional[str] = "Unknown"
    last_name: Optional[str] = ""
    current_role: Optional[str] = "Unknown Role"
    company_name: Optional[str] = "Unknown Company"
    recent_achievements: Optional[List[str]] = []
    inferred_interests: Optional[List[str]] = []

# 2. Define the Scraper
def scrape_profile(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Ensure auth.json is in the same directory as this script
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()
        
        page.goto(url)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000) 
        
        raw_text = page.inner_text("body")
        browser.close()
        return raw_text

# 3. Define the Parser (Fault-Tolerant Version)
def extract_json_profile(raw_text):
    cleaned_text = "\n".join([line for line in raw_text.split('\n') if line.strip()])
    truncated_text = cleaned_text[:6000] 
    
    prompt = f"""
    You are a precise data extraction agent. Extract the prospect's profile from the following raw website text.
    Respond ONLY with a valid JSON object. Do not include any text outside the JSON.
    
    CRITICAL RULES:
    1. If you cannot find the actual first name, last name, or company in the text, omit the JSON key entirely.
    2. DO NOT output the strings "None", "N/A", or "Unknown".
    
    Target structure (omit missing keys):
    {{
      "first_name": "John",
      "last_name": "Doe",
      "current_role": "VP of Engineering",
      "company_name": "Tech Corp",
      "recent_achievements": ["Scaled infrastructure by 40%"],
      "inferred_interests": ["Cloud Computing", "Machine Learning"]
    }}
    
    Raw Text:
    {truncated_text} 
    """

    print("Analyzing profile with local LLM...")
    response = ollama.chat(
        model='llama3',
        messages=[{'role': 'user', 'content': prompt}],
        format='json'
    )
    
    # Load the raw JSON from Llama 3
    raw_dict = json.loads(response['message']['content'])
    
    # Scrub literal "None" or "Unknown" strings
    clean_dict = {k: v for k, v in raw_dict.items() if str(v).lower() not in ["none", "unknown", "n/a", "null"]}
    
    # Pass through Pydantic to enforce schema
    validated_profile = ProspectProfile(**clean_dict)
    
    return validated_profile.model_dump()

# 4. Define the Email Drafter (FireLLama Persona)
def draft_personalized_email(profile_data):
    print("Drafting personalized FireLLama outreach...")
    
    achievements_list = profile_data.get('recent_achievements', [])
    if isinstance(achievements_list, list):
        achievements_str = ', '.join(achievements_list)
    else:
        achievements_str = str(achievements_list)
    
    prompt = f"""
    You are an elite technical sales consultant at FireLLama Technology, a custom software and AI development company. 
    Write a concise, 3-sentence cold email to this prospect.
    
    Prospect Data:
    Name: {profile_data.get('first_name')}
    Company: {profile_data.get('company_name')}
    Role: {profile_data.get('current_role')}
    Achievements: {achievements_str}
    
    Rules:
    1. Keep it strictly under 3 sentences.
    2. Specifically mention one of their recent achievements to prove you researched them.
    3. Propose a brief chat about how FireLLama can help them build scalable custom software, integrate AI automation, or accelerate their digital transformation.
    4. Do not use generic greetings like "I hope this email finds you well."
    5. Maintain a professional, consultative, and value-driven tone.
    """

    response = ollama.chat(
        model='llama3',
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    return response['message']['content'].strip()

# 5. Execute the Pipeline
if __name__ == "__main__":
    print("Starting bulk processing pipeline...")
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client["sales_agent"]
    leads_collection = db["prospects"]
    
    # Setup variables for rate limiting
    processed_count = 0
    BATCH_LIMIT = 40  
    
    with open('leads.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        
        for row in csv_reader:
            if processed_count >= BATCH_LIMIT:
                print(f"\n Safe Batch Limit Reached: Successfully processed {BATCH_LIMIT} profiles today. Run again tomorrow!")
                break

            target_url = row['url'].strip()
            if not target_url:
                continue
                
            # Duplicate Check: Skip if we already scraped this person
            if leads_collection.find_one({"source_url": target_url}):
                print(f" Skipping {target_url} - Already in database.")
                continue
                
            print(f"\n--- Processing: {target_url} ---")
            
            try:
                raw_text = scrape_profile(target_url) 
                clean_json = extract_json_profile(raw_text)
                email_draft = draft_personalized_email(clean_json)
                
                clean_json['generated_email'] = email_draft
                clean_json['source_url'] = target_url
                clean_json['status'] = 'drafted' 
                
                leads_collection.insert_one(clean_json)
                print(" Data extracted, email drafted, and saved to MongoDB!")
                
                processed_count += 1
                
                # Human Mimicry (Only sleep if we aren't about to exit the loop)
                if processed_count < BATCH_LIMIT:
                    delay = random.uniform(12.7, 27.3)
                    print(f" Sleeping for {round(delay, 1)} seconds to mimic human behavior...")
                    time.sleep(delay)
                
            except Exception as e:
                print(f" Failed to process {target_url}: {e}")

    print(f"\nPipeline complete! Successfully drafted {processed_count} new leads.")