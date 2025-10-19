# train_stamp.py
import torch
import torch.nn as nn
import torch.optim as optim
from collections import Counter
from torch.utils.data import DataLoader
from stamp_model import STAMP, SessionDataset, collate_fn, NegativeSampler, device
import pandas as pd
from sklearn.model_selection import train_test_split
# ---------------------------
# Training loop
# ---------------------------
def train_epoch(model, dataloader, optimizer, neg_sampler, n_neg=100, grad_clip=5.0):
    model.train()
    total_loss = 0.0
    bce = nn.BCEWithLogitsLoss()
    for seqs, lengths, targets in dataloader:
        seqs, targets = seqs.to(device), targets.to(device)
        B = seqs.size(0)

        negs = torch.LongTensor(neg_sampler.sample(B, n_neg)).to(device)
        pos_col = targets.view(B, 1)
        candidates = torch.cat([pos_col, negs], dim=1)

        logits = model(seqs, candidates)
        labels = torch.zeros_like(logits, dtype=torch.float, device=device)
        labels[:, 0] = 1.0

        loss = bce(logits, labels)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()

        total_loss += loss.item() * B

    return total_loss / len(dataloader.dataset)


# ---------------------------
# Evaluation (Precision@K)
# ---------------------------
def precision_at_k(model, sessions_for_eval, item_count, K=20, batch_size=512, max_seq_len=50):
    model.eval()
    pairs = []
    for s in sessions_for_eval:
        for t in range(1, len(s)):
            pairs.append((s[:t][-max_seq_len:], s[t]))

    hits, tot = 0, 0
    with torch.no_grad():
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i+batch_size]
            seqs = [b[0] for b in batch]
            targets = [b[1] for b in batch]
            max_len = max(len(s) for s in seqs)
            padded = [[0]*(max_len - len(s)) + s for s in seqs]
            seq_tensor = torch.LongTensor(padded).to(device)
            all_items = torch.arange(item_count, device=device).unsqueeze(0).expand(len(batch), item_count)
            logits = model(seq_tensor, all_items)
            topk = torch.topk(logits, K, dim=1).indices.cpu().numpy()
            for r, tgt in enumerate(targets):
                tot += 1
                if tgt in topk[r]:
                    hits += 1
    return hits / tot if tot > 0 else 0.0


# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    ratings_path = "../clean_data/ratings.csv"  
    print(f"📂 Loading ratings from: {ratings_path}")
    ratings = pd.read_csv(ratings_path)
    ratings = ratings[["user_id", "book_isbn", "book_rating"]]
    sessions_by_user = ratings.groupby("user_id")["book_isbn"].apply(list).tolist()
    sessions = [s for s in sessions_by_user if len(s) > 1]
    print(f"✅ Created {len(sessions)} sessions (users with >=2 books rated)")
    sessions_train, sessions_val = train_test_split(sessions, test_size=0.1, random_state=42)

    # Build ISBN → integer ID mapping
    unique_books = sorted({isbn for session in sessions for isbn in session})
    book2id = {isbn: i+1 for i, isbn in enumerate(unique_books)}  # reserve 0 for padding
    id2book = {i+1: isbn for i, isbn in enumerate(unique_books)}

    # Convert sessions from ISBN to integer IDs
    sessions_train = [[book2id[b] for b in s if b in book2id] for s in sessions_train]
    sessions_val = [[book2id[b] for b in s if b in book2id] for s in sessions_val]

    num_items = len(book2id) + 1 
    pad_idx = 0

    print(f"🔢 num_items = {num_items}")

    train_dataset = SessionDataset(sessions_train)
    val_dataset = SessionDataset(sessions_val)
    train_loader = DataLoader(
        train_dataset, batch_size=512, shuffle=True,
        collate_fn=lambda b: collate_fn(b, pad_idx=pad_idx, max_seq_len=50)
    )

    item_freq = Counter([item for s in sessions_train for item in s])
    neg_sampler = NegativeSampler(num_items=num_items, item_freq_counter=item_freq, power=0.75)
    model = STAMP(num_items=num_items, embed_dim=100, pad_idx=pad_idx, dropout=0.2).to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.005, weight_decay=1e-6)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.9)
    n_epochs = 30
    n_neg = 100

    for epoch in range(1, n_epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, neg_sampler, n_neg=n_neg)
        scheduler.step()
        print(f"Epoch {epoch} | Train Loss: {train_loss:.4f}")

        if epoch % 2 == 0:
            prec5 = precision_at_k(model, sessions_val[:2000], num_items, K=5)
            prec20 = precision_at_k(model, sessions_val[:2000], num_items, K=20)
            print(f"  Val Prec@5: {prec5:.4f} | Prec@20: {prec20:.4f}")

        torch.save({
            "epoch": epoch,
            "model_state": model.state_dict(),
            "opt_state": optimizer.state_dict()
        }, f"stamp_epoch{epoch}.pt")
