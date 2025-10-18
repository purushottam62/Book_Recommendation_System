import torch
import torch.nn as nn

class STAMP(nn.Module):
    def __init__(self, num_items, embed_dim=64):
        super(STAMP, self).__init__()
        self.item_embedding = nn.Embedding(num_items, embed_dim)
        self.attn = nn.Linear(embed_dim * 2, embed_dim)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim * 2, embed_dim),
            nn.ReLU(),
            nn.Linear(embed_dim, num_items)
        )

    def forward(self, session_items, target_mask=None):
        """
        session_items: tensor of shape (batch, seq_len)
        """
        embeddings = self.item_embedding(session_items)  # (batch, seq_len, embed_dim)
        short_term = embeddings[:, -1, :]                # last item → short-term interest
        global_interest = embeddings.mean(dim=1)         # mean over sequence
        combined = torch.cat([short_term, global_interest], dim=-1)
        scores = self.mlp(combined)
        return scores
