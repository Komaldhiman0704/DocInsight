#!/usr/bin/env python3
"""
Diagnose global search issues
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 60)
print("DIAGNOSING GLOBAL SEARCH")
print("=" * 60)

# Test 1: Check if documents are uploaded
print("\n📄 Checking Documents...")
try:
    from services.document_store import get_all_documents
    
    docs = get_all_documents()
    print(f"  • Total documents uploaded: {len(docs)}")
    
    if len(docs) == 0:
        print("  ⚠️  NO DOCUMENTS UPLOADED!")
        print("  → Upload a PDF first, then try searching again")
    else:
        for doc in docs:
            print(f"    - {doc['filename']} ({doc['chunk_count']} chunks)")
    
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 2: Check vector store contents
print("\n🔍 Checking Vector Store...")
try:
    from services.vector_store import get_vectorstore
    
    vs = get_vectorstore()
    # Try a simple similarity search to see if anything is indexed
    try:
        results = vs.similarity_search_with_score("test", k=1)
        print(f"  • Vector store indexed: {len(results)} results found for 'test'")
        
        if len(results) > 0:
            doc, score = results[0]
            print(f"    - Sample result score: {score:.3f}")
            print(f"    - Sample content: {doc.page_content[:80]}...")
        else:
            print("  ⚠️  VECTOR STORE IS EMPTY!")
            print("  → No chunks indexed. Make sure PDF was processed correctly")
    except ImportError as ie:
        print(f"  ⚠️  Dependency issue: {str(ie)[:60]}...")
        print("  → This is expected if sentence-transformers isn't fully compatible")
    
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 3: Test the actual search function
print("\n🔎 Testing Search Function...")
try:
    from services.vector_store import get_docs_with_scores
    from services.document_store import get_all_documents
    
    all_docs = get_all_documents()
    
    if len(all_docs) == 0:
        print("  ⚠️  No documents to search")
    else:
        # Try searching for a generic term
        results = get_docs_with_scores(query="document", doc_ids=None)
        print(f"  • Search results for 'document': {len(results)} found")
        
        if len(results) > 0:
            for i, (doc, score) in enumerate(results[:3]):
                print(f"    {i+1}. Score: {score:.3f}, Page: {doc.metadata.get('page', 1)}")
        else:
            print("  ⚠️  No results for generic search term")
            print("  → This suggests vector store indexing issue")
    
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Recommendations
print("\n" + "=" * 60)
print("RECOMMENDATIONS:")
print("=" * 60)
print("1. ✓ Upload a PDF file using the upload area")
print("2. ✓ Wait for the file to be processed (summary generation)")  
print("3. ✓ Try searching for common words from the document (PDF, page, etc)")
print("4. ✓ If still no results, try asking a question in chat first")
print("   (this tests if the vector store is working)")
print("\nNote: Search will only return results if:")
print("  • At least one document is uploaded")
print("  • The document was successfully indexed into the vector store")
print("  • Your search term appears in the document content")
