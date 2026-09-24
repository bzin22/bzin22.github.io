---
permalink: /projects/
title: "Projects"
author_profile: true
---

## Predicting Hacker News engagement

**Independent project · Baseline evaluation complete; embedding experiments in progress**

How much of a post’s eventual engagement can be predicted using information available when it is submitted?

I designed and orchestrated the project. The Python pipeline processes 4,739,207 usable Hacker News stories and identified periods where archived scores reflected submission-time snapshots rather than mature outcomes. After excluding those periods, the baseline evaluation uses 3,568,252 training posts from 2006–2022 and 599,937 test posts from 2024–2025. Historical author and domain features use earlier observations with a score-settling lag.

I compared simple historical baselines, Ridge regression, and XGBoost. The combined-feature Ridge model achieved a test Spearman correlation of 0.297, compared with 0.050 for the trailing-mean baseline. RMSE on log-transformed scores improved by about 3.6%, showing that the features helped ranking more than prediction of score magnitude. XGBoost remained behind Ridge on ranking after early stopping.

The project also includes PyTorch implementations of CBOW and skip-gram objectives with negative sampling, with targeted training experiments on text8. The full embedding variants and their downstream Hacker News comparison remain unfinished.

**Tools:** Python, pandas, scikit-learn, XGBoost, PyTorch.

## Reconstructing Adam optimization experiments

**Independent implementation study · MNIST experiments complete**

I implemented Adam, AdaGrad, RMSProp, AdaDelta, and SGD with Nesterov momentum in NumPy, together with manual forward and backward passes for logistic regression and a multilayer perceptron.

The experiments revisit optimizer comparisons from Kingma and Ba’s Adam paper. In my 200-epoch MNIST experiment with dropout, AdaGrad reached a lower final training loss than Adam, differing from the paper’s reported ordering. I documented that discrepancy and possible explanations involving the tuning horizon and gradient sparsity; these remain hypotheses rather than established causes.

The project demonstrates numerical implementation, experiment design, and diagnosis of reproduction gaps. The CIFAR-10 extension is unfinished.

[Repository](https://github.com/bzin22/adam-optimizer-recreation)

## Freshfleet: robotic cleaning end effectors

**Mechanical design case study · Write-up in preparation**

At Freshfleet, I designed compliant end effectors for cleaning vehicle seats and floors with a UR10e robot arm, including the cleaning mechanism, electronics, and actuation.

CAD renders and a write-up of the end-effector design are in preparation.

## Technical preparation

**Programming languages:** Python.

**Methods demonstrated in projects:** Text processing, dictionary-based NLP, chronological model evaluation, feature engineering, linear and tree-based prediction, numerical optimization, manual backpropagation, and event-study analysis.

**Libraries and tools:** NumPy, pandas, PyTorch, scikit-learn, XGBoost, Git, and automated testing.

**Additional study:** Reinforcement learning, Markov decision processes, and policy optimization through independent coursework.
