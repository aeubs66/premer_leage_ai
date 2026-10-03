"""Compact CPU MLP. Optional torch is imported only when this model is used."""

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from football_ai.models.base import normalize


class NeuralModel:
    def __init__(self, parameters=None, width=32, epochs=60, threads=2, seed=42):
        self.parameters, self.width, self.epochs = parameters or {}, width, epochs
        self.threads, self.seed = threads, seed

    def fit(self, features, matches):
        import torch
        from torch import nn

        torch.set_num_threads(self.threads)
        torch.manual_seed(self.seed)
        torch.use_deterministic_algorithms(True)
        rng = np.random.default_rng(self.seed)
        # Early stopping uses the trailing training period; no external validation labels enter fitting.
        boundary = int(len(matches) * 0.85)
        day = matches[boundary].kickoff.date()
        while boundary > 0 and matches[boundary - 1].kickoff.date() == day:
            boundary -= 1
        if boundary < 20:
            raise ValueError("Too few chronological neural training samples")
        self.columns = list(features.columns)
        self.imputer = SimpleImputer(strategy="median", keep_empty_features=True, add_indicator=True)
        self.scaler = StandardScaler()
        self.imputer.fit(features.iloc[:boundary])
        self.scaler.fit(self.imputer.transform(features.iloc[:boundary]))
        numeric = torch.tensor(self.scaler.transform(self.imputer.transform(features)), dtype=torch.float32)
        self.teams = {team: i + 1 for i, team in enumerate(sorted({m.home_team for m in matches[:boundary]} | {m.away_team for m in matches[:boundary]}))}
        home = torch.tensor([self.teams.get(m.home_team, 0) for m in matches])
        away = torch.tensor([self.teams.get(m.away_team, 0) for m in matches])
        targets = torch.tensor([m.outcome for m in matches])
        embedding_size = self.parameters.get("embedding_size", 4)
        self.embedding = nn.Embedding(len(self.teams) + 1, embedding_size, padding_idx=0)
        self.network = nn.Sequential(nn.Linear(numeric.shape[1] + 2 * embedding_size, self.width), nn.GELU(),
                                     nn.Dropout(self.parameters.get("dropout", 0.2)), nn.Linear(self.width, self.width // 2), nn.GELU(), nn.Linear(self.width // 2, 3))
        optimizer = torch.optim.AdamW(list(self.embedding.parameters()) + list(self.network.parameters()),
                                      lr=self.parameters.get("learning_rate", 0.001), weight_decay=self.parameters.get("weight_decay", 0.01))
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=4, factor=0.5)
        loss_fn = nn.CrossEntropyLoss()
        best_loss, stale, best = float("inf"), 0, None
        batch_size = self.parameters.get("batch_size", 64)
        for epoch in range(self.epochs):
            self.network.train()
            self.embedding.train()
            permutation = rng.permutation(boundary)
            for start in range(0, boundary, batch_size):
                index = permutation[start:start + batch_size]
                logits = self.network(torch.cat([numeric[index], self.embedding(home[index]), self.embedding(away[index])], dim=1))
                loss = loss_fn(logits, targets[index])
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(list(self.network.parameters()) + list(self.embedding.parameters()), 1)
                optimizer.step()
            self.network.eval()
            with torch.no_grad():
                logits = self.network(torch.cat([numeric[boundary:], self.embedding(home[boundary:]), self.embedding(away[boundary:])], dim=1))
                validation_loss = loss_fn(logits, targets[boundary:]).item()
            scheduler.step(validation_loss)
            if validation_loss < best_loss - 1e-5:
                best_loss, stale = validation_loss, 0
                best = ({k: v.detach().clone() for k, v in self.network.state_dict().items()}, {k: v.detach().clone() for k, v in self.embedding.state_dict().items()})
            else:
                stale += 1
            if stale >= 10:
                break
        assert best is not None
        self.network.load_state_dict(best[0])
        self.embedding.load_state_dict(best[1])
        self.network.eval()
        self.embedding.eval()
        self.best_loss, self.epochs_run = best_loss, epoch + 1
        return self

    def predict_proba(self, features, matches):
        import torch
        numeric = torch.tensor(self.scaler.transform(self.imputer.transform(features[self.columns])), dtype=torch.float32)
        home = torch.tensor([self.teams.get(m.home_team, 0) for m in matches])
        away = torch.tensor([self.teams.get(m.away_team, 0) for m in matches])
        with torch.no_grad():
            logits = self.network(torch.cat([numeric, self.embedding(home), self.embedding(away)], dim=1))
            return normalize(torch.softmax(logits, dim=1).numpy())

    def __getstate__(self):
        state = self.__dict__.copy()
        state["network_bytes"] = [(k, v.detach().numpy()) for k, v in self.network.state_dict().items()]
        state["embedding_bytes"] = [(k, v.detach().numpy()) for k, v in self.embedding.state_dict().items()]
        state["input_dim"] = self.network[0].in_features
        del state["network"], state["embedding"]
        return state

    def __setstate__(self, state):
        import torch
        from torch import nn
        self.__dict__.update(state)
        self.network = nn.Sequential(nn.Linear(self.input_dim, self.width), nn.GELU(), nn.Dropout(self.parameters.get("dropout", 0.2)), nn.Linear(self.width, self.width // 2), nn.GELU(), nn.Linear(self.width // 2, 3))
        self.embedding = nn.Embedding(len(self.teams) + 1, self.parameters.get("embedding_size", 4), padding_idx=0)
        self.network.load_state_dict({k: torch.tensor(v) for k, v in self.network_bytes})
        self.embedding.load_state_dict({k: torch.tensor(v) for k, v in self.embedding_bytes})
        self.network.eval()
        self.embedding.eval()
