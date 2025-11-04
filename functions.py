from passlib.context import CryptContext
import boto3
import spacy
import os
from spacy.pipeline import EntityRuler

#SpaCy model
nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")
patterns = [
    {"label": "TEST_NAME", "pattern": [{"LOWER": "hemoglobin"}]},
    {"label": "TEST_NAME", "pattern": [{"LOWER": "hb"}]},
    {"label": "TEST_NAME", "pattern": [{"LOWER": "wbc"}]},
    {"label": "TEST_NAME", "pattern": [{"LOWER": "rbc"}]},
    {"label": "TEST_NAME", "pattern": [{"LOWER": "platelet"}]},
    {"label": "TEST_NAME", "pattern": [{"LOWER": "mcv"}]},
    {"label": "TEST_NAME", "pattern": [{"LOWER": "mch"}]},
    {"label": "TEST_NAME", "pattern": [{"LOWER": "mchc"}]},
    {"label": "VALUE", "pattern": [{"LIKE_NUM": True}]}
]
ruler.add_patterns(patterns)

textract = boto3.client(
    'textract',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name='ap-south-1'
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def process_document(file_bytes: bytes):
    response = textract.analyze_document(
        Document={'Bytes': file_bytes},
        FeatureTypes=['TABLES', 'FORMS']
    )

    details = " ".join(
        block.get("Text", "") for block in response.get("Blocks", []) if block.get("BlockType") == "LINE"
    )

    doc = nlp(details)

    structured_data = {}
    last_test = None
    for ent in doc.ents:
        if ent.label_ == "TEST_NAME":
            last_test = ent.text.strip()
        elif ent.label_ == "VALUE" and last_test:
            structured_data[last_test] = ent.text.strip()
            last_test = None

    return structured_data