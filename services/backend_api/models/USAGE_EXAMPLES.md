
# AI Model Usage Examples
# =======================

## 1. Job Classification (Bayesian)

```python
from admin_portal.services.ai_model_loader import get_trained_models

models = get_trained_models()

cv_text = "Senior Python Developer with 5 years experience in Django and Flask"

# Vectorize
cv_vector = models['vectorizer'].transform([cv_text])

# Predict
category = models['bayesian'].predict(cv_vector)[0]
confidence = max(models['bayesian'].predict_proba(cv_vector)[0])

print(f"Category: {category}")
print(f"Confidence: {confidence:.1%}")
```

## 2. Semantic Similarity (Sentence-BERT)

```python
from admin_portal.services.ai_model_loader import get_model

embedder = get_model('embedder')

cv_text = "Python Developer"
job_text = "Software Engineer"

cv_embedding = embedder.encode(cv_text)
job_embedding = embedder.encode(job_text)

from sentence_transformers.util import cos_sim
similarity = cos_sim(cv_embedding, job_embedding)

print(f"Similarity: {similarity[0][0]:.1%}")
```

## 3. Entity Extraction (spaCy)

```python
from admin_portal.services.ai_model_loader import get_model

nlp = get_model('spacy')

text = "John Smith worked as Senior Developer at Google"
doc = nlp(text)

for ent in doc.ents:
    print(f"{ent.text}: {ent.label_}")
```

## 4. Salary Prediction (Random Forest)

```python
from admin_portal.services.ai_model_loader import get_model

salary_model = get_model('salary')

features = [
    5,      # years_experience
    15,     # skills_count
    3,      # education_level (Bachelor)
    2000    # text_length
]

predicted_salary = salary_model.predict([features])[0]
print(f"Predicted Salary: ${predicted_salary:,.0f}")
```

## 5. Complete Admin Page Integration

```python
# In admin_portal/pages/08_AI_Enrichment_Engine.py

import streamlit as st
from services.ai_model_loader import get_trained_models

st.title("AI Enrichment Engine")

models = get_trained_models()

uploaded_file = st.file_uploader("Upload CV")

if uploaded_file:
    cv_text = uploaded_file.read().decode('utf-8')

    # 1. Job Classification
    cv_vector = models['vectorizer'].transform([cv_text])
    category = models['bayesian'].predict(cv_vector)[0]
    confidence = max(models['bayesian'].predict_proba(cv_vector)[0])

    st.metric("Job Category", category)
    st.caption(f"Confidence: {confidence:.0%}")

    # 2. Entity Extraction
    doc = models['spacy'](cv_text)

    entities = {
        'PERSON': [],
        'ORG': [],
        'GPE': []
    }

    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text)

    st.subheader("Extracted Entities")
    st.write("People:", entities['PERSON'])
    st.write("Organizations:", entities['ORG'])
    st.write("Locations:", entities['GPE'])

    # 3. Semantic Embedding
    embedding = models['embedder'].encode(cv_text)

    st.metric("Embedding Dimension", len(embedding))
    st.caption(f"First 5 values: {embedding[:5]}")
```

## 6. Portal Bridge Integration

```python
# In shared_backend/services/portal_bridge.py

from admin_portal.services.ai_model_loader import get_trained_models

class IntelligenceService:
    def __init__(self):
        self.models = get_trained_models()

    def analyze_career(self, cv_data):
        cv_text = cv_data.get('text', '')

        # Real AI analysis!
        results = {
            'job_classification': self._classify_job(cv_text),
            'entities': self._extract_entities(cv_text),
            'embedding': self._get_embedding(cv_text).tolist()
        }

        return results

    def _classify_job(self, text):
        vector = self.models['vectorizer'].transform([text])
        category = self.models['bayesian'].predict(vector)[0]
        confidence = max(self.models['bayesian'].predict_proba(vector)[0])

        return {'category': category, 'confidence': float(confidence)}

    def _extract_entities(self, text):
        doc = self.models['spacy'](text)
        return [{'text': ent.text, 'label': ent.label_} for ent in doc.ents]

    def _get_embedding(self, text):
        return self.models['embedder'].encode(text)
```
