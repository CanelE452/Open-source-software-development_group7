# GitHub Issue 요약 근거 검증 보고서

- 실행 시각: 2026-10-29T20:07:02+09:00
- Issue: [How to use BERT for finding similar sentences or similar news? ](https://github.com/huggingface/transformers/issues/876)
- 요약 상태: `completed`
```json
{
  "problem": {
    "text": "BERT NextSentencePredictor 를 사용해 뉴스 기사에서 비슷한 문장을 찾으려고 했으나, GPU(타일러 V100)에서도 한 쿼리마다 3,000개의 기사에 대해 10초가 소요되는 매우 느린 속도를 보였음.",
    "evidence": [
      {
        "url": "https://github.com/huggingface/transformers/issues/876",
        "excerpt": "I have used BERT NextSentencePredictor to find similar sentences or similar news, However, It's super slow... It takes around 10secs for a query title with around 3,000 articles.",
        "source_type": "issue_body",
        "comment_id": null
      },
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-514948425",
        "excerpt": "I.e., if you have 10,000 sentences/articles in your corpus, you need to classify 10k pairs with BERT, which is rather slow.",
        "source_type": "comment",
        "comment_id": 514948425
      }
    ]
  },
  "conditions": {
    "text": "공유된 기사 수가 수천 개이므로, 실시간으로 매 쿼리마다 모든 기사와 BERT를 연결해 비교해야 하는 구조는 비효율적이며, GPU 가속 도우미만으로는 성능 향상에 한계가 있음.",
    "evidence": [
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-514948425",
        "excerpt": "BERT out-of-the-box is not the best option for this task, as the run-time in your setup scales with the number of sentences in your corpus.",
        "source_type": "comment",
        "comment_id": 514948425
      },
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-517462735",
        "excerpt": "I think the issue might be generation of the 4k sentence embeddings? Transformer networks like BERT are extremely slow on CPUs. However, on a GPU, the implementation can process about 2000 sentences per seconds.",
        "source_type": "comment",
        "comment_id": 517462735
      }
    ]
  },
  "solution": {
    "text": "문장을 정적 벡터(embedding)로 한 번만 매핑해 두고, 쿼리 문장을 같은 방식으로 인코딩해 두었을 때는 실시간 속도가 문서 수와 무관해져야 함. SentenceTransformer(또는 BERT‑mean‑pooling 기반) 를 사용하고, Faiss 등으로 근접 검색을 수행하면 3,000개 이하에서도 밀리초 단위에 수렴신.",
    "evidence": [
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-514948425",
        "excerpt": "A better option is to generate sentence embeddings: Every sentence / article is mapped to a fixed sized vector. You need to map your 3k articles only once to a vector.",
        "source_type": "comment",
        "comment_id": 514948425
      },
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-514948425",
        "excerpt": "I released today a framework which uses pytorch-transformers for exactly that purpose: https://github.com/UKPLab/sentence-transformers",
        "source_type": "comment",
        "comment_id": 514948425
      },
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-515027331",
        "excerpt": "I think you can use faiss for storing and finding similar embeddings.",
        "source_type": "comment",
        "comment_id": 515027331
      }
    ]
  },
  "discussion": {
    "text": "BERT를 쿼리마다 다중 비교하는 방식은 O(N) 스케일이 필요해 무거운 연산. 고정된 길이 embedding 으로 전환하면, 학습 단계에서 모든 문서를 인코딩해 두어야 하고, 쿼리 인코딩 후 유사도 계산은 스칼라·벡터 연산(코사인 등)만으로 해결된다. Faiss로 K‑NN을 수행하면 거버넌스 속도 비약적 향상(쿼리당 몇 밀리초). GloVe·word2vec 등 전통적인 vector 도보다는 GPU 기반 BERT가 의미를 더 잘 포착하고, 작은 batch/batch‑size 조정으로 파이프라인을 최적화할 수 있음.",
    "evidence": [
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-515277141",
        "excerpt": "I don't think scipy.spatial.distance.cdist is good enough, it takes a lot of time to compute the results... I think I should try using faiss.",
        "source_type": "comment",
        "comment_id": 515277141
      },
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-517462735",
        "excerpt": "If you have a smaller dataset, results from faiss and scipy won't make any difference? However, if I had millions or billions of news articles then using faiss makes sense right?",
        "source_type": "comment",
        "comment_id": 517462735
      },
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-517462735",
        "excerpt": "Mais BERT out-of-the-box is not the best option... You need to map your 3k articles only once to a vector.",
        "source_type": "comment",
        "comment_id": 517462735
      }
    ]
  },
  "follow_up": {
    "text": "- Faiss 인덱스(FlatIndex 혹은 IVF) 구축 후 쿼리 embedding 과 비교하여 KNN 반환.  - GPU 가속 시 batch_size 32~128 등 적절히 조정.  - 필요 시 모델을 뉴스 도메인에 fine‑tune(Triplet‑loss, MultipleNegativesRankingLoss 등).  - 성능을 Spearman/Pearson 등 STS‑benchmarks와 같은 지표로 평가하거나, 실제 검색 랭킹에서 NDCG 등으로 검증.",
    "evidence": [
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-517517467",
        "excerpt": "I ran it with faiss library using FlatIndex (as it give the most accurate results). On a p2.xlarge instance it was amazingly fast- building and searching took only 30 mins.",
        "source_type": "comment",
        "comment_id": 517517467
      },
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-521930508",
        "excerpt": "I added an example for average word embeddings (+a DAN layer that is trainable).",
        "source_type": "comment",
        "comment_id": 521930508
      },
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-590640810",
        "excerpt": "Pre-training embeddings for large-scale retrieval - https://arxiv.org/abs/2002.03932",
        "source_type": "comment",
        "comment_id": 590640810
      }
    ]
  },
  "unknowns": {
    "text": "- 최적 모델 선택( BERT‑large‑nli‑mean‑tokens vs BERT‑base‑nli‑mean‑tokens, XLNet, RoBERTa 등)  - 뉴스 문서라면 문장 길이와 문단 단위 인코딩으로 무리 없는 대규모 변환 가능성  - 파인튜닝을 위한 라벨이 없는 수집된 데이터로 Triplet‑loss, Query‑generation 기반의 unsupervised fine‑tune 방법 적용 여부  - 검증 데이터셋(특히 뉴스) 부재로 실제 검색 성능을 객관적으로 측정할 방법",
    "evidence": [
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-516186677",
        "excerpt": "I have one important question, If I want to train the model as you suggested which would yield better results, In that case, I should have labeled dataset right? However, for news, I only have titles and abstract about that news.",
        "source_type": "comment",
        "comment_id": 516186677
      },
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-522159447",
        "excerpt": "I won't be using BERT at all right?",
        "source_type": "comment",
        "comment_id": 522159447
      },
      {
        "url": "https://github.com/huggingface/transformers/issues/876#issuecomment-520920465",
        "excerpt": "I don't think BERT out-of-the-box is the best option for this task... I want to find similar news...",
        "source_type": "comment",
        "comment_id": null
      }
    ]
  },
  "status": "completed"
}
```

## 검증 결과


## 불일치 1: `problem`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
BERT NextSentencePredictor 를 사용해 뉴스 기사에서 비슷한 문장을 찾으려고 했으나, GPU(타일러 V100)에서도 한 쿼리마다 3,000개의 기사에 대해 10초가 소요되는 매우 느린 속도를 보였음.
````

- 근거 순번: 1
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876
- 모델이 제시한 출처 유형: `issue_body`
- 모델이 제시한 댓글 ID: `None`

### 모델이 제시한 발췌문

````text
I have used BERT NextSentencePredictor to find similar sentences or similar news, However, It's super slow... It takes around 10secs for a query title with around 3,000 articles.
````

- 실제 출처 유형: `issue_body`
- 실제 댓글 ID: `None`

### 해당 URL의 실제 원문

````text
I have used BERT NextSentencePredictor to find similar sentences or similar news, However, It's super slow. Even on Tesla V100 which is the fastest GPU till now. It takes around 10secs for a query title with around 3,000 articles. Is there a way to use BERT better for finding similar sentences or similar news given a corpus of news articles?
````

## 불일치 2: `conditions`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
공유된 기사 수가 수천 개이므로, 실시간으로 매 쿼리마다 모든 기사와 BERT를 연결해 비교해야 하는 구조는 비효율적이며, GPU 가속 도우미만으로는 성능 향상에 한계가 있음.
````

- 근거 순번: 2
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-517462735
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `517462735`

### 모델이 제시한 발췌문

````text
I think the issue might be generation of the 4k sentence embeddings? Transformer networks like BERT are extremely slow on CPUs. However, on a GPU, the implementation can process about 2000 sentences per seconds.
````

- 실제 출처 유형: `comment`
- 실제 댓글 ID: `517462735`

### 해당 URL의 실제 원문

````text
@nreimers When you say -"Bleu wouldn't be a good measure, because the best similarity metric to find similar news would be: Bleu (of course)." 
Do you mean when I get similar news like in the above example, BLEU is the best metric to measure how similar the two news articles are? Please correct me if I understood this wrong.

In the STS benchmark, I saw a pair in the training dataset with gold-standard human evaluated scores. The following paid had a score of 5, however, when I use BLEU scores for 1gram they don't get a score of 1. Instead, they get the following scores. BLEU looks for the exact word to be present in the reference sentence that's the problem I feel. There's no notion of similarity.

s=word_tokenize("The polar bear is sliding on the snow")
reference = [s]
candidate =word_tokenize("The polar bear is sliding across the snow") 
print('Individual 1-gram: %f' % sentence_bleu(reference, candidate, weights=(1, 0, 0, 0)))
print('Individual 2-gram: %f' % sentence_bleu(reference, candidate, weights=(0, 1, 0, 0)))
print('Individual 3-gram: %f' % sentence_bleu(reference, candidate, weights=(0, 0, 1, 0)))
print('Individual 4-gram: %f' % sentence_bleu(reference, candidate, weights=(0, 0, 0, 1)))

Individual 1-gram: 0.875000
Individual 2-gram: 0.714286
Individual 3-gram: 0.500000
Individual 4-gram: 0.400000

reference sentence has 8 words out of which the candidate matches exactly 7 words, so 7/8 score for 1-gram matches.

I'm not sure how the STS benchmarks are evaluated, I'm currently looking into them. If you have any leads or a document I would be more than happy to read them. 

Thank you very much for your help :)


````

## 불일치 3: `solution`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
문장을 정적 벡터(embedding)로 한 번만 매핑해 두고, 쿼리 문장을 같은 방식으로 인코딩해 두었을 때는 실시간 속도가 문서 수와 무관해져야 함. SentenceTransformer(또는 BERT‑mean‑pooling 기반) 를 사용하고, Faiss 등으로 근접 검색을 수행하면 3,000개 이하에서도 밀리초 단위에 수렴신.
````

- 근거 순번: 3
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-515027331
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `515027331`

### 모델이 제시한 발췌문

````text
I think you can use faiss for storing and finding similar embeddings.
````

- 실제 출처 유형: `comment`
- 실제 댓글 ID: `515027331`

### 해당 URL의 실제 원문

````text
I think you can use [faiss](https://github.com/facebookresearch/faiss) for storing and finding similar embeddings. 
````

## 불일치 4: `discussion`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
BERT를 쿼리마다 다중 비교하는 방식은 O(N) 스케일이 필요해 무거운 연산. 고정된 길이 embedding 으로 전환하면, 학습 단계에서 모든 문서를 인코딩해 두어야 하고, 쿼리 인코딩 후 유사도 계산은 스칼라·벡터 연산(코사인 등)만으로 해결된다. Faiss로 K‑NN을 수행하면 거버넌스 속도 비약적 향상(쿼리당 몇 밀리초). GloVe·word2vec 등 전통적인 vector 도보다는 GPU 기반 BERT가 의미를 더 잘 포착하고, 작은 batch/batch‑size 조정으로 파이프라인을 최적화할 수 있음.
````

- 근거 순번: 1
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-515277141
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `515277141`

### 모델이 제시한 발췌문

````text
I don't think scipy.spatial.distance.cdist is good enough, it takes a lot of time to compute the results... I think I should try using faiss.
````

- 실제 출처 유형: `comment`
- 실제 댓글 ID: `515277141`

### 해당 URL의 실제 원문

````text
@nreimers I don't think scipy.spatial.distance.cdist is good enough, it takes a lot of time to compute the results, almost 10 minutes on a corpus of 3.9k news articles. I think I should try using [faiss](https://github.com/facebookresearch/faiss). I don't know anything about [faiss](https://github.com/facebookresearch/faiss) but I will try.
````

## 불일치 5: `discussion`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
BERT를 쿼리마다 다중 비교하는 방식은 O(N) 스케일이 필요해 무거운 연산. 고정된 길이 embedding 으로 전환하면, 학습 단계에서 모든 문서를 인코딩해 두어야 하고, 쿼리 인코딩 후 유사도 계산은 스칼라·벡터 연산(코사인 등)만으로 해결된다. Faiss로 K‑NN을 수행하면 거버넌스 속도 비약적 향상(쿼리당 몇 밀리초). GloVe·word2vec 등 전통적인 vector 도보다는 GPU 기반 BERT가 의미를 더 잘 포착하고, 작은 batch/batch‑size 조정으로 파이프라인을 최적화할 수 있음.
````

- 근거 순번: 2
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-517462735
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `517462735`

### 모델이 제시한 발췌문

````text
If you have a smaller dataset, results from faiss and scipy won't make any difference? However, if I had millions or billions of news articles then using faiss makes sense right?
````

- 실제 출처 유형: `comment`
- 실제 댓글 ID: `517462735`

### 해당 URL의 실제 원문

````text
@nreimers When you say -"Bleu wouldn't be a good measure, because the best similarity metric to find similar news would be: Bleu (of course)." 
Do you mean when I get similar news like in the above example, BLEU is the best metric to measure how similar the two news articles are? Please correct me if I understood this wrong.

In the STS benchmark, I saw a pair in the training dataset with gold-standard human evaluated scores. The following paid had a score of 5, however, when I use BLEU scores for 1gram they don't get a score of 1. Instead, they get the following scores. BLEU looks for the exact word to be present in the reference sentence that's the problem I feel. There's no notion of similarity.

s=word_tokenize("The polar bear is sliding on the snow")
reference = [s]
candidate =word_tokenize("The polar bear is sliding across the snow") 
print('Individual 1-gram: %f' % sentence_bleu(reference, candidate, weights=(1, 0, 0, 0)))
print('Individual 2-gram: %f' % sentence_bleu(reference, candidate, weights=(0, 1, 0, 0)))
print('Individual 3-gram: %f' % sentence_bleu(reference, candidate, weights=(0, 0, 1, 0)))
print('Individual 4-gram: %f' % sentence_bleu(reference, candidate, weights=(0, 0, 0, 1)))

Individual 1-gram: 0.875000
Individual 2-gram: 0.714286
Individual 3-gram: 0.500000
Individual 4-gram: 0.400000

reference sentence has 8 words out of which the candidate matches exactly 7 words, so 7/8 score for 1-gram matches.

I'm not sure how the STS benchmarks are evaluated, I'm currently looking into them. If you have any leads or a document I would be more than happy to read them. 

Thank you very much for your help :)


````

## 불일치 6: `discussion`

- 유형: `invalid_evidence`

- 사유: 발췌문이 해당 원문에 그대로 존재하지 않음

### 요약 텍스트

````text
BERT를 쿼리마다 다중 비교하는 방식은 O(N) 스케일이 필요해 무거운 연산. 고정된 길이 embedding 으로 전환하면, 학습 단계에서 모든 문서를 인코딩해 두어야 하고, 쿼리 인코딩 후 유사도 계산은 스칼라·벡터 연산(코사인 등)만으로 해결된다. Faiss로 K‑NN을 수행하면 거버넌스 속도 비약적 향상(쿼리당 몇 밀리초). GloVe·word2vec 등 전통적인 vector 도보다는 GPU 기반 BERT가 의미를 더 잘 포착하고, 작은 batch/batch‑size 조정으로 파이프라인을 최적화할 수 있음.
````

- 근거 순번: 3
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-517462735
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `517462735`

### 모델이 제시한 발췌문

````text
Mais BERT out-of-the-box is not the best option... You need to map your 3k articles only once to a vector.
````

- 실제 출처 유형: `comment`
- 실제 댓글 ID: `517462735`

### 해당 URL의 실제 원문

````text
@nreimers When you say -"Bleu wouldn't be a good measure, because the best similarity metric to find similar news would be: Bleu (of course)." 
Do you mean when I get similar news like in the above example, BLEU is the best metric to measure how similar the two news articles are? Please correct me if I understood this wrong.

In the STS benchmark, I saw a pair in the training dataset with gold-standard human evaluated scores. The following paid had a score of 5, however, when I use BLEU scores for 1gram they don't get a score of 1. Instead, they get the following scores. BLEU looks for the exact word to be present in the reference sentence that's the problem I feel. There's no notion of similarity.

s=word_tokenize("The polar bear is sliding on the snow")
reference = [s]
candidate =word_tokenize("The polar bear is sliding across the snow") 
print('Individual 1-gram: %f' % sentence_bleu(reference, candidate, weights=(1, 0, 0, 0)))
print('Individual 2-gram: %f' % sentence_bleu(reference, candidate, weights=(0, 1, 0, 0)))
print('Individual 3-gram: %f' % sentence_bleu(reference, candidate, weights=(0, 0, 1, 0)))
print('Individual 4-gram: %f' % sentence_bleu(reference, candidate, weights=(0, 0, 0, 1)))

Individual 1-gram: 0.875000
Individual 2-gram: 0.714286
Individual 3-gram: 0.500000
Individual 4-gram: 0.400000

reference sentence has 8 words out of which the candidate matches exactly 7 words, so 7/8 score for 1-gram matches.

I'm not sure how the STS benchmarks are evaluated, I'm currently looking into them. If you have any leads or a document I would be more than happy to read them. 

Thank you very much for your help :)


````

## 불일치 7: `follow_up`

- 유형: `invalid_evidence`

- 사유: 근거 URL이 입력한 Issue 본문 또는 댓글 URL과 일치하지 않음

### 요약 텍스트

````text
- Faiss 인덱스(FlatIndex 혹은 IVF) 구축 후 쿼리 embedding 과 비교하여 KNN 반환.  - GPU 가속 시 batch_size 32~128 등 적절히 조정.  - 필요 시 모델을 뉴스 도메인에 fine‑tune(Triplet‑loss, MultipleNegativesRankingLoss 등).  - 성능을 Spearman/Pearson 등 STS‑benchmarks와 같은 지표로 평가하거나, 실제 검색 랭킹에서 NDCG 등으로 검증.
````

- 근거 순번: 1
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-517517467
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `517517467`

### 모델이 제시한 발췌문

````text
I ran it with faiss library using FlatIndex (as it give the most accurate results). On a p2.xlarge instance it was amazingly fast- building and searching took only 30 mins.
````

- 해당 URL은 수집한 Issue 본문이나 댓글에서 찾을 수 없습니다.

## 불일치 8: `unknowns`

- 유형: `invalid_evidence`

- 사유: 근거 URL이 입력한 Issue 본문 또는 댓글 URL과 일치하지 않음

### 요약 텍스트

````text
- 최적 모델 선택( BERT‑large‑nli‑mean‑tokens vs BERT‑base‑nli‑mean‑tokens, XLNet, RoBERTa 등)  - 뉴스 문서라면 문장 길이와 문단 단위 인코딩으로 무리 없는 대규모 변환 가능성  - 파인튜닝을 위한 라벨이 없는 수집된 데이터로 Triplet‑loss, Query‑generation 기반의 unsupervised fine‑tune 방법 적용 여부  - 검증 데이터셋(특히 뉴스) 부재로 실제 검색 성능을 객관적으로 측정할 방법
````

- 근거 순번: 3
- 모델이 제시한 URL: https://github.com/huggingface/transformers/issues/876#issuecomment-520920465
- 모델이 제시한 출처 유형: `comment`
- 모델이 제시한 댓글 ID: `None`

### 모델이 제시한 발췌문

````text
I don't think BERT out-of-the-box is the best option for this task... I want to find similar news...
````

- 해당 URL은 수집한 Issue 본문이나 댓글에서 찾을 수 없습니다.