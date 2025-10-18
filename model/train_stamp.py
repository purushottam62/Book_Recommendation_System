import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from stamp_model import STAMP
import torch.nn as nn
import torch.optim as optim

class BookSessionDataset(Dataset):
    def __init__(self, seq_file, book_to_idx):
        df = pd.read_pickle(seq_file)
        self.sessions = df
        self.book_to_idx = book_to_idx

    def __len__(self):
        return len(self.sessions)

    def __getitem__(self, idx):
        seq = [self.book_to_idx[b] for b in self.sessions.iloc[idx]["input_sequence"]]
        target = self.book_to_idx[self.sessions.iloc[idx]["target"]]
        return torch.tensor(seq), torch.tensor(target)

def collate_fn(batch):
    sequences, targets = zip(*batch)
    max_len = max(len(seq) for seq in sequences)
    padded = [torch.cat([seq, torch.zeros(max_len - len(seq), dtype=torch.long)]) for seq in sequences]
    return torch.stack(padded), torch.tensor(targets)

def train_stamp():
    # --- Step 1: Load data ---
    ratings = pd.read_csv("./../clean_data/ratings.csv")
    books = ratings["book_isbn"].unique()
    book_to_idx = {b: i for i, b in enumerate(books)}
    idx_to_book = {i: b for b, i in book_to_idx.items()}

    dataset = BookSessionDataset("./../clean_data/sequences.pkl", book_to_idx)
    loader = DataLoader(dataset, batch_size=128, shuffle=True, collate_fn=collate_fn)

    # --- Step 2: Model, loss, optimizer ---
    model = STAMP(num_items=len(book_to_idx))
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # --- Step 3: Train ---
    for epoch in range(5):
        model.train()
        total_loss = 0
        for sequences, targets in loader:
            optimizer.zero_grad()
            outputs = model(sequences)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1}: loss = {total_loss / len(loader):.4f}")

    # --- Step 4: Save ---
    torch.save(model.state_dict(), "./stamp.pth")
    print("✅ Training complete. Model saved to ./stamp.pth")

if __name__ == "__main__":
    train_stamp()

