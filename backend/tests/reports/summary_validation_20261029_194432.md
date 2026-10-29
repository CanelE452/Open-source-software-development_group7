# GitHub Issue 요약 근거 검증 보고서

- 실행 시각: 2026-10-29T19:44:32+09:00
- Issue: [How to use BERT for finding similar sentences or similar news? ](https://github.com/huggingface/transformers/issues/876)
- 요약 상태: `completed`

## 검증 결과


## 불일치 1: `conditions`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
코퍼스가 크면 BERT를 쌍을 비추는 방식으로 사용하면 시간이 비례해 두 배보다 훨씬 느려집니다. GPU를 활용하고도 10~15초가 걸리며, 한 번이라도 전체 코퍼스를 tensor로 바꾸면 비용이 크게 발생합니다.
````

- 근거 순번: 2
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-515027331
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `515027331`

### 모델이 제시한 발췌문

````text
I think you can use [faiss] for storing and finding similar embeddings.
````

- 실제 출처 유형: `comment`
- 실제 댓글 ID: `515027331`

### 해당 URL의 실제 원문

````text
I think you can use [faiss](https://github.com/facebookresearch/faiss) for storing and finding similar embeddings. 
````

## 불일치 2: `solution`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
문장(기사)을 한 번만 임베딩해 두고, 새 질의도 한 번만 임베딩한 뒤 cosine‑similarity(또는 다른 거리)로 유사도를 계산합니다. Sentence‑Transformers 라이브러리를 사용해 BERT 기반 문장 임베딩을 만들면 GPU에서도 수백~수천 개 문장을 초당 인코딩할 수 있고, FAISS를 이용해 인덱싱하면 4k~10k 문서에서도 단 몇 밀리초에 검색이 가능합니다.
````

- 근거 순번: 3
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-515027331
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `515027331`

### 모델이 제시한 발췌문

````text
I think you can use [faiss] for storing and finding similar embeddings.
````

- 실제 출처 유형: `comment`
- 실제 댓글 ID: `515027331`

### 해당 URL의 실제 원문

````text
I think you can use [faiss](https://github.com/facebookresearch/faiss) for storing and finding similar embeddings. 
````

## 불일치 3: `discussion`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
Sentence‑Transformers를 적용하면 GPU에서도 2,000 sentences/second 정도 속도로 인코딩이 가능해지며, CPU에서는 80 sentences/second 정도가 일반적입니다. 기존의 scipy.spatial.distance.cdist는 대규모 코퍼스에서 몇 분이 걸릴 정도가 되지만, FAISS를 쓰면 몇 밀리초 내에 거리를 계산할 수 있습니다. BLEU와 같은 평가 지표는 문장 유사성에 적합하지 않으며, Spearman 상관계수를 사용해 임베딩과 금형 스코어를 비교합니다.
````

- 근거 순번: 3
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-517558969
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `517558969`

### 모델이 제시한 발췌문

````text
No, BLEU is a terrible idea for evaluation. STS is usually evaluated using Pearson correlation between gold and predicted labels. But Pearson correlation is also a bad idea: ... I strongly recommend to use Spearman correlation for comparison.
````

- 실제 출처 유형: `comment`
- 실제 댓글 ID: `517558969`

### 해당 URL의 실제 원문

````text
No, BLEU is a terrible idea for evaluation.

STS is usually evaluated using Pearson correlation between gold and predicted labels. But Pearson correlation is also a bad idea:
https://aclweb.org/anthology/C16-1009

I strongly recommend to use Spearman correlation for comparison. 
````

## 불일치 4: `follow_up`

- 유형: `invalid_evidence`

- 사유: 근거 URL이 입력한 Issue 본문 또는 댓글 URL과 일치하지 않음

### 요약 텍스트

````text
사용자는 BERT 기반 임베딩을 사용해 코퍼스를 인코딩하고 FAISS에 인덱싱한 뒤, 질의 문장을 임베딩하고 유사도를 계산해 결과를 반환합니다. BM25와 결합하여 먼저 두 번째 단계를 재랭킹하면 더 높은 정확도를 얻을 수 있으며, 필요 시 모델 파인튜닝(Triplet‑Loss 등)을 적용할 수 있습니다.
````

- 근거 순번: 1
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-518186677
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `516186677`

### 모델이 제시한 발췌문

````text
If I want to train the model as you suggested which would yield better results, In that case, I should have labeled dataset right? However, for news, I only have titles and abstract about that news.
````

- 해당 URL은 수집한 Issue 본문이나 댓글에서 찾을 수 없습니다.

## 불일치 5: `follow_up`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
사용자는 BERT 기반 임베딩을 사용해 코퍼스를 인코딩하고 FAISS에 인덱싱한 뒤, 질의 문장을 임베딩하고 유사도를 계산해 결과를 반환합니다. BM25와 결합하여 먼저 두 번째 단계를 재랭킹하면 더 높은 정확도를 얻을 수 있으며, 필요 시 모델 파인튜닝(Triplet‑Loss 등)을 적용할 수 있습니다.
````

- 근거 순번: 2
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-516272045
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `516272045`

### 모델이 제시한 발췌문

````text
I also uploaded an example for semantic search, where each sentence in a corpus is mapped to a vector and than cosine-similarity is used to find the most similar sentences / vectors
````

- 실제 출처 유형: `comment`
- 실제 댓글 ID: `516272045`

### 해당 URL의 실제 원문

````text
Hi,
XLNet achieved state-of-the-art performance for supervised tasks like classification. But it is unclear if it generates also good embeddings for unsupervised tasks.

In the framework you can choose XLNet, but I was only able to produce results that are slightly below those of BERT.

Others also have problems getting a good performance with Xlnet for supervised tasks, as it appears that it is extremely sensitive to the hyper parameters.

If you have millions of docs, faiss makes sense. With scipy, you get exact scores. With faiss, the scores are fuzzy and the returned most similar vectors must not necessarily be the actual most similar vectors. There can be small variations. But I think the difference will be small.

Often you have in your data some structure, like categories or links between news articles. This structure can be used to fine-tune a model. Let's say you have links linking to similar events. Than you train the network with triplet loss with the two linked articles and one random other article as negative example.

This will give you a vector space where (possibly) linked articles are close. 
````

## 검증 범위 및 한계

이 보고서는 근거 URL, 출처 유형, 댓글 ID, 발췌문이 수집한 원문과 일치하는지를 기록합니다.
발췌문이 실제 원문에 존재하더라도 요약 문장의 의미를 논리적으로 뒷받침하는지까지 판정하지는 않습니다.
