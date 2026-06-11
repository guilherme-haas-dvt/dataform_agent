from google import genai

client = genai.Client(
    vertexai=True,
    project="ghilherme-haas-sandbox",  # ← este exactamente
    location="global"
)

for model in client.models.list():
    print(model.name)