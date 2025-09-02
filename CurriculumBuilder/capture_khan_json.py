import json
import os
from mitmproxy import http
from datetime import datetime

# --- Configuration ---
SAVE_DIRECTORY = "khan_academy_json"

# --- Global State ---
questions_to_capture = set()
saved_questions = set()
questions_captured_count = 0

class KhanAcademyPassiveCapture:
    def __init__(self):
        if not os.path.exists(SAVE_DIRECTORY):
            os.makedirs(SAVE_DIRECTORY)
        print("[INFO] Passive Capture addon loaded. Waiting for you to start an exercise...")

    def response(self, flow: http.HTTPFlow) -> None:
        # --- Part 1: Capture the manifest and list of question IDs ---
        if "api/internal/graphql/getOrCreatePracticeTask" in flow.request.pretty_url:
            self.handle_practice_task(flow)

        # --- Part 2: Capture individual question JSONs as they are requested by the browser ---
        if "api/internal/graphql/getAssessmentItem" in flow.request.pretty_url:
            self.handle_assessment_item(flow)

    def handle_practice_task(self, flow: http.HTTPFlow):
        """
        Parses the main task response to get the full list of question IDs to look for.
        """
        global questions_to_capture
        print("[INFO] Practice Task detected. Building list of questions to capture...")
        data = json.loads(flow.response.content)
        
        try:
            reserved_items = data['data']['getOrCreatePracticeTask']['result']['userTask']['task']['reservedItems']
            for item in reserved_items:
                # The ID is the part after the '|'
                item_id = item.split('|')[1]
                questions_to_capture.add(item_id)
            
            print(f"[INFO] Built list of {len(questions_to_capture)} questions. As you answer them, they will be saved.")

        except (KeyError, TypeError) as e:
            print(f"[ERROR] Could not find question IDs in the manifest. Structure may have changed. Error: {e}")

    def handle_assessment_item(self, flow: http.HTTPFlow):
        """
        Saves the JSON data from a getAssessmentItem response if it's on our list.
        """
        global saved_questions, questions_captured_count
        data = json.loads(flow.response.content)
        
        try:
            item = data['data']['assessmentItem']['item']
            item_id = item['id']
            
            # Only save if it's a question we're looking for and we haven't already saved it.
            if item_id in questions_to_capture and item_id not in saved_questions:
                saved_questions.add(item_id)
                
                filename = os.path.join(SAVE_DIRECTORY, f"{item_id}.json")
                perseus_json_str = item['itemData']
                perseus_data = json.loads(perseus_json_str)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(perseus_data, f, ensure_ascii=False, indent=4)
                
                questions_captured_count += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"  -> Captured! Total: {questions_captured_count} ({timestamp})", flush=True)

        except (json.JSONDecodeError, KeyError, TypeError):
            pass

addons = [KhanAcademyPassiveCapture()]
