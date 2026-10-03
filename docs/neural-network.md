# The compact neural network

Intuition: learn both numeric feature combinations and small vectors representing teams. A team embedding is a learned coordinate system, not a manually assigned popularity score.

Read `models/neural.py`. With batch B, numeric feature count F, and embedding size E, numeric inputs have shape `[B,F]`; two lookups produce `[B,E]` each. Concatenation produces `[B,F+2E]`. A linear layer computes `XW^T+b`, where W has shape `[32,F+2E]` in LIGHT and b `[32]`.

GELU adds nonlinearity, dropout regularizes during training, and another 16-unit layer feeds three logits. Cross-entropy uses logits directly: `-log P(correct class)`. Inference applies softmax to obtain `[B,3]` probabilities.

Backpropagation differentiates loss through the matrix products, activations, and embedding lookups. AdamW updates parameters using gradient estimates and decoupled weight decay. Gradient clipping limits unstable updates. A scheduler lowers learning rate when the trailing training-period loss stops improving; early stopping preserves the best weights.

The last 15% of the training prefix, grouped by date, is reserved for early stopping. Imputation, scaling, and embedding vocabulary use the earlier prefix only. Unknown clubs map to a zero embedding. Deterministic seeds and CPU operations support repeatable fitting; library or hardware changes can still alter results.

Optional neural tuning uses the same nested temporal search when `tune_neural` is enabled in configuration. The network joins the forecast only if validation favors a recipe using it. An implemented neural candidate is not proof it adds predictive value.

Exercise: write down every tensor shape for B=64, F=350, E=4. Explain why dropout is disabled at inference.
