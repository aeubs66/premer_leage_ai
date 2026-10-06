export type Fixture = {
  id: string;
  kickoff: string;
  home_team: string;
  away_team: string;
  season: string;
  date_only: boolean;
};
export type Probabilities = { home: number; draw: number; away: number };
export type CalibrationBin = {
  lower: number;
  upper: number;
  count: number;
  mean_probability: number | null;
  observed_frequency: number | null;
};
export type Metrics = {
  n: number;
  log_loss: number;
  brier: number;
  accuracy: number;
  ece: number;
  calibration_bins: CalibrationBin[];
};
export type Prediction = {
  prediction_id: string;
  fixture_id: string;
  match: { home_team: string; away_team: string; kickoff: string };
  probabilities: Probabilities;
  predicted_winner: string;
  predicted_score: string;
  expected_goals: { home: number; away: number };
  score_probabilities: { score: string; probability: number }[];
  score_matrix: number[][];
  other_scores_probability: number;
  model_predictions: Record<string, Probabilities>;
  ensemble_members: string[];
  model_disagreement: string;
  uncertainty: {
    label: string;
    entropy: number;
    jensen_shannon_divergence: number;
    validation_n: number;
    validation_ece: number;
    historical_bin: CalibrationBin | null;
    method: string;
  };
  context: Record<string, Record<string, number | null>>;
  explanation: {
    title: string;
    method: string;
    caution: string;
    factors: {
      feature: string;
      value: number | null;
      logit_contribution: number;
      direction: string;
    }[];
  };
  data_coverage: {
    available_features: number;
    total_features: number;
    player_information: boolean;
    xg_available: boolean;
    historical_availability_assumed: boolean;
  };
  model_version: string;
  dataset_version?: string;
  feature_version?: string;
  features_as_of?: string;
  generated_at: string;
  warning: string;
  result: { home_goals: number; away_goals: number; log_loss: number } | null;
};
export type FormMatch = {
  kickoff: string;
  opponent: string;
  venue: string;
  goals_for: number;
  goals_against: number;
  points: number;
  result: string;
  xg: number | null;
  xga: number | null;
  elo_before: number;
};
export type Performance = {
  available: boolean;
  message?: string;
  version?: string;
  report?: {
    test_season: string;
    validation: Metrics;
    test: Metrics;
    comparison: Record<string, Metrics>;
    ensemble: { kind: string; members: string[] };
    calibration: string;
    limitations: string[];
  };
};

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let message = "The analytics service is unavailable. Please try again.";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      /* Non-JSON upstream errors retain the clear default message. */
    }
    throw new Error(message);
  }
  return response.json();
}

export const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
export const initials = (team: string) =>
  team
    .split(" ")
    .filter((x) => !["&", "FC", "United", "City"].includes(x))
    .map((x) => x[0])
    .slice(0, 3)
    .join("");
export const modelName = (name: string) =>
  ({
    elo: "Elo",
    poisson: "Poisson",
    dixon_coles: "Dixon–Coles",
    xgboost: "XGBoost",
    xgboost_no_h2h: "XGBoost · no H2H",
    neural: "Neural network",
    frequency: "League frequency",
    home_baseline: "Home baseline",
    previous_season: "Previous season",
    selected: "Selected forecast",
  })[name] || name;
