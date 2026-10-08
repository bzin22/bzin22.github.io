---
permalink: /research/
title: "Research"
author_profile: true
---

## Research direction

I am interested in how firms make operational decisions under uncertainty, how disruptions move through production networks, and what can be learned about these processes from text and market data. My current work focuses on measurement and empirical evaluation. Longer term, I want to develop computational models that help evaluate how operational and policy decisions affect firms and markets.

## Supply-chain risk language and stock-market reactions

*Evidence from US hardware firms · Independent research · 2026–present*

Does the way managers discuss supply-chain problems convey information associated with stock-market reactions? Motivated by my experience in hardware product development, I study this question using 11,950 earnings calls from 378 US hardware firms covering fiscal years 2010–2019.

Building on Theile et al. (2026), I construct dictionary-based measures of supply-chain risk and resolution language, using a vocabulary derived from 50,000 annual filings. The analysis combines Carhart four-factor abnormal returns, portfolios that allocate tied scores proportionally, and regressions with firm and calendar-quarter fixed effects.

Calls in the highest-risk portfolio have two-day abnormal returns **1.69 percentage points below** those in the lowest-risk portfolio. With fixed effects, a one-standard-deviation increase in risk language is associated with a **0.82 percentage point lower return**. On the 5,476-call subsample with earnings-surprise data, adding a provider-reported surprise control reduces the estimate from −0.85 to −0.71 percentage points. Evidence for resolution language is weaker.

<figure class="research-figure">
  <img src="{{ '/images/scrisk-hardware-result.png' | relative_url }}" alt="Mean two-day abnormal returns by fractional SCRisk portfolio: 1.13% in Q1 and −0.56% in Q5; error bars show firm-clustered 95% confidence intervals." width="1895" height="1130" loading="lazy" decoding="async">
  <figcaption>Mean CAR(0,1) by fractional SCRisk portfolio, fiscal years 2010–2019. Bars show 95% confidence intervals clustered by firm. Sample: 11,950 calls from 378 US hardware firms. Portfolios share observations when scores are tied.</figcaption>
</figure>

These findings describe associations: other earnings news, sample selection, and event timing limit causal interpretation. My ongoing work examines whether the relationship is stronger for firms that depend on critical suppliers they cannot readily replace.

<a href="{{ '/files/supply-chain-risk-hardware-report.pdf' | relative_url }}">Read the report (PDF)</a> · <a href="https://github.com/bzin22/supply_chain_risk_and_reactions">Research repository</a>

<style>
  .research-figure {
    max-width: 820px;
    margin: 1.5em auto;
  }

  .research-figure img {
    display: block;
    width: 100%;
    height: auto;
    background: #fff;
  }

  .research-figure figcaption {
    margin-top: 0.6em;
  }
</style>
