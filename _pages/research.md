---
permalink: /research/
title: "Research"
author_profile: true
---

## Research direction

I am interested in how firms make operational decisions under uncertainty, how disruptions move through production networks, and what can be learned about these processes from text and market data. My current work focuses on measurement and empirical evaluation. Longer term, I want to develop computational models that help evaluate how operational and policy decisions affect firms and markets.

## Supply-chain language and stock-market reactions

**Independent research · 2026 · Ongoing**

**Question.** Is the language managers use to discuss supply-chain risk and its resolution associated with abnormal stock returns around earnings announcements?

**Data and methods.** The analysis covers 58,305 earnings calls from 2,200 companies covering 2010–2019. The final portfolio sample contains 52,533 calls from 2,026 firms after market-data and industry-classification filters. The study uses reconstructed supply-chain, risk, and resolution dictionaries, with the supply-chain vocabulary derived using PPMI and truncated SVD. I compare text measures with cumulative abnormal returns from a Carhart four-factor model.

**Current finding.** Mean two-day abnormal returns decline from +0.52% in the lowest fractional risk portfolio to −0.41% in the highest. The input data produced a significant number of supply chain risk scores with a value of zero, spanning the entirety of the first quintile and much of the second.

<figure class="research-figure">
  <img
    src="{{ '/images/scrisk-result.png' | relative_url }}"
    alt="Mean two-day abnormal returns decrease across fractional risk portfolios, from 0.52% in Q1 to −0.41% in Q5; error bars show firm-clustered 95% intervals."
    width="1980"
    height="1530"
    loading="lazy"
    decoding="async"
  >
  <figcaption>Mean CAR(0,1) by fractional SCRisk portfolio, 2010–2019. Bars show 95% intervals clustered by firm. Final sample: 52,533 calls from 2,026 firms. Portfolios share observations when scores are tied.</figcaption>
</figure>

**Scope and limitations.** Events use reported earnings-release dates, which may differ from conference-call dates; the analysis makes no after-hours adjustment. Portfolio intervals account for repeated observations within firms; the analysis does not yet include controlled regressions or common-date dependence.

**Next question.** I plan to examine a separately defined subset of hardware companies with documented international supply-chain exposure, retaining the full-sample baseline.

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
