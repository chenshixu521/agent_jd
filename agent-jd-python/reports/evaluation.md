# RAG Evaluation

本目录只记录真实执行结果，不预填或编造指标。

## 运行方式

```bash
python -m scripts.eval_rag --provider hash --details
python -m scripts.eval_rag --provider sentence_transformers --details
```

## 指标

- Recall@3：前 3 个去重文档中召回的相关文档比例。
- Recall@5：前 5 个去重文档中召回的相关文档比例。
- MRR：第一个相关文档排名倒数的平均值。

## 记录模板

| 日期 | Provider / Model | Recall@3 | Recall@5 | MRR | 备注 |
| --- | --- | ---: | ---: | ---: | --- |
| 2026-07-20 | hash baseline + BM25/RRF | 0.8690 | 0.9048 | 0.8810 | 14 条仓库内开发查询，仅作回归基线 |
| 2026-07-20 | BAAI/bge-small-zh-v1.5 + BM25/RRF | 1.0000 | 1.0000 | 1.0000 | CPU 离线模型，14 条仓库内开发查询 |

> 开发集与知识库来自同一仓库，指标可能偏乐观；对外写入简历前应增加匿名真实 JD 和人工标注的独立测试集。
