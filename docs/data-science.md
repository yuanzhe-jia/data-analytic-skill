# Data Science

Data science, regardless of job titles (business analyst, data scientist, or ML engineer), ultimately serves to answer **four fundamental business questions** using different technical stacks. These four questions form a logical chain:

1. **Benchmark** – “How good/bad are we right now?” (building the ruler)
2. **Classification** – “Who is who? What changed?” (spotting the change)
3. **Attribution** – “Why did it happen? How much did each factor contribute?” (explaining the past)
4. **Prediction** – “What will happen next?” (forecasting the future)

Below is a practical framework that walks through a typical business scenario – e.g., a sudden drop in “Average Minutes Per Page” – using these four lenses.

## Benchmark – Building the Ruler

**Business question:** *How is the metric behaving normally? Is the current change meaningful?*

Before any diagnosis, you need a **baseline** and a **threshold** to determine if the observed change is worth investigating.

| Technique | Description |
| :--- | :--- |
| **Descriptive statistics** | mean, median, percentiles, standard deviation |
| **Normalization & scaling** | Z-score, min-max, PSI (Population Stability Index) |
| **Time‑series baselines** | year‑over‑year, month‑over‑month, week‑over‑week |
| **Control charts** | Shewhart, EWMA, CUSUM |

**Example:** “The 12% drop is statistically significant and requires further analysis.”

## Classification – Spotting the Change

**Business question:** *What changed? Which segments or time points are unusual?*

This step answers “who is who?” by partitioning data into normal vs. abnormal groups, or by clustering similar entities.

| Technique | Description |
| :--- | :--- |
| **Statistical thresholds** | Z-score, IQR for univariate anomaly flags |
| **ML‑based detectors** | Random Forest, SVM, XGBoost/LightGBM |
| **Clustering for segmentation** | K‑means, DBSCAN, Gaussian Mixture Models (to find natural groups) |
| **Time‑series anomaly detection** | ARIMA (residuals), Prophet (seasonality adjusted), STL decomposition |

**Example:** “The anomaly detector flags that the drop started on July 12th and affects primarily North American mobile users.”

## Attribution – Explaining the Past

**Business question:** *Why did it happen? How much did each factor contribute? What truly caused the change?*

This is the core of **explaining the past**. It combines two complementary sub‑questions:

- **Attribution anlysis** – “How much does each dimension/factor account for the change?”
- **Causal inference** – “What is the true causal effect of a specific intervention?”

### Attribution Analysis (Quantifying contributions)

| Technique | Description |
| :--- | :--- |
| **Heuristic models** | First‑touch, last‑touch, time‑decay (marketing attribution) |
| **Multivariate drilldown** | Variance decomposition, correlation analysis |
| **Game‑theory** | Shapley value (fair contribution distribution) |
| **Regression‑based** | Logistic regression with Shapley value decomposition |
| **Markov chains** | Multi‑touch attribution with removal effects |

**Example:** “Mobile issues explain ~50% of the drop, sports content ~33%, and the new app version ~17%.”

### Causal Inference (Identifying true causes)

| Technique | Description |
| :--- | :--- |
| **Controlled trials** | A/B tests, holdout experiments (gold standard) |
| **Quasi‑experimental** | Difference‑in‑Differences (DiD), Regression Discontinuity, Instrumental Variables |
| **Matching methods** | Propensity Score Matching (PSM), Coarsened Exact Matching |
| **Causal ML** | Causal forests, Double/Debiased ML, Uplift modeling |
| **Graphical models** | DAG + Pearl’s do‑calculus |

**Example:** “A DiD analysis shows that users who received the new app version watched 9% less compared to matched controls – the app update is the root cause.”

> **Important distinction:** Attribution measures correlation‑based contribution; causal inference establishes counterfactual causality. Use both – attribution to allocate responsibility, causality to prove it.

## Prediction – Forecasting the Future

**Business question:** *If we take a certain action (or do nothing), what will happen next?*

Once you understand the past and present, prediction helps you anticipate outcomes and allocate resources.

| Technique | Application |
| :--- | :--- |
| **Classical time series** | ARIMA, SARIMA, Exponential Smoothing (Holt‑Winters) |
| **Regression & tree‑based** | Linear/Ridge/Lasso regression |
| **Deep learning** | LSTM, GRU, Transformer‑based models (Informer, Autoformer) |
| **Probabilistic forecasting** | Prophet (Facebook), Quantile regression, DeepAR |

**Example:** “Using a Prophet model, we predict that reverting the app version would recover 8% of the lost minutes in the next two weeks.”

## Putting It All Together – A Unified Workflow

When facing a metric drop (or any data problem), follow this logical order:

1. **Benchmark** – Do we have a reliable baseline and threshold? (If not, build it.)
2. **Classification** – Is there a statistically meaningful change? Which dimensions?
3. **Attribution** – Why? Quantify contributions and prove causality.
4. **Prediction** – Given the root cause, what is the expected future trajectory under different decisions?

Every data role – whether business analyst, data scientist, or ML engineer – uses different technical stacks (SQL vs. Python, stats vs. deep learning) but ultimately solves these four core business problems. Understanding this helps you choose the right tool for the right question and communicate effectively with stakeholders.
