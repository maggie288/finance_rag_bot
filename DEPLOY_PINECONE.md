# Pinecone Vector Database Setup for Finance RAG Bot

## What is Pinecone?

Pinecone is a managed vector database used for:
- Storing document embeddings for RAG (Retrieval-Augmented Generation)
- Fast similarity search
- Scalable vector storage

## Setup Steps

### 1. Create Pinecone Account

1. Go to https://app.pinecone.io/
2. Sign up for free
3. Verify account email and login

### 2. Create Index

```bash
# Using Pinecone CLI (optional)
pip install pinecone-cli
pinecone login

# Or create via Dashboard
# 1. Click "Create Index"
# 2. Configure:
#    - Name: finance-rag-bot (or your preferred name)
#    - Dimensions: 384 (for all-MiniLM-L6-v2)
#    - Metric: cosine
#    - Pod type: serverless-starter (free tier)
```

### 3. Get API Key

1. Go to https://app.pinecone.io/keys
2. Click "Create API Key"
3. Copy and save your API key securely

### 4. Configure Backend

Add to Railway backend environment variables:

```env
PINECONE_API_KEY=pcsk_xxxxx_xxxxx
PINECONE_INDEX_NAME=finance-rag-bot
```

### 5. Initialize Vector Store (Optional)

If you need to set up the index programmatically:

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="your-api-key")

# Create index (if not exists)
if "finance-rag-bot" not in pc.list_indexes():
    pc.create_index(
        name="finance-rag-bot",
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Get index
index = pc.Index("finance-rag-bot")
```

## Free Tier Limits

| Resource | Limit |
|----------|-------|
| Vectors stored | 100,000 |
| Dimensions | Up to 1024 |
| Pods | 1 (serverless-starter) |
| Requests/month | 1M |

## Index Management

### Delete Index (if needed)
```python
pc.delete_index("finance-rag-bot")
```

### Check Index Stats
```python
index = pc.Index("finance-rag-bot")
print(index.describe_index_stats())
```

## Troubleshooting

### API Key Error
```
AuthenticationError: Invalid API key
```
- Verify API key in Pinecone Dashboard
- Check for extra spaces or characters

### Index Not Found
```
NotFoundError: Index not found
```
- Verify index name matches exactly
- Check region configuration

### Dimension Mismatch
```
ValueError: Dimension of ... does not match index dimension
```
- Ensure using `all-MiniLM-L6-v2` (384 dimensions)
- Or recreate index with correct dimensions

## Cost Optimization

### Serverless (Recommended for Free Tier)
- Pay per request
- No idle costs
- Auto-scales

### Pod-based (Not Recommended)
- Dedicated resources
- Higher cost
- Better for production with high traffic

## Alternative: Use Local Embeddings Only

If you don't need persistent vector storage, the system works with:
- Sentence-transformers (local embeddings, no Pinecone needed)
- In-memory caching for current session

Set in environment:
```env
# Disable Pinecone if not using
USE_PINECONE=false
```

## Integration with RAG Pipeline

The backend already has Pinecone integration. When configured:
1. Documents are uploaded and embedded
2. Embeddings stored in Pinecone
3. Queries search Pinecone for relevant context
4. Results passed to LLM for response

See: `backend/app/services/rag/pipeline.py`
