# Set LLM evaluation temperature to 0

The professor's reproducibility requirement means the same case document must always produce the same score; a future reader or examiner must be able to re-run the evaluation and get identical results. Temperature=0 forces greedy decoding, making LLM output deterministic given a fixed prompt and model version. Combined with BM25 deterministic retrieval, it closes the reproducibility loop. We set temperature=0 on all LLM scoring calls — a reviewer who "fixes" this to a higher value will break reproducibility.
