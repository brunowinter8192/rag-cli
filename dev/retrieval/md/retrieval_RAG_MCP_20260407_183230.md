# Retrieval Sandbox: RAG_MCP

**Timestamp:** 20260407_183230  
**Top-k:** 10  
**Modes:** dense

---

## Query 1: "What is the default ef_search value for HNSW indexes in pgvector?"


### dense

#### Rank 1 | Score: 0.8111 | Chunk: 8 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

as 2 limiters: maximum number of records returned and limitation on accuracy. If you are trying to return 100 nearest neighbors and the _ef_search_ value is set to 40 (which is the default), then the query will only be capable of returning 40 rows. _ef_search_ also limits accuracy, as nested graphs will not be traversed beyond the count. Thus, relying on few data points for comparison.

A smaller _ef_search_ value will result in faster queries at the risk of inaccuracy. You can set it for a session as below, or use `SET LOCAL` to constrain to a transaction.

```sql
SET hnsw.ef_search = 5;
```

## Using HNSW - A code sample

For this code sample, we will continue to use the SQL code found within the [Postgres AI Tutorial](https://github.com/CrunchyData/Postgres-AI-Tutorial). Pull down that file, and load it into a Postgres database with the pgvector extension. If you do not have a database with the pgvector extension, try [Crunchy Bridge for your Postgres hosting](https://crunchybridge.com/login) and install the extension there. To load the file, run:

```bash
bash> cat recipe-tracker.sql | psql 'postgres://user@password:host:port/database'
```

This schema is a set of recipes from the Armed Services Recipe list. We have categorized these recipes using OpenAI as defined in [Postgres + AI blog post in this series](https://www.crunchydata.com/blog/whats-postgres-got-to-do-with-ai). Then, connect to your Postgres database and run this query:

```sql
SELECT
   name


#### Rank 2 | Score: 0.7499 | Chunk: 1 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

TL;DR

HNSW is cutting edge for all vector based indexing. To build an HNSW index, run something like the following:

```sql
CREATE INDEX ON recipes
USING hnsw (embedding vector_l2_ops)
WITH (m = 4, ef_construction = 10);
```

These indexes will:
  * use approximations (not precision)
  * be more performant than list-based indexes
  * require longer index build times
  * and require more memory

Tradeoffs:
  * Indexes will take longer to build depending on values for _m_ and _ef_construction_. When increased, these values will slow the speed of index build drastically, while not improving performance. Yet, it may increase accuracy of response.
  * To search more than 40 nearest neighbors, increase this `SET hnsw.ef_search = x;` value. Where `x` is the value of nearest neighbors you want to return.
  * Not all queries will work with HNSW. As we said in the [vector performance blog post](https://www.crunchydata.com/blog/pgvector-performance-for-developers), use `EXPLAIN` to ensure your query is using the index. If it is not using the index, simplify your query until it is, then build back to your complexity.

## What is HNSW?

HNSW is short for Hierarchical Navigable Small World. But, HNSW isn't just one algorithm — it's kind of like 3 algorithms in a trench coat. The first algorithm was [first presented in a paper in 2011](https://www.iiis.org/CDs2011/CD2011IDI/ICTA_2011/PapersPdf/CT175ON.pdf). It used graph topology to find the vertex (or element) with the local minimum nearest neighbor. Then, a couple more papers were published, but the [one in 2014

#### Rank 3 | Score: 0.7236 | Chunk: 0 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

<!-- source: https://www.crunchydata.com/blog/hnsw-indexes-with-postgres-and-pgvector -->

# HNSW Indexes with Postgres and pgvector

Christopher Winslett
Sep 1, 2023 · 12 min read

Postgres' [pgvector extension](https://github.com/pgvector/pgvector) recently added HNSW as a new index type for vector data. This levels up the database for vector-based embeddings output by AI models. A few months ago, we had written about approximate nearest neighbor [pgvector performance using the available list-based indexes](https://www.crunchydata.com/blog/pgvector-performance-for-developers). Now, with the addition of HNSW, pgvector can use the latest graph based algorithms to approximate nearest neighbor queries. As with all things databases, there are trade-offs, so don't throw away the list-based methodologies — and don't throw away the techniques we discussed in [scaling vector data](https://www.crunchydata.com/blog/scaling-vector-data-with-postgres).



#### Rank 4 | Score: 0.7117 | Chunk: 16 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

time — but as always, much of ANN is a case of balancing these three factors.
If, instead, we’d like to improve our search speeds — we can do that too! All we do is add an IVF component to our index. There is plenty to discuss when adding IVF or PQ to our index, so we wrote an [entire article on mixing-and-matching of indexes](https://www.pinecone.io/learn/series/faiss/composite-indexes/).
That’s it for this article covering the Hierarchical Navigable Small World graph for vector similarity search! Now that you’ve learned the intuition behind HNSW and how to implement it in Faiss, you’re ready to go ahead and test HNSW indexes in your own vector search applications, or use a managed solution like [Pinecone](https://www.pinecone.io/) or OpenSearch that has vector search ready-to-go!
If you’d like to continue learning more about vector search and how you can use it to supercharge your own applications, we have a [whole set of learning materials](https://www.pinecone.io/learn/) aiming to bring you up to speed with the world of vector search.
## References
[1] E. Bernhardsson, [ANN Benchmarks](https://github.com/erikbern/ann-benchmarks) (2021), GitHub
[2] W. Pugh, [Skip lists: a probabilistic alternative to balanced trees](https://15721.courses.cs.cmu.edu/spring2018/papers/08-oltpindexes1/pugh-skiplists-cacm1990.pdf) (1990), Communications of the ACM, vol. 33, no.6, pp. 668-676
[3] Y. Malkov, D. Yashunin, [Efficient and robust approximate nearest neighbor search 

#### Rank 5 | Score: 0.71 | Chunk: 15 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

and search time when searching for only one query. When using lower M values, the search time remains almost unchanged for different efConstruction values.
That all looks great, but what about the memory usage of the HNSW index? Here things can get slightly _less_ appealing.
![Memory usage with increasing values of M using our Sift1M dataset. efSearch and efConstruction have no effect on the memory usage.](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2Fe04d23ccd76d8bdc568542bebe75a75e7d36a21e-1480x1050.png&w=3840&q=75)
Memory usage with increasing values of M using our Sift1M dataset. efSearch and efConstruction have no effect on the memory usage.
Both `efConstruction` and `efSearch` do not affect index memory usage, leaving us only with `M`. Even with `M` at a low value of `2`, our index size is already above 0.5GB, reaching almost 5GB with an `M` of `512`.
So although HNSW produces incredible performance, we need to weigh that against high memory usage and the inevitable high infrastructure costs that this can produce.
#### Improving Memory Usage and Search Speeds
HNSW is not the best index in terms of memory utilization. However, if this is important and using [another index](https://www.pinecone.io/learn/series/faiss/vector-indexes/) isn’t an option, we can improve it by compressing our vectors using [product quantization (PQ)](https://www.pinecone.io/learn/series/faiss/product-quantization/). Using PQ will reduce recall and increase

#### Rank 6 | Score: 0.7095 | Chunk: 4 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

HNSW thesis, you can go back and read the [`HnswSearchLayer` function](https://github.com/pgvector/pgvector/blob/a8e257e1f1aaf4c8c9019dcf4ac41bea98a41fff/src/hnswutils.c#L546) for fun. Additionally, see how the [HNSW implementation calculates and caches distances](https://github.com/pgvector/pgvector/blob/a8e257e1f1aaf4c8c9019dcf4ac41bea98a41fff/src/hnswutils.c#L674)

## The advantages of HNSW

HNSW is much faster to query than the traditional list-based query algorithm. This performance is because the use of graphs and layers reduces the number of distance comparisons that are being run. And because fewer distance comparisons, we can run more queries concurrently as well.

## Tradeoffs for HNSW

The most obvious trade off for HNSW indexes is that they are approximations. But, this is no different than any existing vector index, so aside from a table-scan of comparisons. If you need absolutes, it is best to run the non-indexed query that calculates distance for each row.

The second trade-off for HNSW indexes is they can be expensive to build. The two largest contributing variables for these indexes are: size of the dataset and complexity of the index. For moderate datasets of > 1M rows, it can take 6 minutes to build some of the simplest of indexes. During that time, the database will use all the R

#### Rank 7 | Score: 0.7081 | Chunk: 12 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

we compare the distribution between our Python implementation and that of Faiss, we see very similar results:
In[12]:
```
chosen_levels = []
rng = np.random.default_rng(12345)
for _ in range(1_000_000):
    chosen_levels.append(random_level(assign_probas, rng))
```

In[13]:
```
np.bincount(chosen_levels)
```

Out[13]:
```
array([968821,  30170,    985,     23,       1],
      dtype=int64)
```

![Distribution of vertices across layers in both the Faiss implementation \(left\) and the Python implementation \(right\).](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2F75658a08c25dabc1405f769c76fd2929c051853b-1920x930.png&w=3840&q=75)
Distribution of vertices across layers in both the Faiss implementation (left) and the Python implementation (right).
The Faiss implementation also ensures that we _always_ have at least one vertex in the highest layer to act as the entry point to our graph.
### HNSW Performance
Now that we’ve explored all there is to explore on the theory behind HNSW and how this is implemented in Faiss — let’s look at the effect of different parameters on our recall, search and build times, and the memory usage of each.
We will be modifying three parameters: `M`, `efSearch`, and `efConstruction`. And we will be indexing the Sift1M dataset, which you can download and prepare using [this script](https://gist.github.com/jamescalam/a09a16c17b677f2cf9c019114711f3bf).
As we did before, we initialize our index like so:
```
index = faiss.IndexHNSWFlat(d, M)
```

The two other parameters, `

#### Rank 8 | Score: 0.6964 | Chunk: 14 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

parameters when searching for 1000 queries. Note that the y-axis is using a log scale.
Although higher parameter values provide us with better recall, the effect on search times can be dramatic. Here we search for `1000` similar vectors (`xq[:1000]`), and our recall/search-time can vary from 80%-1ms to 100%-50ms. If we’re happy with a rather terrible recall, search times can even reach 0.1ms.
If you’ve been following our [articles on vector similarity search](https://www.pinecone.io/learn/), you may recall that `efConstruction` has a [negligible effect on search-time](https://www.pinecone.io/learn/series/faiss/vector-indexes/) — but that is not the case here…
When we search using a few queries, it _is_ true that `efConstruction` has little effect on search time. But with the `1000` queries used here, the small effect of `efConstruction` becomes much more significant.
If you believe your queries will mostly be low volume, `efConstruction` is a great parameter to increase. It can improve recall with little effect on _search time_ , particularly when using lower `M` values.
![efConstruction and search time when searching for only one query. When using lower M values, the search time remains almost unchanged for different efConstruction values.](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.san

#### Rank 9 | Score: 0.6904 | Chunk: 0 | Document: www_crunchydata_com__blog__pgvector-performance-for-developers.md

<!-- source: https://www.crunchydata.com/blog/pgvector-performance-for-developers -->

# Performance Tips Using Postgres and pgvector

Christopher Winslett
May 5, 2023 · 7 min read

**Note: pgvector 0.5 released HNSW indexes which improved performance significantly. Read more about it [HNSW Indexes with Postgres and pgvector](https://www.crunchydata.com/blog/hnsw-indexes-with-postgres-and-pgvector). We have additional articles in this [Postgres AI series](https://www.crunchydata.com/blog/topic/ai).**

As we've been helping people get started with AI in Postgres with `pgvector`, there have been few questions around performance. At a basic level, pgvector performance relies on 3 things:

  1. Are your queries using indexes?
  2. Are you setting your `list` size appropriately for your data set?
  3. Do you have enough memory for your indexes + ability to change settings?

For an intro to using pgvector, see [What's Postgres Got To Do With AI](https://www.crunchydata.com/blog/whats-postgres-got-to-do-with-ai). In it, we discuss the vector datatype, querying, and indexing options. During this blog post, we will refer to a "recipes". In the prior blog post, we built an AI powered recipe recommendation engine.

## Do you want an index?

Probably you do. It is important to note that vector indexes allow "approximate nearest neighbor" (ANN) searching. So if you have a hard requirement that a query return absolutely 100% of all nearby vectors, you are going to be stuck with full scans, which will be slow on large data sets.

However, most vector use cas

#### Rank 10 | Score: 0.6826 | Chunk: 11 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

LIMIT 5;
```

Long-story short, the simpler the better for HNSW usage.

## HNSW indexes and scaling

HNSW indexes are much more performant than the older list-based indexes. They also use more resources. Concurrency is improved, but many of the processes we laid out in the [Scaling PGVector blog post](https://www.crunchydata.com/blog/scaling-vector-data-with-postgres) are still applicable.

  1. Physical separation of data: because of the build requirements of the indexes, continue to host your vec


## Query 2: "By how much does Contextual Retrieval combined with reranking reduce the top-20-chunk retrieval failure rate?"


### dense

#### Rank 1 | Score: 0.8019 | Chunk: 10 | Document: www_anthropic_com__engineering__contextual-retrieval.md

chunks (we used the top 20);
  4. Pass the top-K chunks into the model as context to generate the final result.

![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F8f82c6175a64442ceff4334b54fac2ab3436a1d1-3840x2160.png&w=3840&q=75)_Combine Contextual Retrieva and Reranking to maximize retrieval accuracy._
### Performance improvements
There are several reranking models on the market. We ran our tests with the [Cohere reranker](https://cohere.com/rerank). Voyage[ also offers a reranker](https://docs.voyageai.com/docs/reranker), though we did not have time to test it. Our experiments showed that, across various domains, adding a reranking step further optimizes retrieval.
Specifically, we found that Reranked Contextual Embedding and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 67% (5.7% → 1.9%).
![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F93a70cfbb7cca35bb8d86ea0a23bdeeb699e8e58-3840x2160.png&w=3840&q=75)_Reranked Contextual Embedding and Contextual BM25 reduces the top-20-chunk retrieval failure rate by 67%._
#### Cost and latency considerations
One important consideration with reranking is the impact on latency and cost, especially when reranking a large number of chunks. Beca

#### Rank 2 | Score: 0.8019 | Chunk: 10 | Document: www_anthropic_com__news__contextual-retrieval.md

chunks (we used the top 20);
  4. Pass the top-K chunks into the model as context to generate the final result.

![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F8f82c6175a64442ceff4334b54fac2ab3436a1d1-3840x2160.png&w=3840&q=75)_Combine Contextual Retrieva and Reranking to maximize retrieval accuracy._
### Performance improvements
There are several reranking models on the market. We ran our tests with the [Cohere reranker](https://cohere.com/rerank). Voyage[ also offers a reranker](https://docs.voyageai.com/docs/reranker), though we did not have time to test it. Our experiments showed that, across various domains, adding a reranking step further optimizes retrieval.
Specifically, we found that Reranked Contextual Embedding and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 67% (5.7% → 1.9%).
![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F93a70cfbb7cca35bb8d86ea0a23bdeeb699e8e58-3840x2160.png&w=3840&q=75)_Reranked Contextual Embedding and Contextual BM25 reduces the top-20-chunk retrieval failure rate by 67%._
#### Cost and latency considerations
One important consideration with reranking is the impact on latency and cost, especially when reranking a large number of chunks. Beca

#### Rank 3 | Score: 0.8006 | Chunk: 8 | Document: www_anthropic_com__engineering__contextual-retrieval.md

in the appendix - contextualizing improves performance in every embedding-source combination we evaluated.
#### Performance improvements
Our experiments showed that:
  * **Contextual Embeddings reduced the top-20-chunk retrieval failure rate by 35%** (5.7% → 3.7%).
  * **Combining Contextual Embeddings and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 49%** (5.7% → 2.9%).

![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F7f8d739e491fe6b3ba0e6a9c74e4083d760b88c9-3840x2160.png&w=3840&q=75)_Combining Contextual Embedding and Contextual BM25 reduce the top-20-chunk retrieval failure rate by 49%._
#### Implementation considerations
When implementing Contextual Retrieval, there are a few considerations to keep in mind:
  1. **Chunk boundaries:** Consider how you split your documents into chunks. The choice of chunk size, chunk boundary, and chunk overlap can affect retrieval performance1.
  2. **Embedding model:** Whereas Contextual Retrieval improves performance across all embedding models we tested, some models may benefit more than others. We found [Gemini](https://ai.google.dev/gemini-api/docs/embeddings) and [Voyage](https://www.voyageai.com/) embeddings to be particularly effective.
  3. **Custom contextualizer prompts:** While the generic prompt we provided works well, you may be able to achieve even better results with prompts tailored to your specific domain or use case (for example, including a glossary of key terms that might only be defined in other documents in the knowledge base).


#### Rank 4 | Score: 0.8006 | Chunk: 8 | Document: www_anthropic_com__news__contextual-retrieval.md

in the appendix - contextualizing improves performance in every embedding-source combination we evaluated.
#### Performance improvements
Our experiments showed that:
  * **Contextual Embeddings reduced the top-20-chunk retrieval failure rate by 35%** (5.7% → 3.7%).
  * **Combining Contextual Embeddings and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 49%** (5.7% → 2.9%).

![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F7f8d739e491fe6b3ba0e6a9c74e4083d760b88c9-3840x2160.png&w=3840&q=75)_Combining Contextual Embedding and Contextual BM25 reduce the top-20-chunk retrieval failure rate by 49%._
#### Implementation considerations
When implementing Contextual Retrieval, there are a few considerations to keep in mind:
  1. **Chunk boundaries:** Consider how you split your documents into chunks. The choice of chunk size, chunk boundary, and chunk overlap can affect retrieval performance1.
  2. **Embedding model:** Whereas Contextual Retrieval improves performance across all embedding models we tested, some models may benefit more than others. We found [Gemini](https://ai.google.dev/gemini-api/docs/embeddings) and [Voyage](https://www.voyageai.com/) embeddings to be particularly effective.
  3. **Custom contextualizer prompts:** While the generic prompt we provided works well, you may be able to achieve even better results with prompts tailored to your specific domain or use case (for example, including a glossary of key terms that might only be defined in other documents in the knowledge base).


#### Rank 5 | Score: 0.7475 | Chunk: 11 | Document: www_anthropic_com__news__contextual-retrieval.md

reranking adds an extra step at runtime, it inevitably adds a small amount of latency, even though the reranker scores all the chunks in parallel. There is an inherent trade-off between reranking more chunks for better performance vs. reranking fewer for lower latency and cost. We recommend experimenting with different settings on your specific use case to find the right balance.
## Conclusion
We ran a large number of tests, comparing different combinations of all the techniques described above (embedding model, use of BM25, use of contextual retrieval, use of a reranker, and total # of top-K results retrieved), all across a variety of different dataset types. Here’s a summary of what we found:
  1. Embeddings+BM25 is better than embeddings on their own;
  2. Voyage and Gemini have the best embeddings of the ones we tested;
  3. Passing the top-20 chunks to the model is more effective than just the top-10 or top-5;
  4. Adding context to chunks improves retrieval accuracy a lot;
  5. Reranking is better than no reranking;
  6. **All these benefits stack** : to maximize performance improvements, we can combine contextual embeddings (from Voyage or Gemini) with contextual BM25, plus a reranking step, and adding the 20 chunks to the prompt.

We encourage all developers working with knowledge bases to use [our cookbook](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide) to experiment with these approaches to unlock new levels of performance.
## Appendix

#### Rank 6 | Score: 0.7475 | Chunk: 11 | Document: www_anthropic_com__engineering__contextual-retrieval.md

reranking adds an extra step at runtime, it inevitably adds a small amount of latency, even though the reranker scores all the chunks in parallel. There is an inherent trade-off between reranking more chunks for better performance vs. reranking fewer for lower latency and cost. We recommend experimenting with different settings on your specific use case to find the right balance.
## Conclusion
We ran a large number of tests, comparing different combinations of all the techniques described above (embedding model, use of BM25, use of contextual retrieval, use of a reranker, and total # of top-K results retrieved), all across a variety of different dataset types. Here’s a summary of what we found:
  1. Embeddings+BM25 is better than embeddings on their own;
  2. Voyage and Gemini have the best embeddings of the ones we tested;
  3. Passing the top-20 chunks to the model is more effective than just the top-10 or top-5;
  4. Adding context to chunks improves retrieval accuracy a lot;
  5. Reranking is better than no reranking;
  6. **All these benefits stack** : to maximize performance improvements, we can combine contextual embeddings (from Voyage or Gemini) with contextual BM25, plus a reranking step, and adding the 20 chunks to the prompt.

We encourage all developers working with knowledge bases to use [our cookbook](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide) to experiment with these approaches to unlock new levels of performance.
## Appendix

#### Rank 7 | Score: 0.7462 | Chunk: 7 | Document: www_anthropic_com__news__contextual-retrieval.md

to the chunk before embedding it and before creating the BM25 index.
Here’s what the preprocessing flow looks like in practice:
![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F2496e7c6fedd7ffaa043895c23a4089638b0c21b-3840x2160.png&w=3840&q=75)_Contextual Retrieval is a preprocessing technique that improves retrieval accuracy._  

If you’re interested in using Contextual Retrieval, you can get started with [our cookbook](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide).
### Using Prompt Caching to reduce the costs of Contextual Retrieval
Contextual Retrieval is uniquely possible at low cost with Claude, thanks to the special prompt caching feature we mentioned above. With prompt caching, you don’t need to pass in the reference document for every chunk. You simply load the document into the cache once and then reference the previously cached content. Assuming 800 token chunks, 8k token documents, 50 token context instructions, and 100 tokens of context per chunk, **the one-time cost to generate contextualized chunks is $1.02 per million document tokens**.
#### Methodology
We experimented across various knowledge domains (codebases, fiction, ArXiv papers, Science Papers), embedding models, retrieval strategies, and evaluation metrics. We’ve included a few examples of the questions and answers we used for each domain in [Appendix II](https://assets.anthropic.com/m/1632cded0a125333/original/Contextual-Retrieval-Appendix-2.pdf).
The graphs below show the average performance across all knowledge domains with the top-performing embedding configuration (Gemini Text 004) and retrieving the top-20-chunks. We use 1 minus recall@20 as our evaluation metric, which measures the percentage of relevant documents that fail to be retrieved within the top 20 chunks. You can see the full res

#### Rank 8 | Score: 0.7462 | Chunk: 7 | Document: www_anthropic_com__engineering__contextual-retrieval.md

to the chunk before embedding it and before creating the BM25 index.
Here’s what the preprocessing flow looks like in practice:
![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F2496e7c6fedd7ffaa043895c23a4089638b0c21b-3840x2160.png&w=3840&q=75)_Contextual Retrieval is a preprocessing technique that improves retrieval accuracy._  

If you’re interested in using Contextual Retrieval, you can get started with [our cookbook](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide).
### Using Prompt Caching to reduce the costs of Contextual Retrieval
Contextual Retrieval is uniquely possible at low cost with Claude, thanks to the special prompt caching feature we mentioned above. With prompt caching, you don’t need to pass in the reference document for every chunk. You simply load the document into the cache once and then reference the previously cached content. Assuming 800 token chunks, 8k token documents, 50 token context instructions, and 100 tokens of context per chunk, **the one-time cost to generate contextualized chunks is $1.02 per million document tokens**.
#### Methodology
We experimented across various knowledge domains (codebases, fiction, ArXiv papers, Science Papers), embedding models, retrieval strategies, and evaluation metrics. We’ve included a few examples of the questions and answers we used for each domain in [Appendix II](https://assets.anthropic.com/m/1632cded0a125333/original/Contextual-Retrieval-Appendix-2.pdf).
The graphs below show the average performance across all knowledge domains with the top-performing embedding configuration (Gemini Text 004) and retrieving the top-20-chunks. We use 1 minus recall@20 as our evaluation metric, which measures the percentage of relevant documents that fail to be retrieved within the top 20 chunks. You can see the full res

#### Rank 9 | Score: 0.718 | Chunk: 9 | Document: www_anthropic_com__engineering__contextual-retrieval.md

**Number of chunks:** Adding more chunks into the context window increases the chances that you include the relevant information. However, more information can be distracting for models so there's a limit to this. We tried delivering 5, 10, and 20 chunks, and found using 20 to be the most performant of these options (see appendix for comparisons) but it’s worth experimenting on your use case.

**Always run evals:** Response generation may be improved by passing it the contextualized chunk and distinguishing between what is context and what is the chunk.
## Further boosting performance with Reranking
In a final step, we can combine Contextual Retrieval with another technique to give even more performance improvements. In traditional RAG, the AI system searches its knowledge base to find the potentially relevant information chunks. With large knowledge bases, this initial retrieval often returns a lot of chunks—sometimes hundreds—of varying relevance and importance.
Reranking is a commonly used filtering technique to ensure that only the most relevant chunks are passed to the model. Reranking provides better responses and reduces cost and latency because the model is processing less information. The key steps are:
  1. Perform initial retrieval to get the top potentially relevant chunks (we used the top 150);
  2. Pass the top-N chunks, along with the user's query, through the reranking model;
  3. Using a reranking model, give each chunk a score based on its relevance and importance to the prompt, then select the top-

#### Rank 10 | Score: 0.718 | Chunk: 9 | Document: www_anthropic_com__news__contextual-retrieval.md

**Number of chunks:** Adding more chunks into the context window increases the chances that you include the relevant information. However, more information can be distracting for models so there's a limit to this. We tried delivering 5, 10, and 20 chunks, and found using 20 to be the most performant of these options (see appendix for comparisons) but it’s worth experimenting on your use case.

**Always run evals:** Response generation may be improved by passing it the contextualized chunk and distinguishing between what is context and what is the chunk.
## Further boosting performance with Reranking
In a final step, we can combine Contextual Retrieval with another technique to give even more performance improvements. In traditional RAG, the AI system searches its knowledge base to find the potentially relevant information chunks. With large knowledge bases, this initial retrieval often returns a lot of chunks—sometimes hundreds—of varying relevance and importance.
Reranking is a commonly used filtering technique to ensure that only the most relevant chunks are passed to the model. Reranking provides better responses and reduces cost and latency because the model is processing less information. The key steps are:
  1. Perform initial retrieval to get the top potentially relevant chunks (we used the top 150);
  2. Pass the top-N chunks, along with the user's query, through the reranking model;
  3. Using a reranking model, give each chunk a score based on its relevance and importance to the prompt, then select the top-


## Query 3: "What MRR@10 does SPLADE-v3 achieve on the MS MARCO dev set?"


### dense

#### Rank 1 | Score: 0.7961 | Chunk: 0 | Document: arxiv__2403.06789__splade-v3.md

# SPLADE-v3: New baselines for SPLADE

Carlos Lassance Cohere (Work done while at Naver) cadurosar at gmail dot com

Hervé Déjean, Thibault Formal, Stéphane Clinchant Naver Labs Europe first.lastname at naverlabs dot com

# Abstract

A companion to the release of the latest version of the SPLADE library. We describe changes to the training structure and present our latest series of models – SPLADE-v3. We compare this new version to BM25, SPLADE ^ { + + } , as well as rerankers, and showcase its effectiveness via a meta-analysis over more than 40 query sets. SPLADE-v3 further pushes the limit of SPLADE models: it is statistically significantly more effective than both BM25 and S P L A D E { + + } , while comparing well to cross-encoder re-rankers. Specifically, it gets more than 40 MRR @ 10 on the MS MARCO dev set, and improves by \uparrow 2% the out-of-domain results on the BEIR benchmark.

# 1 Introduction

This technical report is a companion to the release of the latest version of the SPLADE library1. Given the improvements stemming from simple modifications to the overall training structure, we believe that it is worth releasing new models – despite the lack of novelty 

#### Rank 2 | Score: 0.7652 | Chunk: 4 | Document: arxiv__2403.06789__splade-v3.md

The base SPLADE-v3 model5 starts from SPLADE ^ { + + } Self Distil, and is trained with a mix of KL-Div and MarginMSE, with 8 negatives per query sampled from SPLADE ^ { + + } Self Distil. All the other hyperparameters are similar to previous SPLADE iterations. Importantly, note that in all of our experiments, we use the original MS MARCO collection without the titles [12, 13].

Evaluation To assess the effectiveness of the model, we use the meta-analysis procedure introduced in RANGER [18, 19]. We use up to 44 query sets – relying on the ir_datasets library [15] – coming from different datasets, including 1. MS MARCO passages (4 query sets), 2. MS MARCO v2 passages (4 query sets), 3. BEIR (13 query sets), 4. LoTTE (12 query sets), 5. Antique, 6. TREC-CAR (y1) (2 query sets), 7. Natural Questions, 8. TriviaQA, 9. TREC-TB (3 query sets), and 10. TREC-MQ (2 query sets). We use n D C G * @ 10 to measure effectiveness, where \ n D C G * stands for the nDCG considering only the judged documents (encountered in the retrieved top- k ) if the dataset has both positive and negative judgments – otherwise, we use the standard nDCG @ 10 .

Comparison to BM25 First, we compare our method to BM25 and present the resulting metaanalysis in Figure 1. We notice statistically significant improvements in most of the 44 query sets, with only 3 query sets presenting a statistical decrease in effectiveness. These query sets are Webis Touché-2020 and the two TREC-MQ que

#### Rank 3 | Score: 0.7565 | Chunk: 7 | Document: arxiv__2403.06789__splade-v3.md

of posting lists to traverse).

Table 1: Comparison of results as averages per dataset. We report MRR @ 10 for MS MARCO (MSM), n D C G @ 10 for TREC, mean nDCG @ 10 for BEIR (13 datasets), and mean Success \textcircled { a } 5 over all non-pooled subsets of the Forum (LoTTE-F) and Search (LoTTE-S) tasks for LoTTE [17]. We also report the FLOPS measure as a loose indicator of efficiency [7].

| Model | MSM | TREC19 | TREC20 | BEIR 13 | LoTTE-S | LoTTE-F | FLOPS |
|---|---|---|---|---|---|---|---|
| SPLADE++SD | 37.6 | 73.0 | 71.8 | 50.7 | - | 1 | 1.4 |
| SPLADE-v3 | 40.2 | 72.3 | 75.4 | 51.7 | 74.7 | 66.0 | 1.2 |
| SPLADE-v3-DistilBERT | 38.7 | 75.2 | 74.4 | 50.0 | 70.3 | 62.8 | 1.4 |
| SPLADE-v3-Lexical | 40.0 | 71.2 | 73.6 | 49.1 | 74.2 | 64.5 | 0.6 |
| SPLADE-v3-Doc | 37.8 | 71.5 | 70.3 | 47.0 | 71.1 | 59.0 | 1.4 |

Table 2: nDCG @ 10 over the set of 13 datasets of BEIR [20].

| Dataset | SPLADE++SD | SPLADE-v3 | SPLADE-v3-DistilBERT | SPLADE-v3-Lexical | SPLADE-v3-Doc |
|---|---|---|---|---|---|
| Argu Ana | 51.8 | 50.9 | 48.4 | 52.7 | 46.7 |
| Climate-FEVER | 23.7 | 23.3 | 22.8 | 21.8 | 15.9 |
| DBPedia-entity | 43.6 | 45.0 | 42.6 | 42.8 | 36.1 |
| FEVER | 79.6 | 79.6 | 79.6 | 78.5 | 68.9 |
| FiQA-2018 | 34.9 | 37.4 | 33.9 | 36.4 | 33.6 |
| HotpotQA | 69.3 | 69.2 | 67.8 | 68.5 | 

#### Rank 4 | Score: 0.7507 | Chunk: 8 | Document: arxiv__2403.06789__splade-v3.md

|
| NFCorpus | 34.5 | 35.7 | 34.8 | 34.7 | 33.8 |
| NQ | 53.3 | 58.6 | 54.9 | 56.1 | 52.1 |
| Quora | 84.9 | 81.4 | 81.7 | 73.4 | 77.5 |
| SCIDOCS | 16.1 | 15.8 | 14.8 | 15.9 | 15.2 |
| Sci Fact | 71.0 | 71.0 | 68.5 | 71.5 | 68.8 |
| TREC-COVID | 72.5 | 74.8 | 70.0 | 63.6 | 68.1 |
| Touche-2020 | 24.2 | 29.3 | 30.1 | 22.7 | 27.0 |
| Average | 50.7 | 51.7 | 50.0 | 49.1 | 47.0 |

# 5 Conclusion

This technical report describes the release of SPLADE-v3 models. We have shown through extensive evaluations that this new series of SPLADE models is statistically significantly more effective than previous iterations. In most query sets – including zero-shot settings – SPLADE-v3 outperforms BM25 and can even rival some re-rankers.

# References

[1] E. Bassani. ranx: A blazing-fast python library for ranking evaluation and comparison. In European Conference on Information Retrieval, pages 259–264. Springer, 2022.
[2] N. Craswell, B. Mitra, E. Yilmaz, D. F. Campos, J. Lin, E. M. Voorhees, and I. Soboroff. Overview of the trec 2022 deep learning track. In Text Retrieval Conference, 2022.
[3] H. Déjean, S. Clinchant, C. Lassance, S. Lupart, and T. Formal. Benchmarking middle-trained language models for neural search. ar Xiv preprint ar Xiv: 2306.02867, 2023.
[4] T. Formal, C. Lassance, B. Piwowarski, and S. Clinchant. Splade v2: Sparse lexical and expansion model for information retrieval, 2021.
[5] T. Formal, C. Lassance, B. Piwowarski, and S. Clinchant. From dis

#### Rank 5 | Score: 0.733 | Chunk: 5 | Document: arxiv__2403.06789__splade-v3.md

sets. For Touché-2020, we are still unsure what is the actual issue, but this observation is recurrent with learned ranking models [5, 11, 20]. For TREC-MQ, there could be an issue with the long documents that may need to be decomposed into passages. Notice the large summary effect, meaning that over the whole set of comparisons, SPLADE-v3 vastly outperforms BM25 (even if it is less efficient).

Comparison to SPLADE ^ { + + } Self Distil We now compare SPLADE-v3 to the previous SPLADE model used at initialization – SPLADE ^ { + + } Self Distil. Ideally, there should not be any loss in effectiveness for any of the tested query sets. We present the meta-analysis in Figure 2. We notice that only Quora suffered from a significant decrease in effectiveness, with most other datasets presenting a gain of effectiveness, with the overall summary effect being positive towards the new baseline.

Comparison to re-rankers We finally compare SPLADE-v3 to cross-encoder re-rankers. More specifically, we consider two models that re-rank the top k = 50 documents returned by SPLADE-v3: MiniLM6 and DeBERTaV37 – we present the results in Figure 3 and Figure 4 respectively. Note that higher k could be used for re-ranking – but we believe that re-ranking 50 documents already constitutes a good efficiency-effectiveness trade-off, especially when re-ranking a well-tuned firststage retriever. For MiniLM, we notice that the summary effect is close to 0 when we consider a 95% confidence interval and that there is not much difference between the origina

#### Rank 6 | Score: 0.718 | Chunk: 6 | Document: arxiv__2403.06789__splade-v3.md

and the re-ranked ones – except for a few datasets that could just be “outliers” in the effectiveness of MiniLM. However, in the case of DeBERTaV3, we see the opposite: for most query sets the re-ranker is able to outperform SPLADE-v3 – except for Argu Ana whose “counter-argument” task might be more intricate for a re-ranker.

# 4 SPLADE-v3-DistilBERT, SPLADE-v3-Lexical and SPLADE-v3-Doc

In addition, we also release three other SPLADE-v3 variants:

1. SPLADE-v3-DistilBERT8, which instead starts training from DistilBERT – and thus has a smaller inference “footprint”.
2. SPLADE-v3-Lexical9, for which we remove query expansion, thus reducing the retrieval FLOPS (and improving efficiency) [6].
3. SPLADE-v3-Doc10, which starts training from Co Condenser, and where no computation is done for the query – which can be seen as a simple binary Bag-of-Words [4, 6].

Table 1 summarizes the results as averages over datasets – detailed results over the set of 13 BEIR datasets can be found in Table 2. We note that SPLADE-v3-Lexical is (very) effective on MS MARCO as well as LoTTE, but struggles on BEIR (out-of-domain). While the DistilBERT version is a clear downgrade from the BERT version, it remains however more effective than the lexical version on BEIR. SPLADE-v3-Doc is the less effective approach overall, especially in “zero-shot”, showing that (even) a minimal amount of computation on the query side is important. However, its performance remains quite competitive w.r.t. state-of-the-art dense bi-encoders, especially given its efficiency (no query encoding, and a short 

#### Rank 7 | Score: 0.6803 | Chunk: 1 | Document: arxiv__2403.06789__splade-v3.md

for a proper publication. We thus aim to document this new series of models – named SPLADE-v3 – and provide the community with better SPLADE “baselines”. We have been using this new version of the code for most of our recent works.

# 2 Better Training

We detail in the following several improvements that have been made to the training of SPLADE models.

# 2.1 Multiple Negatives Per Batch

Following Tevatron [9], the library now allows training with more than one hard negative. We find that increasing the number of negatives improves the results, especially in the in-domain [3] setting, but does not add much to out-of-domain generalization. We use negatives coming from a SPLADE ^ { + + } [5] model, and consider 100 negatives – 50 from the top-50 and 50 chosen at random from the top- . 1 k .

# 2.2 Better Distillation Scores

To further improve SPLADE’s effectiveness, we use an ensemble of cross-encoder re-rankers to generate our distillation scores – instead of the standard approach relying on a single model [11, 5, 4 ] ^ { 2 } . We generate two types of scores: 1. the simple ensemble of scores, and 2. the “rescored” version, where we use affine transformations to make some of the data statistics (average and std score values) similar to the ones encountered in the previous distillation setting 3. We use the following open-source models on Hugging Face to generate the scores:

1. cross-encoder/ms-m

#### Rank 8 | Score: 0.6793 | Chunk: 3 | Document: arxiv__2403.06789__splade-v3.md

(used for SPLADE v2 [4] and S P L A D E { + + } [4]). Given the extra negatives, we noticed empirically that the MarginMSE (resp. KL-Div) focused more on Recall (resp. Precision). We then chose to combine both, with different weights \lambda_K L = 1 for KL-Div, \lambda_M S E = 0.05 for MarginMSE – based on cross-validation), which overall led to better results.

# 2.4 Further Fine-Tuning SPLADE

We also noticed that starting from SPLADE ^ { + + } Self Distil4 – which exhibits slight zero-shot boosts when compared to SPLADE ^ { + + } Ensemble Distil [5] – and applying the previous changes led to better effectiveness when compared to starting from a Co Condenser [8] or a DistilBERT[16] checkpoint. We are still not sure about the cause(s) of this effect, but we believe that a sort of curriculum learning – as the one investigated in Zeng et al. [21] – could happen and lead to the observed improvements, but it still needs to be better investigated.

# 3 A New Baseline, S

#### Rank 9 | Score: 0.6573 | Chunk: 11 | Document: arxiv__2403.06789__splade-v3.md

evaluation of information retrieval models. ar Xiv preprint ar Xiv: 2104.08663, 2021.
[21] H. Zeng, H. Zamani, and V. Vinay. Curriculum learning for dense retrieval distillation. In Proceedings of the 45th International ACM SIGIR Conference on Research and Development in Information Retrieval, pages 1979–1983, 2022.

![](images/.jpg)
Figure 1

#### Rank 10 | Score: 0.6345 | Chunk: 10 | Document: arxiv__2403.06789__splade-v3.md

S. Clinchant. The tale of two msmarco - and their unfair comparisons. In Proceedings of the 46th International ACM SIGIR Conference on Research and Development in Information Retrieval, SIGIR ’23, page 2431–2435, New York, NY, USA, 2023. Association for Computing Machinery.
[14] S.-C. Lin, J.-H. Yang, and J. Lin. Distilling dense representations for ranking using tightlycoupled teachers, 2020.
[15] S. Mac Avaney, A. Yates, S. Feldman, D. Downey, A. Cohan, and N. Goharian. Simplified data wrangling with ir_datasets. In SIGIR, 2021.
[16] V. Sanh, L. Debut, J. Chaumond, and T. Wolf. Distilbert, a distilled version of bert: smaller, faster, cheaper and lighter, 102019.
[17] K. Santhanam, O. Khattab, J. Saad-Falcon, C. Potts, and M. Zaharia. ColBERTv2: Effective and efficient retrieval via lightweight late interaction. In M. Carpuat, M.-C. de Marneffe, and I. V. Meza Ruiz, editors, Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, pages 3715–3734, Seattle, United States, July 2022. Association for Computational Linguistics.
[18] M. Sertkan, S. Althammer, and S. Hofstätter. Ranger: A toolkit for effect-size based multi-task evaluation. ar Xiv preprint ar Xiv: 2305.15048, 2023.
[19] M. Sertkan, S. Althammer, S. Hofstätter, P. Knees, and J. Neidhardt. Exploring effect-size-based meta-analysis for multi-dataset evaluation. 2023.
[20] N. Thakur, N. Reimers, A. Rücklé, A. Srivastava, and I. Gurevych. Beir: A heterogenous benchmark for zer


## Query 4: "What embedding dimension does Qwen3-Embedding-8B produce by default?"


### dense

#### Rank 1 | Score: 0.7122 | Chunk: 4 | Document: arxiv__2506.05176__qwen3-embedding.md

of the Qwen3 backbone models (including 0.6B, 4B, and 8B), we ultimately trained three text embedding models and three text reranking models. To facilitate their application in downstream tasks, the Qwen3 Embedding series supports several practical features, such as flexible dimension representation for embedding models and customizable instructions for both embedding and reranking models.

We evaluate the Qwen3 Embedding series across a comprehensive set of benchmarks spanning multiple tasks and domains. Experimental results demonstrate that our embedding and reranking models achieve state-of-the-art performance, performing competitively against leading proprietary models in several retrieval tasks. For example, the flagship model Qwen3-8B-Embedding attains a score of 70.58 on the MTEB Multilingual benchmark (Enevoldsen et al., 2025) and 80.68 on the MTEB Code benchmark (Enevoldsen et al., 2025), surpassing the previous state-of-the-art proprietary embedding model, Gemini-Embedding (Lee et al., 2025b). Moreover, our reranking model delivers competitive results across a range of retrieval tasks. The Qwen3-Reranker-0.6B model exceeds previously top-performing models in numerous retrieval tasks, while the larger Qwen3-Reranker-8B model demonstrates even superior performance, improving ranking results by 3.0 points over the 0.6B model across multiple tasks. Furthermore, we include a constructive ablation study to elucidate the key factors contributing to the superior performance of the Qwen3 Embedding series, providi

#### Rank 2 | Score: 0.694 | Chunk: 30 | Document: arxiv__2506.05176__qwen3-embedding.md

| 75.70 | 65.20 |
| gte-Qwen2-1.5B-instruct | 1.5B | 67.12 | 67.79 | 72.53 | 54.61 | 79.5 | 68.21 | 71.86 | 60.05 |
| Qwen3-Embedding-0.6B | 0.6B | 66.33 | 67.44 | 71.40 | 68.74 | 76.42 | 62.58 | 71.03 | 54.52 |
| Qwen3-Embedding-4B | 4B | 72.26 | 73.50 | 75.46 | 77.89 | 83.34 | 66.05 | 77.03 | 61.26 |
| Qwen3-Embedding-8B | 8B | 73.84 | 75.00 | 76.97 | 80.08 | 84.23 | 66.99 | 78.21 | 63.53 |

| MTEB(Code,v1) | Avg. | Apps | COIR- Code Search- Net | Code- Edit- Search | Code- Feedback- MT | Code- Feedback- ST | Code- Search Net- CCR | Code- Search Net | Code- Trans- Ocean- Contest | Code- Trans- Ocean-DL | | Stack- CosQA Overflow- QA | Synthetic- Text2SQL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BGEmultilingual | 62.04 | 22.93 | 68.14 | 60.48 | 60.52 | 76.70 | 73.23 | 83.43 | 86.84 | 32.64 | 27.93 | 92.93 | 58.67 |
| NV-Embed-v2 | 63.74 | 29.72 | 61.85 | 73.96 | 60.27 | 81.72 | 68.82 | 86.61 | 89.14 | 33.40 | 34.82 | 92.36 | 60.90 |
| gte-Qwen2-7B-instruct | 62.17 | 28.39 | 71.79 | 67.06 | 57.66 | 85.15 | 66.24 | 86.96 | 81.83 | 32.17 | 31.26 | 84.34 | 53.22 |
| gte Qwestrct68 | | 28.91 | 71.56 | 59.60 | 49.92 | 81.92 | 72.08 | 91.08 | 79.02 | 32.73 | 32.23 | 90.27 | 54.49 |
| BGE-M3 (Dense) | 58.22 | 14.77 | 58.07 | 59.83 | 47.86 | 69.27 | 53.55 | 61.98 | 86.22 | 29.37 | 27.36 | 80.71 | 49.65 |
| Jina-v3 | 58.85 | 28.99 | 67.83 | 57.24 | 59.66 | 78.13 | 54.17 | 85.50 | 77.37 | 30.91 | 35.15 | 90.79 | 41.49 |
| Qwen3-Embedding-0.6B 75.41 | | 75.34 | 84.69 | 64.42 | 90.82 | 86.39 | 91.72 | 91.01 | 86.05 | 31.36 | 36.48 | 89.99 | 76.74 |
| Qwen3-Embedding-4B | 80.06 | 89.18 | 87.93 | 76.49 | 93.21 | 89.51 | 95.59 | 92.34 | 90.99 | 35.04 | 37.98 | 94.32 | 78.21 |
| Qwen3-Embedding-8B | 80.68 | 91.07 | 89.51 | 76.97 | 93.70 | 89.93 | 96.35 | 92.66 | 93.73 | 32.81 | 

#### Rank 3 | Score: 0.6785 | Chunk: 5 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

Qwen-3-Embedding-0.6B: 0.6B parameters, 1024 dimensions  
- Qwen-3-Embedding-4B: 4B parameters, 2560 dimensions  
- Qwen-3-Embedding-8B: 8B parameters, 4096 dimensions  
- BGE-M3: 0.6B parameters, serving as the primary baseline
Additional baselines include NV-Embed-v2, multilingual-e5-large-instruct, and proprietary APIs (Gemini, text-embedding-3-large) for context.
4.3 Implementation Details
All models are evaluated using the standardized mteb evaluation framework. For reranking experiments, we retrieve top-100 candidates using the embedding model and subsequently apply reranking models for refinement. ONNX quantization experiments follow the methodology described in Tanskanen (2024), using dynamic quantization to reduce model size and latency.
## 5. Results and Analysis
### 5.1 Main Performance Comparison
5.1.1 MTEB English v2 Benchmark
![](https://miro.medium.com/v2/resize:fit:1000/1*TJdz0CJaB1bdBWa6vj5hRg.png)
Key Observations:  
- Qwen-3-Embedding-0.6B outperforms BGE-M3 by 18.7% on MTEB English tasks (70.70 vs 59.56) despite identical parameter count  
- The performance gap extends across all task categories, with particularly strong improvements in retrieval (+11.36 points) and clustering tasks  
- Scaling to 8B parameters yields only marginal gains over the 4B model (75.22 vs 74.60), suggesting diminishing returns for English tasks
5.1.2 Multilingual and Code Retrieval
![](https://miro.medium.com/v2/resize:fit:1000/1*4-Sv9GwHdrnf2C6w-lmbCA.png)
Analysis:  
- Qwen-3-Embedding-0.6B demonstrates consistent multilingual superi

#### Rank 4 | Score: 0.6607 | Chunk: 29 | Document: arxiv__2506.05176__qwen3-embedding.md

61.83 | 86.57 | 33.43 |
| Qwen3-Embedding-4B | 4B | 74.60 | 68.09 | 89.84 | 57.51 | 87.01 | 50.76 | 68.46 | 88.72 | 34.39 |
| Qwen3-Embedding-8B | 8B | 75.22 | 68.70 | 90.43 | 58.57 | 87.52 | 51.56 | 69.44 | 88.58 | 34.83 |

Table 7: Results on MTEB(eng, v2) (Muennighoff et al., 2023). We compare models from the online leaderboard.

Table 8: Results on C-MTEB (Xiao et al., 2024) (MTEB(cmn, v1).

| MTEB(cmn, v1) | Param | Mean (Task) | Mean (Type) | Class- ification | Clus- tering | Pair Class. | Rerank | Retrieval | STS |
|---|---|---|---|---|---|---|---|---|---|
| multilingual-e5-large-instruct | 0.6B | 58.08 | 58.24 | 69.80 | 48.23 | 64.52 | 57.45 | 63.65 | 45.81 |
| gte-Qwen2-7B-instruct | 7.6B | 71.62 | 72.19 | 75.77 | 66.06 | 81.16 | 6

#### Rank 5 | Score: 0.6564 | Chunk: 3 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

multiple vectors per document, enabling fine-grained similarity computation at the cost of increased storage.
BGE-M3 uniquely integrates all three approaches, allowing hybrid retrieval strategies that combine semantic and lexical signals. Qwen-3, conversely, focuses on optimizing dense retrieval through scaled architecture and advanced training methodologies.
### 2.2 Benchmarking Standards
The Massive Text Embedding Benchmark (MTEB) has emerged as the de facto standard for evaluating embedding models across 111 languages and multiple task types. Recent extensions include:  
- MTEB English v2: 56 tasks covering classification, clustering, retrieval, and semantic textual similarity  
- CMTEB: Chinese-specific evaluation suite with 6 task categories  
-MTEB Code: Code retrieval and understanding tasks  
- MMTEB: Multilingual evaluation across diverse languages and domains
These benchmarks enable standardized comparison of model capabilities beyond single-domain performance metrics.
## 3. Model Architectures and Training
### 3.1 Qwen-3 Embedding Series
The Qwen-3 embedding models leverage the Qwen3 language model as a base, implementing a standard bi-encoder architecture where queries and documents are encoded independently into dense vectors. Key architectural features include:
- Parameter Scaling: Models available at 0.6B, 4B, and 8B parameters to balance performance and computational cost  
- Dimension Flexibility: Embedding dimensions of 1024, 2560, and 4096 respectively, enabling quality-compression tradeoffs  
- Synthetic Dataset G

#### Rank 6 | Score: 0.6533 | Chunk: 10 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

for informed embedding model selection in production environments.
## References
_Zhang, Y., et al. (2025). Qwen3 Embedding: Advancing Text Embedding and Reranking with Synthetic Data and Scaled Architecture.  
Muennighoff, N., et al. (2023). MTEB: Massive Text Embedding Benchmark. Proceedings of the 17th Conference of the European Chapter of the Association for Computational Linguistics.  
Tanskanen, A. (2024). Guidebook to the State-of-the-Art Embeddings and Optimization Techniques.

#### Rank 7 | Score: 0.6512 | Chunk: 5 | Document: arxiv__2506.05176__qwen3-embedding.md

insights into its effectiveness.

In the following sections, we describe the design of the model architecture, detail the training procedures, present the experimental results for both the embedding and reranking models of the Qwen3 Embedding Series, and conclude this technical report by summarizing the key findings and outlining potential directions for future research.

# 2 Model Architecture

The core idea behind embedding and reranking models is to evaluate relevance in a task-aware manner. Given a query q and a document d , embedding and reranking models assess their relevance based on a similarity criterion defined by instruction I . To enable the models for task-aware relevance estimation, training data is often organized as \{ I_i , q_i , d_i ^ { + } , d_i , 1 ^ { - } , - - - , d_i , n ^ { - } \} , , where d_i ^ { + } represents a positive (relevant) document for query q_i , and d_i , j ^ { - } are negative (irrelevant) documents. Training the model on diverse text pairs broadens its applicability to a range of downstream tasks, including retrieval, semantic textual similarity, classification, and clustering.

![](images/.jpg)
Figure 1: Model architecture of Qwen3-Embedding (left) and Qwen3-Reranker (right).

Architecture The Qwen3 embedding and reranking models are built on the dense version of Qwen3 foundation models and are available in three sizes: 0.6B, 4B, and 8B parameters. We initialize these models using the Qwen3 foundation models to leverage their cap

#### Rank 8 | Score: 0.6462 | Chunk: 0 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

<!-- source: https://medium.com/@mrAryanKumar/comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retrieval-72c0e6895413 -->
# Comparative Analysis of Qwen-3 and BGE-M3 Embedding Models for Multilingual Information Retrieval
**_Aryan Kumar  
Data Scientist, Nakakita Seisakusho Co., Ltd._**
![](https://miro.medium.com/v2/resize:fit:700/1*hHaGImPQn35ZHyR2WjPSSg.png)
This study presents a comprehensive comparative analysis of the Qwen-3 embedding model series against the BGE-M3 embedding model across multiple retrieval benchmarks and practical deployment scenarios. Our evaluation spans standard benchmarks including MTEB (English v2), CMTEB (Chinese), MTEB Code, and MMTEB multilingual tasks. Experimental results demonstrate that Qwen-3 models consistently outperform BGE-M3 across all evaluated dimensions, with Qwen-3-Embedding-0.6B achieving a 7.9% relative improvement on MMTEB (64.33 vs 59.56) while maintaining identical parameter count. The flagship Qwen-3-Embedding-8B model attains state-of-the-art performance with 75.22 MTEB English score, surpassing even proprietary models like Gemini Embedding. We further

#### Rank 9 | Score: 0.6453 | Chunk: 8 | Document: arxiv__2511.22240__pipeline-optimization.md

testing was not performed as all models were evaluated on identical test sets, making relative comparisons directly interpretable.

# 5. RESULTS

# 5.1 Embedding Model Comparison

Table 1 presents the performance of each embedding model using 2000-character chunking and HNSW indexing. The results demonstrate that higher-dimensional models dramatically outperform smaller alternatives.

TABLE I

| Mode1 | Dim | Acc@3 | NDCG@3 | Acc@5 | NDCG@5 | Acc@10 | NDCG@10 |
|---|---|---|---|---|---|---|---|
| all-mpnet-base-v2 | 768 | 0.268 | 0.229 | 0.31 | 0.246 | 0.37 | 0.266 |
| bge-base-en-v1.5 | 768 | 0.24 | 0.205 | 0.276 | 0.22 | 0.32 | 0.234 |
| bge-large-en-v1.5 | 1024 | 0.3 | 0.26 | 0.343 | 0.278 | 0.396 | 0.295 |
| gte-base-en-v1.5 | 768 | 0.389 | 0.338 | 0.434 | 0.357 | 0.492 | 0.376 |
| gte-large-en-v1.5 | 1024 | 0.412 | 0.356 | 0.462 | 0.378 | 0.522 | 0.396 |
| Qwen3-Embed-0.6B | 1024 | 0.516 | 0.461 | 0.562 | 0.48 | 0.611 | 0.496 |
| Qwen3-Embed-4B | 2560 | 0.556 | 0.503 | 0.601 | 0.522 | 0.647 | 0.537 |
| Qwen3-Embed-8B | 4096 | 0.571 | 0.516 | 0.612 | 0.533 | 0.663 | 0.549 |

Key Findings:

Qwen3-Embedding-8B (4096-dim) achieves Top-3 accuracy of 0.571 and NDCG@3
of 0.516
GTE-large (1024-dim) scores 0.412 and 0.356 for the same metrics
Even Qwen3-Embedding-4B (2560-dim) outperforms all 768/1024-dimensional
models (Accuracy \mathcal { @ 3 = 0.556 } versus 0.412)
Increasing embedding dimensionality yields approximately 10–15 percentage point
improvements in accuracy

The performance gap between model families is substantial. The Qwen3 series consistently outperforms 

#### Rank 10 | Score: 0.6407 | Chunk: 6 | Document: arxiv__2506.05176__qwen3-embedding.md

in text modeling and instruction following. The model layers, hidden size, and context length for each model configuration are detailed in Table 1.

Embedding Models For text embeddings, we utilize LLMs with causal attention, appending an [EOS] token at the end of the input sequence. The final embedding is derived from the hidden state of the last layer corresponding to this [EOS] token.

To ensure embeddings follow instructions during downstream tasks, we concatenate the instruction and the query into a single input context, while leaving the document unchanged before processing with LLMs. The input format for queries is as follows:

| {Instruction} {Query}<|endoftext|> |

Reranking Models To more accurately evaluate text similarity, we employ LLMs for point-wise reranking within a single context. Similar to the embedding model, to enable instruction-following capability, we include the instruction in the input context. We use the LLM chat template and frame the similarity assessment task as a binary classification problem. The input to LLMs adheres to the template shown below:

| Model Type | Models | Size | Layers | Sequence Length | Embedding Dimension | MRL Support | Instruction Aware |
|---|---|---|---|---|---|---|---|
| Text Embedding | Qwen3-Embedding-0.6B Qwen3-Embedding-4B Qwen3-Embedding-8B | 0.6B 4B 8B | 283636 | 32K 32K 32K | 102425604096 | Yes Yes Yes | Yes Yes Yes |
| Text Reranking | Qwen3-Reranker-0.6B Qwen3-Reranker-4B Qwen3-Reranker-8B | 0.6B 4B 8B | 283636 | 32K 32K 32K | - = | 1 |


## Query 5: "What new index scan feature was introduced in pgvector 0.8.0 to fix partial results when combining HNSW with WHERE clause filters?"


### dense

#### Rank 1 | Score: 0.8799 | Chunk: 0 | Document: www_thenile_dev__blog__pgvector-080.md

<!-- source: https://www.thenile.dev/blog/pgvector-080 -->

## Announcing: pgvector 0.8.0 released and available on Nile

Gwen Shapira — 2024-11-05

The pgvector community shipped the much anticipated version 0.8.0 with significant performance and functionality improvements. Naturally, we couldn't wait to make it available to Nile users.
## Release highlights
Per the official release notes, pgvector 0.8.0 includes:
  * Added support for iterative index scans
  * Added casts for arrays to sparsevec
  * Improved cost estimation for better index selection when filtering
  * Improved performance of HNSW index scans
  * Improved performance of HNSW inserts and on-disk index builds
  * Dropped support for Postgres 12

The most anticipated feature is iterative index scanning, which addresses a longstanding challenge with vector indexes. Previously, filters were applied after the index scan completed, which often yielded fewer results than expected. According to the pgvector documentation:
> With approximate indexes, filtering is applied after the index is scanned. If a condition matches 10% of rows, with HNSW and the de

#### Rank 2 | Score: 0.8219 | Chunk: 3 | Document: www_thenile_dev__blog__pgvector-080.md

vectors, it would have missed some results as expected.
Lets try with a tweaked configuration:
```
SET hnsw.ef_search = 3;
SET

SELECT id, category, embedding<=>'[1,2,3]'  AS distance
FROM filtest WHERE category=1 ORDER BY distance LIMIT 3;
 id | category |      distance
----+----------+--------------------
  3 |        1 | 1.0714285714285714
  2 |        1 | 1.0714285714285714
(2 rows)

```

This is the partial result that I expected!
### Iterative index scans in pgvector 0.8.0
Now lets see how the same query behaves in pgvector 0.8.0:
```
SELECT extversion FROM pg_extension WHERE extname = 'vector';
 extversion
------------
 0.8.0

SET hnsw.ef_search = 3;
SET

SELECT id, category, embedding<=>'[1,2,3]'  AS distance
FROM filtest WHERE category=1 ORDER BY distance LIMIT 3;
 id | category |      distance
----+----------+--------------------
  1 |        1 | 1.0714285714285714
  2 |        1 | 1.0714285714285714
  3 |        1 | 1.0714285714285714
(3 rows)

```

Great! pgvector 0.8.0 delivers! Yes, but not in the way you think:
```
SHOW hnsw.iterative_scan;
 hnsw.iterative_scan
---------------------
 off
(1 row)

```

Oops! `hnsw.iterative_scan` is disabled. So how did it still work? Use of `explain` shows that the index wasn't used:
```
EXPLAIN SELECT id, category, embedding<=>'[1,2,3]' AS distance
FROM filtest WHERE category=1 ORDER

#### Rank 3 | Score: 0.7951 | Chunk: 5 | Document: www_thenile_dev__blog__pgvector-080.md

rows)

SET hnsw.iterative_scan = relaxed_order; -- enable iterative scan
SET

SELECT id, category, embedding<=>'[1,2,3]'  AS distance
FROM filtest WHERE category=1 ORDER BY distance LIMIT 3;
 id | category |      distance
----+----------+--------------------
  2 |        1 | 1.0714285714285714
  3 |        1 | 1.0714285714285714
  1 |        1 | 1.0714285714285714
(3 rows)

```

And we can see that pgvector 0.8.0 and iterative scans work as expected. As a bonus, we also saw the cost optimization in action, and learned about `hnsw.ef_search` query configuration. One last tip:

#### Rank 4 | Score: 0.7723 | Chunk: 4 | Document: www_thenile_dev__blog__pgvector-080.md

distance LIMIT 3;
                             QUERY PLAN
---------------------------------------------------------------------
 Limit  (cost=25.09..25.10 rows=3 width=16)
   ->  Sort  (cost=25.09..25.11 rows=6 width=16)
         Sort Key: ((embedding <=> '[1,2,3]'::vector))
         ->  Seq Scan on filtest  (cost=0.00..25.02 rows=6 width=16)
               Filter: (category = 1)
(5 rows)

```

This is due to a different improvement in pgvector 0.8.0:
> Improved cost estimation for better index selection when filtering
It is really silly to use a vector index when scanning a 6-row table. So with the improved cost estimation, it no longer happens. This is good news, but I really want to check the iterative scan. So lets force the use of index and try again:
```
SET enable_seqscan=false; -- force use of index, don't do this in production!
SET

SELECT id, category, embedding<=>'[1,2,3]'  AS distance
FROM filtest WHERE category=1 ORDER BY distance LIMIT 3;
 id | category |      distance
----+----------+--------------------
  2 |        1 | 1.0714285714285714
  3 |        1 | 1.

#### Rank 5 | Score: 0.7538 | Chunk: 1 | Document: www_thenile_dev__blog__pgvector-080.md

hnsw.ef_search of 40, only 4 rows will match on average.
Common workarounds include scanning more rows, using partial indexes, or partitioning, but these methods can be impractical or undesirable. The new iterative scan feature offers a more straightforward and intuitive solution:
  1. Scan the vector index
  2. Apply filter
  3. Check if enough results are returned. If not, repeat the scan.

Lets see this in action with a very small example. I strongly recommend running small experiments - you learn so much if the actual results don't match your expectations. Follow along for important pgvector lessons:
To start, I create a table with sample data:
```
CREATE TABLE filtest(id INTEGER, category INTEGER, embedding vector(3));
INSERT INTO filtest VALUES
    (1, 1, '[3, 1, -2]'),
    (2, 1, '[3, 1, -2]'),
    (3, 1, '[3, 1, -2]'),
    (1, 2, '[1.1, 2.2, 3.3]'),
    (2, 2, '[1.1, 2.2, 3.3]'),
    (3, 2, '[1.1, 2.2, 3.3]');
CREATE INDEX ON filtest USING hnsw (embedding vector_cosine_ops);

```

The table contains six rows divided into two categories. Vectors in category 2 closely resemble `[1, 2, 3]`, while vectors in category 1 differ significantly, representing **orthogonal** (unrelated) da

#### Rank 6 | Score: 0.7514 | Chunk: 2 | Document: www_thenile_dev__blog__pgvector-080.md

In real use-cases, categories can be different companies (tenants), different departments within the same company, genres if the table stores information about movies, etc. Anything that you may want to use for filtering.
What would you expect the following query to return?
```
SELECT id, category, embedding<=>'[1,2,3]'  AS distance
FROM filtest WHERE category=1
ORDER BY distance LIMIT 3;

```

### Index scans in pgvector 0.7.4
I searched for 3 vectors, from category 1, that are closest to `[1,2,3]`, so the correct answer is to return all vectors from category 1. However, this is what I expected pgvector 0.7.4 to do:
  1. Scan the vector index and find the 3 vectors closest to `[1,2,3]`, some of which should belong to category 2.
  2. Filter the results and keep only vectors from category 1.
  3. Return partial results.

However, in practice:
```
SELECT extversion FROM pg_extension WHERE extname = 'vector';
 extversion
------------
 0.7.4
(1 row)

SELECT id, category, embedding<=>'[1,2,3]'  AS distance
FROM filtest WHERE category=1 ORDER BY distance LIMIT 3;
 id | category |      distance
----+----------+--------------------
  3 |        1 | 1.0714285714285714
  1 |        1 | 1.0714285714285714
  2 |        1 | 1.0714285714285714

```

Why are we seeing the correct results? Because pgvector's default configuration for the number of rows to scan in the vector index is 40. So the index scan returned the entire table, and after filtering, we got the right result. Thats the problem with small examples... if I tried wit

#### Rank 7 | Score: 0.7005 | Chunk: 0 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

<!-- source: https://www.crunchydata.com/blog/hnsw-indexes-with-postgres-and-pgvector -->

# HNSW Indexes with Postgres and pgvector

Christopher Winslett
Sep 1, 2023 · 12 min read

Postgres' [pgvector extension](https://github.com/pgvector/pgvector) recently added HNSW as a new index type for vector data. This levels up the database for vector-based embeddings output by AI models. A few months ago, we had written about approximate nearest neighbor [pgvector performance using the available list-based indexes](https://www.crunchydata.com/blog/pgvector-performance-for-developers). Now, with the addition of HNSW, pgvector can use the latest graph based algorithms to approximate nearest neighbor queries. As with all things databases, there are trade-offs, so don't throw away the list-based methodologies — and don't throw away the techniques we discussed in [scaling vector data](https://www.crunchydata.com/blog/scaling-vector-data-with-postgres).



#### Rank 8 | Score: 0.6914 | Chunk: 10 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

data sets, the rows will return sightly different rows due to the effect of approximation:

```
name
--------------------------
 Cookies, chocolate chip
 Cookies, crisp chocolate
 Cookies, chocolate drop
 Bar, toffee, crisp
 Cookies, peanut butter
```

To see that the query is using the index, you'll see that the index scan lists using `recipes_embedding_idx` index on the next to-last row:

```
QUERY PLAN
--------------------------------------------------------------------------------------------------
 Limit  (cost=100.49..118.22 rows=5 width=30)
   InitPlan 1 (returns $0)
     ->  Index Scan using recipes_pkey on recipes recipes_1  (cost=0.28..8.31 rows=1 width=18)
           Index Cond: (id = 151)
   ->  Index Scan using recipes_embedding_idx on recipes  (cost=92.18..2645.18 rows=720 width=30)
         Order By: (embedding <-> $0)
```

As listed in the TL;DR, the index optimizer is not perfect with HNSW, and prefers a simpler query. If we run a similar query but include a CTE, the HNSW index is not used by the optimizer:

```sql
EXPLAIN WITH random_recipe AS
(
   SELECT
      id,
      embedding
   FROM
      recipes
   WHERE
      recipes.id = 151 LIMIT 5
)
SELECT
   recipes.id,
   recipes.name
FROM
   recipes,
   random_recipe
WHERE
   recipes.id != random_recipe.id
ORDER BY
   recipes.embedding <-> random_recipe.em

#### Rank 9 | Score: 0.6873 | Chunk: 0 | Document: www_crunchydata_com__blog__pgvector-performance-for-developers.md

<!-- source: https://www.crunchydata.com/blog/pgvector-performance-for-developers -->

# Performance Tips Using Postgres and pgvector

Christopher Winslett
May 5, 2023 · 7 min read

**Note: pgvector 0.5 released HNSW indexes which improved performance significantly. Read more about it [HNSW Indexes with Postgres and pgvector](https://www.crunchydata.com/blog/hnsw-indexes-with-postgres-and-pgvector). We have additional articles in this [Postgres AI series](https://www.crunchydata.com/blog/topic/ai).**

As we've been helping people get started with AI in Postgres with `pgvector`, there have been few questions around performance. At a basic level, pgvector performance relies on 3 things:

  1. Are your queries using indexes?
  2. Are you setting your `list` size appropriately for your data set?
  3. Do you have enough memory for your indexes + ability to change settings?

For an intro to using pgvector, see [What's Postgres Got To Do With AI](https://www.crunchydata.com/blog/whats-postgres-got-to-do-with-ai). In it, we discuss the vector datatype, querying, and indexing options. During this blog post, we will refer to a "recipes". In the prior blog post, we built an AI powered recipe recommendation engine.

## Do you want an index?

Probably you do. It is important to note that vector indexes allow "approximate nearest neighbor" (ANN) searching. So if you have a hard requirement that a query return absolutely 100% of all nearby vectors, you are going to be stuck with full scans, which will be slow on large data sets.

However, most vector use cas

#### Rank 10 | Score: 0.6608 | Chunk: 11 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

LIMIT 5;
```

Long-story short, the simpler the better for HNSW usage.

## HNSW indexes and scaling

HNSW indexes are much more performant than the older list-based indexes. They also use more resources. Concurrency is improved, but many of the processes we laid out in the [Scaling PGVector blog post](https://www.crunchydata.com/blog/scaling-vector-data-with-postgres) are still applicable.

  1. Physical separation of data: because of the build requirements of the indexes, continue to host your vec


## Query 6: "How does Hypothetical Document Embedding (HyDE) work and what is the averaging step?"


### dense

#### Rank 1 | Score: 0.7885 | Chunk: 4 | Document: docs_haystack_deepset_ai__docs__hypothetical-document-embeddings-hyde.md

"adapter.answers")  
pipeline.connect("adapter.output", "embedder.documents")  
pipeline.connect("embedder.documents", "hyde.documents")  
query = "What should I do if I have a fever?"  
result = pipeline.run(data={"prompt_builder": {"question": query}})  
  
## 'hypothetical_embedding': [0.0990725576877594, -0.017647066991776227, 0.05918873250484467, ...]}  

```

Here's the graph of the resulting pipeline:
![HyDE pipeline implementation flowchart showing prompt builder, generator, adapter, embedder, and hypothetical document embedder components](https://docs.haystack.deepset.ai/img/74f3daa-hyde.png)
This pipeline example turns your query into one embedding.
You can continue and feed this embedding to any [Embedding Retriever](https://docs.haystack.deepset.ai/docs/retrievers#dense-embedding-based-retrievers) to find similar documents in your Document Store.
## Additional References[​](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde#additional-references "Direct link to Additional References")
📚 Article: [Optimizing Retrieval wi

#### Rank 2 | Score: 0.7587 | Chunk: 0 | Document: docs_haystack_deepset_ai__docs__hypothetical-document-embeddings-hyde.md

<!-- source: https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde -->

# Hypothetical Document Embeddings (HyDE)
Enhance the retrieval in Haystack using HyDE method by generating a mock-up hypothetical document for an initial query.
## When Is It Helpful?[​](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde#when-is-it-helpful "Direct link to When Is It Helpful?")
The HyDE method is highly useful when:
  * The performance of the retrieval step in your pipeline is not good enough (for example, low Recall metric).
  * Your retrieval step has a query as input and returns documents from a larger document base.
  * Particularly worth a try if your data (documents or queries) come from a special domain that is very different from the typical datasets that Retrievers are trained on.

## How Does It Work?[​](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde#how-does-it-work "Direct link to How Does It Work?")
Many embedding retrievers generalize poorly to new, unseen domains. This approach tries to tackle this problem. Given a query, the Hypothetical Document Embeddings (HyDE) first zero-shot prompts an instruction-following language model to generate a “fake” hypothetical document that captures relevant textual patterns from the initial query - in practice, this is done five times. Then, it encodes each hypothetical document into an embedding vector and averages them. The resulting, single embedding can be used to identify a nei

#### Rank 3 | Score: 0.7563 | Chunk: 3 | Document: docs_haystack_deepset_ai__docs__hypothetical-document-embeddings-hyde.md

@component.output_types(hypothetical_embedding=List[float])  
    def run(self, documents: List[Document]):  
        stacked_embeddings = array([doc.embedding for doc in documents])  
        avg_embeddings = mean(stacked_embeddings, axis=0)  
        hyde_vector = avg_embeddings.reshape((1, len(avg_embeddings)))  
        return {"hypothetical_embedding": hyde_vector[0].tolist()}  

```

Then, assemble them all into a pipeline:
python
```
from haystack import Pipeline  
  
pipeline = Pipeline()  
pipeline.add_component(name="prompt_builder", instance=prompt_builder)  
pipeline.add_component(name="generator", instance=generator)  
pipeline.add_component(name="adapter", instance=adapter)  
pipeline.add_component(name="embedder", instance=embedder)  
pipeline.add_component(name="hyde", instance=HypotheticalDocumentEmbedder())  
  
pipeline.connect("prompt_builder", "generator")  
pipe

#### Rank 4 | Score: 0.7512 | Chunk: 1 | Document: docs_haystack_deepset_ai__docs__hypothetical-document-embeddings-hyde.md

in the document embedding space from which similar actual documents are retrieved based on vector similarity. As with any other retriever, these retrieved documents can then be used downstream in a pipeline (for example, in a Generator for RAG). Refer to the paper “[Precise Zero-Shot Dense Retrieval without Relevance Labels](https://aclanthology.org/2023.acl-long.99/)” for more details.
![HyDE model architecture diagram showing how GPT generates hypothetical documents from queries in multiple languages, which are then matched with real documents via a Contriever model](https://docs.haystack.deepset.ai/img/2d00628-Untitled_2.png)
## How To Build It in Haystack?[​](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde#how-to-build-it-in-haystack "Direct link to How To Build It in Haystack?")
First, prepare all the components that you would need:
python
```
import os  
from numpy import array, mean  
from typing import List  
  
from haystack.components.generators.openai import OpenAIGenerator  
from haystack.components.builders import PromptBuilder  
from haystack import component, Document  
from haystack.components.converters import OutputAdapter  
from haystack.components.embedders import SentenceTransformersDocumentEmbedder  
  
## We need to ensure we have the OpenAI API key in our environment variables  
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_KEY"  
  
## Initializing standard Haystack components  
generator = OpenAIGenerator(  
    model="gpt-3.5-turbo",  
    generation_kwargs={"n": 5, "temperature":

#### Rank 5 | Score: 0.7232 | Chunk: 2 | Document: docs_haystack_deepset_ai__docs__hypothetical-document-embeddings-hyde.md

"max_tokens": 400},  
)  
prompt_builder = PromptBuilder(  
    template="""Given a question, generate a paragraph of text that answers the question.    Question: {{question}}    Paragraph:""",  
)  
  
adapter = OutputAdapter(  
    template="{{answers | build_doc}}",  
    output_type=List[Document],  
    custom_filters={"build_doc": lambda data: [Document(content=d) for d in data]},  
)  
  
embedder = SentenceTransformersDocumentEmbedder(  
    model="sentence-transformers/all-MiniLM-L6-v2",  
)  
embedder.warm_up()  
  
  
## Adding one custom component that returns one, "average" embedding from multiple (hypothetical) document embeddings  
@component  
class HypotheticalDocumentEmbedde

#### Rank 6 | Score: 0.6979 | Chunk: 0 | Document: docs_haystack_deepset_ai__docs__advanced-rag-techniques.md

<!-- source: https://docs.haystack.deepset.ai/docs/advanced-rag-techniques -->

# Advanced RAG Techniques
This section of documentation talks about advanced RAQ techniques you can implement with Haystack.
Read more about [Hypothetical Document Embeddings (HyDE)](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde),
or check out one of our cookbooks 🧑‍🍳:
  * [Using Hypothetical Document Embedding (HyDE) to Improve Retrieval](https://haystack.deepset.ai/cookbook/using_hyde_for_improved_retrieval)
  * [Query Decomposition and Reasoning](https://haystack.deepset.ai/cookbook/query_decomposition)
  * [Improving Retrieval by Embedding Meaningful Meta

#### Rank 7 | Score: 0.572 | Chunk: 2 | Document: docs_together_ai__docs__how-to-implement-contextual-rag-from-anthropic.md

using quantized small 1-3B models along with prompt caching makes this more feasible. Prompt caching allows key and value matrices corresponding to the document to be cached for future LLM calls.

```python
CONTEXTUAL_RAG_PROMPT = """
Given the document below, we want to explain what the chunk captures in the document.

{WHOLE_DOCUMENT}

Here is the chunk we want to explain:

{CHUNK_CONTENT}

Answer ONLY with a succinct explaination of the meaning of the chunk in the context of the whole document above.
"""
```

```python
from typing import List
import together, os
from together import Together

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = Together(api_key=TOGETHER_API_KEY)


def generate_prompts(document: str, chunks: List[str]) -> List[str]:
    prompts = []
    for chunk in chunks:
        prompt = CONTEXTUAL_RAG_PROMPT.format(
            WHOLE_DOCUMENT=document,
            CHUNK_CONTENT=chunk,
        )
        prompts.append(prompt)
    return prompts


prompts = generate_prompts(pg_essay, chunks)


def generate_context(prompt: str):
    response = client.chat.completions.create(
        model="Qwen/Qwen3.5-9B",
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
    )
    return response.choices[0].message.content
```

```python
contextual_chunks = [
    generate_context(prompts[i]) + " " + chunks[i] for i in range(len(chunks))
]
```

## Vector Index

We will now use `multilingual-e5-large-instruct` to embed the augmented chunks above into a vector index.

```python
from typing import List
import together

#### Rank 8 | Score: 0.5693 | Chunk: 9 | Document: research_trychroma_com__context-rot.md

each chunk using text-embedding-3-large
  3. Use UMAP [[14](https://research.trychroma.com/context-rot#umap)] for dimensionality reduction with the following parameters: n_neighbors=30, min_dist=0.05, n_components=50, random_state=42
  4. Use HDBSCAN [[15](https://research.trychroma.com/context-rot#hdbscan)] to create clusters with the following parameters: min_cluster_size=10, min_samples=15
  5. Get 20 representative chunks for the largest clusters using maximal marginal relevance (MMR)
  6. Manually examine the largest clusters to determine their themes and style

Using this method, we identify writing advice as a common topic for PG essays, often in anecdotal form. For arXiv papers, we identify information retrieval as a common topic, specifically re-ranking.
We write a corresponding question for each topic:
> PG essays: "What was the best writing advice I got from my college classmate?"
> arXiv papers: "Which low-latency reranker is preferred for scientific domains?"
Questions fo

#### Rank 9 | Score: 0.565 | Chunk: 5 | Document: arxiv__2511.22240__pipeline-optimization.md

question generation process follows these steps:

1. Chunk Extraction: Documents are segmented using the configured chunking strategy
2. Prompt Engineering: Each chunk is provided to the LLM with instructions to generate a relevant question
3. Quality Filtering: Generated questions undergo automated quality checks
4. Manual Validation: A subset undergoes human review to ensure quality

This synthetic generation approach has been successfully employed in prior work on information retrieval evaluation [4, 5, 6], demonstrating that LLM-generated queries can serve as effective proxies for real user information needs when properly validated.

# 3.3 Validation and CI/CD Integration

The generated pairs undergo manual validation to ensure quality and remove noise [1]. All pipeline steps are integrated into a CI/CD framework, enabling automatic synthesis and testing whenever the document corpus or models change [1]. This infrastructure supports:

Automated data preprocessing and cleaning Batch question generation with quality control Continuous model evaluation and comparison Version control and reproducibility

The pipeline also supports fine-tuning downstream models on the synthetic data if needed, providing flexibility for iterative improvement. This automated approach ensures that evaluation remains consistent across model updates and enables rapid experimentation.

# 4. EXPERIMENTAL SETUP

# 4.1 Vector Database Configuration

We utilize Milvus as the vector database for all experiments. For most configurations, we employ the H

#### Rank 10 | Score: 0.5535 | Chunk: 12 | Document: arxiv__2506.05176__qwen3-embedding.md

documents along with their role candidates to the prompt. This guides the model in outputting the most suitable role configuration for query generation. Moreover, the prompt incorporates various dimensions such as query type (e.g., keyword, factual, summary, judgment), query length, difficulty, and language. This multidimensional approach ensures the quality and diversity of the synthetic data.

Finally, we create a total of approximately 150 million pairs of multi-task weak supervision training data. Our experiments reveal that the embedding model trained with these synthetic data performs exceptionally well in downstream evaluations, particularly surpassing many previously supervised models in the MTEB Multilingual benchmarks. This m


## Query 7: "What is the required minimum value of ef_construction relative to m when building an HNSW index?"


### dense

#### Rank 1 | Score: 0.7584 | Chunk: 7 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

as is done during search). This process is repeated until reaching our chosen _insertion layer_. Here begins phase two of construction.
The _ef_ value is increased to `efConstruction` (a parameter we set), meaning more nearest neighbors will be returned. In phase two, these nearest neighbors are candidates for the links to the new inserted element _q_  _and_ as entry points to the next layer.
_M_ neighbors are added as links from these candidates — the most straightforward selection criteria are to choose the closest vectors.
After working through multiple iterations, there are two more parameters that are considered when adding links. _M_max_ , which defines the maximum number of links a vertex can have, and _M_max0_ , which defines the same but for vertices in _layer 0_.
![Explanation of the number of links assigned to each vertex and the effect of M, M_max, and M_max0.](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2Fdc5cb11ea197ceb4e1f18214066c8c51526b9af5-1920x1080.png&w=3840&q=75)
Explanation of the number of links assigned to each vertex and the effect of M, M_max, and M_max0.
The stopping condition for insertion is reaching the local minimum in _layer 0_.
## Implementation of HNSW
We will implement HNSW using the Facebook AI Simil

#### Rank 2 | Score: 0.7575 | Chunk: 7 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

During the build, the list is sorted by distance and truncated at a length of _ef_construction_ 's value. Once the value is placed within the graph, this list will be truncated to the length of _m_. The relationship between _ef_construction_ and _m_ is the reason _ef_construction_ is required to be 2x the value of _m_. The larger the value for _ef_construction_ the slower the index build.

What is the best values for _m_ and __ef_construction__? In our tests, we have confirmed the statements from [the original paper](https://arxiv.org/pdf/1603.09320.pdf):

> The only meaningful construction parameter left for the user is M. A reasonable range of M is from 5 to 48. Simulations show that smaller M generally produces better results for lower recalls and/or lower dimensional data, while bigger M is better for high recall and/or high dimensional data.

And for _ef_construction_ :

> Construction speed/index quality tradeoff is controlled via the efConstruction parameter. (…) Further increase of the efConstruction leads to little extra performance but in exchange of significantly longer construction time.

So, long-story short, keep the numbers relatively small because the quality improvement isn't worth the performance hit.

## Query tuning values

### ef_search

This value functions the same as the _ef_construction_ value, except for queries. This is a query-time parameter that limits the number of nearest neighbors maintained in the list. Because of this, _ef_search

#### Rank 3 | Score: 0.725 | Chunk: 1 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

TL;DR

HNSW is cutting edge for all vector based indexing. To build an HNSW index, run something like the following:

```sql
CREATE INDEX ON recipes
USING hnsw (embedding vector_l2_ops)
WITH (m = 4, ef_construction = 10);
```

These indexes will:
  * use approximations (not precision)
  * be more performant than list-based indexes
  * require longer index build times
  * and require more memory

Tradeoffs:
  * Indexes will take longer to build depending on values for _m_ and _ef_construction_. When increased, these values will slow the speed of index build drastically, while not improving performance. Yet, it may increase accuracy of response.
  * To search more than 40 nearest neighbors, increase this `SET hnsw.ef_search = x;` value. Where `x` is the value of nearest neighbors you want to return.
  * Not all queries will work with HNSW. As we said in the [vector performance blog post](https://www.crunchydata.com/blog/pgvector-performance-for-developers), use `EXPLAIN` to ensure your query is using the index. If it is not using the index, simplify your query until it is, then build back to your complexity.

## What is HNSW?

HNSW is short for Hierarchical Navigable Small World. But, HNSW isn't just one algorithm — it's kind of like 3 algorithms in a trench coat. The first algorithm was [first presented in a paper in 2011](https://www.iiis.org/CDs2011/CD2011IDI/ICTA_2011/PapersPdf/CT175ON.pdf). It used graph topology to find the vertex (or element) with the local minimum nearest neighbor. Then, a couple more papers were published, but the [one in 2014

#### Rank 4 | Score: 0.7221 | Chunk: 6 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

through the multi-layer structure of an HNSW graph.
## Graph Construction
During graph construction, vectors are iteratively inserted one-by-one. The number of layers is represented by parameter _L_. The probability of a vector insertion at a given layer is given by a probability function normalized by the _‘level multiplier’ m_L_ , where _m_L = ~0_ means vectors are inserted at _layer 0_ only.
![The probability function is repeated for each layer \(other than layer 0\). The vector is added to its insertion layer and every layer below it.](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2Ff105cb148aae44f77fa7e3df7b7f8c0256bcbec4-1920x980.png&w=3840&q=75)
The probability function is repeated for each layer (other than layer 0). The vector is added to its insertion layer and every layer below it.
The creators of HNSW found that the best performance is achieved when we minimize the overlap of shared neighbors across layers. _Decreasing m_L_ can help minimize overlap (pushing more vectors to _layer 0_), but this increases the average number of traversals during search. So, we use an _m_L_ value which balances both. _A rule of thumb for this optimal value is_  _`1/ln(M)`__[1]_.
Graph construction starts at the top layer. After entering the graph the algorithm greedily traverse across edges, finding the _ef_ nearest neighbors to our inserted vector _q_ — at this point _ef = 1_.
After finding the local minimum, it moves down to the next layer (

#### Rank 5 | Score: 0.718 | Chunk: 12 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

we compare the distribution between our Python implementation and that of Faiss, we see very similar results:
In[12]:
```
chosen_levels = []
rng = np.random.default_rng(12345)
for _ in range(1_000_000):
    chosen_levels.append(random_level(assign_probas, rng))
```

In[13]:
```
np.bincount(chosen_levels)
```

Out[13]:
```
array([968821,  30170,    985,     23,       1],
      dtype=int64)
```

![Distribution of vertices across layers in both the Faiss implementation \(left\) and the Python implementation \(right\).](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2F75658a08c25dabc1405f769c76fd2929c051853b-1920x930.png&w=3840&q=75)
Distribution of vertices across layers in both the Faiss implementation (left) and the Python implementation (right).
The Faiss implementation also ensures that we _always_ have at least one vertex in the highest layer to act as the entry point to our graph.
### HNSW Performance
Now that we’ve explored all there is to explore on the theory behind HNSW and how this is implemented in Faiss — let’s look at the effect of different parameters on our recall, search and build times, and the memory usage of each.
We will be modifying three parameters: `M`, `efSearch`, and `efConstruction`. And we will be indexing the Sift1M dataset, which you can download and prepare using [this script](https://gist.github.com/jamescalam/a09a16c17b677f2cf9c019114711f3bf).
As we did before, we initialize our index like so:
```
index = faiss.IndexHNSWFlat(d, M)
```

The two other parameters, `

#### Rank 6 | Score: 0.7145 | Chunk: 6 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

and the same algorithm described above to place the value within the graph. When building, each point needs to be on the graph, thus each point needs to connect to the nearest points it can find. On large datasets, it would be impossible to scan all rows and connect them in a graph to their closet neighbors within a reasonable time — thus use the following limits to constrain the build process.

_m_ is the number of connections to nearest neighbors (vertices) made per point per layer within the index. When building the graph indexes, the database is seeking nearest neighbors to build out the vertices, and _m_ is the maximum count for that layer. By limiting the number of connections, the index limits the number of connections between points at that layer. Thus, the build time improves with smaller values of _m_. All you have to know is that in the original paper, as _m_ approaches infinity, it creates "graphs with polylogarithmic complexity".

### ef_construction

_ef_construction_ is candidate list-size used during index build. Above, in the illustration, I was telling you to keep a list of 10 closet, and discard any outside those 10. During index build, the database walks through each record placing that record's values within the index structure. Later records use the index that is currently built to more quickly position the currently processed record. As the index build process moves through the layers, it keeps a list of closest values from the prio

#### Rank 7 | Score: 0.6925 | Chunk: 4 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

HNSW thesis, you can go back and read the [`HnswSearchLayer` function](https://github.com/pgvector/pgvector/blob/a8e257e1f1aaf4c8c9019dcf4ac41bea98a41fff/src/hnswutils.c#L546) for fun. Additionally, see how the [HNSW implementation calculates and caches distances](https://github.com/pgvector/pgvector/blob/a8e257e1f1aaf4c8c9019dcf4ac41bea98a41fff/src/hnswutils.c#L674)

## The advantages of HNSW

HNSW is much faster to query than the traditional list-based query algorithm. This performance is because the use of graphs and layers reduces the number of distance comparisons that are being run. And because fewer distance comparisons, we can run more queries concurrently as well.

## Tradeoffs for HNSW

The most obvious trade off for HNSW indexes is that they are approximations. But, this is no different than any existing vector index, so aside from a table-scan of comparisons. If you need absolutes, it is best to run the non-indexed query that calculates distance for each row.

The second trade-off for HNSW indexes is they can be expensive to build. The two largest contributing variables for these indexes are: size of the dataset and complexity of the index. For moderate datasets of > 1M rows, it can take 6 minutes to build some of the simplest of indexes. During that time, the database will use all the R

#### Rank 8 | Score: 0.6908 | Chunk: 15 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

and search time when searching for only one query. When using lower M values, the search time remains almost unchanged for different efConstruction values.
That all looks great, but what about the memory usage of the HNSW index? Here things can get slightly _less_ appealing.
![Memory usage with increasing values of M using our Sift1M dataset. efSearch and efConstruction have no effect on the memory usage.](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2Fe04d23ccd76d8bdc568542bebe75a75e7d36a21e-1480x1050.png&w=3840&q=75)
Memory usage with increasing values of M using our Sift1M dataset. efSearch and efConstruction have no effect on the memory usage.
Both `efConstruction` and `efSearch` do not affect index memory usage, leaving us only with `M`. Even with `M` at a low value of `2`, our index size is already above 0.5GB, reaching almost 5GB with an `M` of `512`.
So although HNSW produces incredible performance, we need to weigh that against high memory usage and the inevitable high infrastructure costs that this can produce.
#### Improving Memory Usage and Search Speeds
HNSW is not the best index in terms of memory utilization. However, if this is important and using [another index](https://www.pinecone.io/learn/series/faiss/vector-indexes/) isn’t an option, we can improve it by compressing our vectors using [product quantization (PQ)](https://www.pinecone.io/learn/series/faiss/product-quantization/). Using PQ will reduce recall and increase

#### Rank 9 | Score: 0.6883 | Chunk: 8 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

Search (Faiss) library, and test different construction and search parameters and see how these affect index performance.
To initialize the HNSW index we write:
In[2]:
```
# setup our HNSW parameters
d = 128  # vector size
M = 32

index = faiss.IndexHNSWFlat(d, M)
print(index.hnsw)
```

Out[2]:
```
<faiss.swigfaiss.HNSW; proxy of <Swig Object of type 'faiss::HNSW *' at 0x7f91183ef120> >

```

With this, we have set our `M` parameter — the number of neighbors we add to each vertex on insertion, but we’re missing _M_max_ and _M_max0_.
In Faiss, these two parameters are set automatically in the `set_default_probas` method, called at index initialization. The _M_max_ value is set to `M`, and _M_max0_ set to `M*2` (find further detail in the [notebook](https://github.com/pinecone-io/examples/blob/master/learn/search/faiss-ebook/hnsw-faiss/hnsw_faiss.ipynb)).
Before building our `index` with `index.add(xb)`, we will find that the number of layers (or _levels_ in Faiss) are not set:
In[3]:
```
# the HNSW index starts with no levels
index.hnsw.max_level
```

Out[3]:
```
-1
```

In[4]:
```
# and levels (or layers) are empty too
levels = faiss.vector_to_array(index.hnsw.levels)
np.bincount(levels)
```

Out[4]:
```
array([], dtype=int64)
```

If we go ahead and build the index, we’ll find that both of these para

#### Rank 10 | Score: 0.6855 | Chunk: 5 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

it has available in `maintenance_work_mem`, while redlining the CPU. Long-story short, test it on a production-size dataset before embarking.

The third trade-off for HNSW indexes is that they are sizable — the index for 1M rows of AI embeddings can be 8GB or larger. For performance reasons, you'll want all of this index in memory. HNSW is fast because it uses resources.

## Index tuning values

In the illustrations above, we showed how the index progressed through executing a query. But how are these indexes built? Think of index build for HNSW as a massive query that pre-calculates a larger number of distances. Index tuning is all about how the database limits the algorithms to build those indexes. Go back to the initial illustration and ask the question "how do we build an HNSW index from the data set?"

Points are saved to the top and middle layer based on probability: 1% are saved to the top layer, and 5% are saved to the middle layer. To build the index, the database loops through all values. As it loops to the next value, the algorithm uses the previously built ind


## Query 8: "Around what embedding dimension does Matryoshka Representation Learning hit a sweet spot for Qwen3-Embedding-0.6B on retrieval quality vs storage cost?"


### dense

#### Rank 1 | Score: 0.8639 | Chunk: 0 | Document: medium.com__yashasvimantha_matryoshka-embeddings-finding-the-sweet-spot-between-embedding-size-and-retrieval-quality-for.md

<!-- source: https://medium.com/@yashasvimantha/matryoshka-embeddings-finding-the-sweet-spot-between-embedding-size-and-retrieval-quality-for-e9d8d7e4278e -->

# **Matryoshka Embeddings — Finding the sweet spot between Embedding size and retrieval quality for Qwen3 0.6b**

By Yashasvi Mantha · 3 min read · Jun 28, 2025

We all know about Matryoshka embeddings. If not, its basically the way an embeddings model is trained where we can truncate the embeddings to a given size and still have not so much of a quality drop. There are a lot of advantages of truncating the embeddings to a lower size. One of them being; its cheaper to store the vectors. This becomes important as we scale things up for search. When we have a model that gives out a vector of size `1024` and have to store millions of documents that cost of storing those can add up quite considerably. Especially when we have to store the vectors in memory for low latency. So Matryoshka Representation learning can help us bring down storage costs along with having a minimal quality drop.
But the question, how much smaller can we go? Obviously just like most things in life, there is a trade-off between quality and compute/storage. This blog is about answering that.
Choosing a model (that provides a outputs size of 1024 for example); how small can I slice to optimize trade-off?
Heavily inspired from the [Hybrid Search](https://docs.vespa.ai/en/tutorials/hyb

#### Rank 2 | Score: 0.7674 | Chunk: 2 | Document: medium.com__yashasvimantha_matryoshka-embeddings-finding-the-sweet-spot-between-embedding-size-and-retrieval-quality-for.md

to YashasviMantha/matryoshka-analysis development by creating an account on GitHub. github.com ](https://github.com/YashasviMantha/matryoshka-analysis?source=post_page-----e9d8d7e4278e---------------------------------------)
## **Results:**

![](https://miro.medium.com/v2/resize:fit:700/1*i928yhtoyZxEEeNOrwxgkg.png)
Graph for the performance trade off

**Bigger is not always better:**

Obviously, if we dont slice the embeddings at all; we see the higest score. But around the 100–120 range the performance actually goes down. So if someone was considering a 120 size embeddings, it would be better to go lower to 100 than 120.
Similarly the quality doesnt always increase with dimensions. 762–766 provides better retrieval than 768–774. The increase is always not linear. Or maybe I am being a bit too picky?
**The sweet spot**
Now, it depends on the retrieval use case but for me, its seems like is around the early 400 range is a good trade of

#### Rank 3 | Score: 0.7039 | Chunk: 1 | Document: medium.com__yashasvimantha_matryoshka-embeddings-finding-the-sweet-spot-between-embedding-size-and-retrieval-quality-for.md

post from the vespa team. I thought, lets take a small dataset, brute force the evaluation with different embeddings size and find out.
So I did exactly that in [this notebook](https://github.com/YashasviMantha/matryoshka-analysis/blob/main/analysis.ipynb). And I wanted to test out the most recent new [Qwen3 Embeddings 0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) model.
The testing set I used was the _BEIR_ slice of _nfcorpus_. I calculated the embeddings at full capacity of 1024. And tested right from 1 to 1024 embeddings size on the test set; with my evaluation method to be _nDCG@10_. While I do realize the model isn't designed to go smaller than _32_ ; I was curious on the performance in smaller sizes.
The results were quite surprising.
Some things to keep in mind before getting to the results:
> - The test set is pretty small but a well respected benchmark.
> - `nDCG@10` may change with different HSNW configurations. I used chromaDB for the graph.
> Ranking is a very data specific task. Similar results might not be reproducible with a different dataset.
Source code present in the github repo:
## [GitHub - YashasviMantha/matryoshka-analysi

#### Rank 4 | Score: 0.6851 | Chunk: 3 | Document: medium.com__yashasvimantha_matryoshka-embeddings-finding-the-sweet-spot-between-embedding-size-and-retrieval-quality-for.md

I say this because the incremental gain above 450 might be too costly in a resource constrained environment.
Also above the `650` the gain becomes very small. Almost next to nothing.
**Drilling Down**
If we wanted to go crazy and also check how its behaving above `650` in a more granular way:

![](https://miro.medium.com/v2/resize:fit:700/1*Ng39ZMHRO6EAvM4rxkcCOw.png)
Zooming in the above graph

Again, we are looking into numbers that are very close to each other.
## **Finally**
The goal here was not to find the perfect embedding size; but to understand if the quality reduction was considerable on size reduction. We can almost half the embedding size and not make the retrieval quality really bad. Which is huge beca

#### Rank 5 | Score: 0.6773 | Chunk: 5 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

Qwen-3-Embedding-0.6B: 0.6B parameters, 1024 dimensions  
- Qwen-3-Embedding-4B: 4B parameters, 2560 dimensions  
- Qwen-3-Embedding-8B: 8B parameters, 4096 dimensions  
- BGE-M3: 0.6B parameters, serving as the primary baseline
Additional baselines include NV-Embed-v2, multilingual-e5-large-instruct, and proprietary APIs (Gemini, text-embedding-3-large) for context.
4.3 Implementation Details
All models are evaluated using the standardized mteb evaluation framework. For reranking experiments, we retrieve top-100 candidates using the embedding model and subsequently apply reranking models for refinement. ONNX quantization experiments follow the methodology described in Tanskanen (2024), using dynamic quantization to reduce model size and latency.
## 5. Results and Analysis
### 5.1 Main Performance Comparison
5.1.1 MTEB English v2 Benchmark
![](https://miro.medium.com/v2/resize:fit:1000/1*TJdz0CJaB1bdBWa6vj5hRg.png)
Key Observations:  
- Qwen-3-Embedding-0.6B outperforms BGE-M3 by 18.7% on MTEB English tasks (70.70 vs 59.56) despite identical parameter count  
- The performance gap extends across all task categories, with particularly strong improvements in retrieval (+11.36 points) and clustering tasks  
- Scaling to 8B parameters yields only marginal gains over the 4B model (75.22 vs 74.60), suggesting diminishing returns for English tasks
5.1.2 Multilingual and Code Retrieval
![](https://miro.medium.com/v2/resize:fit:1000/1*4-Sv9GwHdrnf2C6w-lmbCA.png)
Analysis:  
- Qwen-3-Embedding-0.6B demonstrates consistent multilingual superi

#### Rank 6 | Score: 0.6725 | Chunk: 7 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

reduces from 2272MB to 571MB post-quantization, with 20% memory usage reduction.
For Qwen-3–0.6B, preliminary testing shows similar optimization potential, though official quantization results are pending publication. The larger Qwen-3 models (4B/8B) require substantially more computational resources, necessitating careful consideration of quality-cost tradeoffs.
5.3.2 Latency and Throughput
![](https://miro.medium.com/v2/resize:fit:549/1*7ut1ypBjLHDDOqbLjUTEfg.png)
Latency measured on AWS c5.2xlarge for 512-token inputs. BGE-M3 data from Tanskanen (2024)
### 5.4 Ablation and Feature Analysis
Key factors contributing to Qwen-3’s superior performance include:
1. Training Data Quality: Extensive synthetic data generation targeting hard negative examples  
2. Architecture Scaling: Efficient parameter allocation across transformer layers  
3. Task Diversity: Training on 80+ languages versus BGE-M3’s more limited multilingual corpus  
4. Instruction Tuning: Explicit instruction-aware training improves zero-shot task performance
BGE-M3’s strength lies in its hybrid retrieval capability, enabling flexible combination of dense and sparse signals — though our results indicate dense-only Qwen-3 models still outperform the hybrid approach on most tasks.
## 6. Discussion
### 6.1 Model Selection Guidelines
Based on our comparative analysis, we propose the following selection criteria:
Choose Qwen-3 embeddings when:  
- Maximum retrieval accuracy is prioritized  
- Multilingual performance across 80+ languages is required  
- Computational resources support models >1B parame

#### Rank 7 | Score: 0.6578 | Chunk: 4 | Document: arxiv__2506.05176__qwen3-embedding.md

of the Qwen3 backbone models (including 0.6B, 4B, and 8B), we ultimately trained three text embedding models and three text reranking models. To facilitate their application in downstream tasks, the Qwen3 Embedding series supports several practical features, such as flexible dimension representation for embedding models and customizable instructions for both embedding and reranking models.

We evaluate the Qwen3 Embedding series across a comprehensive set of benchmarks spanning multiple tasks and domains. Experimental results demonstrate that our embedding and reranking models achieve state-of-the-art performance, performing competitively against leading proprietary models in several retrieval tasks. For example, the flagship model Qwen3-8B-Embedding attains a score of 70.58 on the MTEB Multilingual benchmark (Enevoldsen et al., 2025) and 80.68 on the MTEB Code benchmark (Enevoldsen et al., 2025), surpassing the previous state-of-the-art proprietary embedding model, Gemini-Embedding (Lee et al., 2025b). Moreover, our reranking model delivers competitive results across a range of retrieval tasks. The Qwen3-Reranker-0.6B model exceeds previously top-performing models in numerous retrieval tasks, while the larger Qwen3-Reranker-8B model demonstrates even superior performance, improving ranking results by 3.0 points over the 0.6B model across multiple tasks. Furthermore, we include a constructive ablation study to elucidate the key factors contributing to the superior performance of the Qwen3 Embedding series, providi

#### Rank 8 | Score: 0.652 | Chunk: 8 | Document: arxiv__2511.22240__pipeline-optimization.md

testing was not performed as all models were evaluated on identical test sets, making relative comparisons directly interpretable.

# 5. RESULTS

# 5.1 Embedding Model Comparison

Table 1 presents the performance of each embedding model using 2000-character chunking and HNSW indexing. The results demonstrate that higher-dimensional models dramatically outperform smaller alternatives.

TABLE I

| Mode1 | Dim | Acc@3 | NDCG@3 | Acc@5 | NDCG@5 | Acc@10 | NDCG@10 |
|---|---|---|---|---|---|---|---|
| all-mpnet-base-v2 | 768 | 0.268 | 0.229 | 0.31 | 0.246 | 0.37 | 0.266 |
| bge-base-en-v1.5 | 768 | 0.24 | 0.205 | 0.276 | 0.22 | 0.32 | 0.234 |
| bge-large-en-v1.5 | 1024 | 0.3 | 0.26 | 0.343 | 0.278 | 0.396 | 0.295 |
| gte-base-en-v1.5 | 768 | 0.389 | 0.338 | 0.434 | 0.357 | 0.492 | 0.376 |
| gte-large-en-v1.5 | 1024 | 0.412 | 0.356 | 0.462 | 0.378 | 0.522 | 0.396 |
| Qwen3-Embed-0.6B | 1024 | 0.516 | 0.461 | 0.562 | 0.48 | 0.611 | 0.496 |
| Qwen3-Embed-4B | 2560 | 0.556 | 0.503 | 0.601 | 0.522 | 0.647 | 0.537 |
| Qwen3-Embed-8B | 4096 | 0.571 | 0.516 | 0.612 | 0.533 | 0.663 | 0.549 |

Key Findings:

Qwen3-Embedding-8B (4096-dim) achieves Top-3 accuracy of 0.571 and NDCG@3
of 0.516
GTE-large (1024-dim) scores 0.412 and 0.356 for the same metrics
Even Qwen3-Embedding-4B (2560-dim) outperforms all 768/1024-dimensional
models (Accuracy \mathcal { @ 3 = 0.556 } versus 0.412)
Increasing embedding dimensionality yields approximately 10–15 percentage point
improvements in accuracy

The performance gap between model families is substantial. The Qwen3 series consistently outperforms 

#### Rank 9 | Score: 0.6452 | Chunk: 8 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

- Reranking pipelines need strong performance gains
Choose BGE-M3 when:  
- Deployment constraints require aggressive optimization (ONNX quantization)  
- Hybrid retrieval (dense + sparse) is architecturally beneficial  
- Processing extremely long documents (>4k tokens) is common  
- Model size must be minimized without major accuracy degradation
### 6.2 Practical Deployment Considerations
For production systems at Nakakita Seisakusho Co., Ltd. and similar industrial environments, several factors merit consideration:
1. Resource Provisioning: Qwen-3–0.6B requires ~1.2GB VRAM (FP32) versus BGE-M3’s ~0.9GB, but delivers measurably better accuracy  
2. Quantization Strategy: Both models support ONNX quantization, though BGE-M3 has more mature tooling  
3. Chunking Strategy: Performance remains stable up to 4k tokens for Qwen-3, but BGE-M3’s native 8k context may benefit long-document applications  
4. Vector Storage: Qwen-3–0.6B’s 1024-dim vectors require 33% more storage than BGE-M3’s 768-dim output, impacting large-scale deployments
### 6.3 Limitations and Future Work
This study has several limitations warranting future investigation:
- Language Coverage: While Qwen-3 supports 80+ languages, performance on low-resource languages remains underexplored  
- Domain Specificity: Neither model’s performance on specialized technical domains (e.g., manufacturing, engineering documentation typical at Nakakita Seisakusho) has been systematically evaluated  
- Dynamic Quantization Impact: Qwen-3 quantization effects require empirical validation to matc

#### Rank 10 | Score: 0.6431 | Chunk: 9 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

established optimization pathways  
- Long-Context Evaluation: Performance beyond 4k tokens, where BGE-M3’s architecture may provide advantages, needs deeper analysis
Future research should focus on:  
1. Domain-adapted evaluation for industrial applications  
2. Direct comparison of quantized model variants  
3. Cost-benefit analysis across varying retrieval scales (1M to 1B documents)  
4. Integration patterns with reranking and hybrid retrieval systems
## 7. Thoughts
This comparative study demonstrates that the Qwen-3 embedding series significantly outperforms BGE-M3 across standardized benchmarks, achieving 18.7% higher accuracy on MTEB English and 8.0% better multilingual performance at equivalent 0.6B parameter scales. The Qwen-3–8B model establishes new state-of-the-art results on multilingual and code retrieval tasks, surpassing proprietary alternatives.
However, BGE-M3 maintains compelling advantages in deployment flexibility, particularly through mature ONNX optimization pathways achieving 3x inference speedup with minimal accuracy degradation. For organizations prioritizing computational efficiency and hybrid retrieval capabilities, BGE-M3 remains a viable option.
For data scientists and engineers at Nakakita Seisakusho Co., Ltd. implementing multilingual RAG systems, we recommend Qwen-3-Embedding-0.6B as the default choice, scaling to Qwen-3–4B for high-accuracy requirements. BGE-M3 should be reserved for scenarios demanding extreme optimization or native long-context processing. Our analysis provides empirical fo


## Query 9: "What are the tradeoffs between cross-encoder rerankers and bi-encoder retrievers in a two-stage retrieval pipeline?"


### dense

#### Rank 1 | Score: 0.6804 | Chunk: 12 | Document: arxiv__2511.22240__pipeline-optimization.md

due to higher-dimensional distance calculations.

The trade-off between accuracy gains and computational overhead must be carefully considered in production deployments. For latency-sensitive applications, GTE-large (1024-d) combined with reranking may provide an optimal balance, achieving 0.506 Top-3 accuracy with lower computational cost than Qwen3-8B.

# 6.2 Neural Reranking Benefits

Incorporating neural re-rankers provides substantial accuracy improvements. For example, adding the BGE cross-encoder to the GTE-large pipeline increases Acc@3 from 0.412 to 0.506—a gain of approximately 9.4 percentage points. The MiniLM reranker similarly enhances top-K accuracy across all K values.

This finding indicates that optimal pipelines should employ semantic search for high-recall initial retrieval, followed by learned re-rankers for precision refinement. The two-stage approach leverages the complementary strengths of bi-encoders (efficiency) and cross-encoders (accuracy).

Interestingly, reranking bridges approximately half the performance gap between 2000-character and 512-character chunking strategies (comparing 0.4120 . 506 versus 0.460), suggesting that re-rankers can partially compensate for suboptimal chunking configurations. This finding has practical implications: systems with existing coarse-grained chunking can achieve significant improvements simply by adding a reranking stage.

# 6.3 Chunking Granularity Effects

Finer-grained chunking consistently improves performance

#### Rank 2 | Score: 0.6656 | Chunk: 7 | Document: arxiv__2511.22240__pipeline-optimization.md

coherence while allowing variable lengths.

# 4.3 Reranking Pipeline

For reranking experiments, we retrieve the top-10 hits from the initial vector search and apply a cross-encoder reranker. We test two reranking models:

bge-reranker-large: A BERT-based cross-encoder trained for passage reranking [20]
ms-marco-MiniLM-L-6-v2: A lightweight cross-encoder trained on MS MARCO dataset [17]

Reranking is disabled for baseline configurations to establish performance without second-stage refinement. The reranking process takes the original query and each of the top-10 retrieved passages, computing a relevance score through the crossencoder. Passages are then re-ordered according to these scores.

# 4.4 Evaluation Protocol

Each configuration is evaluated by computing:

Top-K Accuracy at K \in \{ 3 , 5 , 10 \} NDCG at K \in \{ 3 , 5 , 10 \}

Metrics are averaged over the entire test set (11,975 query-chunk pairs) to provide robust performance estimates. Statistical signific

#### Rank 3 | Score: 0.6573 | Chunk: 10 | Document: arxiv__2511.22240__pipeline-optimization.md

advantages in preserving discourse coherence and may perform better on queries requiring contextual understanding.

# 5.3 Reranking Results

Table 3 demonstrates that neural reranking substantially enhances retrieval quality. The combination of semantic search and cross-encoder reranking achieves the highest accuracy in our experiments.

# TABLE III

# EFFECT OF RERANKING ON EMBEDDINGS

| Embedding | Reranker | Acc@3 | NDCG@3 | Acc@5 | NDCG@5 | Acc@10 | NDCG@10 |
|---|---|---|---|---|---|---|---|
| BGE-large(1024-d) | None | 0.300 | 0.260 | 0.343 | 0.278 | 0.396 | 0.295 |
| BGE-large(1024-d) | BGE-reranker | 0.387 | 0.368 | 0.393 | 0.370 | 0.396 | 0.371 |
| GTE-large(1024-d) | None | 0.412 | 0.356 | 0.462 | 0.378 | 0.522 | 0.396 |
| GTE-large(1024-d) | MiniLM | 0.480 | 0.442 | 0.504 | 0.452 | 0.522 | 0.457 |
| GTE-large(1024-d) | BGE-reranker with2000 characters | 0.506 | 0.480 | 0.516 | 0.484 | 0.522 | 0.486 |
| GTE-large(1024-d) | BGE-reranker with512 characters | 0.527 | 0.502 | 0.539 | 0.507 | 0.544 | 0.509 |
| GTE-large(1024-d) | BGE(Semantic) | 0.503 | 0.472 | 0.524 | 0.481 | 0.553 | 0.490 |

# Key Findings:

Adding BGE cross-encoder to GTE-large pipeline raises Acc @ 3 from 0.412 to 0.506
(9.4 percentage point gain)
MiniLM reranker improves \operatorname { A c c } @ 3 to 0.480, demonstrating consistent gains
Combining

#### Rank 4 | Score: 0.6425 | Chunk: 3 | Document: arxiv__2511.22240__pipeline-optimization.md

as meeting transcripts are segmented into chunks before embedding. We compare recursive chunking strategies with fixed sizes of 2000 or 512 characters against a service-based semantic chunking method. Service-based semantic chunking leverages natural language understanding to identify coherent semantic boundaries, creating variable-length segments that respect topical and discourse structure.

Previous work has shown that chunk size significantly impacts retrieval quality [1, 2, 3]. Smaller fixed-size chunks often yield queries more focused on specific topics, while semantic chunking aims to preserve contextual coherence [8, 9]. Both approaches can improve retrieval accuracy and reduce noise.

# 2.3 Neural Reranking

Beyond raw embedding similarity, we experiment with neural re-rankers.

Specifically, we employ cross-encoder models such as bge-reranker-large and msmarco-MiniLM-L-6-v2 to reorder the top-N search results. Cross-encoders process query-document pairs jointly, enabling fine-grained interaction modeling that biencoders cannot capture [17, 23].

These models re-score candidate passages given the query, significantly improving precision by considering fine-grained semantic relationships [10, 11]. The two-stage retrieval paradigm—fast bi-encoder retrieval followed by accurate cross-encoder reranking—has become standard prac

#### Rank 5 | Score: 0.6348 | Chunk: 11 | Document: www_anthropic_com__news__contextual-retrieval.md

reranking adds an extra step at runtime, it inevitably adds a small amount of latency, even though the reranker scores all the chunks in parallel. There is an inherent trade-off between reranking more chunks for better performance vs. reranking fewer for lower latency and cost. We recommend experimenting with different settings on your specific use case to find the right balance.
## Conclusion
We ran a large number of tests, comparing different combinations of all the techniques described above (embedding model, use of BM25, use of contextual retrieval, use of a reranker, and total # of top-K results retrieved), all across a variety of different dataset types. Here’s a summary of what we found:
  1. Embeddings+BM25 is better than embeddings on their own;
  2. Voyage and Gemini have the best embeddings of the ones we tested;
  3. Passing the top-20 chunks to the model is more effective than just the top-10 or top-5;
  4. Adding context to chunks improves retrieval accuracy a lot;
  5. Reranking is better than no reranking;
  6. **All these benefits stack** : to maximize performance improvements, we can combine contextual embeddings (from Voyage or Gemini) with contextual BM25, plus a reranking step, and adding the 20 chunks to the prompt.

We encourage all developers working with knowledge bases to use [our cookbook](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide) to experiment with these approaches to unlock new levels of performance.
## Appendix

#### Rank 6 | Score: 0.6348 | Chunk: 11 | Document: www_anthropic_com__engineering__contextual-retrieval.md

reranking adds an extra step at runtime, it inevitably adds a small amount of latency, even though the reranker scores all the chunks in parallel. There is an inherent trade-off between reranking more chunks for better performance vs. reranking fewer for lower latency and cost. We recommend experimenting with different settings on your specific use case to find the right balance.
## Conclusion
We ran a large number of tests, comparing different combinations of all the techniques described above (embedding model, use of BM25, use of contextual retrieval, use of a reranker, and total # of top-K results retrieved), all across a variety of different dataset types. Here’s a summary of what we found:
  1. Embeddings+BM25 is better than embeddings on their own;
  2. Voyage and Gemini have the best embeddings of the ones we tested;
  3. Passing the top-20 chunks to the model is more effective than just the top-10 or top-5;
  4. Adding context to chunks improves retrieval accuracy a lot;
  5. Reranking is better than no reranking;
  6. **All these benefits stack** : to maximize performance improvements, we can combine contextual embeddings (from Voyage or Gemini) with contextual BM25, plus a reranking step, and adding the 20 chunks to the prompt.

We encourage all developers working with knowledge bases to use [our cookbook](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide) to experiment with these approaches to unlock new levels of performance.
## Appendix

#### Rank 7 | Score: 0.6298 | Chunk: 10 | Document: www_anthropic_com__engineering__contextual-retrieval.md

chunks (we used the top 20);
  4. Pass the top-K chunks into the model as context to generate the final result.

![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F8f82c6175a64442ceff4334b54fac2ab3436a1d1-3840x2160.png&w=3840&q=75)_Combine Contextual Retrieva and Reranking to maximize retrieval accuracy._
### Performance improvements
There are several reranking models on the market. We ran our tests with the [Cohere reranker](https://cohere.com/rerank). Voyage[ also offers a reranker](https://docs.voyageai.com/docs/reranker), though we did not have time to test it. Our experiments showed that, across various domains, adding a reranking step further optimizes retrieval.
Specifically, we found that Reranked Contextual Embedding and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 67% (5.7% → 1.9%).
![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F93a70cfbb7cca35bb8d86ea0a23bdeeb699e8e58-3840x2160.png&w=3840&q=75)_Reranked Contextual Embedding and Contextual BM25 reduces the top-20-chunk retrieval failure rate by 67%._
#### Cost and latency considerations
One important consideration with reranking is the impact on latency and cost, especially when reranking a large number of chunks. Beca

#### Rank 8 | Score: 0.6298 | Chunk: 10 | Document: www_anthropic_com__news__contextual-retrieval.md

chunks (we used the top 20);
  4. Pass the top-K chunks into the model as context to generate the final result.

![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F8f82c6175a64442ceff4334b54fac2ab3436a1d1-3840x2160.png&w=3840&q=75)_Combine Contextual Retrieva and Reranking to maximize retrieval accuracy._
### Performance improvements
There are several reranking models on the market. We ran our tests with the [Cohere reranker](https://cohere.com/rerank). Voyage[ also offers a reranker](https://docs.voyageai.com/docs/reranker), though we did not have time to test it. Our experiments showed that, across various domains, adding a reranking step further optimizes retrieval.
Specifically, we found that Reranked Contextual Embedding and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 67% (5.7% → 1.9%).
![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F93a70cfbb7cca35bb8d86ea0a23bdeeb699e8e58-3840x2160.png&w=3840&q=75)_Reranked Contextual Embedding and Contextual BM25 reduces the top-20-chunk retrieval failure rate by 67%._
#### Cost and latency considerations
One important consideration with reranking is the impact on latency and cost, especially when reranking a large number of chunks. Beca

#### Rank 9 | Score: 0.6158 | Chunk: 9 | Document: Fusion_Functions_Hybrid_Retrieval.md

do not capture the semantic similarity between queries and documents, which may be an important signal indicative of relevance. It has been shown that both of these issues can be remedied by Transformer-based [38] pre-trained language models such as BERT [8]. Applied to the ranking task, such models [25, 27–29] have advanced the state of the art dramatically on benchmark datasets [26].

The computationally intensive inference of these deep models often renders them too inefficient for first-stage retrieval, however, making them more suitable for re-ranking stages. But by cleverly disentangling the query and document transformations into the so-called dual-encoder architecture, where, in the resulting design, the “embedding” of a document can be computed independently of queries, we can pre-compute document vectors and store them offline. In this way, we substantially reduce the computational cost during inference as it is only necessary to obtain the vector representation of the query during inference. At a high level, these models project queries and documents onto a low-dimensional vector space where semantically similar points stay closer to each other. By doing so, we transform the retrieval problem to one of similarity search or approximate nearest neighbor search—the k nearest neighbors to a query vector are the desired top- k document

#### Rank 10 | Score: 0.6112 | Chunk: 0 | Document: docs_voyageai_com__docs__reranker.md

<!-- source: https://docs.voyageai.com/docs/reranker -->

# Rerankers
A reranker, given a query and many documents, returns the (ranks of) relevancy between the query and documents. The documents oftentimes are the preliminary results from an embedding-based retrieval system, and the reranker refines the ranks of these candidate documents and provides more accurate relevancy scores.
Unlike [embedding](https://docs.voyageai.com/docs/embeddings) models that encode queries and documents separately, rerankers are [cross-encoders](https://www.sbert.net/examples/applications/cross-encoder/README.html) that jointly process a pair of query and document, enabling more accurate relevancy prediction. Thus, it is a common practice to apply a reranker on the top candidates retrieved with embedding-based search (or with lexical search algorithms such as [BM25](https://en.wikipedia.org/wiki/Okapi_BM25) and [TF-IDF](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)).
# 
Model Choices
[](https://docs.voyageai.com/docs/reranker#model-choices)
Voyage currently provides the following reranker models:
Model | Context Length (tokens) | Description  
---|---|---  
`rerank-2.5` | 32,000 | Our generalist reranker optimized for quality with instruction-following and multilingual support. See [blog post](https://blog.voyageai.com/2025/08/11/rerank-2-5) for details.  
`rerank-2.5-lite` | 32,000 | Our generalist reranker optimized for both latency and quality with instruction-following and multilingual support. See [blog post](https://blog.voyageai.com/2025/08/11/rerank-2-5) for deta


## Query 10: "How does hybrid search combining dense and sparse retrieval improve retrieval quality compared to using either alone, especially for out-of-domain queries?"


### dense

#### Rank 1 | Score: 0.6574 | Chunk: 65 | Document: Fusion_Functions_Hybrid_Retrieval.md

2020. Dense passage retrieval for open-domain question answering. In Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP’20).
[14] Saar Kuzi, Mingyang Zhang, Cheng Li, Michael Bendersky, and Marc Najork. 2020. Leveraging semantic and lexical matching to improve the recall of document retrieval systems: A hybrid approach. ar Xiv:cs.IR/2010.01195 (2020).
[15] Hang Li, Shuai Wang, Shengyao Zhuang, Ahmed Mourad, Xueguang Ma, Jimmy Lin, and Guido Zuccon. 2022. To interpolate or not to interpolate: PRF, dense and sparse retrievers. In Proceedings of the 45th International ACM SIGIR Conference on Research and Development in Information Retrieval. 2495–2500.
[16] Jimmy Lin, Rodrigo Nogueira, and Andrew Yates. 2021. Pretrained Transformers for text ranking: BERT and beyond. ar Xiv:cs.IR/2010.06467 (2021).
[17] Tie-Yan Liu. 2009. Learning to rank for information retrieval. Foundations and Trends in Information Retrieval 3, 3 (2009), 225–331.
[18] Yi Luan, Jacob Eisenstein, Kristina Toutanova, and Michael Collins. 2021. Sparse, dense, and attentional representations for text retrieval. Transactions of the Association for Computational Linguistics 9 (2021), 329–345.
[19] Ji Ma, Ivan Korotkov, Keith Hall, and Ryan T. Mc Donald. 2020. Hybrid first-stage retrieval models for biomedical literature. In Proceedings of the Conference and Labs of the Evaluation Forum (CLEF’20).
[20] Xueguang Ma, Kai Sun, Ronak Pradeep, and Jimmy J. Lin. 2021. A replication study of dense

#### Rank 2 | Score: 0.6551 | Chunk: 3 | Document: Fusion_Functions_Hybrid_Retrieval.md

recent works [5, 13, 14, 19, 20, 42] began exploring methods to fuse together lexical and semantic retrieval: for a query q and ranked lists of documents R_L E X and R_S_{ E M } retrieved separately by lexical and semantic search systems respectively, the task is to construct a final ranked list R_F U S I O N so as to improve retrieval quality. This is often referred to as hybrid search.

It is becoming increasingly clear that hybrid search does indeed lead to meaningful gains in retrieval quality, especially when applied to out-of-domain datasets [5, 40]—settings in which the semantic retrieval component uses a model that was not trained or fine-tuned on the target dataset. What is less clear and is worthy of further investigation, however, is how this fusion is done.

One intuitive and common approach is to linearly combine lexical and semantic scores [13, 20, 40]. If f_L E X ( q , d ) and f_S E M ( q , d ) represent the lexical and semantic scores of document d with respect to query q , then a linear (or more accurately, convex) combination is expressed as f_C o NVEX= \alpha f_S E M + ( 1 - \alpha ) f_L E X where 0 \leq \alpha \leq 1 . Because lexical scores (e.g., BM25) and semantic scores (e.g., dot product) may be unbounded, often they are normalized with min-max scaling [16, 40] prior to fusion.

A recent 

#### Rank 3 | Score: 0.6384 | Chunk: 0 | Document: Fusion_Functions_Hybrid_Retrieval.md

# An Analysis of Fusion Functions for Hybrid Retrieval

SEBASTIAN BRUCH

SIYU GAI, University of California, Berkeley, Berkeley, CA, United States

AMIR INGBER

Open Access Support provided by: University of California, Berkeley

Published: 18 August 2023
Online AM: 20 May 2023
Accepted: 03 May 2023
Revised: 03 March 2023
Received: 22 September 2022

# An Analysis of Fusion Functions for Hybrid Retrieval

SEBASTIAN BRUCH, Pinecone, USA SIYU GAI, University of California, Berkeley, USA AMIR INGBER, Pinecone, Israel

We study hybrid search in text retrieval where lexical and semantic search are fused together with the intuition that the two are complementary in how they model relevance. In particular, we examine fusion by a convex combination of lexical and semantic scores, as well as the reciprocal rank fusion (RRF) method, and identify their advantages and potential pitfalls. Contrary to existing studies, we find RRF to be sensitive to its parameters; that the learning of a convex combination fusion is generally agnostic to the choice of score normalization; that convex combination outperforms RRF in in-domain and out-of-domain settings; and finally, that convex combination is sample efficient, requiring only a small set of training examples to tune its only parameter to a target domain.

# CCS Concepts: - Information systems Retrieval mo

#### Rank 4 | Score: 0.6306 | Chunk: 2 | Document: Fusion_Functions_Hybrid_Retrieval.md

been explored extensively. Early methods model text as a bag of words and compute the similarity of two pieces of text using a statistical measure such as the term frequency–inverse document frequency family, with BM25 [33, 34] being its most prominent member. We refer to retrieval with a bag of words model as lexical search and the similarity scores computed by such a system as lexical scores.

Lexical search is simple, efficient, (naturally) “zero-shot,” and generally effective but has important limitations: it is susceptible to the vocabulary mismatch problem and, moreover, does not take into account the semantic similarity of queries and documents [5]. That, it turns out, is what deep learning models are excellent at. With the rise of pre-trained language models such as BERT [8], it is now standard practice to learn a vector representation of queries and documents that does capture their semantics, and thereby reduce top- k retrieval to the problem of finding k nearest neighbors in the resulting vector space [9, 13, 16, 32, 40, 44]—where closeness is measured using vector similarity or distance. We refer to this method as semantic search and the similarity scores computed by such a system as semantic scores.

Hypothesizing that lexical and semantic search are complementary in how they model r

#### Rank 5 | Score: 0.6229 | Chunk: 10 | Document: Fusion_Functions_Hybrid_Retrieval.md

This approximate nearest neighbor problem can be solved efficiently using a number of algorithms such as FAISS [12] or Hierarchical Navigable Small World Graphs [22] available as open source packages or through a managed service such as Pinecone,2 creating an opportunity to use deep models and vector representations for first-stage retrieval [13, 44]—a setup that we refer to as semantic search.

Semantic search, however, has its own limitations. Previous studies [5, 37] have shown, for example, that when applied to out-of-domain datasets, their performance is often worse than BM25. Observing that lexical and semantic retrievers can be complementary in the way they model relevance [5], it is only natural to consider a hybrid approach where lexical and semantic similarities both contribute to the makeup of final retrieved list. To date, there have been many studies [13, 14, 18–20, 40, 42, 47] that do just that, where most focus on in-domain tasks with one exception [5] that considers a zero-shot application as well. Most of these works only use one of the many existing fusion functions in experiments, but none compares the main ideas comprehensively. We review the popular fusion functions from these works in the

#### Rank 6 | Score: 0.6221 | Chunk: 16 | Document: Fusion_Functions_Hybrid_Retrieval.md

from a crossencoder and a ColBERT model. In Appendix C, we fuse Splade and Tas-B, and in Appendix D, we fuse Tas-B and all-MiniLM-L6-v2.

We note that both Splade and Tas-B were fine-tuned on the MS MARCO dataset. As such, in all the supplementary experiments, results reported on the MS MARCO dataset should be in-domain, whereas the remaining datasets represent out-of-domain distributions.

Evaluation. Unless noted otherwise, we form the union set for every query from the candidates retrieved by the lexical and semantic search systems. We then compute missing scores where required, compute f Fusion on the union set, and re-order according to the hybrid scores. We then measure Recall@1000 and N D C G @ 1000 to quantify ranking quality, as recommended by Zamani et al. [46]. Due to the much smaller size of Sci Fact and NFCorpus, we evaluate Recall and NDCG at rank cutoff 100 instead, retrieving roughly 2% and 2.7% of the size of the dataset, respectively. We note that this choice of cutoff does not affect the outcome of our experiments or change our conclusions, but it more clearly highlights the differences between the various methods; recall approaches 1 regardless of the retrieval method if rank cutoff was 1,000 (or 20% and 27% of the size of the datasets). Further note that we choose to evaluate deep (i.e., with a larger rank cutoff) rather than shallow metrics per the discussion in the work of Wang et a

#### Rank 7 | Score: 0.6213 | Chunk: 6 | Document: Fusion_Functions_Hybrid_Retrieval.md

an unsurprising yet important fact: tuning \alpha in a convex combination fusion function is extremely sample-efficient, requiring just a handful of labeled queries to arrive at a value suitable for a target domain, regardless of the magnitude of shift in the data distribution. RRF, however, is relatively less sample-efficient and converges to a relatively less effective retrieval system.

We believe that our findings, both theoretical and empirical, are important and pertinent to the research in this field. Our analysis leads us to believe that the convex combination formulation is theoretically sound, empirically effective, sample-efficient, and robust to domain shift. Moreover, unlike the parameters in RRF, the parameter(s) of a convex function are highly interpretable and, if no training samples are available, can be adjusted to incorporate domain knowledge.

We organized the remainder of this article as follows. In Section 2, we review the relevant literature on hybrid search. Section 3 then introduces our adopted notation and provides details of our empirical setup, thereby providing context for the theoretical and empirical

#### Rank 8 | Score: 0.6194 | Chunk: 52 | Document: Fusion_Functions_Hybrid_Retrieval.md

of each function on the resulting set, and evaluate the resulting function on the test split. These figures depict NDCG  @ 1000 as a function of the size of the tuning set, averaged over five trials with the shaded regions illustrating the 95% confidence intervals. For reference, we have also plotted NDCG on the test split for RRF ( \eta = 60 ) ) and TM2C2 with \alpha = 0.8 from Table 2.

Interpretability and Sample Efficiency. The question of hybrid retrieval is an important topic in Information Retrieval (IR). What makes it particularly pertinent is its zero-shot applicability, a property that makes deep models reusable, reducing computational costs and emissions as a result [3, 35], and enabling resource-constrained research labs to innovate. Given the strong evidence supporting the idea that hybrid retrieval is most valuable when applied to out-of-domain datasets [5], we believe that f_H Y B R I D should be robust to distributional shifts and should not need training or fine-tuning on target datasets. This implies that either the function must be non-parametric, that its parameters can be tuned efficiently with respect to the training samples required, or that they are highly interpretable such that their value can 

#### Rank 9 | Score: 0.619 | Chunk: 0 | Document: docs_haystack_deepset_ai__docs__hypothetical-document-embeddings-hyde.md

<!-- source: https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde -->

# Hypothetical Document Embeddings (HyDE)
Enhance the retrieval in Haystack using HyDE method by generating a mock-up hypothetical document for an initial query.
## When Is It Helpful?[​](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde#when-is-it-helpful "Direct link to When Is It Helpful?")
The HyDE method is highly useful when:
  * The performance of the retrieval step in your pipeline is not good enough (for example, low Recall metric).
  * Your retrieval step has a query as input and returns documents from a larger document base.
  * Particularly worth a try if your data (documents or queries) come from a special domain that is very different from the typical datasets that Retrievers are trained on.

## How Does It Work?[​](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde#how-does-it-work "Direct link to How Does It Work?")
Many embedding retrievers generalize poorly to new, unseen domains. This approach tries to tackle this problem. Given a query, the Hypothetical Document Embeddings (HyDE) first zero-shot prompts an instruction-following language model to generate a “fake” hypothetical document that captures relevant textual patterns from the initial query - in practice, this is done five times. Then, it encodes each hypothetical document into an embedding vector and averages them. The resulting, single embedding can be used to identify a nei

#### Rank 10 | Score: 0.6126 | Chunk: 63 | Document: Fusion_Functions_Hybrid_Retrieval.md

In Proceedings of the 36th International ACM SIGIR Conference on Research and Development in Information Retrieval. 997–1000.
[3] Sebastian Bruch, Claudio Lucchese, and Franco Maria Nardini. 2022. Re NeuIR: Reaching efficiency in neural information retrieval. In Proceedings of the 45th International ACM SIGIR Conference on Research and Development in Information Retrieval. 3462–3465.
[4] Sebastian Bruch, Masrour Zoghi, Michael Bendersky, and Marc Najork. 2019. Revisiting approximate metric optimization in the age of deep neural networks. In Proceedings of the 42nd International ACM SIGIR Conference on Research and Development in Information Retrieval. 1241–1244.
[5] Tao Chen, Mingyang Zhang, Jing Lu, Michael Bendersky, and Marc Najork. 2022. Out-of-domain semantics to the rescue! Zero-shot hybrid retrieval models. In Advances in Information Retrieval. Lecture Notes in Computer Science, Vol. 13185. Springer, 95–110.
[6] Gordon V. Cormack, Charles L. A. Clarke, and Stefan Buettcher. 2009. Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. In Proceedings of the 32nd International ACM SIGIR Conference on Research and Development in Information Retrieval. 758–759.
[7] Van Dang, Michael Bendersky, and W. Bruce Croft. 2013. Two-stage learning to rank for information retrieval. In Adv


## Query 11: "What is late chunking and how does it preserve contextual information across chunk boundaries compared to traditional chunk-then-embed approaches?"


### dense

#### Rank 1 | Score: 0.8341 | Chunk: 1 | Document: weaviate_io__blog__late-chunking.md

"Direct link to What is Late Chunking?")
The similarity between the names "late chunking" and "late interaction" is intentional—the authors of late chunking chose the name to reflect its connection with late interaction.
![Chunking Strategies](https://weaviate.io/assets/images/chunking-strategies-fc580e49a4d70ed6abee51cad6ec1eb4.png)
Late chunking is a novel approach that aims to preserve contextual information across large documents by inverting the traditional order of embedding and chunking. The key distinction lies in when the chunking occurs:
  1. **Traditional approach:** Chunk first, then embed each chunk separately.
  2. **Late chunking:** Embed the entire document first, then chunk the embeddings.

This method utilizes a long context embedding model to create token embeddings for every token in a document. These token-level embeddings are then broken up and pooled into multiple embeddings representing each chunk in the text.
In typical setups, all token embeddings would be pooled (mean, cls, etc.) into a single vector representation for the entire document. However, with the rise of RAG applications, there's growing concern that a single vector for long documents doesn't preserve enough contextual information, potentially sacrificing precision during retrieval.
Late chunking addresses this by maintaining the contextual relationships between tokens across the entire document during the embedding

#### Rank 2 | Score: 0.797 | Chunk: 11 | Document: weaviate_io__blog__late-chunking.md

chunks, however with the naive approach there is no ability to **condition** the two separate embeddings with information about their neighboring chunks.
However, when we apply late chunking this contextual conditioning is preserved and we are able to return the two exact paragraphs needed to answer the query in a RAG application.
Let's revisit our theoretical storage comparison from earlier:
Approach | Total embeddings required per document | Number of Documents | Total Vectors Stored | Storage Required  
---|---|---|---|---  
**Late Interaction (no pooling)** | 8,000 | 100,000 | 800 million | ~2.46 TB  
**Naive Approach (chunking before inference)** | 16 ( 8,000 / 512 ) | 100,000 | 1.6 million | ~4.9 GB  
**Late Chunking (chunking after inference)** | 16 ( 8,000 / 512 ) | 100,000 | 1.6 million | ~4.9 GB  
As we can see late chunking offers the same reduction in storage requirements as the naive approach while giving stronger preservation of the contextual information that late interaction offers.
If interested in more examples, here is another great notebook from Danny Williams [exploring Late Chunking with quesitons about Berlin!](https://github.com/weaviate/recipes/blob/main/weaviate-features/services-research/late_chunking_berlin.ipynb)
## What this means for users building RAG applications?[​](https://weaviate.io/blog/late-chunking#what-this-means-for-users-building-rag-applications "Direct link to What this means for users building RAG applications?")
We believe that late chunking is extremely promising

#### Rank 3 | Score: 0.7868 | Chunk: 6 | Document: weaviate_io__blog__late-chunking.md

just right? Well, late chunking may exactly that.
## How Late Chunking Works[​](https://weaviate.io/blog/late-chunking#how-late-chunking-works "Direct link to How Late Chunking Works")
As mentioned earlier late chunking origins are linked closely with late interaction in that both utilise the token-level vector representations that are produced during the forward pass of an embedding model.
Unlike late interaction, there is a pooling step that occurs after the initial inference. This pooling differs from traditional embedding models that pool all representations from every token into a single representation. In late chunking, this pooling is done on segments of the text according to some predetermined chunking strategy that can be aligned based on token spans or boundary cues, thus the term late chunking.
The result is that a long document is still represented by numerous embeddings but critically those embeddings are primed with contextual information relevant to their neighboring chunks.
### What's required[​](https://weaviate.io/blog/late-chunking#whats

#### Rank 4 | Score: 0.7845 | Chunk: 9 | Document: Beyond_Chunk_Then_Embed_Taxonomy.md

discourse structure, it is constrained by the latency and cost associated with LLM inference.

Notably, semantically-informed and LLM-guided methods often build upon structured methods. For instance, semantic splitting requires an initial sentence-level pass, while both proposition-based and Lumber Chunker typically operate on pre-identified paragraphs.

# 2.2 Embedding-Chunking Ordering

The second dimension of our framework is the embedding-chunking ordering, which defines the sequence of chunking and embedding operations. The pre-embedding chunking paradigm, the most common approach, segments the document first and then embeds each resulting chunk in isolation. While simple and scalable, this approach ignores contextual information that may exist across chunk boundaries.

Conversely, contextualized chunking (also known as late chunking) reverses this order. A long-context embedding model first processes the entire document to generate token-level embeddings that incorporate global context [Günther et al.(2024), Rau et al.(2025)]. Segmentation boundaries are then applied to these context-aware representations. The final embedding for each chunk is produced by pooling (e.g., averaging) its token embeddings. This approach preserves cross-chunk relationships, though the added context may reduce discriminability between chunks within the same document.


#### Rank 5 | Score: 0.7643 | Chunk: 14 | Document: weaviate_io__blog__late-chunking.md

(Twitter)](https://twitter.com/weaviate_io)
## Don't want to miss another blog post?
Sign up for our bi-weekly newsletter to stay updated!
  
By submitting, I agree to the [Terms of Service ](https://weaviate.io/service)and [Privacy Policy](https://weaviate.io/privacy).
**Tags:**
  * [concepts](https://weaviate.io/blog/tags/concepts)

[](https://github.com/weaviate/weaviate-io/tree/main/blog/2024-09-05-late-chunking/index.mdx)
[Newer Post Weaviate Named to Will Reed’s Top 100](https://weaviate.io/blog/will-reed-announcement)[Older Post Enriching and Ingesting Data into Weaviate with Aryn](https://weaviate.io/blog/sycamore-and-weaviate)
  * [What is Late Chunking?](https://weaviate.io/blog/late-chunking#what-is-late-chunking)
  * [Current Approaches to Long Context Retrieval](https://weaviate.io/blog/late-chunking#current-approaches-to-long-context-retrieval)
    * [Naive Chunking](https://weaviate.io/blog/late-chunking#naive-chunking)
    * [Late Interaction and ColBERT](https://weaviate.io/blog/late-chunking#late-interaction-and-colbert)
    * [Too hot, too cold, just right?](https://weaviate.io/blog/late-chunking#too-hot-too-cold-just-right)
  * [How Late Chunking Works](https://weaviate.io/blog/late-chunking#how-late-chunking-works)
    * [What's required](https://weaviate.io/blog/late-chunking#whats-required)
  * [Lat

#### Rank 6 | Score: 0.7549 | Chunk: 7 | Document: weaviate_io__blog__late-chunking.md

"Direct link to What's required")
Late chunking requires a relatively simple alteration to the pooling step of the embedding model that can be implemented in **under 30 lines of code** and its vectors can be ingested as individual chunks into a vector database without any modification to the retrieval pipeline.
There are however some requirements needed ahead of performing late chunking:
  1. **Long context models** are a requirement as we need token representation for the entirety of the long document to make them contextually aware. Notably, JinaAI tested using their model [jina-embeddings-v2-small-en](https://huggingface.co/jinaai/jina-embeddings-v2-small-en) which has the highest performance to parameter ratio on MTEB's long embed retrieval benchmark. This model supports up to 8192 tokens which is roughly equivalent to 10 standard pages of text. This model also uses a mean pooling strategy in typical behavior which is a requirement for any model looking to take advantage of late interaction.
  2. **Chunking logic:** being able to chunk text ahead of inference as well as associating each chunk with its corresponding token spans is also critical to making late chunking work. Luckily there are many ways to create chunks in this manner and given late chunking's ability to condition each chunk on previous ones chunking approaches like fixed-size chunking without any overlap may be all that is needed.

## Late Chunking in Action[​](https://weaviate.i

#### Rank 7 | Score: 0.7545 | Chunk: 0 | Document: weaviate_io__blog__late-chunking.md

<!-- source: https://weaviate.io/blog/late-chunking -->

# Late Chunking: Balancing Precision and Cost in Long Context Retrieval
September 5, 2024 · 13 min read
[![Charles Pierse](https://weaviate.io/img/people/icon/charles-pierse.jpg)](https://github.com/cdpierse)
[Charles Pierse](https://github.com/cdpierse)
Head of Weaviate Labs
[![Connor Shorten](https://weaviate.io/img/people/icon/connor.jpg)](https://github.com/CShorten)
[Connor Shorten](https://github.com/CShorten)
Product Researcher
[![Akanksha Sharma](https://weaviate.io/img/people/icon/akanksha.jpg)](https://www.linkedin.com/in/akankshasharmaiitg/)
[Akanksha Sharma](https://www.linkedin.com/in/akankshasharmaiitg/)
Product Management Intern
Large-scale RAG applications that require long context retrieval deal with a unique set of challenges. The volume of data is often huge, while the precision of the retrieval system is critical. However, ensuring high-quality retrieval in such systems is often at odds with cost and performance. For users this can present a difficult balancing act. But there may be a new solution that can even the scales.
Two weeks ago, [JinaAI announced](https://jina.ai/news/late-chunking-in-long-context-embedding-models/) a new methodology to aid in long-context retrieval called late chunking. This article explores why late chunking may just be the happy medium between naive (but inexpensive) solutions and more sophisticated (but costly) solutions like ColBERT for users looking to build high-quality retrieval systems on long documents.
## What is Late Chunking?

#### Rank 8 | Score: 0.7369 | Chunk: 2 | Document: weaviate_io__blog__late-chunking.md

and only afterwards dividing these contextually-rich embeddings into chunks. This approach aims to strike a balance between the precision of full-document embedding and the granularity needed for effective retrieval.
Additionally, this method can help mitigate issues associated with very long documents, such as expensive LLM calls, increased latency, and a higher chance of hallucination.
## Current Approaches to Long Context Retrieval[​](https://weaviate.io/blog/late-chunking#current-approaches-to-long-context-retrieval "Direct link to Current Approaches to Long Context Retrieval")
### Naive Chunking[​](https://weaviate.io/blog/late-chunking#naive-chunking "Direct link to Naive Chunking")
This approach breaks up a long document into chunks (for which there exist numerous [chunking strategies](https://docs.weaviate.io/academy/py/standalone/chunking)) and individually embeds each of those chunks. While this solution can work in some setups it inherently does not account for any contextual dependencies that may exist between chunks because their embeddings are generated independently. Take for example the below paragraph:
> _Alice went for a walk in the woods one day and on her walk, she spotted something

#### Rank 9 | Score: 0.7232 | Chunk: 12 | Document: weaviate_io__blog__late-chunking.md

a number of reasons:
  * It lessens the requirement for very tailored chunking strategies
  * It provides a cost-effective path forward for users doing long context retrieval
  * Its additions can be implemented in under 30 lines of code and require no modification to the retrieval pipeline
  * It can result in a reduction of the total number of documents required to be returned at query time
  * It can enable more efficient calls to LLMs by passing less context that is more relevant.

## Conclusion[​](https://weaviate.io/blog/late-chunking#conclusion "Direct link to Conclusion")
In retrieval, there is no one-size-fits-all solution and the best approach will always be that which solves the **user's problem** given their specific constraints. However, if you want to avoid the pitfalls of naive chunking and the high potential costs of ColBERT, late chunking may be a great alternative for you to explore when you need to strike a balance between cost and performance.
Late chunking is a new approach and as such there is limited data available on its performance in benchmarks, which for long context retrieval are already scarcely available. The initial [quantitative benchmarks from JinaAI](https://github.com/jina-ai/late-chunking) are promising showing improved results across the board against naive chunking. Specifically the relative uplift in performance from late chunking was also shown to improve as the **document length in characters increased** , which makes sense given where the late chunking operation comes into effect.
We are ke

#### Rank 10 | Score: 0.7214 | Chunk: 16 | Document: Beyond_Chunk_Then_Embed_Taxonomy.md

the relative ranking is preserved: Lumber Chunker achieves the highest effectiveness among all methods, confirming the original findings.

Original Claim: Contextualized chunking (embedding the document before segmentation) preserves global context, thereby improving retrieval effectiveness on standard in-corpus benchmarks compared to embedding chunks independently [Günther et al.(2024)].

Our Reproduction: Results in Table 2 compare contextualized chunking (Con-C) to pre-embedding chunking (Pre-C) using Jina-v24, the main model from the original study. Overall, our reproduction confirms the original findings: contextualized chunking consistently outperforms pre-embedding chunking across datasets and segmentation methods. The only exception is semantic splitting, which shows inconsistent results on FiQA and TREC-COVID. We speculate this discrepancy may stem from version differences in the Llama Index Semantic Splitter Node Parser implementation5, as this is the only segmentation method relying on an external library with version-dependent behaviour.

Summary. Having confirmed that both Lumber Chunker’s effectiveness advantage for in-document retrieval and Late Chunking’s benefits for in-corpus retrieval are reproducible, we proceed to investigate the four research questions. The following sections extend these findings by evaluating all segmentation methods


## Query 12: "What is Contextual Retrieval and what two sub-techniques does it combine to reduce retrieval failures?"


### dense

#### Rank 1 | Score: 0.6929 | Chunk: 7 | Document: www_anthropic_com__engineering__contextual-retrieval.md

to the chunk before embedding it and before creating the BM25 index.
Here’s what the preprocessing flow looks like in practice:
![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F2496e7c6fedd7ffaa043895c23a4089638b0c21b-3840x2160.png&w=3840&q=75)_Contextual Retrieval is a preprocessing technique that improves retrieval accuracy._  

If you’re interested in using Contextual Retrieval, you can get started with [our cookbook](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide).
### Using Prompt Caching to reduce the costs of Contextual Retrieval
Contextual Retrieval is uniquely possible at low cost with Claude, thanks to the special prompt caching feature we mentioned above. With prompt caching, you don’t need to pass in the reference document for every chunk. You simply load the document into the cache once and then reference the previously cached content. Assuming 800 token chunks, 8k token documents, 50 token context instructions, and 100 tokens of context per chunk, **the one-time cost to generate contextualized chunks is $1.02 per million document tokens**.
#### Methodology
We experimented across various knowledge domains (codebases, fiction, ArXiv papers, Science Papers), embedding models, retrieval strategies, and evaluation metrics. We’ve included a few examples of the questions and answers we used for each domain in [Appendix II](https://assets.anthropic.com/m/1632cded0a125333/original/Contextual-Retrieval-Appendix-2.pdf).
The graphs below show the average performance across all knowledge domains with the top-performing embedding configuration (Gemini Text 004) and retrieving the top-20-chunks. We use 1 minus recall@20 as our evaluation metric, which measures the percentage of relevant documents that fail to be retrieved within the top 20 chunks. You can see the full res

#### Rank 2 | Score: 0.6929 | Chunk: 7 | Document: www_anthropic_com__news__contextual-retrieval.md

to the chunk before embedding it and before creating the BM25 index.
Here’s what the preprocessing flow looks like in practice:
![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F2496e7c6fedd7ffaa043895c23a4089638b0c21b-3840x2160.png&w=3840&q=75)_Contextual Retrieval is a preprocessing technique that improves retrieval accuracy._  

If you’re interested in using Contextual Retrieval, you can get started with [our cookbook](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide).
### Using Prompt Caching to reduce the costs of Contextual Retrieval
Contextual Retrieval is uniquely possible at low cost with Claude, thanks to the special prompt caching feature we mentioned above. With prompt caching, you don’t need to pass in the reference document for every chunk. You simply load the document into the cache once and then reference the previously cached content. Assuming 800 token chunks, 8k token documents, 50 token context instructions, and 100 tokens of context per chunk, **the one-time cost to generate contextualized chunks is $1.02 per million document tokens**.
#### Methodology
We experimented across various knowledge domains (codebases, fiction, ArXiv papers, Science Papers), embedding models, retrieval strategies, and evaluation metrics. We’ve included a few examples of the questions and answers we used for each domain in [Appendix II](https://assets.anthropic.com/m/1632cded0a125333/original/Contextual-Retrieval-Appendix-2.pdf).
The graphs below show the average performance across all knowledge domains with the top-performing embedding configuration (Gemini Text 004) and retrieving the top-20-chunks. We use 1 minus recall@20 as our evaluation metric, which measures the percentage of relevant documents that fail to be retrieved within the top 20 chunks. You can see the full res

#### Rank 3 | Score: 0.6823 | Chunk: 8 | Document: www_anthropic_com__news__contextual-retrieval.md

in the appendix - contextualizing improves performance in every embedding-source combination we evaluated.
#### Performance improvements
Our experiments showed that:
  * **Contextual Embeddings reduced the top-20-chunk retrieval failure rate by 35%** (5.7% → 3.7%).
  * **Combining Contextual Embeddings and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 49%** (5.7% → 2.9%).

![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F7f8d739e491fe6b3ba0e6a9c74e4083d760b88c9-3840x2160.png&w=3840&q=75)_Combining Contextual Embedding and Contextual BM25 reduce the top-20-chunk retrieval failure rate by 49%._
#### Implementation considerations
When implementing Contextual Retrieval, there are a few considerations to keep in mind:
  1. **Chunk boundaries:** Consider how you split your documents into chunks. The choice of chunk size, chunk boundary, and chunk overlap can affect retrieval performance1.
  2. **Embedding model:** Whereas Contextual Retrieval improves performance across all embedding models we tested, some models may benefit more than others. We found [Gemini](https://ai.google.dev/gemini-api/docs/embeddings) and [Voyage](https://www.voyageai.com/) embeddings to be particularly effective.
  3. **Custom contextualizer prompts:** While the generic prompt we provided works well, you may be able to achieve even better results with prompts tailored to your specific domain or use case (for example, including a glossary of key terms that might only be defined in other documents in the knowledge base).


#### Rank 4 | Score: 0.6823 | Chunk: 8 | Document: www_anthropic_com__engineering__contextual-retrieval.md

in the appendix - contextualizing improves performance in every embedding-source combination we evaluated.
#### Performance improvements
Our experiments showed that:
  * **Contextual Embeddings reduced the top-20-chunk retrieval failure rate by 35%** (5.7% → 3.7%).
  * **Combining Contextual Embeddings and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 49%** (5.7% → 2.9%).

![](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F7f8d739e491fe6b3ba0e6a9c74e4083d760b88c9-3840x2160.png&w=3840&q=75)_Combining Contextual Embedding and Contextual BM25 reduce the top-20-chunk retrieval failure rate by 49%._
#### Implementation considerations
When implementing Contextual Retrieval, there are a few considerations to keep in mind:
  1. **Chunk boundaries:** Consider how you split your documents into chunks. The choice of chunk size, chunk boundary, and chunk overlap can affect retrieval performance1.
  2. **Embedding model:** Whereas Contextual Retrieval improves performance across all embedding models we tested, some models may benefit more than others. We found [Gemini](https://ai.google.dev/gemini-api/docs/embeddings) and [Voyage](https://www.voyageai.com/) embeddings to be particularly effective.
  3. **Custom contextualizer prompts:** While the generic prompt we provided works well, you may be able to achieve even better results with prompts tailored to your specific domain or use case (for example, including a glossary of key terms that might only be defined in other documents in the knowledge base).


#### Rank 5 | Score: 0.6676 | Chunk: 4 | Document: www_anthropic_com__news__contextual-retrieval.md

into smaller chunks for efficient retrieval. While this approach works well for many applications, it can lead to problems when individual chunks lack sufficient context.
For example, imagine you had a collection of financial information (say, U.S. SEC filings) embedded in your knowledge base, and you received the following question: _"What was the revenue growth for ACME Corp in Q2 2023?"_
A relevant chunk might contain the text: _"The company's revenue grew by 3% over the previous quarter."_ However, this chunk on its own doesn't specify which company it's referring to or the relevant time period, making it difficult to retrieve the right information or use the information effectively.
## Introducing Contextual Retrieval
Contextual Retrieval solves this problem by prepending chunk-specific explanatory context to each chunk before embedding (“Contextual Embeddings”) and creating the BM25 index (“Contextual BM25”).


#### Rank 6 | Score: 0.6676 | Chunk: 4 | Document: www_anthropic_com__engineering__contextual-retrieval.md

into smaller chunks for efficient retrieval. While this approach works well for many applications, it can lead to problems when individual chunks lack sufficient context.
For example, imagine you had a collection of financial information (say, U.S. SEC filings) embedded in your knowledge base, and you received the following question: _"What was the revenue growth for ACME Corp in Q2 2023?"_
A relevant chunk might contain the text: _"The company's revenue grew by 3% over the previous quarter."_ However, this chunk on its own doesn't specify which company it's referring to or the relevant time period, making it difficult to retrieve the right information or use the information effectively.
## Introducing Contextual Retrieval
Contextual Retrieval solves this problem by prepending chunk-specific explanatory context to each chunk before embedding (“Contextual Embeddings”) and creating the BM25 index (“Contextual BM25”).


#### Rank 7 | Score: 0.6536 | Chunk: 0 | Document: www_anthropic_com__news__contextual-retrieval.md

<!-- source: https://www.anthropic.com/news/contextual-retrieval -->

# Introducing Contextual Retrieval
Published Sep 19, 2024
For an AI model to be useful in specific contexts, it often needs access to background knowledge. 
For an AI model to be useful in specific contexts, it often needs access to background knowledge. For example, customer support chatbots need knowledge about the specific business they're being used for, and legal analyst bots need to know about a vast array of past cases.
Developers typically enhance an AI model's knowledge using Retrieval-Augmented Generation (RAG). RAG is a method that retrieves relevant information from a knowledge base and appends it to the user's prompt, significantly enhancing the model's response. The problem is that traditional RAG solutions remove context when encoding information, which often results in the system failing to retrieve the relevant information from the knowledge base.
In this post, we outline a method that dramatically improves the retrieval step in RAG. The method is called “Contextual Retrieval” and uses two sub-techniques: Contextual Embeddings and Contextual BM25. This method can reduce the number of failed retrievals by 49% and, when combined with reranking, by 67%. These represent significant improvements in retrieval accuracy, which directly translates to better performance in downstream tasks. 
You can easily deploy your own Contextual Retrieval solution with Claude

#### Rank 8 | Score: 0.6524 | Chunk: 0 | Document: www_anthropic_com__engineering__contextual-retrieval.md

<!-- source: https://www.anthropic.com/engineering/contextual-retrieval -->

# Introducing Contextual Retrieval
Published Sep 19, 2024
For an AI model to be useful in specific contexts, it often needs access to background knowledge. 
For an AI model to be useful in specific contexts, it often needs access to background knowledge. For example, customer support chatbots need knowledge about the specific business they're being used for, and legal analyst bots need to know about a vast array of past cases.
Developers typically enhance an AI model's knowledge using Retrieval-Augmented Generation (RAG). RAG is a method that retrieves relevant information from a knowledge base and appends it to the user's prompt, significantly enhancing the model's response. The problem is that traditional RAG solutions remove context when encoding information, which often results in the system failing to retrieve the relevant information from the knowledge base.
In this post, we outline a method that dramatically improves the retrieval step in RAG. The method is called “Contextual Retrieval” and uses two sub-techniques: Contextual Embeddings and Contextual BM25. This method can reduce the number of failed retrievals by 49% and, when combined with reranking, by 67%. These represent significant improvements in retrieval accuracy, which directly translates to better performance in downstream tasks. 
You can easily deploy your own Contextual Retrieval solution with Claude

#### Rank 9 | Score: 0.6263 | Chunk: 5 | Document: www_anthropic_com__news__contextual-retrieval.md

return to our SEC filings collection example. Here's an example of how a chunk might be transformed:
```
original_chunk = "The company's revenue grew by 3% over the previous quarter."

contextualized_chunk = "This chunk is from an SEC filing on ACME corp's performance in Q2 2023; the previous quarter's revenue was $314 million. The company's revenue grew by 3% over the previous quarter."
```

Copy
It is worth noting that other approaches to using context to improve retrieval have been proposed in the past. Other proposals include: [adding generic document summaries to chunks](https://aclanthology.org/W02-0405.pdf) (we experimented and saw very limited gains), [hypothetical document embedding](https://arxiv.org/abs/2212.10496), and [summary-based indexing](https://www.llamaindex.ai/blog/a-new-document-summary-index-for-llm-powered-qa-systems-9a32ece2f9ec) (we evaluated and saw low performance). These methods differ from what is proposed in this post.
### Implementing Contextual Retrieval
Of course, it would be far too much work to manually annotate the thousands or even millions of chunks in a knowledge base. To implement Contextual Retrieval, we turn to Claude. We’ve written a prompt that instructs the model to provide concise, chunk-specific context that explains the chunk using the context of the overall document. We used the following Claude 3 Haiku pr

#### Rank 10 | Score: 0.6263 | Chunk: 5 | Document: www_anthropic_com__engineering__contextual-retrieval.md

return to our SEC filings collection example. Here's an example of how a chunk might be transformed:
```
original_chunk = "The company's revenue grew by 3% over the previous quarter."

contextualized_chunk = "This chunk is from an SEC filing on ACME corp's performance in Q2 2023; the previous quarter's revenue was $314 million. The company's revenue grew by 3% over the previous quarter."
```

Copy
It is worth noting that other approaches to using context to improve retrieval have been proposed in the past. Other proposals include: [adding generic document summaries to chunks](https://aclanthology.org/W02-0405.pdf) (we experimented and saw very limited gains), [hypothetical document embedding](https://arxiv.org/abs/2212.10496), and [summary-based indexing](https://www.llamaindex.ai/blog/a-new-document-summary-index-for-llm-powered-qa-systems-9a32ece2f9ec) (we evaluated and saw low performance). These methods differ from what is proposed in this post.
### Implementing Contextual Retrieval
Of course, it would be far too much work to manually annotate the thousands or even millions of chunks in a knowledge base. To implement Contextual Retrieval, we turn to Claude. We’ve written a prompt that instructs the model to provide concise, chunk-specific context that explains the chunk using the context of the overall document. We used the following Claude 3 Haiku pr


## Query 13: "How does SPLADE represent text as sparse embeddings and what makes it more effective than BM25 for neural information retrieval?"


### dense

#### Rank 1 | Score: 0.7272 | Chunk: 9 | Document: arxiv__2403.06789__splade-v3.md

to hard negative sampling: Making sparse neural ir models more effective. In Proceedings of the 45th International ACM SIGIR Conference on Research and Development in Information Retrieval, pages 2353–2359, 2022.
[6] T. Formal, C. Lassance, B. Piwowarski, and S. Clinchant. Towards effective and efficient sparse neural information retrieval. ACM Trans. Inf. Syst., dec 2023. Just Accepted.
[7] T. Formal, B. Piwowarski, and S. Clinchant. SPLADE: Sparse Lexical and Expansion Model for First Stage Ranking. In Proc. SIGIR, page 2288–2292, 2021.
[8] L. Gao and J. Callan. Unsupervised corpus aware language model pre-training for dense passage retrieval. In S. Muresan, P. Nakov, and A. Villavicencio, editors, Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), pages 2843–2853, Dublin, Ireland, May 2022. Association for Computational Linguistics.
[9] L. Gao, X. Ma, J. Lin, and J. Callan. Tevatron: An efficient and flexible toolkit for dense retrieval. ar Xiv preprint ar Xiv: 2203.05765, 2022.
[10] S. Hofstätter, S. Althammer, M. Schröder, M. Sertkan, and A. Hanbury. Improving efficient neural ranking models with cross-architecture knowledge distillation, 2021.
[11] C. Lassance and S. Clinchant. An efficiency study for splade models. In Proceedings of the 45th International ACM SIGIR Conference on Research and Development in Information Retrieval, pages 2220–2226, 2022.
[12] C. Lassance and S. Clinchant. The tale of two ms marco – and their unfair comparisons, 2023.
[13] C. Lassance 

#### Rank 2 | Score: 0.7214 | Chunk: 8 | Document: arxiv__2403.06789__splade-v3.md

|
| NFCorpus | 34.5 | 35.7 | 34.8 | 34.7 | 33.8 |
| NQ | 53.3 | 58.6 | 54.9 | 56.1 | 52.1 |
| Quora | 84.9 | 81.4 | 81.7 | 73.4 | 77.5 |
| SCIDOCS | 16.1 | 15.8 | 14.8 | 15.9 | 15.2 |
| Sci Fact | 71.0 | 71.0 | 68.5 | 71.5 | 68.8 |
| TREC-COVID | 72.5 | 74.8 | 70.0 | 63.6 | 68.1 |
| Touche-2020 | 24.2 | 29.3 | 30.1 | 22.7 | 27.0 |
| Average | 50.7 | 51.7 | 50.0 | 49.1 | 47.0 |

# 5 Conclusion

This technical report describes the release of SPLADE-v3 models. We have shown through extensive evaluations that this new series of SPLADE models is statistically significantly more effective than previous iterations. In most query sets – including zero-shot settings – SPLADE-v3 outperforms BM25 and can even rival some re-rankers.

# References

[1] E. Bassani. ranx: A blazing-fast python library for ranking evaluation and comparison. In European Conference on Information Retrieval, pages 259–264. Springer, 2022.
[2] N. Craswell, B. Mitra, E. Yilmaz, D. F. Campos, J. Lin, E. M. Voorhees, and I. Soboroff. Overview of the trec 2022 deep learning track. In Text Retrieval Conference, 2022.
[3] H. Déjean, S. Clinchant, C. Lassance, S. Lupart, and T. Formal. Benchmarking middle-trained language models for neural search. ar Xiv preprint ar Xiv: 2306.02867, 2023.
[4] T. Formal, C. Lassance, B. Piwowarski, and S. Clinchant. Splade v2: Sparse lexical and expansion model for information retrieval, 2021.
[5] T. Formal, C. Lassance, B. Piwowarski, and S. Clinchant. From dis

#### Rank 3 | Score: 0.714 | Chunk: 0 | Document: arxiv__2403.06789__splade-v3.md

# SPLADE-v3: New baselines for SPLADE

Carlos Lassance Cohere (Work done while at Naver) cadurosar at gmail dot com

Hervé Déjean, Thibault Formal, Stéphane Clinchant Naver Labs Europe first.lastname at naverlabs dot com

# Abstract

A companion to the release of the latest version of the SPLADE library. We describe changes to the training structure and present our latest series of models – SPLADE-v3. We compare this new version to BM25, SPLADE ^ { + + } , as well as rerankers, and showcase its effectiveness via a meta-analysis over more than 40 query sets. SPLADE-v3 further pushes the limit of SPLADE models: it is statistically significantly more effective than both BM25 and S P L A D E { + + } , while comparing well to cross-encoder re-rankers. Specifically, it gets more than 40 MRR @ 10 on the MS MARCO dev set, and improves by \uparrow 2% the out-of-domain results on the BEIR benchmark.

# 1 Introduction

This technical report is a companion to the release of the latest version of the SPLADE library1. Given the improvements stemming from simple modifications to the overall training structure, we believe that it is worth releasing new models – despite the lack of novelty 

#### Rank 4 | Score: 0.6929 | Chunk: 4 | Document: arxiv__2403.06789__splade-v3.md

The base SPLADE-v3 model5 starts from SPLADE ^ { + + } Self Distil, and is trained with a mix of KL-Div and MarginMSE, with 8 negatives per query sampled from SPLADE ^ { + + } Self Distil. All the other hyperparameters are similar to previous SPLADE iterations. Importantly, note that in all of our experiments, we use the original MS MARCO collection without the titles [12, 13].

Evaluation To assess the effectiveness of the model, we use the meta-analysis procedure introduced in RANGER [18, 19]. We use up to 44 query sets – relying on the ir_datasets library [15] – coming from different datasets, including 1. MS MARCO passages (4 query sets), 2. MS MARCO v2 passages (4 query sets), 3. BEIR (13 query sets), 4. LoTTE (12 query sets), 5. Antique, 6. TREC-CAR (y1) (2 query sets), 7. Natural Questions, 8. TriviaQA, 9. TREC-TB (3 query sets), and 10. TREC-MQ (2 query sets). We use n D C G * @ 10 to measure effectiveness, where \ n D C G * stands for the nDCG considering only the judged documents (encountered in the retrieved top- k ) if the dataset has both positive and negative judgments – otherwise, we use the standard nDCG @ 10 .

Comparison to BM25 First, we compare our method to BM25 and present the resulting metaanalysis in Figure 1. We notice statistically significant improvements in most of the 44 query sets, with only 3 query sets presenting a statistical decrease in effectiveness. These query sets are Webis Touché-2020 and the two TREC-MQ que

#### Rank 5 | Score: 0.6815 | Chunk: 11 | Document: arxiv__2403.06789__splade-v3.md

evaluation of information retrieval models. ar Xiv preprint ar Xiv: 2104.08663, 2021.
[21] H. Zeng, H. Zamani, and V. Vinay. Curriculum learning for dense retrieval distillation. In Proceedings of the 45th International ACM SIGIR Conference on Research and Development in Information Retrieval, pages 1979–1983, 2022.

![](images/.jpg)
Figure 1

#### Rank 6 | Score: 0.6762 | Chunk: 5 | Document: arxiv__2403.06789__splade-v3.md

sets. For Touché-2020, we are still unsure what is the actual issue, but this observation is recurrent with learned ranking models [5, 11, 20]. For TREC-MQ, there could be an issue with the long documents that may need to be decomposed into passages. Notice the large summary effect, meaning that over the whole set of comparisons, SPLADE-v3 vastly outperforms BM25 (even if it is less efficient).

Comparison to SPLADE ^ { + + } Self Distil We now compare SPLADE-v3 to the previous SPLADE model used at initialization – SPLADE ^ { + + } Self Distil. Ideally, there should not be any loss in effectiveness for any of the tested query sets. We present the meta-analysis in Figure 2. We notice that only Quora suffered from a significant decrease in effectiveness, with most other datasets presenting a gain of effectiveness, with the overall summary effect being positive towards the new baseline.

Comparison to re-rankers We finally compare SPLADE-v3 to cross-encoder re-rankers. More specifically, we consider two models that re-rank the top k = 50 documents returned by SPLADE-v3: MiniLM6 and DeBERTaV37 – we present the results in Figure 3 and Figure 4 respectively. Note that higher k could be used for re-ranking – but we believe that re-ranking 50 documents already constitutes a good efficiency-effectiveness trade-off, especially when re-ranking a well-tuned firststage retriever. For MiniLM, we notice that the summary effect is close to 0 when we consider a 95% confidence interval and that there is not much difference between the origina

#### Rank 7 | Score: 0.6678 | Chunk: 7 | Document: arxiv__2403.06789__splade-v3.md

of posting lists to traverse).

Table 1: Comparison of results as averages per dataset. We report MRR @ 10 for MS MARCO (MSM), n D C G @ 10 for TREC, mean nDCG @ 10 for BEIR (13 datasets), and mean Success \textcircled { a } 5 over all non-pooled subsets of the Forum (LoTTE-F) and Search (LoTTE-S) tasks for LoTTE [17]. We also report the FLOPS measure as a loose indicator of efficiency [7].

| Model | MSM | TREC19 | TREC20 | BEIR 13 | LoTTE-S | LoTTE-F | FLOPS |
|---|---|---|---|---|---|---|---|
| SPLADE++SD | 37.6 | 73.0 | 71.8 | 50.7 | - | 1 | 1.4 |
| SPLADE-v3 | 40.2 | 72.3 | 75.4 | 51.7 | 74.7 | 66.0 | 1.2 |
| SPLADE-v3-DistilBERT | 38.7 | 75.2 | 74.4 | 50.0 | 70.3 | 62.8 | 1.4 |
| SPLADE-v3-Lexical | 40.0 | 71.2 | 73.6 | 49.1 | 74.2 | 64.5 | 0.6 |
| SPLADE-v3-Doc | 37.8 | 71.5 | 70.3 | 47.0 | 71.1 | 59.0 | 1.4 |

Table 2: nDCG @ 10 over the set of 13 datasets of BEIR [20].

| Dataset | SPLADE++SD | SPLADE-v3 | SPLADE-v3-DistilBERT | SPLADE-v3-Lexical | SPLADE-v3-Doc |
|---|---|---|---|---|---|
| Argu Ana | 51.8 | 50.9 | 48.4 | 52.7 | 46.7 |
| Climate-FEVER | 23.7 | 23.3 | 22.8 | 21.8 | 15.9 |
| DBPedia-entity | 43.6 | 45.0 | 42.6 | 42.8 | 36.1 |
| FEVER | 79.6 | 79.6 | 79.6 | 78.5 | 68.9 |
| FiQA-2018 | 34.9 | 37.4 | 33.9 | 36.4 | 33.6 |
| HotpotQA | 69.3 | 69.2 | 67.8 | 68.5 | 

#### Rank 8 | Score: 0.6669 | Chunk: 15 | Document: Fusion_Functions_Hybrid_Retrieval.md

analysis of fusion functions is not limited to lexical-semantic search per se: all normalization and fusion functions studied in this work can be applied to arbitrary scoring functions! As such, we conduct additional experiments using a variety of pairs of retrieval models to confirm the generality of the main theoretical findings of this work. We report these results in Appendices A through D.

In Appendix A, we examine the fusion of the Splade model with BM25. Splade7 [9] is a deep learning model that produces sparse representations for a given piece of text, where each non-zero entry in the resulting embedding is the importance weight of a term in the BERT [8] Word Piece [43] vocabulary comprising of roughly 30,000 terms. Appendix B studies the fusion of BM25 with the Tas-B [10] model.8 Tas-B is a bi-encoder model that was trained using supe

#### Rank 9 | Score: 0.6349 | Chunk: 6 | Document: arxiv__2403.06789__splade-v3.md

and the re-ranked ones – except for a few datasets that could just be “outliers” in the effectiveness of MiniLM. However, in the case of DeBERTaV3, we see the opposite: for most query sets the re-ranker is able to outperform SPLADE-v3 – except for Argu Ana whose “counter-argument” task might be more intricate for a re-ranker.

# 4 SPLADE-v3-DistilBERT, SPLADE-v3-Lexical and SPLADE-v3-Doc

In addition, we also release three other SPLADE-v3 variants:

1. SPLADE-v3-DistilBERT8, which instead starts training from DistilBERT – and thus has a smaller inference “footprint”.
2. SPLADE-v3-Lexical9, for which we remove query expansion, thus reducing the retrieval FLOPS (and improving efficiency) [6].
3. SPLADE-v3-Doc10, which starts training from Co Condenser, and where no computation is done for the query – which can be seen as a simple binary Bag-of-Words [4, 6].

Table 1 summarizes the results as averages over datasets – detailed results over the set of 13 BEIR datasets can be found in Table 2. We note that SPLADE-v3-Lexical is (very) effective on MS MARCO as well as LoTTE, but struggles on BEIR (out-of-domain). While the DistilBERT version is a clear downgrade from the BERT version, it remains however more effective than the lexical version on BEIR. SPLADE-v3-Doc is the less effective approach overall, especially in “zero-shot”, showing that (even) a minimal amount of computation on the query side is important. However, its performance remains quite competitive w.r.t. state-of-the-art dense bi-encoders, especially given its efficiency (no query encoding, and a short 

#### Rank 10 | Score: 0.6305 | Chunk: 64 | Document: Fusion_Functions_Hybrid_Retrieval.md

in Information Retrieval. Springer, 423–434.
[8] Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2019. BERT: Pre-training of deep bidirectional transformers for language understanding. In Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers). 4171–4186.
[9] Thibault Formal, Carlos Lassance, Benjamin Piwowarski, and Stéphane Clinchant. 2022. From distillation to hard negative sampling: Making sparse neural IR models more effective. In Proceedings of the 45th International ACM SIGIR Conference on Research and Development in Information Retrieval. 2353–2359.
[10] Sebastian Hofstätter, Sheng-Chieh Lin, Jheng-Hong Yang, Jimmy Lin, and Allan Hanbury. 2021. Efficiently teaching an effective dense retriever with balanced topic aware sampling. In Proceedings of the 44th International ACM SIGIR Conference on Research and Development in Information Retrieval. 113–122.
[11] Kalervo Järvelin and Jaana Kekäläinen. 2000. IR evaluation methods for retrieving highly relevant documents. In Proceedings of the 23rd Annual International ACM SIGIR Conference on Research and Development in Information Retrieval. ACM, New York, NY, 41–48.
[12] Jeff Johnson, Matthijs Douze, and Hervé Jégou. 2021. Billion-scale similarity search with GPUs. IEEE Transactions on Big Data 7 (2021), 535–547. Y


## Query 14: "What HNSW parameters control the tradeoff between index build speed, index quality, and query accuracy?"


### dense

#### Rank 1 | Score: 0.7996 | Chunk: 4 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

HNSW thesis, you can go back and read the [`HnswSearchLayer` function](https://github.com/pgvector/pgvector/blob/a8e257e1f1aaf4c8c9019dcf4ac41bea98a41fff/src/hnswutils.c#L546) for fun. Additionally, see how the [HNSW implementation calculates and caches distances](https://github.com/pgvector/pgvector/blob/a8e257e1f1aaf4c8c9019dcf4ac41bea98a41fff/src/hnswutils.c#L674)

## The advantages of HNSW

HNSW is much faster to query than the traditional list-based query algorithm. This performance is because the use of graphs and layers reduces the number of distance comparisons that are being run. And because fewer distance comparisons, we can run more queries concurrently as well.

## Tradeoffs for HNSW

The most obvious trade off for HNSW indexes is that they are approximations. But, this is no different than any existing vector index, so aside from a table-scan of comparisons. If you need absolutes, it is best to run the non-indexed query that calculates distance for each row.

The second trade-off for HNSW indexes is they can be expensive to build. The two largest contributing variables for these indexes are: size of the dataset and complexity of the index. For moderate datasets of > 1M rows, it can take 6 minutes to build some of the simplest of indexes. During that time, the database will use all the R

#### Rank 2 | Score: 0.7947 | Chunk: 1 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

TL;DR

HNSW is cutting edge for all vector based indexing. To build an HNSW index, run something like the following:

```sql
CREATE INDEX ON recipes
USING hnsw (embedding vector_l2_ops)
WITH (m = 4, ef_construction = 10);
```

These indexes will:
  * use approximations (not precision)
  * be more performant than list-based indexes
  * require longer index build times
  * and require more memory

Tradeoffs:
  * Indexes will take longer to build depending on values for _m_ and _ef_construction_. When increased, these values will slow the speed of index build drastically, while not improving performance. Yet, it may increase accuracy of response.
  * To search more than 40 nearest neighbors, increase this `SET hnsw.ef_search = x;` value. Where `x` is the value of nearest neighbors you want to return.
  * Not all queries will work with HNSW. As we said in the [vector performance blog post](https://www.crunchydata.com/blog/pgvector-performance-for-developers), use `EXPLAIN` to ensure your query is using the index. If it is not using the index, simplify your query until it is, then build back to your complexity.

## What is HNSW?

HNSW is short for Hierarchical Navigable Small World. But, HNSW isn't just one algorithm — it's kind of like 3 algorithms in a trench coat. The first algorithm was [first presented in a paper in 2011](https://www.iiis.org/CDs2011/CD2011IDI/ICTA_2011/PapersPdf/CT175ON.pdf). It used graph topology to find the vertex (or element) with the local minimum nearest neighbor. Then, a couple more papers were published, but the [one in 2014

#### Rank 3 | Score: 0.7749 | Chunk: 8 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

Search (Faiss) library, and test different construction and search parameters and see how these affect index performance.
To initialize the HNSW index we write:
In[2]:
```
# setup our HNSW parameters
d = 128  # vector size
M = 32

index = faiss.IndexHNSWFlat(d, M)
print(index.hnsw)
```

Out[2]:
```
<faiss.swigfaiss.HNSW; proxy of <Swig Object of type 'faiss::HNSW *' at 0x7f91183ef120> >

```

With this, we have set our `M` parameter — the number of neighbors we add to each vertex on insertion, but we’re missing _M_max_ and _M_max0_.
In Faiss, these two parameters are set automatically in the `set_default_probas` method, called at index initialization. The _M_max_ value is set to `M`, and _M_max0_ set to `M*2` (find further detail in the [notebook](https://github.com/pinecone-io/examples/blob/master/learn/search/faiss-ebook/hnsw-faiss/hnsw_faiss.ipynb)).
Before building our `index` with `index.add(xb)`, we will find that the number of layers (or _levels_ in Faiss) are not set:
In[3]:
```
# the HNSW index starts with no levels
index.hnsw.max_level
```

Out[3]:
```
-1
```

In[4]:
```
# and levels (or layers) are empty too
levels = faiss.vector_to_array(index.hnsw.levels)
np.bincount(levels)
```

Out[4]:
```
array([], dtype=int64)
```

If we go ahead and build the index, we’ll find that both of these para

#### Rank 4 | Score: 0.7716 | Chunk: 12 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

we compare the distribution between our Python implementation and that of Faiss, we see very similar results:
In[12]:
```
chosen_levels = []
rng = np.random.default_rng(12345)
for _ in range(1_000_000):
    chosen_levels.append(random_level(assign_probas, rng))
```

In[13]:
```
np.bincount(chosen_levels)
```

Out[13]:
```
array([968821,  30170,    985,     23,       1],
      dtype=int64)
```

![Distribution of vertices across layers in both the Faiss implementation \(left\) and the Python implementation \(right\).](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2F75658a08c25dabc1405f769c76fd2929c051853b-1920x930.png&w=3840&q=75)
Distribution of vertices across layers in both the Faiss implementation (left) and the Python implementation (right).
The Faiss implementation also ensures that we _always_ have at least one vertex in the highest layer to act as the entry point to our graph.
### HNSW Performance
Now that we’ve explored all there is to explore on the theory behind HNSW and how this is implemented in Faiss — let’s look at the effect of different parameters on our recall, search and build times, and the memory usage of each.
We will be modifying three parameters: `M`, `efSearch`, and `efConstruction`. And we will be indexing the Sift1M dataset, which you can download and prepare using [this script](https://gist.github.com/jamescalam/a09a16c17b677f2cf9c019114711f3bf).
As we did before, we initialize our index like so:
```
index = faiss.IndexHNSWFlat(d, M)
```

The two other parameters, `

#### Rank 5 | Score: 0.7703 | Chunk: 5 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

it has available in `maintenance_work_mem`, while redlining the CPU. Long-story short, test it on a production-size dataset before embarking.

The third trade-off for HNSW indexes is that they are sizable — the index for 1M rows of AI embeddings can be 8GB or larger. For performance reasons, you'll want all of this index in memory. HNSW is fast because it uses resources.

## Index tuning values

In the illustrations above, we showed how the index progressed through executing a query. But how are these indexes built? Think of index build for HNSW as a massive query that pre-calculates a larger number of distances. Index tuning is all about how the database limits the algorithms to build those indexes. Go back to the initial illustration and ask the question "how do we build an HNSW index from the data set?"

Points are saved to the top and middle layer based on probability: 1% are saved to the top layer, and 5% are saved to the middle layer. To build the index, the database loops through all values. As it loops to the next value, the algorithm uses the previously built ind

#### Rank 6 | Score: 0.7582 | Chunk: 7 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

During the build, the list is sorted by distance and truncated at a length of _ef_construction_ 's value. Once the value is placed within the graph, this list will be truncated to the length of _m_. The relationship between _ef_construction_ and _m_ is the reason _ef_construction_ is required to be 2x the value of _m_. The larger the value for _ef_construction_ the slower the index build.

What is the best values for _m_ and __ef_construction__? In our tests, we have confirmed the statements from [the original paper](https://arxiv.org/pdf/1603.09320.pdf):

> The only meaningful construction parameter left for the user is M. A reasonable range of M is from 5 to 48. Simulations show that smaller M generally produces better results for lower recalls and/or lower dimensional data, while bigger M is better for high recall and/or high dimensional data.

And for _ef_construction_ :

> Construction speed/index quality tradeoff is controlled via the efConstruction parameter. (…) Further increase of the efConstruction leads to little extra performance but in exchange of significantly longer construction time.

So, long-story short, keep the numbers relatively small because the quality improvement isn't worth the performance hit.

## Query tuning values

### ef_search

This value functions the same as the _ef_construction_ value, except for queries. This is a query-time parameter that limits the number of nearest neighbors maintained in the list. Because of this, _ef_search

#### Rank 7 | Score: 0.754 | Chunk: 7 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

as is done during search). This process is repeated until reaching our chosen _insertion layer_. Here begins phase two of construction.
The _ef_ value is increased to `efConstruction` (a parameter we set), meaning more nearest neighbors will be returned. In phase two, these nearest neighbors are candidates for the links to the new inserted element _q_  _and_ as entry points to the next layer.
_M_ neighbors are added as links from these candidates — the most straightforward selection criteria are to choose the closest vectors.
After working through multiple iterations, there are two more parameters that are considered when adding links. _M_max_ , which defines the maximum number of links a vertex can have, and _M_max0_ , which defines the same but for vertices in _layer 0_.
![Explanation of the number of links assigned to each vertex and the effect of M, M_max, and M_max0.](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2Fdc5cb11ea197ceb4e1f18214066c8c51526b9af5-1920x1080.png&w=3840&q=75)
Explanation of the number of links assigned to each vertex and the effect of M, M_max, and M_max0.
The stopping condition for insertion is reaching the local minimum in _layer 0_.
## Implementation of HNSW
We will implement HNSW using the Facebook AI Simil

#### Rank 8 | Score: 0.738 | Chunk: 15 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

and search time when searching for only one query. When using lower M values, the search time remains almost unchanged for different efConstruction values.
That all looks great, but what about the memory usage of the HNSW index? Here things can get slightly _less_ appealing.
![Memory usage with increasing values of M using our Sift1M dataset. efSearch and efConstruction have no effect on the memory usage.](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2Fe04d23ccd76d8bdc568542bebe75a75e7d36a21e-1480x1050.png&w=3840&q=75)
Memory usage with increasing values of M using our Sift1M dataset. efSearch and efConstruction have no effect on the memory usage.
Both `efConstruction` and `efSearch` do not affect index memory usage, leaving us only with `M`. Even with `M` at a low value of `2`, our index size is already above 0.5GB, reaching almost 5GB with an `M` of `512`.
So although HNSW produces incredible performance, we need to weigh that against high memory usage and the inevitable high infrastructure costs that this can produce.
#### Improving Memory Usage and Search Speeds
HNSW is not the best index in terms of memory utilization. However, if this is important and using [another index](https://www.pinecone.io/learn/series/faiss/vector-indexes/) isn’t an option, we can improve it by compressing our vectors using [product quantization (PQ)](https://www.pinecone.io/learn/series/faiss/product-quantization/). Using PQ will reduce recall and increase

#### Rank 9 | Score: 0.7328 | Chunk: 13 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

and `efSearch` can be modified _after_ we have initialized our `index`.
```
index.hnsw.efConstruction = efConstruction
index.add(xb)  # build the index
index.hnsw.efSearch = efSearch
# and now we can search
index.search(xq[:1000], k=1)
```

Our `efConstruction` value _must_ be set before we construct the index via `index.add(xb)`, but `efSearch` can be set anytime before searching.
Let’s take a look at the recall performance first.
![Recall@1 performance for various M, efConstruction, and efSearch parameters.](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2Fe8c281c3626226a76389fa344a71eb57f70cf879-1920x980.png&w=3840&q=75)
Recall@1 performance for various M, efConstruction, and efSearch parameters.
High `M` and `efSearch` values can make a big difference in recall performance — and it’s also evident that a reasonable `efConstruction` value is needed. We can also increase `efConstruction` to achieve higher recall at lower `M` and `efSearch` values.
However, this performance does not come for free. As always, we have a balancing act between recall and search time — let’s take a look.
![Search time in µs for various M, efConstruction, and efSearch parameters when searching for 1000 queries. Note that the y-axis is using a log scale.](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2Fvr8gru94%2Fproduction%2F876bf66aba408959042888efe72c55db4d6b3b41-1920x980.png&w=3840&q=75)
Search time in µs for various M, efConstruction, and efSe

#### Rank 10 | Score: 0.7275 | Chunk: 14 | Document: www_pinecone_io__learn__series__faiss__hnsw.md

parameters when searching for 1000 queries. Note that the y-axis is using a log scale.
Although higher parameter values provide us with better recall, the effect on search times can be dramatic. Here we search for `1000` similar vectors (`xq[:1000]`), and our recall/search-time can vary from 80%-1ms to 100%-50ms. If we’re happy with a rather terrible recall, search times can even reach 0.1ms.
If you’ve been following our [articles on vector similarity search](https://www.pinecone.io/learn/), you may recall that `efConstruction` has a [negligible effect on search-time](https://www.pinecone.io/learn/series/faiss/vector-indexes/) — but that is not the case here…
When we search using a few queries, it _is_ true that `efConstruction` has little effect on search time. But with the `1000` queries used here, the small effect of `efConstruction` becomes much more significant.
If you believe your queries will mostly be low volume, `efConstruction` is a great parameter to increase. It can improve recall with little effect on _search time_ , particularly when using lower `M` values.
![efConstruction and search time when searching for only one query. When using lower M values, the search time remains almost unchanged for different efConstruction values.](https://www.pinecone.io/_next/image/?url=https%3A%2F%2Fcdn.san


## Query 15: "How does LLM performance degrade with increasing context length and what factors influence the rate of degradation?"


### dense

#### Rank 1 | Score: 0.7977 | Chunk: 31 | Document: research_trychroma_com__context-rot.md

demonstrate that LLMs exhibit inconsistent performance across context lengths, even for simple tasks. However, this evaluation is not exhaustive of real-world use cases. In practice, long context applications are often far more complex, requiring synthesis or multi-step reasoning. Based on our findings, we would expect performance degradation to be even more severe under those conditions.
Our results have implications for future work on long context evaluations as well. A common limitation, also noted in prior work on long context benchmarks, is the tendency to conflate input length with task difficulty, as longer inputs often introduce more complex reasoning. We focus our experiments to isolate input length as a factor and maintain task difficulty as a constant. An important direction for future work is to disentangle how much of a model’s performance degradation stems from the intrinsic difficulty of the task itself versus its ability to effectively handle long contexts.
We also do not explain the mechanisms behind this performance degradation. Our observations suggest that structural properties of the context, such as the placement or repetition of relevant information, can influence model behavior, however we do not have a definitive answer for why that occurs. Investigating these effects would require a deeper investigation into m

#### Rank 2 | Score: 0.7767 | Chunk: 32 | Document: research_trychroma_com__context-rot.md

interpretability, which is beyond the scope of this report.
More broadly, our findings point to the importance of context engineering: the careful construction and management of a model’s context window. Where and how information is presented in a model’s context strongly influences task performance, making this a meaningful direction of future work for optimizing model performance.
# #
Through our experiments, we demonstrate that LLMs do not maintain consistent performance across input lengths. Even on tasks as simple as non-lexical retrieval or text replication, we see increasing non-uniformity in performance as input length grows.
Our results highlight the need for more rigorous long-context evaluation beyond current benchmarks, as well as the importance of context engineering. Whether relevant information is present in a model’s context is not all that matters; what matters more is how that information is presented. We demonstrate that even the most capable models are sensitive to this, making effective context engineering essential for reliable performance.
# #
[1] (July 16, 2025) Latent List insights added and clarifications made by Kiran Vodrahalli (Google Deepmind)
[2] Original source for examples: https://arxiv.org/pdf/2410.10813
# #
[1] Kamradt, G. (2023). Needle In A Haystack - Pressure Testing LLMs [GitHub Repository]. [Link](https://github.com/gkamradt/LLMTest_NeedleInAHaystack)
[2] Wu, D., Wang, H., Yu, W., Zhang, Y., Chang, K.-W., and Yu, D. (2025). LongMemEval: Benchmarking Chat Assistants o

#### Rank 3 | Score: 0.7327 | Chunk: 0 | Document: research_trychroma_com__context-rot.md

<!-- source: https://research.trychroma.com/context-rot -->

# #
It is common for modern LLMs to have input context lengths in the millions of tokens. Gemini 1.5 Pro [[3](https://research.trychroma.com/context-rot#gemini-1.5-pro)] first introduced their 1M context window in early 2024, followed by the recent GPT-4.1’s 1M context window [[4](https://research.trychroma.com/context-rot#gpt-4.1)] and Llama 4 with 10M [[5](https://research.trychroma.com/context-rot#llama-4)]. The use case for long context is compelling: longer context means that the LLM can process more information with each call and generate more informed outputs.
Long context evaluations for these models often demonstrate consistent performance across input lengths. However, these evaluations are narrow in scope and not representative of how long context is used in practice. The most commonly used test, Needle in a Haystack (NIAH), is a simple lexical retrieval task often used to generalize a model’s ability to reliably handle long context. Real applications, such as agent tasks or summarization, demand significantly more processing and reasoning over broader, often more ambiguous information.
Designing realistic long context benchmarks is challenging. Tasks often grow in complexity as input length increases, making it difficult to isolate whether performance drops are due to longer inputs or inherently harder problems. To address this, our experiments hold task complexity constant while varying only the input length—allowing us to directly measure the effect of input length alone.
## #
We pres

#### Rank 4 | Score: 0.7279 | Chunk: 25 | Document: research_trychroma_com__context-rot.md

of tasks due to finish_reason='content_filter’.
We analyze outputs along several dimensions:
  * Normalized Levenshtein distance
  * Presence and position of unique word
    * Correct: Unique word is present and appears at the correct index
    * Incorrect position: Unique word appears, but at the wrong index
  * Word count difference (number of words in input - number of words generated)

## #
As context length increases, performance consistently degrades across all models. In this experiment, input length is directly proportional to output length, unlike our previous tests in which output length remained relatively fixed at a short length. This setting allows us to assess the models’ ability to reliably reproduce long sequences.
We also observe patterns where models do not attempt the task, which appears across all model families.
![](https://research.trychroma.com/img/context_rot/repeated_words/claude_line_plot.png)
Repeated Words - Claude Family
We observe that Sonnet 3.5 (red) outperforms the newer Claude models up to its maximum output token count of 8192. Opus 4 (blue), while exhibiting the slowest degradation rate

#### Rank 5 | Score: 0.6945 | Chunk: 30 | Document: research_trychroma_com__context-rot.md

orange orange orange--g.-g/2021/01/20/orange-county-california-sheriff-deputies-wore...
Repeated Words - Gemini 2.5 Pro Sample Outputs
![](https://research.trychroma.com/img/context_rot/repeated_words/qwen_line_plot.png)
Repeated Words - Qwen Family
We only observe non-attempts with Qwen3-8B, with make up 4.21% of tasks. With this model, we observe random outputs starting from around 5000 words:
> Okay, I'm going to take a break. Let me know, I'm not in the mood. I need to chill out. I'm going to go somewhere and get some fresh air. Maybe go to the beach, or just chill out somewhere. I don't know, but I need to take a break. Let me know, I'm not in the mood. I need to chill out. I'm going to go somewhere and get some fresh air. Maybe go to the beach, or just chill out somewhere. I don't know, but I need to take a break. Let me know, I'm not in the mood. I need to chill out. I'm going to go somewhere and get some fresh air. Maybe go to the beach, or just chill out somewhere. I don't know, but I need to take a break. Let me know, I'm not in the mood. I need to chill out. I'm going to go somewhere and get some fresh air. Maybe go to the beach, or just chill out somewhere. I don't know, but I need to take a break. Let me know, I'm not in the mood. I need to chill out. I'm going to go somewhere and...
Repeated Words - Qwen3-8B Output on 'golden' | 'Golden' (5,000 words)
# #
Our exp

#### Rank 6 | Score: 0.6725 | Chunk: 29 | Document: research_trychroma_com__context-rot.md

to generate random outputs and a more diverse set of them.
![](https://research.trychroma.com/img/context_rot/repeated_words/gemini_line_plot.png)
Repeated Words - Gemini Family
Generally, we see a performance degradation across models as context length increases. With Gemini 2.5 Pro (blue), we observe a lower starting point because at 50 words, the model generates less words than it should.
Across all word combinations and models in this family—except Gemini 2.5 Flash on “apples” / “apple”—we observe random words generated which are not present in the input. This typically starts around 500-750 words, with Gemini 2.5 Pro showing the greatest variability, followed by 2.0 Flash, then 2.5 Flash.
> "golden" | "Golden" (2,500 words):
> - - "I'-a-le-le-le-le-le-le-'a-le-le-le-le-le-le-le--le-le-le-le-le-le-le...
> "orange" | "run" (10,000 words):


#### Rank 7 | Score: 0.6671 | Chunk: 18 | Document: research_trychroma_com__context-rot.md

so it can focus solely on reasoning. Adding irrelevant context adds the additional step of identifying what is relevant, forcing the model to perform two tasks simultaneously.
We systematically test the effect of adding this additional step with increased input length through two conditions:
  1. Focused input, containing only the relevant parts and so the model just has to do simple reasoning.
  2. Full input, which utilizes the full 113k token LongMemEval input that includes irrelevant context. In this case, the model has to perform retrieval across the long context in addition to reasoning.

We verify that the models are highly capable of succeeding on the focused inputs, then observe consistent performance degradation with the full inputs. This performance drop suggests that adding irrelevant context, and thereby adding an additional step of retrieval, significantly impacts a model’s ability to maintain reliable performance.
## #
Given a chat history between a user and assistant, the model’s task is to answer a question relating to part of that chat history.
![](https://research.trychroma.com/img/context_rot/longmemeval/ex.png)
LongMemEval - Examples by Question Type [[2](https://research.trychroma.com/context-rot#longmemeval-source)]
We use LongMemEval_s and filter for tasks that fall under the knowledge update, temporal reasoning, and multi-session categories. We then manually clean this dataset as some questions are too ambiguous and/or can not be answered, filtering out 38 prompts to end up with 306 total prompts. These prompts average out to ~113k tokens.
T

#### Rank 8 | Score: 0.6609 | Chunk: 1 | Document: research_trychroma_com__context-rot.md

the following:
  * An evaluation across 18 LLMs, including leading closed-source and open-weights models, revealing nonuniform performance with increasing input length.
  * A writeup of observed model-specific behavior patterns when handling distractors and varying question-answer similarity.
  * The [complete codebase](https://github.com/chroma-core/context-rot) to replicate our results.

# #
One of the most widely used benchmarks for evaluating a model’s long context capabilities is Needle in a Haystack (NIAH). While useful as a scalable test, it measures a narrow capability: lexical retrieval. Models typically perform well on NIAH, which has led to the perception that long-context is largely solved.
However, NIAH underestimates what most long context tasks require in practice. Variants of NIAH, like NoLiMa [[6](https://research.trychroma.com/context-rot#nolima)] which include needle-question pairs with non-lexical matches, reveal significant performance drops. Other tasks that appear similar in regards to difficulty, such as AbsenceBench [[7](https://research.trychroma.com/context-rot#absencebench)] which tests models for recognizing the absence of a given snippet of text, also demonstrate performance degradation with growing input length.
Additionally, long context tasks often involve disambiguating amongst distractors as part of the task. One examp

#### Rank 9 | Score: 0.6472 | Chunk: 11 | Document: research_trychroma_com__context-rot.md

needle-question pairs.
![](https://research.trychroma.com/img/context_rot/longmemeval/needle_question_sim_arxiv.png)
NIAH: Needle-Question Similarity (thinking/non-thinking modes of the same model are treated separately) - arXiv haystack/arXiv needles High Performance: upper 33% performance Blue: high-similarity needles (upper 50% similarity) Red: low-similarity needles (lower 50% similarity)
At short input lengths, the models perform well even on low-similarity pairs. We see this most clearly in the high/medium-performance models, demonstrating that these models are capable of succeeding at this task for all needle-question pairs.
The observed performance degradation at longer input lengths is not due to the intrinsic difficulty of the needle-question pairing. By holding the needle-question pair fixed and varying only the amount of irrelevant content, we isolate input size as the primary factor in performance decline.
We also examine whether needle position influences performance. Testing across 11 needle positions, we find no notable variation in performance for this specific NIAH task.
# #
It has already been established with older models that distractors degrade model performance and have non-uniform impact. Newer models are claimed to reliably handle any distractor, but does this hold true as input length increases?
Our experiments reveal that the impact of distractors and their non-uniformity amplifies as input length grows across models, including the latest state-of-the-art models. We also observe distinct behaviors across model families in how th

#### Rank 10 | Score: 0.64 | Chunk: 7 | Document: research_trychroma_com__context-rot.md

Paul Graham essays, where each essay follows a structured organization of ideas to form an argument. To evaluate whether this structure influences model performance, we compare two conditions:
  * Original: preserves the natural flow of ideas within each excerpt
  * Shuffled: sentences are randomly reordered throughout the haystack to maintain the same overall topic without logical continuity

We demonstrate the following:
  * Across all experiments, model performance consistently degrades with increasing input length.
  * Lower similarity needle-question pairs increases the rate of performance degradation.
  * Distractors have non-uniform impact on model performance with regards to how distracting they are relative to each other. We see this impact more prominently as input length increases, and observe distinctions in how various models respond to them.
  * Needle-haystack similarity does not have a uniform effect on model performance, suggesting the need for further investigation.
  * The structural pattern of the haystack consistently shows an impact on how models process long inputs.

## #
For every unique combination of needle type, haystack topic, and haystack structure, we test each model across:
  * 8 input lengths
  * 11 needle positions

We evaluate each model across its maximum context window with temperature=0 unless that setting is incompatible (i.e. o3) or explicitly discouraged (i.e. Qwen’s “thinking mode”). For Qwen models, we apply the YaRN method [[13](https://research.trychroma.com/context-rot#yarn)] to extend from 32,76


## Query 16: "What are the tradeoffs between fixed-size, semantic, and LLM-guided chunking strategies for RAG retrieval quality?"


### dense

#### Rank 1 | Score: 0.7913 | Chunk: 3 | Document: Rethinking_Chunk_Size_Long_Document_Retrieval.md

Tokens/Doc |
|---|---|---|---|---|---|---|
| NarrativeQA | 1073 | 1.9 | 51830.4 | 8.5 | 12.6 | 8983.5 |
| Natural Questions (NQ) | 25010 | 1.0 | 6918.2 | 9.0 | 6.8 | 2864.8 |
| NewsQA* | 685 | 11.9 | 8484.5 | 6.5 | 5.2 | 3265.3 |
| COVID-QA* | 55 | 2.1 | 10009.2 | 8.8 | 11.1 | 2904.5 |
| TechQA* | 45 | 10.6 | 7597.2 | 51.1 | 46.9 | 2130.1 |
| SQuAD* | 306 | 43.7 | 7998.3 | 9.9 | 3.9 | 2949.3 |

Despite its widespread use, fixed-size chunking may not be optimal for all datasets. For instance, hierarchical chunking methods have been shown to improve retrieval by preserving semantic coherence within chunks [10]. Moreover, the challenge of evaluating chunking strategies stems from the difficulty of establishing ground truth relevance in retrieval [11]. While prior work has explored chunking in traditional retrieval systems, there is limited research on how fixed-size chunking impacts retrieval performance across documents of varying domains in modern RAG architectures. We address this research gap through a structured set of ablations on different domain-specific datasets across different chunk sizes and embedding models. For reproducibility of results, our code is available on Github 1. Our key contributions can be summarized as follows:

- We systematically evaluate the impact of fixed-size chunking on retrieval effectiveness across multiple datasets, analyzing recall @ k trends for different chunk sizes and embeddi

#### Rank 2 | Score: 0.7827 | Chunk: 12 | Document: zilliz_com__learn__guide-to-chunking-strategies-for-rag.md

risk of context loss and improving the coherence of [semantic search](https://zilliz.com/glossary/semantic-search) in the output in [NLP applications](https://zilliz.com/learn/top-5-nlp-applications). However, it also increases the computational and cognitive load, since more text is processed multiple times, and this trade-off needs to be managed based on the specific requirements of the task.
In RAG systems, the choice of chunking strategy can significantly impact the effectiveness of the retrieval process and, by extension, the quality of the generated outputs. Whether through fixed-size, semantic, or hybrid chunking, the goal called chunking remains to optimize how information is segmented, indexed, and retrieved to support efficient and accurate natural language generation. The strategic implementation of chunking can be the difference between a performant system and one that struggles with latency and relevance, highlighting its critical role in the architecture of advanced NLP solutions.
## **Chunking and Vectorization in Text Retrieval**
Chunking significantly influences the effectiveness of vectorization in text retrieval systems. Proper chunking ensures that text vectors encapsulate the necessary semantic information, which enhances retrieval accuracy and efficiency. For instance, chunking strategies that 

#### Rank 3 | Score: 0.7771 | Chunk: 25 | Document: zilliz_com__learn__guide-to-chunking-strategies-for-rag.md

* [**Implementing Chunking in RAG Pipelines**](https://zilliz.com/learn/guide-to-chunking-strategies-for-rag#Implementing-Chunking-in-RAG-Pipelines)
  * [**Performance Optimization in RAG Systems Through Chunking Strategies**](https://zilliz.com/learn/guide-to-chunking-strategies-for-rag#Performance-Optimization-in-RAG-Systems-Through-Chunking-Strategies)
  * [**Case Studies on Successful RAG Implementations with Innovative Chunking Strategies**](https://zilliz.com/learn/guide-to-chunking-strategies-for-rag#Case-Studies-on-Successful-RAG-Implementations-with-Innovative-Chunking-Strategies)
  * [**Conclusion: The Strategic Significance of Chunking in RAG Systems**](https://zilliz.com/learn/guide-to-chunking-strategies-for-rag#Conclusion-The-Strategic-Significance-of-Chunking-in-RAG-Systems)
  * [**Recap of Key Points**](https://zilliz.com/learn/guide-to-chun

#### Rank 4 | Score: 0.7736 | Chunk: 6 | Document: zilliz_com__learn__guide-to-chunking-strategies-for-rag.md

generate accurate and relevant outputs.

  * **Balanced Information Distribution:** Chunking ensures that the information is evenly distributed across the dataset, which helps maintain a balanced retrieval process. This uniform distribution prevents the retrieval model from being biased towards longer documents that might otherwise dominate the retrieval results if the corpus were not chunked.

## Detailed Exploration of Chunking Strategies in RAG Systems
Advanced RAG](https://zilliz.com/blog/advanced-rag-apps-with-llamaindex) techniques like the following chunking strategies are crucial for optimizing the efficiency of RAG systems in processing and understanding large texts. Let’s go deeper into three primary chunking strategies—fixed-size chunking, semantic chunking, and hybrid chunking—and how they can be applied effectively in RAG contexts.
  1. **Fixed-Size Chunking:** Fixed-size chunking involves breaking down text into uniformly sized pieces based on a predefined number of characters, words, or tokens. This method is straightforward, making it a popular choice for initial data processing phases where quick data traversal is needed.
    1. **Strategy:** This technique involves dividing text into chunks of a predetermined size, such as every 100 words or every 500 characters.
    2. **

#### Rank 5 | Score: 0.773 | Chunk: 1 | Document: Rethinking_Chunk_Size_Long_Document_Retrieval.md

Snowflake performs better with smaller chunks, excelling at fine-grained, entity-based matching. Our results underscore the trade-offs between chunk size, embedding models, and dataset characteristics, emphasizing the need for improved chunk quality measures, and more comprehensive datasets to advance chunk-based retrieval in long-document Information Retrieval (IR).

# 1 Introduction

Retrieval-Augmented Generation (RAG) has emerged as a powerful paradigm in natural language processing (NLP), enabling large language models (LLMs) to enhance response accuracy by incorporating relevant external knowledge retrieved from document corpora [1] [2]. This approach has significantly improved performance in knowledge-intensive tasks by mitigating the limitations of parametric memory in LLMs and enhancing factual consistency [3]. The effectiveness of RAG systems heavily depend on document chunking strategies, which segment textual data into manageable units before retrieval. Among various chunking techniques, fixed-size token-based chunking remains a prevalent method due to its simplicity and ease of implementation [4]. Fixed-size chunking segments documents into uniform token-length chunks, ensuring compatibility with transformer-based architectures that have strict token limits [5].

However, despite its widesp

#### Rank 6 | Score: 0.7711 | Chunk: 0 | Document: Rethinking_Chunk_Size_Long_Document_Retrieval.md

# RETHINKING CHUNK SIZE FOR LONG-DOCUMENT RETRIEVAL: A MULTI-DATASET ANALYSIS

Sinchana Ramakanth Bhat Fraunhofer IAIS Germany sinchana.ramakanth.bhat@iais.fraunhofer.de

Max Rudat Fraunhofer IAIS Germany max.rudat@iais.fraunhofer.de

Jannis Spiekermann Fraunhofer IAIS Germany jannis.spiekermann@iais.fraunhofer.de

Nicolas Flores-Herr Fraunhofer IAIS Germany Nicolas.Flores-Herre@iais.fraunhofer.de

June 10, 2025

# ABSTRACT

Chunking is a crucial preprocessing step in retrieval-augmented generation (RAG) systems, significantly impacting retrieval effectiveness across diverse datasets. In this study, we systematically evaluate fixed-size chunking strategies and their influence on retrieval performance using multiple embedding models. Our experiments, conducted on both short-form and long-form datasets, reveal that chunk size plays a critical role in retrieval effectiveness - smaller chunks (64-128 tokens) are optimal for datasets with concise, fact-based answers, whereas larger chunks (512-1024 tokens) improve retrieval in datasets requiring broader contextual understanding. We also analyze the impact of chunking on different embedding models, finding that they exhibit distinct chunking sensitivities. While models like Stella benefit from larger chunks, leveraging global context for long-rang

#### Rank 7 | Score: 0.7607 | Chunk: 9 | Document: zilliz_com__learn__guide-to-chunking-strategies-for-rag.md

quality of generated responses​.
    4. **Disadvantages:**
      1. More complex to implement as it requires understanding of the text structure and content.
    5. **When to Use:** Semantic chunking is particularly beneficial in content-sensitive applications like document summarization or legal document analysis, where understanding the full context and nuances of the language is essential.

  1. **Hybrid Chunking:** Hybrid chunking combines multiple chunking methods to leverage the benefits of both fixed-size and semantic chunking, optimizing both speed and accuracy.
    1. **Strategy:** Combines multiple chunking methods to leverage the advantages of each. For example, a system might use fixed-length chunking for initial data processing and switch to semantic chunking when more precise retrieval is necessary.
    2. **Implementation:** An initial pass might use fixed-size chunking for quick indexing, followed by semantic chunking during the retrieval phase to ensure contextual integrity. Integrating tools like **spaCy** for semantic analysis with custom scripts for fixed-size chunking can create a robust [chunking strategy](https://zilliz.com/blog/experimenting-with-different-chunking-strategies-via-langchain) that adapts to various needs.
    3. **Advantages:** Balances speed and contextual integrity by adapting the chunking method based on the task requirements.
    4. **Disadvantages:** Can be more resource-intensive to implement and maintain.
    5. **When to Use:**
      1. **Enterprise Systems:** In customer service chatbots, hybrid chunking can quickly retrieve customer query-related information while ensuring the responses are contextually appropriate and semantically rich.
   

#### Rank 8 | Score: 0.7563 | Chunk: 0 | Document: zilliz_com__learn__guide-to-chunking-strategies-for-rag.md

<!-- source: https://zilliz.com/learn/guide-to-chunking-strategies-for-rag -->

# A Guide to Chunking Strategies for Retrieval Augmented Generation (RAG)
May 15, 202416 min read
We explored various facets of chunking strategies within Retrieval-Augmented Generation (RAG) systems in this guide. 
By [Rahul ](https://zilliz.com/authors/Rahul_)
Read the entire series
  * [Build AI Apps with Retrieval Augmented Generation (RAG)](https://zilliz.com/learn/Retrieval-Augmented-Generation)
  * [Mastering LLM Challenges: An Exploration of Retrieval Augmented Generation](https://zilliz.com/learn/RAG-handbook)
  * [Key NLP technologies in Deep Learning](https://zilliz.com/learn/nlp-technologies-in-deep-learning)
  * [How to Evaluate RAG Applications](https://zilliz.com/learn/How-To-Evaluate-RAG-Applications)
  * [Optimizing RAG with Rerankers: The Role and Trade-offs ](https://zilliz.com/learn/optimize-rag-with-rerankers-the-role-and-tradeoffs)
  * [Exploring the Frontier of Multimodal Retrieval-Augmented Generation (RAG)](https://zilliz.com/learn/multimodal-RAG)
  * [Enhancing ChatGPT with Milvus: Powering AI with Long-Term Memory](https://zilliz.com/learn/enhancing-chatgpt-with-milvus)
  * [How to Enhance the Performance of Your RAG Pipeline](https://zilliz.com/learn/how-to-enhance-the-performance-of-your-rag-pipeline)
  * [Enhancing ChatGPT with Milvus: Powering AI with Long-Term Memory](https://zilliz.com/learn/enhancing-chatgpt-with-milvus)
  * [Pandas DataFrame: Chunking and Vectorizing with Milvus](https:

#### Rank 9 | Score: 0.756 | Chunk: 4 | Document: zilliz_com__learn__guide-to-chunking-strategies-for-rag.md

traditional seq2seq and task-specific models that rely solely on extracting answers from texts​.
  * **Flexibility Across Tasks:** Beyond question answering, RAG has shown promise in other complex tasks, like generating content for scenarios modeled after the game "Jeopardy," where precise and factual language is crucial. This adaptability makes it a powerful tool across various domains of NLP.

For further details, the foundational concepts and [applications of RAG](https://zilliz.com/blog/how-to-evaluate-retrieval-augmented-generation-rag-applications) are thoroughly discussed in the work by Lewis et al. (2020), available through their NeurIPS paper and other publications ( Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks, [https://ar5iv.labs.arxiv.org/html/2005.11401)​​](https://ar5iv.labs.arxiv.org/html/2005.11401\)%E2%80%8B%E2%80%8B)
## Chunking
"Chunking" (and sometimes called "llm chunking")refers to dividing a large text corpus into smaller, manageable pieces or segments. Each recursive chunking part acts as a standalone unit of information that can be individually indexed and retrieved. For instance, in the development of RAG models, as Lewis et al. (2020) described, Wikipedia articles are split into disjoint 100-word chunks to create a total of around 21 million documents that serve as the retrieval database​. This chunking technique is crucial for enhancing the efficiency and accuracy of the retrieval process, which in turn impacts th

#### Rank 10 | Score: 0.755 | Chunk: 23 | Document: zilliz_com__learn__guide-to-chunking-strategies-for-rag.md

can influence the overall system performance.
  * **Tools and Metrics:** The tools and metrics that can be used to monitor and evaluate the effectiveness of chunking strategies are critical for ongoing optimization efforts.
  * **Real-World Case Studies:** Examples from successful implementations illustrated how innovative chunking strategies can lead to significant improvements in RAG systems.

## **Final Thoughts on Choosing the Right Chunking Strategy**
Choosing the appropriate advanced RAG techniques is paramount in enhancing the functionality and efficiency of RAG systems. The right strategy utilize chunking ensures that the system not only retrieves the most relevant information but also generates coherent and contextually rich responses to relevant documents. The impact of well-implemented chunking strategies on RAG performance can influence the precision of information retrieval and the quality of content generation.
## **Further Reading and Resources on RAG and Chunking**
  * For a foundational understanding, the original paper by Lewis et al. on RAG is essential. It offers in-depth explanations of the mechanisms and applications of RAG in knowledge-intensive NLP tasks.
  * "Mastering RAG: Advanced Chunking Techniques for LLM Applications" on Galileo provides a deeper dive into various chunking strategies and their impact on RAG system performance, emphasizing the integration of [LLMs](https://zilliz.com/glossary/large-language-models-\(llms\)) for enhanced retrieval and generation processes​.
  * Joining AI and NLP commun


## Query 17: "How do Reciprocal Rank Fusion and convex combination score fusion differ in their behavior and which is more suitable for hybrid retrieval?"


### dense

#### Rank 1 | Score: 0.8245 | Chunk: 0 | Document: Fusion_Functions_Hybrid_Retrieval.md

# An Analysis of Fusion Functions for Hybrid Retrieval

SEBASTIAN BRUCH

SIYU GAI, University of California, Berkeley, Berkeley, CA, United States

AMIR INGBER

Open Access Support provided by: University of California, Berkeley

Published: 18 August 2023
Online AM: 20 May 2023
Accepted: 03 May 2023
Revised: 03 March 2023
Received: 22 September 2022

# An Analysis of Fusion Functions for Hybrid Retrieval

SEBASTIAN BRUCH, Pinecone, USA SIYU GAI, University of California, Berkeley, USA AMIR INGBER, Pinecone, Israel

We study hybrid search in text retrieval where lexical and semantic search are fused together with the intuition that the two are complementary in how they model relevance. In particular, we examine fusion by a convex combination of lexical and semantic scores, as well as the reciprocal rank fusion (RRF) method, and identify their advantages and potential pitfalls. Contrary to existing studies, we find RRF to be sensitive to its parameters; that the learning of a convex combination fusion is generally agnostic to the choice of score normalization; that convex combination outperforms RRF in in-domain and out-of-domain settings; and finally, that convex combination is sample efficient, requiring only a small set of training examples to tune its only parameter to a target domain.

# CCS Concepts: - Information systems Retrieval mo

#### Rank 2 | Score: 0.8184 | Chunk: 4 | Document: Fusion_Functions_Hybrid_Retrieval.md

[5] argues that convex combination is sensitive to its parameter \alpha and the choice of score normalization.1 They claim and show empirically, instead, that Reciprocal Rank Fusion (RRF) [6] may be a more suitable fusion as it is non-parametric and may be utilized in a zero-shot manner. They demonstrate its impressive performance even in zero-shot settings on a number of benchmark datasets.

This work was inspired by the claims made in the work of Chen et al. [5]. Whereas Chen et al. [5] address how various hybrid methods perform relative to one another in an empirical study, we re-examine their findings and analyze why these methods work and what contributes to their relative performance. Our contributions thus can best be summarized as an in-depth examination of fusion functions and their behavior.

As our first research question (RQ1), we investigate whether the convex combination fusion is a reasonable choice and study its sensitivity to the normalization protocol. We show that although normalization is essential to create a bounded function and thereby bestow consistency to the fusion across dom

#### Rank 3 | Score: 0.8148 | Chunk: 3 | Document: Fusion_Functions_Hybrid_Retrieval.md

recent works [5, 13, 14, 19, 20, 42] began exploring methods to fuse together lexical and semantic retrieval: for a query q and ranked lists of documents R_L E X and R_S_{ E M } retrieved separately by lexical and semantic search systems respectively, the task is to construct a final ranked list R_F U S I O N so as to improve retrieval quality. This is often referred to as hybrid search.

It is becoming increasingly clear that hybrid search does indeed lead to meaningful gains in retrieval quality, especially when applied to out-of-domain datasets [5, 40]—settings in which the semantic retrieval component uses a model that was not trained or fine-tuned on the target dataset. What is less clear and is worthy of further investigation, however, is how this fusion is done.

One intuitive and common approach is to linearly combine lexical and semantic scores [13, 20, 40]. If f_L E X ( q , d ) and f_S E M ( q , d ) represent the lexical and semantic scores of document d with respect to query q , then a linear (or more accurately, convex) combination is expressed as f_C o NVEX= \alpha f_S E M + ( 1 - \alpha ) f_L E X where 0 \leq \alpha \leq 1 . Because lexical scores (e.g., BM25) and semantic scores (e.g., dot product) may be unbounded, often they are normalized with min-max scaling [16, 40] prior to fusion.

A recent 

#### Rank 4 | Score: 0.7584 | Chunk: 5 | Document: Fusion_Functions_Hybrid_Retrieval.md

the specific choice of normalization is a rather small detail: there always exist convex combinations of scores normalized by min-max, standard score, or any other linear transformation that are rank-equivalent. In fact, when formulated as a per-query learning problem, the solution found for a dataset that is normalized with one scheme can be transformed to a solution for a different choice.

We next investigate the properties of Reciprocal Rank Fusion (RRF). We first unpack RRF and examine its sensitivity to its parameters as our second research question (RQ2)—contrary to Chen et al. [5], we adopt a parametric view of RRF where we have as many parameters as there are retrieval functions to fuse, a quantity that is always one more than that in a convex combination. We find that, in contrast to a convex combination, a tuned RRF generalizes poorly to out-of-domain datasets. We then intuit that because RRF is a function of ranks, it disregards the distribution of scores and, as such, discards useful information. Observe that the distance between raw scores plays no role in determining their hybrid score—a behavior we find counter-intuitive in a metric space where distance does matter. Examining this property constitutes our third and final research question (RQ3).

Finally, we empirically dem

#### Rank 5 | Score: 0.755 | Chunk: 6 | Document: Fusion_Functions_Hybrid_Retrieval.md

an unsurprising yet important fact: tuning \alpha in a convex combination fusion function is extremely sample-efficient, requiring just a handful of labeled queries to arrive at a value suitable for a target domain, regardless of the magnitude of shift in the data distribution. RRF, however, is relatively less sample-efficient and converges to a relatively less effective retrieval system.

We believe that our findings, both theoretical and empirical, are important and pertinent to the research in this field. Our analysis leads us to believe that the convex combination formulation is theoretically sound, empirically effective, sample-efficient, and robust to domain shift. Moreover, unlike the parameters in RRF, the parameter(s) of a convex function are highly interpretable and, if no training samples are available, can be adjusted to incorporate domain knowledge.

We organized the remainder of this article as follows. In Section 2, we review the relevant literature on hybrid search. Section 3 then introduces our adopted notation and provides details of our empirical setup, thereby providing context for the theoretical and empirical

#### Rank 6 | Score: 0.7534 | Chunk: 17 | Document: Fusion_Functions_Hybrid_Retrieval.md

[40] to understand the performance of each system more completely.

# 4 ANALYSIS OF CONVEX COMBINATION OF RETRIEVAL SCORES

We are interested in understanding the behavior and properties of fusion functions. In the remainder of this work, we study through that lens the two popular methods that are representative of existing ideas in the literature, beginning with a convex combination of scores.

As noted earlier, most existing works use a convex combination of lexical and semantic scores as follows: f_C o N v E X ( q , d ) = \alpha f_S E M ( q , d ) + ( 1 - \alpha ) f_L E X ( q , d ) for some 0 \leq \alpha \leq 1 . When \alpha = 1 , the preceding collapses to semantic scores and when 0 to lexical scores.

An interesting property of this fusion is that it takes into account the distribution of scores. In other words, the distance between lexical (or semantic) scores of two documents plays a significant role in determining their final hybrid score. One disadvantage, however, is that the range of f_S E M can be quite different from f_L E X . Moreover, as with term frequency–inverse document frequency in lexical search or with inner product in semantic search, the range of individual functions f_o may depend on the norm of the query and document vectors (e.g., BM25 is a function of the number of query terms). As such, an

#### Rank 7 | Score: 0.7502 | Chunk: 7 | Document: Fusion_Functions_Hybrid_Retrieval.md

of fusion functions. In Section 4, we begin our analysis by a detailed look at the convex combination of retrieval scores. We then examine RRF in Section 5. In Section 6, we summarize our observations and identify the properties a fusion function should have to behave well in hybrid retrieval. We then conclude this work and state future research directions in Section 7.

# 2 RELATED WORK

A multi-stage ranking system is typically composed of a retrieval stage and several subsequent re-ranking stages, where the retrieved candidates are ordered using more complex ranking functions [2, 39]. Conventional wisdom has that retrieval must be recall-oriented while improving ranking quality may be left to the re-ranking stages, which are typically Learning to Rank (LtR) models [17, 24, 29, 39, 41]. There is indeed much research on the tradeoffs between recall 

#### Rank 8 | Score: 0.7459 | Chunk: 36 | Document: Fusion_Functions_Hybrid_Retrieval.md

work, we use \phi_T M M and denote a convex combination of scores normalized by it by TM2C2 for brevity. Where the theoretical minimum does not exist (e.g., with the Tas-B model), we use \phi _{ M M } instead and denote it by M2C2.

# 5 ANALYSIS OF RRF

Chen et al. [5] show that RRF performs better and more reliably than a convex combination of normalized scores. RRF is computed as follows:

f_R R F ( q , d ) = \frac { 1 } { \eta + \pi_L E X ( q , d ) } + \frac { 1 } { \eta + \pi_S E M ( q , d ) } ,
where \eta is a free parameter. Chen et al. [5] take a non-parametric view of RRF, where the parameter \eta is set to its default value 60, to apply the fusion to out-of-domain datasets in a zero-shot manner. In this work, we additionally take a parametric view of RRF, where as we elaborate later, the number of free parameters is the same as the number of functions being fused together, a quantity that is always larger than the number of parameters in a convex combination.

Let us begin by comparing the performance of RRF and TM2C2 empirically to get a sense of their relative efficacy. We first verify whether hybrid retrieval leads to significant gains in in-domain and out-of-domain experiments. In a way, we seek to confirm the findings reported by Chen et al. [5] and compare the two fusion functions in the process.

Table 2 summarizes our results for our primary models, with results for the remaining fusions reported in the appendices. We note that we set RRF’s \eta to 60 per Chen et al. [5] but tuned TM2C2’s \alpha on the validation set of the in-domain datasets and fou

#### Rank 9 | Score: 0.7357 | Chunk: 56 | Document: Fusion_Functions_Hybrid_Retrieval.md

of query-document pairs, we acknowledge that this may change if our analysis was conducted on a per-query basis— itself a rather non-trivial effort. For example, it is unclear if bringing non-linearity to the design of the fusion function or the normalization itself leads to a more accurate prediction of \alpha on a per-query basis. We leave an exploration of this question to future work.

We also note that although our analysis does not exclude the use of multiple retrieval engines as input, and indeed can be extended, both theoretically and empirically, to a setting where we have more than just lexical and semantic scores, it is nonetheless important to conduct experiments and validate that our findings generalize. In particular, we ask if the role of normalization changes when fusing three or more models, and if so, what the behavior of convex is given a particular normalization function, and how that compares with RRF. We believe, however, that our current assumptions are practical and are reflective of the current state of hybrid search where we typically fuse only lexical and semantic retrieval systems. As such, we leave an extended analysis of fusion on multiple retrieval systems to future work.

# APPENDICES

# A FUSION OF SPLADE AND BM25

This section summarizes key results from additional experiments that examine the fusion of SPLADE and BM25 scores. Table 5 compares the effect of fusion on retrieval quality. Figure 13 illustrates the effect of different normalization schemes on the conve

#### Rank 10 | Score: 0.7283 | Chunk: 54 | Document: Fusion_Functions_Hybrid_Retrieval.md

labeling effort. Finally, although RRF does not settle on a value and its parameters are sensitive to the training sample, its performance does more or less converge. However, the performance of the fully parameterized RRF is still sub-optimal compared with TM2C2.

In Figure 12, we also include a convex combination of fully parameterized RRF terms, denoted by RRF-CC and defined as follows:

f_R R F ( q , d ) = ( 1 - \alpha ) \frac { 1 } { \eta_L E X + \pi_L E X ( q , d ) } + \alpha \frac { 1 } { \eta_S E M + \pi_S E M ( q , d ) } ,
where \alpha , \eta_L E X , and \eta_S E M are tunable parameters. The question that this particular formulation tries to answer is whether adding an additional weight to the combination of the RRF terms affects retrieval quality. From the figure, it is clear that the addition of this parameter does not have a significant impact on the overall performance. This also serves as additional evidence supporting the claim that Lipschitz continuity is an important property.

# 7 CONCLUSION

We studied the behavior of two popular functions that fuse together lexical and semantic retrieval to produce hybrid retrieval, and identified their advantages and pitfalls. Importantly, we investigated several questions and claims 


## Query 18: "How do Qwen3 embedding models compare to BGE-M3 and GTE models across standard retrieval benchmarks like MTEB?"


### dense

#### Rank 1 | Score: 0.8621 | Chunk: 0 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

<!-- source: https://medium.com/@mrAryanKumar/comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retrieval-72c0e6895413 -->
# Comparative Analysis of Qwen-3 and BGE-M3 Embedding Models for Multilingual Information Retrieval
**_Aryan Kumar  
Data Scientist, Nakakita Seisakusho Co., Ltd._**
![](https://miro.medium.com/v2/resize:fit:700/1*hHaGImPQn35ZHyR2WjPSSg.png)
This study presents a comprehensive comparative analysis of the Qwen-3 embedding model series against the BGE-M3 embedding model across multiple retrieval benchmarks and practical deployment scenarios. Our evaluation spans standard benchmarks including MTEB (English v2), CMTEB (Chinese), MTEB Code, and MMTEB multilingual tasks. Experimental results demonstrate that Qwen-3 models consistently outperform BGE-M3 across all evaluated dimensions, with Qwen-3-Embedding-0.6B achieving a 7.9% relative improvement on MMTEB (64.33 vs 59.56) while maintaining identical parameter count. The flagship Qwen-3-Embedding-8B model attains state-of-the-art performance with 75.22 MTEB English score, surpassing even proprietary models like Gemini Embedding. We further

#### Rank 2 | Score: 0.8564 | Chunk: 3 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

multiple vectors per document, enabling fine-grained similarity computation at the cost of increased storage.
BGE-M3 uniquely integrates all three approaches, allowing hybrid retrieval strategies that combine semantic and lexical signals. Qwen-3, conversely, focuses on optimizing dense retrieval through scaled architecture and advanced training methodologies.
### 2.2 Benchmarking Standards
The Massive Text Embedding Benchmark (MTEB) has emerged as the de facto standard for evaluating embedding models across 111 languages and multiple task types. Recent extensions include:  
- MTEB English v2: 56 tasks covering classification, clustering, retrieval, and semantic textual similarity  
- CMTEB: Chinese-specific evaluation suite with 6 task categories  
-MTEB Code: Code retrieval and understanding tasks  
- MMTEB: Multilingual evaluation across diverse languages and domains
These benchmarks enable standardized comparison of model capabilities beyond single-domain performance metrics.
## 3. Model Architectures and Training
### 3.1 Qwen-3 Embedding Series
The Qwen-3 embedding models leverage the Qwen3 language model as a base, implementing a standard bi-encoder architecture where queries and documents are encoded independently into dense vectors. Key architectural features include:
- Parameter Scaling: Models available at 0.6B, 4B, and 8B parameters to balance performance and computational cost  
- Dimension Flexibility: Embedding dimensions of 1024, 2560, and 4096 respectively, enabling quality-compression tradeoffs  
- Synthetic Dataset G

#### Rank 3 | Score: 0.8451 | Chunk: 2 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

reported, no systematic analysis exists comparing these two prominent approaches across standardized benchmarks and practical deployment metrics. We evaluate both models on:  
- Standard academic benchmarks (MTEB, CMTEB, MMTEB)  
- Code-specific retrieval tasks  
- Real-world performance characteristics including latency and memory footprint  
- Optimization strategies for production deployment
Our findings indicate that Qwen-3 models deliver superior retrieval accuracy across all tested configurations, while BGE-M3 maintains advantages in specific optimization pathways and deployment flexibility. This analysis provides data scientists and engineers with empirical guidance for model selection based on accuracy requirements, computational constraints, and deployment environments.
## 2. Background and Related Work
### 2.1 Embedding Model Architectures
Modern embedding models have evolved from simple word vector approaches to complex transformer-based architectures capable of capturing nuanced semantic relationships. The field has seen three primary innovations:
1. Dense Retrieval: Models like E5 (Wang et al., 2022) and GTE (Li et al., 2023) generate single vector representations for efficient similarity search.
2. Sparse Retrieval: Traditional BM25 methods and learned sparse representations provide lexical matching capabilities interpretable through token weights.
3. Multi-Vector Retrieval: ColBERT-style approaches g

#### Rank 4 | Score: 0.8411 | Chunk: 1 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

practical considerations including computational efficiency, ONNX quantization strategies, and real-world deployment performance. This analysis provides actionable insights for organizations selecting embedding architectures for production multilingual retrieval systems.
Keywords: Qwen-3, BGE-M3, embedding models, semantic search, multilingual retrieval, MTEB benchmark.
## 1. Introduction
Text embedding models have become foundational components in modern information retrieval systems, enabling semantic search, recommendation engines, and retrieval-augmented generation (RAG) pipelines. The recent emergence of multilingual, multi-task embedding architectures has significantly advanced retrieval quality across diverse domains and languages. Two notable frameworks in this evolution are Alibaba’s Qwen-3 embedding series and the BGE-M3 model, both designed to address the challenges of multilingual semantic understanding.
The Qwen-3 embedding series represents a family of models ranging from 0.6B to 8B parameters, built upon the Qwen3 language model architecture. These models implement sophisticated training procedures and synthetic dataset generation techniques to achieve competitive performance against leading proprietary and open-source alternatives. The BGE-M3 (BAAI General Embedding-Multilingual) model, while smaller at 0.6B parameters, pioneered the integration of dense, sparse, and multi-vector retrieval methods in a single architecture.
This comparative study addresses a critical gap in the literature: while individual model performance has be

#### Rank 5 | Score: 0.8276 | Chunk: 9 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

established optimization pathways  
- Long-Context Evaluation: Performance beyond 4k tokens, where BGE-M3’s architecture may provide advantages, needs deeper analysis
Future research should focus on:  
1. Domain-adapted evaluation for industrial applications  
2. Direct comparison of quantized model variants  
3. Cost-benefit analysis across varying retrieval scales (1M to 1B documents)  
4. Integration patterns with reranking and hybrid retrieval systems
## 7. Thoughts
This comparative study demonstrates that the Qwen-3 embedding series significantly outperforms BGE-M3 across standardized benchmarks, achieving 18.7% higher accuracy on MTEB English and 8.0% better multilingual performance at equivalent 0.6B parameter scales. The Qwen-3–8B model establishes new state-of-the-art results on multilingual and code retrieval tasks, surpassing proprietary alternatives.
However, BGE-M3 maintains compelling advantages in deployment flexibility, particularly through mature ONNX optimization pathways achieving 3x inference speedup with minimal accuracy degradation. For organizations prioritizing computational efficiency and hybrid retrieval capabilities, BGE-M3 remains a viable option.
For data scientists and engineers at Nakakita Seisakusho Co., Ltd. implementing multilingual RAG systems, we recommend Qwen-3-Embedding-0.6B as the default choice, scaling to Qwen-3–4B for high-accuracy requirements. BGE-M3 should be reserved for scenarios demanding extreme optimization or native long-context processing. Our analysis provides empirical fo

#### Rank 6 | Score: 0.8232 | Chunk: 5 | Document: medium.com__mrAryanKumar_comparative-analysis-of-qwen-3-and-bge-m3-embedding-models-for-multilingual-information-retriev.md

Qwen-3-Embedding-0.6B: 0.6B parameters, 1024 dimensions  
- Qwen-3-Embedding-4B: 4B parameters, 2560 dimensions  
- Qwen-3-Embedding-8B: 8B parameters, 4096 dimensions  
- BGE-M3: 0.6B parameters, serving as the primary baseline
Additional baselines include NV-Embed-v2, multilingual-e5-large-instruct, and proprietary APIs (Gemini, text-embedding-3-large) for context.
4.3 Implementation Details
All models are evaluated using the standardized mteb evaluation framework. For reranking experiments, we retrieve top-100 candidates using the embedding model and subsequently apply reranking models for refinement. ONNX quantization experiments follow the methodology described in Tanskanen (2024), using dynamic quantization to reduce model size and latency.
## 5. Results and Analysis
### 5.1 Main Performance Comparison
5.1.1 MTEB English v2 Benchmark
![](https://miro.medium.com/v2/resize:fit:1000/1*TJdz0CJaB1bdBWa6vj5hRg.png)
Key Observations:  
- Qwen-3-Embedding-0.6B outperforms BGE-M3 by 18.7% on MTEB English tasks (70.70 vs 59.56) despite identical parameter count  
- The performance gap extends across all task categories, with particularly strong improvements in retrieval (+11.36 points) and clustering tasks  
- Scaling to 8B parameters yields only marginal gains over the 4B model (75.22 vs 74.60), suggesting diminishing returns for English tasks
5.1.2 Multilingual and Code Retrieval
![](https://miro.medium.com/v2/resize:fit:1000/1*4-Sv9GwHdrnf2C6w-lmbCA.png)
Analysis:  
- Qwen-3-Embedding-0.6B demonstrates consistent multilingual superi

#### Rank 7 | Score: 0.8182 | Chunk: 16 | Document: arxiv__2506.05176__qwen3-embedding.md

into English, Chinese, and Multilingual, evaluated on MTEB (Muennighoff et al., 2023), CMTEB (Xiao et al., 2024), MMTEB (Enevoldsen et al., 2025), and MLDR (Chen et al., 2024), respectively; (2) Code Retrieval, evaluated on MTEB-Code (Enevoldsen et al., 2025), which comprises only code-related retrieval data.; and (3) Complex Instruction Retrieval, evaluated on FollowIR (Weller et al., 2024).

Compared Methods We compare our models with the most prominent open-source text embedding models and commercial API services. The open-source models include the GTE (Li et al., 2023; Zhang et al., 2024b), E5 (Wang et al., 2022), and BGE (Xiao et al., 2024) series, as well as NVEmbed-v2 (Lee et al., 2025a), GritLM-7B Muennighoff et al. (2025). The commercial APIs evaluated are text-embedding-3-large from OpenAI, Gemini-embedding from Google, and Cohere-embedmultilingual- - v 3.0 . For reranking, we compare with the rerankers of jina1, mGTE (Zhang et al., 2024b) and BGE- - m 3 (Chen et al., 2024).

# 4.2 Main Results

Embedding In Table 2, we present the evaluation results on MMTEB (Enevoldsen et al., 2025), which comprehensively covers a wide range of embedding tasks across multiple languages. Our Qwen3-Embedding-4B/8B models achieve the best performance, and our smallest model, Qwen3- Embedding-0.6B, only lags behind the best-performing baseline method (Gemini-Embedding), despite having only 0.6B parameters. In Table 3, we pre

#### Rank 8 | Score: 0.8143 | Chunk: 17 | Document: arxiv__2506.05176__qwen3-embedding.md

the evaluation results on MTEB (English, v2) (Muennighoff et al., 2023), CMTEB (Xiao et al., 2024), and MTEB (Code) (Enevoldsen et al., 2025). The scores reflect similar trends as MMTEB, with our Qwen3-Embedding-4B/8B models consistently outperforming others. Notably, the Qwen3-Embedding-0.6B model ranks just behind the Gemini-Embedding, while being competitive with the gte-Qwen2-7B-instruct.

Table 4: Evaluation results for reranking models. We use the retrieval subsets of MTEB(eng, v2), MTEB(cmn, v1) and MMTEB, which are MTEB-R, CMTEB-R and MMTEM-R. The rest are all retrieval tasks. All scores are our runs based on the retrieval top-100 results from the first row.

| | Basic Relevance Retrieval | |
|---|---|---|
| Model | | Param|MTEB-R CMTEB-R MMTEB-R MLDR MTEB-Code FollowIR |
| Qwen3-Embedding-0.6B | 0.6B | 61.82 | 64.64 | 50.26 | 75.41 | 5.09 |
| Jina-multilingual-reranker-v2-base | 0.3B | 58.22 | 63.73 | 39.66 | 58.98 | -0.68 |
| gte-multilingual-reranker-base | 0.3B | 59.51 | 59.44 | 66.33 | 54.18 | -1.64 |
| BGE-reranker-v2-m3 | 0.6B | 57.03 | 58.36 | 59.51 | 41.38 | -0.01 |
| Qwen3-Reranker-0.6B | 0.6B | 65.80 | 66.36 | 67.28 | 73.42 | 5.41 |
| Qwen3-Reranker-4B | 4B | 69.76 | 72.74 | 69.97 | 81.20 | 14.84 |
| Qwen3-Reranker-8B | 8B | 69.02 | 75.9477.4572.94 | 70.19 | 81.22 | 8.05 |

| Model | MMTEB | |MTEB (Eng,v2)| | CMTEB | |MTEB (Code, v1) |
|---|---|---|---|---|
| Qwen3-Embedding-0.6B w/ only sy

#### Rank 9 | Score: 0.8129 | Chunk: 20 | Document: arxiv__2506.05176__qwen3-embedding.md

models’ capabilities. Our comprehensive evaluations demonstrate that the Qwen3-Embedding models achieve state-of-the-art performance across various benchmarks, including MTEB, CMTEB, MMTEB, and several retrieval benchmarks. We are pleased to open-source the Qwen3-Embedding and Qwen3-Reranker models (0.6B, 4B, and 8B), making them available for the community to use and build upon.

# References

Jianlyu Chen, Shitao Xiao, Peitian Zhang, Kun Luo, Defu Lian, and Zheng Liu. M3-embedding: Multi-linguality, multi-functionality, multi-granularity text embeddings through self-knowledge distillation. In Findings of the Association for Computational Linguistics: ACL 2024, pp. 2318–2335, Bangkok, Thailand, August 2024. Association for Computational Linguistics. URL https:// aclanthology.org/2024.findings-acl.137/.
Kenneth Enevoldsen, Isaac Chung, Imene Kerboua, Marton Kardos, Ashwin Mathur, David Stap, ´ Jay Gala, Wissam Siblini, Dominik Krzeminski, Genta Indra Winata, et al. MMTEB: Massive ´ multilingual text embedding benchmark. In The Thirteenth International Conference on Learning Representations, 2025. URL https://openreview.net/forum?id=zl3pfz4VCV.
Tao Ge, Xin Chan, Xiaoyang Wang, Dian Yu, Haitao Mi, and Dong Yu. Scaling synthetic data creation with 1,000,000,000 personas. ar Xiv preprint ar Xiv: 2406.20094, 2024.
Jui-Ting Huang, Ashish Sharma, Shuying Sun, Li Xia, David Zhang, Philip Pronin, Janani Padmanabhan, Giuseppe Ot

#### Rank 10 | Score: 0.8065 | Chunk: 4 | Document: arxiv__2506.05176__qwen3-embedding.md

of the Qwen3 backbone models (including 0.6B, 4B, and 8B), we ultimately trained three text embedding models and three text reranking models. To facilitate their application in downstream tasks, the Qwen3 Embedding series supports several practical features, such as flexible dimension representation for embedding models and customizable instructions for both embedding and reranking models.

We evaluate the Qwen3 Embedding series across a comprehensive set of benchmarks spanning multiple tasks and domains. Experimental results demonstrate that our embedding and reranking models achieve state-of-the-art performance, performing competitively against leading proprietary models in several retrieval tasks. For example, the flagship model Qwen3-8B-Embedding attains a score of 70.58 on the MTEB Multilingual benchmark (Enevoldsen et al., 2025) and 80.68 on the MTEB Code benchmark (Enevoldsen et al., 2025), surpassing the previous state-of-the-art proprietary embedding model, Gemini-Embedding (Lee et al., 2025b). Moreover, our reranking model delivers competitive results across a range of retrieval tasks. The Qwen3-Reranker-0.6B model exceeds previously top-performing models in numerous retrieval tasks, while the larger Qwen3-Reranker-8B model demonstrates even superior performance, improving ranking results by 3.0 points over the 0.6B model across multiple tasks. Furthermore, we include a constructive ablation study to elucidate the key factors contributing to the superior performance of the Qwen3 Embedding series, providi


## Query 19: "What are the scaling strategies and performance tuning considerations for vector search using pgvector at production scale?"


### dense

#### Rank 1 | Score: 0.8104 | Chunk: 5 | Document: www_crunchydata_com__blog__pgvector-performance-for-developers.md

So, make sure your Postgres provider gives you the ability to tune settings.

pgvector provides a comprehensive, performant, and 100% open source database for vector data. As a developer, the key to getting performance from pgvector are:

  1. Ensure your query is using the indexes
  2. Ensure your indexes have the optimal list size
  3. Ensure you have enough memory for the index

_This isn't a static idea._ As you continue to build addition

#### Rank 2 | Score: 0.8082 | Chunk: 11 | Document: www_crunchydata_com__blog__scaling-vector-data-with-postgres.md

the query on the following compacted embedding, we get similar results:

```sql
SELECT
    id, name
FROM recipes
ORDER BY compacted_embedding <-> (SELECT compacted_embedding FROM recipes WHERE id = 151)
LIMIT 5;
```

```
name
--------------------------
 Cookies, chocolate chip
 Cookies, crisp chocolate
 Cookies, chocolate drop
 Cookies, coconut cereal
 Cookies, peanut butter
(5 rows)
```

If your results are like mine, there may be a few trade-offs between the top-5. Not all results will have equal trade-offs, so it is up to you to determine if this fits your use case. Broad datasets will have more detail in smaller differences. Common datasets, like recipes, will have the majority of difference in the vectors with the largest ranges.

## Conclusion

There are a few paths to scaling vector data. Start with the end in mind. Pencil in where your use-case lands on the path between accuracy and performance. First, seek performance, then seek scale. The toolbox is a common one.

As you start building and scaling your pg_vector database:

  * Physically separate the vector db from your other production resources. T

#### Rank 3 | Score: 0.7857 | Chunk: 0 | Document: www_crunchydata_com__blog__scaling-vector-data-with-postgres.md

<!-- source: https://www.crunchydata.com/blog/scaling-vector-data-with-postgres -->

# Scaling Vector Data with Postgres

Christopher Winslett
Aug 25, 2023 · 12 min read

**Note: We have additional articles in this [Postgres AI series](https://www.crunchydata.com/blog/topic/ai).**

[Vector data](https://www.crunchydata.com/blog/whats-postgres-got-to-do-with-ai) has made its way into Postgres and I'm seeing more and more folks using it by the day. As I've seen use cases trickle in, I have been thinking a lot about scaling data and how to set yourself up for performance success from the beginning. The two primary trade-offs are performance versus accuracy. When seeking performance with vector data, we are using nearest neighbor algorithms, and those algorithms are built around probability of proximity. If your use-case requires 100% accuracy on nearest neighbor, performance will be sacrificed.

After choosing between performance versus accuracy, the next tools in the toolbox are caching and partitioning. Caching is obvious in some situations, if your product is finding "similar meals" or "similar products" or "similar support questions", then the similarities will not change rapidly.

For the most part, t

#### Rank 4 | Score: 0.7648 | Chunk: 2 | Document: www_crunchydata_com__blog__scaling-vector-data-with-postgres.md

and build the new index.

Vector data has sizable RAM requirements, so you can keep your operational Postgres database and vector databases on appropriately sized instances. We've recommended physical separation of data previously in [Thinking Fast and Slow with your Data](https://www.crunchydata.com/blog/thinking-fast-vs-slow-with-your-data-in-postgres).

## Performance first

If your use case can benefit from nearest-neighbor vector queries, then start with performance before scaling — concentrate on finding the right tuning for the index. To help with that process, I wrote about [making vector data performant](https://www.crunchydata.com/blog/pgvector-performance-for-developers). Query tuning sounds simple, but just make sure your databases are using the available indexes — small changes to a query will change the inference of the query optimizer, which will not use the index. When it comes to vector queries, keep it simple.

Small setting changes to the index's list values may affect query performance. The time spent tuning the vector data will be much quicker if you are working with physically separate data from the application.

## Categorizing and Separating Data

Separating data can be done with conditional logic or it can be done at the schema level. For logical separation one easy way to do th

#### Rank 5 | Score: 0.7598 | Chunk: 0 | Document: www_crunchydata_com__blog__pgvector-performance-for-developers.md

<!-- source: https://www.crunchydata.com/blog/pgvector-performance-for-developers -->

# Performance Tips Using Postgres and pgvector

Christopher Winslett
May 5, 2023 · 7 min read

**Note: pgvector 0.5 released HNSW indexes which improved performance significantly. Read more about it [HNSW Indexes with Postgres and pgvector](https://www.crunchydata.com/blog/hnsw-indexes-with-postgres-and-pgvector). We have additional articles in this [Postgres AI series](https://www.crunchydata.com/blog/topic/ai).**

As we've been helping people get started with AI in Postgres with `pgvector`, there have been few questions around performance. At a basic level, pgvector performance relies on 3 things:

  1. Are your queries using indexes?
  2. Are you setting your `list` size appropriately for your data set?
  3. Do you have enough memory for your indexes + ability to change settings?

For an intro to using pgvector, see [What's Postgres Got To Do With AI](https://www.crunchydata.com/blog/whats-postgres-got-to-do-with-ai). In it, we discuss the vector datatype, querying, and indexing options. During this blog post, we will refer to a "recipes". In the prior blog post, we built an AI powered recipe recommendation engine.

## Do you want an index?

Probably you do. It is important to note that vector indexes allow "approximate nearest neighbor" (ANN) searching. So if you have a hard requirement that a query return absolutely 100% of all nearby vectors, you are going to be stuck with full scans, which will be slow on large data sets.

However, most vector use cas

#### Rank 6 | Score: 0.7559 | Chunk: 1 | Document: www_crunchydata_com__blog__scaling-vector-data-with-postgres.md

keys to scaling AI data are the same as scaling any other data type: reduce the number of rows in index and reduce the concurrent queries hitting the database. Once the index has done its work, CPU becomes the primary constraint: how fast can you calculate and compare distances between vectors? Scaling vector data is currently about performance mitigation as much as it is overpowering the data.

In the next few weeks, the Postgres pg_vector extension is launching HNSW indexes ([see the commit history for pgvector](https://github.com/pgvector/pgvector/commits/master) loaded with HNSW commits)— a graph-based algorithm for finding nearest neighbor. When HNSW indexes launch, these scaling practices will continue to be applicable. HNSW has better performance and scale than the current list-based indexes, but it too incurs costs in terms of storage and build time.

## Physical separation of data

My biggest advice here is to use a physically separate database for your vector data. Store your application data on one database, and store vector, lookup values and filter values on a separate database. You can easily connect the two with the Postgres foreign data wrapper.

Why separate your AI data? It gives you more flexibility when working with vector data out of AI models. Should you retrain your model, the vector output will be different, and you'll need to rebuild the data and rebuild the indexes. When you want to experiment with the soon-to-launch HNSW indexing strategy, for example, you can [fork your Postgres database](https://docs.crunchybridge.com/how-to/poi

#### Rank 7 | Score: 0.741 | Chunk: 11 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

LIMIT 5;
```

Long-story short, the simpler the better for HNSW usage.

## HNSW indexes and scaling

HNSW indexes are much more performant than the older list-based indexes. They also use more resources. Concurrency is improved, but many of the processes we laid out in the [Scaling PGVector blog post](https://www.crunchydata.com/blog/scaling-vector-data-with-postgres) are still applicable.

  1. Physical separation of data: because of the build requirements of the indexes, continue to host your vec

#### Rank 8 | Score: 0.6931 | Chunk: 0 | Document: www_thenile_dev__blog__pgvector-080.md

<!-- source: https://www.thenile.dev/blog/pgvector-080 -->

## Announcing: pgvector 0.8.0 released and available on Nile

Gwen Shapira — 2024-11-05

The pgvector community shipped the much anticipated version 0.8.0 with significant performance and functionality improvements. Naturally, we couldn't wait to make it available to Nile users.
## Release highlights
Per the official release notes, pgvector 0.8.0 includes:
  * Added support for iterative index scans
  * Added casts for arrays to sparsevec
  * Improved cost estimation for better index selection when filtering
  * Improved performance of HNSW index scans
  * Improved performance of HNSW inserts and on-disk index builds
  * Dropped support for Postgres 12

The most anticipated feature is iterative index scanning, which addresses a longstanding challenge with vector indexes. Previously, filters were applied after the index scan completed, which often yielded fewer results than expected. According to the pgvector documentation:
> With approximate indexes, filtering is applied after the index is scanned. If a condition matches 10% of rows, with HNSW and the de

#### Rank 9 | Score: 0.684 | Chunk: 4 | Document: www_crunchydata_com__blog__pgvector-performance-for-developers.md

for your dataset and query. But that will change tomorrow.

If your application is querying in a way that uses indexes, increasing list size _may_ improve query performance, but will be much, much slower to build.

## Enough memory for your indexes + ability to change memory settings

Keeping indexes in memory is essential, no matter the data set. You'll need the memory for two reasons:

**Have enough RAM for entire index size.** Indexes of vector data sets can be sizeable, and increase in size as the data size increases. In our tests, the indexes sizes were as large as the table sizes. Surprisingly, larger list sizes did not significant impact on the data size of the index — lists = 500 and lists = 2000 generated similar index sizes (only a 1.5% difference).

Check indexes sizes by running the following command in `psql`:

```
\di+ index_name
```

**Have enough RAM to build new indexes.** Building indexes with larger lists requires higher settings for `maintenance_work_mem` — if you do not have the enough memory you'll get an error. When building the lists = 2000 index above, the the `maintenance_work_mem` required 1.3GB of RAM.

```
recipes=# CREATE INDEX ON recipes USING ivfflat (embedding vector_l2_ops) WITH (lists = 2000);
ERROR:  memory required is 1390 MB, maintenance_work_mem is 1024 MB
```

**Ability to change `maintenance_work_mem` settings**. You can't even build indexes with a larger list size unless you can increase the `mainte

#### Rank 10 | Score: 0.6717 | Chunk: 0 | Document: www_crunchydata_com__blog__hnsw-indexes-with-postgres-and-pgvector.md

<!-- source: https://www.crunchydata.com/blog/hnsw-indexes-with-postgres-and-pgvector -->

# HNSW Indexes with Postgres and pgvector

Christopher Winslett
Sep 1, 2023 · 12 min read

Postgres' [pgvector extension](https://github.com/pgvector/pgvector) recently added HNSW as a new index type for vector data. This levels up the database for vector-based embeddings output by AI models. A few months ago, we had written about approximate nearest neighbor [pgvector performance using the available list-based indexes](https://www.crunchydata.com/blog/pgvector-performance-for-developers). Now, with the addition of HNSW, pgvector can use the latest graph based algorithms to approximate nearest neighbor queries. As with all things databases, there are trade-offs, so don't throw away the list-based methodologies — and don't throw away the techniques we discussed in [scaling vector data](https://www.crunchydata.com/blog/scaling-vector-data-with-postgres).




## Query 20: "What techniques exist for enriching document chunks with surrounding context before indexing to improve RAG retrieval accuracy?"


### dense

#### Rank 1 | Score: 0.7858 | Chunk: 6 | Document: www_anthropic_com__engineering__contextual-retrieval.md

to generate context for each chunk:
```
<document> 
{{WHOLE_DOCUMENT}} 
</document> 
Here is the chunk we want to situate within the whole document 
<chunk> 
{{CHUNK_CONTENT}} 
</chunk> 
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. 
```

Copy
The resulting contextual text, usually 50-100 tokens, is prep

#### Rank 2 | Score: 0.7858 | Chunk: 6 | Document: www_anthropic_com__news__contextual-retrieval.md

to generate context for each chunk:
```
<document> 
{{WHOLE_DOCUMENT}} 
</document> 
Here is the chunk we want to situate within the whole document 
<chunk> 
{{CHUNK_CONTENT}} 
</chunk> 
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. 
```

Copy
The resulting contextual text, usually 50-100 tokens, is prep

#### Rank 3 | Score: 0.7727 | Chunk: 5 | Document: www_anthropic_com__engineering__contextual-retrieval.md

return to our SEC filings collection example. Here's an example of how a chunk might be transformed:
```
original_chunk = "The company's revenue grew by 3% over the previous quarter."

contextualized_chunk = "This chunk is from an SEC filing on ACME corp's performance in Q2 2023; the previous quarter's revenue was $314 million. The company's revenue grew by 3% over the previous quarter."
```

Copy
It is worth noting that other approaches to using context to improve retrieval have been proposed in the past. Other proposals include: [adding generic document summaries to chunks](https://aclanthology.org/W02-0405.pdf) (we experimented and saw very limited gains), [hypothetical document embedding](https://arxiv.org/abs/2212.10496), and [summary-based indexing](https://www.llamaindex.ai/blog/a-new-document-summary-index-for-llm-powered-qa-systems-9a32ece2f9ec) (we evaluated and saw low performance). These methods differ from what is proposed in this post.
### Implementing Contextual Retrieval
Of course, it would be far too much work to manually annotate the thousands or even millions of chunks in a knowledge base. To implement Contextual Retrieval, we turn to Claude. We’ve written a prompt that instructs the model to provide concise, chunk-specific context that explains the chunk using the context of the overall document. We used the following Claude 3 Haiku pr

#### Rank 4 | Score: 0.7727 | Chunk: 5 | Document: www_anthropic_com__news__contextual-retrieval.md

return to our SEC filings collection example. Here's an example of how a chunk might be transformed:
```
original_chunk = "The company's revenue grew by 3% over the previous quarter."

contextualized_chunk = "This chunk is from an SEC filing on ACME corp's performance in Q2 2023; the previous quarter's revenue was $314 million. The company's revenue grew by 3% over the previous quarter."
```

Copy
It is worth noting that other approaches to using context to improve retrieval have been proposed in the past. Other proposals include: [adding generic document summaries to chunks](https://aclanthology.org/W02-0405.pdf) (we experimented and saw very limited gains), [hypothetical document embedding](https://arxiv.org/abs/2212.10496), and [summary-based indexing](https://www.llamaindex.ai/blog/a-new-document-summary-index-for-llm-powered-qa-systems-9a32ece2f9ec) (we evaluated and saw low performance). These methods differ from what is proposed in this post.
### Implementing Contextual Retrieval
Of course, it would be far too much work to manually annotate the thousands or even millions of chunks in a knowledge base. To implement Contextual Retrieval, we turn to Claude. We’ve written a prompt that instructs the model to provide concise, chunk-specific context that explains the chunk using the context of the overall document. We used the following Claude 3 Haiku pr

#### Rank 5 | Score: 0.7623 | Chunk: 0 | Document: docs_together_ai__docs__how-to-implement-contextual-rag-from-anthropic.md

<!-- source: https://docs.together.ai/docs/how-to-implement-contextual-rag-from-anthropic -->

# How To Implement Contextual RAG From Anthropic

[Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) is a chunk augmentation technique that uses an LLM to enhance each chunk. Here's an overview of how it works.

## Contextual RAG

  1. For every chunk - prepend an explanatory context snippet that situates the chunk within the rest of the document. -> Get a small cost effective LLM to do this.
  2. Hybrid Search: Embed the chunk using both sparse (keyword) and dense(semantic) embeddings.
  3. Perform rank fusion using an algorithm like Reciprocal Rank Fusion(RRF).
  4. Retrieve top 150 chunks and pass those to a Reranker to obtain top 20 chunks.
  5. Pass top 20 chunks to LLM to generate an answer.

Below we implement each step in this process using Open Source models. To breakdown the concept further we break down the process into a one-time indexing step and a query time step. **Data Ingestion Phase:**

  1. Data processing and chunking
  2. Context generation using Qwen3.5-9B
  3. Vector Embedding and Index Generation
  4. BM25 Keyword Index Generation

**At Query Time:**

  1. Perform retrieval using both indices and combine them using RRF
  2. Reranker to improve retrieval quality
  3. Generation with Llama3.1 405B

## Install Libraries

```
pip install together # To access

#### Rank 6 | Score: 0.7129 | Chunk: 21 | Document: zilliz_com__learn__guide-to-chunking-strategies-for-rag.md

and contextually nuanced. This case highlighted the benefits of context-enriched chunking in a RAG setup, where the retrieval component could leverage broader contextual cues to enhance answer quality and relevance​ (Optimizing Retrieval-Augmented Generation with Advanced Chunking Techniques: [A Comparative Study](https://antematter.io/blogs/optimizing-rag-advanced-chunking-techniques-study)).
  * **Case Study 2 - Advanced Semantic Chunking:** Advanced Semantic Chunking: Another successful implementation of a successful RAG implementation involves advanced semantic chunking techniques to enhance retrieval performance. By dividing documents into semantically coherent chunks rather than merely based on size or token count, the system significantly improved its ability to retrieve relevant information. This strategy ensured each chunk maintained its contextual integrity, leading to more

#### Rank 7 | Score: 0.709 | Chunk: 4 | Document: www_anthropic_com__engineering__contextual-retrieval.md

into smaller chunks for efficient retrieval. While this approach works well for many applications, it can lead to problems when individual chunks lack sufficient context.
For example, imagine you had a collection of financial information (say, U.S. SEC filings) embedded in your knowledge base, and you received the following question: _"What was the revenue growth for ACME Corp in Q2 2023?"_
A relevant chunk might contain the text: _"The company's revenue grew by 3% over the previous quarter."_ However, this chunk on its own doesn't specify which company it's referring to or the relevant time period, making it difficult to retrieve the right information or use the information effectively.
## Introducing Contextual Retrieval
Contextual Retrieval solves this problem by prepending chunk-specific explanatory context to each chunk before embedding (“Contextual Embeddings”) and creating the BM25 index (“Contextual BM25”).


#### Rank 8 | Score: 0.709 | Chunk: 4 | Document: www_anthropic_com__news__contextual-retrieval.md

into smaller chunks for efficient retrieval. While this approach works well for many applications, it can lead to problems when individual chunks lack sufficient context.
For example, imagine you had a collection of financial information (say, U.S. SEC filings) embedded in your knowledge base, and you received the following question: _"What was the revenue growth for ACME Corp in Q2 2023?"_
A relevant chunk might contain the text: _"The company's revenue grew by 3% over the previous quarter."_ However, this chunk on its own doesn't specify which company it's referring to or the relevant time period, making it difficult to retrieve the right information or use the information effectively.
## Introducing Contextual Retrieval
Contextual Retrieval solves this problem by prepending chunk-specific explanatory context to each chunk before embedding (“Contextual Embeddings”) and creating the BM25 index (“Contextual BM25”).


#### Rank 9 | Score: 0.6981 | Chunk: 25 | Document: zilliz_com__learn__guide-to-chunking-strategies-for-rag.md

* [**Implementing Chunking in RAG Pipelines**](https://zilliz.com/learn/guide-to-chunking-strategies-for-rag#Implementing-Chunking-in-RAG-Pipelines)
  * [**Performance Optimization in RAG Systems Through Chunking Strategies**](https://zilliz.com/learn/guide-to-chunking-strategies-for-rag#Performance-Optimization-in-RAG-Systems-Through-Chunking-Strategies)
  * [**Case Studies on Successful RAG Implementations with Innovative Chunking Strategies**](https://zilliz.com/learn/guide-to-chunking-strategies-for-rag#Case-Studies-on-Successful-RAG-Implementations-with-Innovative-Chunking-Strategies)
  * [**Conclusion: The Strategic Significance of Chunking in RAG Systems**](https://zilliz.com/learn/guide-to-chunking-strategies-for-rag#Conclusion-The-Strategic-Significance-of-Chunking-in-RAG-Systems)
  * [**Recap of Key Points**](https://zilliz.com/learn/guide-to-chun

#### Rank 10 | Score: 0.6968 | Chunk: 2 | Document: docs_together_ai__docs__how-to-implement-contextual-rag-from-anthropic.md

using quantized small 1-3B models along with prompt caching makes this more feasible. Prompt caching allows key and value matrices corresponding to the document to be cached for future LLM calls.

```python
CONTEXTUAL_RAG_PROMPT = """
Given the document below, we want to explain what the chunk captures in the document.

{WHOLE_DOCUMENT}

Here is the chunk we want to explain:

{CHUNK_CONTENT}

Answer ONLY with a succinct explaination of the meaning of the chunk in the context of the whole document above.
"""
```

```python
from typing import List
import together, os
from together import Together

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = Together(api_key=TOGETHER_API_KEY)


def generate_prompts(document: str, chunks: List[str]) -> List[str]:
    prompts = []
    for chunk in chunks:
        prompt = CONTEXTUAL_RAG_PROMPT.format(
            WHOLE_DOCUMENT=document,
            CHUNK_CONTENT=chunk,
        )
        prompts.append(prompt)
    return prompts


prompts = generate_prompts(pg_essay, chunks)


def generate_context(prompt: str):
    response = client.chat.completions.create(
        model="Qwen/Qwen3.5-9B",
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
    )
    return response.choices[0].message.content
```

```python
contextual_chunks = [
    generate_context(prompts[i]) + " " + chunks[i] for i in range(len(chunks))
]
```

## Vector Index

We will now use `multilingual-e5-large-instruct` to embed the augmented chunks above into a vector index.

```python
from typing import List
import together

