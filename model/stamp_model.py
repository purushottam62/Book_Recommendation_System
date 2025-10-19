# stamp_model.py
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset

# ---------------------------
# Utility: seed & device
# ---------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------------------------
# Dataset: (session_seq, target)
# ---------------------------
class SessionDataset(Dataset):
    def __init__(self, sessions, min_len=2):
        self.pairs = []
        for s in sessions:
            if len(s) < min_len:
                continue
            for t in range(1, len(s)):
                prefix = s[:t]
                target = s[t]
                self.pairs.append((prefix, target))

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        return self.pairs[idx]


def collate_fn(batch, pad_idx=0, max_seq_len=None):
    seqs = [b[0] for b in batch]
    targets = [b[1] for b in batch]
    lengths = [len(s) for s in seqs]
    max_len = min(max(lengths), max_seq_len or max(lengths))

    padded = []
    for s in seqs:
        s = s[-max_len:]
        pad_len = max_len - len(s)
        padded.append([pad_idx] * pad_len + s)

    seq_tensor = torch.LongTensor(padded)
    lengths = torch.LongTensor(lengths)
    targets = torch.LongTensor(targets)
    return seq_tensor, lengths, targets


# ---------------------------
# STAMP Model Definition
# ---------------------------
class STAMP(nn.Module):
    def __init__(self, num_items, embed_dim=100, pad_idx=0, dropout=0.2):
        super(STAMP, self).__init__()
        self.num_items = num_items
        self.embed_dim = embed_dim
        self.pad_idx = pad_idx

        self.item_embedding = nn.Embedding(num_items, embed_dim, padding_idx=pad_idx)

        self.W1 = nn.Linear(embed_dim, embed_dim, bias=False)
        self.W2 = nn.Linear(embed_dim, embed_dim, bias=False)
        self.W3 = nn.Linear(embed_dim, embed_dim, bias=False)
        self.ba = nn.Parameter(torch.zeros(embed_dim))
        self.W0 = nn.Linear(embed_dim, 1, bias=False)

        self.Ws = nn.Linear(embed_dim, embed_dim, bias=True)
        self.Wt = nn.Linear(embed_dim, embed_dim, bias=True)

        self.dropout = nn.Dropout(dropout)
        self._init_weights()

    def _init_weights(self):
        nn.init.normal_(self.item_embedding.weight, mean=0.0, std=0.0022)
        nn.init.normal_(self.ba, 0.0, 0.01)

    def forward(self, session_items, candidate_items=None):
        B, L = session_items.shape
        emb = self.item_embedding(session_items)
        xt = emb[:, -1, :]
        mask = (session_items != self.pad_idx).unsqueeze(-1).float()
        masked_emb = emb * mask
        denom = mask.sum(dim=1).clamp(min=1.0)
        ms = masked_emb.sum(dim=1) / denom

        W1_xi = self.W1(emb)
        W2_xt = self.W2(xt).unsqueeze(1)
        W3_ms = self.W3(ms).unsqueeze(1)
        pre = W1_xi + W2_xt + W3_ms + self.ba
        activated = torch.sigmoid(pre)
        alpha_raw = self.W0(activated).squeeze(-1)
        alpha_raw = alpha_raw.masked_fill(~(session_items != self.pad_idx), float("-1e9"))
        alpha = torch.softmax(alpha_raw, dim=-1).unsqueeze(-1)
        ma = (alpha * emb).sum(dim=1) + ms

        hs = torch.tanh(self.Ws(ma))
        ht = torch.tanh(self.Wt(xt))
        h = hs * ht

        if candidate_items is not None:
            cand_emb = self.item_embedding(candidate_items)
            logits = torch.einsum("bd,bkd->bk", h, cand_emb)
            return logits

        all_emb = self.item_embedding.weight.unsqueeze(0)  # (1, num_items, D)
        logits = torch.einsum("bd,nd->bn", h, self.item_embedding.weight)
        return logits



# ---------------------------
# Negative Sampling
# ---------------------------
class NegativeSampler:
    def __init__(self, num_items, item_freq_counter=None, power=0.75):
        self.num_items = num_items
        if item_freq_counter is None:
            probs = np.ones(num_items)
        else:
            freq = np.array(
                [item_freq_counter.get(i, 0) for i in range(num_items)], dtype=np.float64
            )
            probs = np.power(freq, power)
            probs = np.clip(probs, 1e-8, None)
        probs = probs / probs.sum()
        self.probs = probs

    def sample(self, batch_size, n_samples):
        samples = np.random.choice(
            self.num_items, size=(batch_size, n_samples), p=self.probs
        )
        return samples
