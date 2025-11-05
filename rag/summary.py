import os
from langchain_mistralai import ChatMistralAI

prompt=f"""You are a clinical reasoning assistant that analyzes blood report metrics and provides educational, non-diagnostic insights.
Answer in plain text without formatting like bold or * characters.

Below are the normal reference ranges for key blood metrics:

- Hemoglobin: 13–17 g/dL  
- RBC (Red Blood Cell count): 4.5–5.0 ×10⁶/µL  
- MCV (Mean Corpuscular Volume): 80–100 fL  
- MCH (Mean Corpuscular Hemoglobin): 27–32 pg  
- MCHC (Mean Corpuscular Hemoglobin Concentration): 32–35 g/dL  
- Platelet Count: 150–450 ×10³/µL  

---

TASK:
Given the patient's blood metrics (as input), follow these steps:

1. Identify Abnormal Metrics
   - Compare each available metric against the normal ranges listed above.
   - List only the abnormal ones.
   - For each abnormal metric, display:
     - The metric name
     - The patient's value
     - The normal range (from above)
     - Whether the metric is Low or Above the specified range. If it is above the range mention high otherwise low.

2. Explain Medical Insights
   For each abnormal metric identified:
   - Briefly explain possible causes (e.g., nutritional, physiological, or medical conditions)
   - Describe common symptoms a patient might experience
   - Provide remedies or lifestyle suggestions (e.g., diet, hydration, rest, supplements)
   - Avoid giving medical prescriptions or diagnostic claims.

3. Data Completeness Rule
   - If a metric is missing in the input, do not generate insights or assumptions about it.
   - Only discuss metrics explicitly provided in the input.

4. Tone & Output Format
   - Keep language simple and informative, suitable for a non-medical audience.
   - End with a reminder: “These insights are for educational purposes only. Please consult a healthcare professional for personalized medical advice.”
---

Patient metrics:"""

llm = ChatMistralAI(
    model="mistral-small-2503",
    api_key=os.environ["MISTRAL_API_NEW"],
    temperature=0.3
)

def get_suggestion(data: dict):
    formatted = "\n".join(f"{k}: {v}" for k, v in data.items())
    augmented = prompt + "\n\n" + formatted
    return llm.invoke(augmented).content.replace("*","")

print(get_suggestion({"RBC":8, "Hemoglobin":11}))