# Fusion Sweep Comparison

| Mode | Params | Doc Recall | Snippet Recall |
|------|--------|-----------|----------------|
| dense | - | 77% | 72% |
| hybrid | K=30 | 80% | 75% |
| hybrid | K=60 | 80% | 75% |
| hybrid | K=90 | 80% | 75% |
| cc | α=0.5 | 80% | 73% |
| cc | α=0.6 | 80% | 73% |
| cc | α=0.7 | 80% | 75% |
| cc | α=0.8 | 80% | 78% |
| cc | α=0.9 | 80% | 72% |
| cc+rerank | α=0.8 | 84% | 77% |
| hybrid+rerank | K=60 | 84% | 77% |
