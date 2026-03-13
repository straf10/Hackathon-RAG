# Complex multi-document evaluation questions

**Available in data:** NVIDIA, Alphabet (Google), Apple, Microsoft, Tesla — **2023–2025**

> Token counts below are **deterministic approximations** (word-based) so you can compare prompts consistently across models even without a tokenizer installed. If you want exact counts, I can switch these to `tiktoken` once it’s available.

---

## Q1 — Multi-company, multi-year revenue growth + drivers

Compare **total revenue** for **NVIDIA**, **Microsoft**, and **Alphabet (Google)** across **2023, 2024, and 2025**. For each company, compute **YoY growth** for 2023→2024 and 2024→2025, identify which year had the **higher YoY growth**, and cite the **specific driver(s)** each company attributes that change to in its 10‑K.

**Total tokens (question):** ~62

### GPT-4.1 Answer

Here is a comparison of total revenue for NVIDIA, Microsoft, and Alphabet (Google) across 2023, 2024, and 2025, including year-over-year (YoY) growth calculations, identification of the year with higher YoY growth for each company, and the specific drivers each company attributed to these changes:

NVIDIA
Total Revenue:

2023: $26,974 million
2024: $60,922 million
2025: $130,497 million
YoY Growth:

2023→2024:
[(60,922 - 26,974) / 26,974] × 100 ≈ 126%
2024→2025:
[(130,497 - 60,922) / 60,922] × 100 ≈ 114%
Year with Higher YoY Growth:
2023→2024 (126% vs. 114%)

Key Drivers:

2023: Growth in Data Center (41%) and Automotive (60%) revenues, led by hyperscale customers, cloud service providers, and increased sales of self-driving and AI cockpit solutions. Gaming and Professional Visualization declined due to channel inventory reductions and macroeconomic challenges.
2024: Surge in Data Center revenue (217%) and Compute & Networking (215%), driven by demand for enterprise software, AI platforms, and NVIDIA Hopper GPU shipments for generative AI and large language models. Gaming and Automotive also grew.
2025: Continued strong demand for accelerated computing and AI solutions, especially the Hopper platform for large language models and generative AI. Data Center networking revenue also increased, with growth in Ethernet for AI and the Spectrum-X platform. Graphics revenue rose due to GeForce RTX 40 Series GPUs.
Microsoft
Total Revenue:

2023: $211,915 million
2024: $245,122 million
2025: $281,724 million
YoY Growth:

2023→2024:
[(245,122 - 211,915) / 211,915] × 100 ≈ 16%
2024→2025:
[(281,724 - 245,122) / 245,122] × 100 ≈ 15%
Year with Higher YoY Growth:
2023→2024 (16% vs. 15%)

Key Drivers:

2023: Growth led by Intelligent Cloud (Azure and cloud services), Productivity and Business Processes (Office 365 Commercial, LinkedIn). More Personal Computing declined due to lower Windows and Devices revenue.
2024: Growth across all segments, especially Intelligent Cloud (Azure), Productivity and Business Processes (Office 365 Commercial), and More Personal Computing (Gaming). Increased costs from cloud and gaming, with gross margin improvements.
2025: Continued growth in all segments, with Intelligent Cloud (Azure), Productivity and Business Processes (Microsoft 365 Commercial cloud), and More Personal Computing (Gaming, Search and news advertising) as main contributors. Investments in AI infrastructure and cloud engineering influenced both revenue and costs.
Alphabet (Google)
Total Revenue:

2023: $307,394 million
2024: $350,018 million
2025: $402,836 million
YoY Growth:

2023→2024:
[(350,018 - 307,394) / 307,394] × 100 ≈ 14%
2024→2025:
[(402,836 - 350,018) / 350,018] × 100 ≈ 15%
Year with Higher YoY Growth:
2024→2025 (15% vs. 14%)

Key Drivers:

2023: Growth in Google Services (Search, YouTube ads) from increased user adoption, advertiser spending, and improved ad formats; Google Cloud revenue also increased.
2024: Revenue growth from Google Services (Search, YouTube, subscriptions, platforms, devices) and Google Cloud, with expanded AI offerings boosting engagement and monetization. Non-advertising revenues grew faster than advertising.
2025: Continued growth in Search, YouTube, Google Cloud (especially AI-driven solutions), and subscriptions/platforms/devices. AI integration (AI Overviews, AI Mode in Search, enterprise AI solutions) and a shift toward non-advertising revenues were significant contributors.  

**Summary Table**


| Company   | 2023 Revenue | 2024 Revenue | 2025 Revenue | 2023→2024 YoY | 2024→2025 YoY | Higher YoY Growth | Main Drivers                                                                           |
| --------- | ------------ | ------------ | ------------ | ------------- | ------------- | ----------------- | -------------------------------------------------------------------------------------- |
| NVIDIA    | $26,974M     | $60,922M     | $130,497M    | 126%          | 114%          | 2023→2024         | Data Center & AI demand, Hopper platform, Automotive, Gaming recovery                  |
| Microsoft | $211,915M    | $245,122M    | $281,724M    | 16%           | 15%           | 2023→2024         | Azure/cloud, Office 365/Microsoft 365, LinkedIn, Gaming, AI infrastructure investments |
| Alphabet  | $307,394M    | $350,018M    | $402,836M    | 14%           | 15%           | 2024→2025         | Search, YouTube, Google Cloud, subscriptions/devices, AI integration and monetization  |


---

Each company’s revenue growth was primarily driven by expansion in cloud and AI-related products and services, with NVIDIA and Microsoft seeing their highest YoY growth in 2023→2024, while Alphabet’s highest YoY growth occurred in 2024→2025, reflecting the impact of their respective business segment performances and strategic investments.

12 reasoning steps + 114 sources.

---

### GPT-5.1 Answer

Here’s a side‑by‑side comparison and then a brief summary by company.

---

## **1. Revenue and YoY growth comparison**

*All amounts in millions of U.S. dollars.*

### **NVIDIA**


| Fiscal year | Revenue | YoY change |
| ----------- | ------- | ---------- |
| 2023        | 26,974  | –          |
| 2024        | 60,922  | **+126%**  |
| 2025        | 130,500 | **+114%**  |


- **Higher YoY growth:** 2023→2024 (126% vs. 114%)

**Management‑described drivers**

- **2023→2024**
  - Massive increase in **Compute & Networking** revenue (up 215%), driven mainly by **Data Center**:
    - **Compute revenue up 266%**, led by higher shipments of the **NVIDIA Hopper GPU computing platform** for:
      - Training and inference of large language models (LLMs)
      - Recommendation engines
      - Generative AI applications
    - **Networking revenue up 133%**, driven by higher **InfiniBand** shipments.
  - **Gaming** grew 15%, helped by normalized channel inventories and stronger gaming demand, but was a secondary driver.
- **2024→2025**
  - Continued strong **Compute & Networking** growth (up 145%), again centered on **Data Center**:
    - **Data Center computing revenue up 162%**, primarily from continued demand for the **Hopper computing platform**for LLMs, recommendation engines, and generative AI.
    - **Data Center networking revenue up 51%**, driven by **“Ethernet for AI”** offerings, including the **Spectrum‑X end‑to‑end Ethernet platform**.
  - **Graphics** up 6%, driven by **GeForce RTX 40 Series GPUs**.

---

### **Microsoft**


| Fiscal year | Revenue | YoY change |
| ----------- | ------- | ---------- |
| 2023        | 211,915 | –          |
| 2024        | 245,122 | **+16%**   |
| 2025        | 281,724 | **+15%**   |


- **Higher YoY growth:** 2023→2024 (≈16% vs. ≈15%)

**Management‑described drivers**

- **2023→2024**
  - Revenue growth across **all three segments**:
    - **Intelligent Cloud**: led by **Azure and other cloud services**.
    - **Productivity and Business Processes**: led by **Office 365 Commercial**.
    - **More Personal Computing**: led by **Gaming**.
  - Within those segments:
    - **Office Commercial products and cloud services**: Office 365 Commercial seat growth and higher revenue per user.
    - **Microsoft 365 Consumer**: subscriber growth.
    - **LinkedIn**: growth across all major lines.
    - **Dynamics 365**: broad‑based workload growth.
    - **Azure and other cloud services**: 30% revenue growth.
- **2024→2025**
  - Company‑wide:
    - **Microsoft Cloud** revenue up 23% to $168.9B.
    - **Server products and cloud services** up 23%, driven by **Azure and other cloud services** revenue growth of 34%.
  - **Productivity and Business Processes**:
    - **Microsoft 365 Commercial** revenue up 14%, with cloud revenue up 15%; driven by seat growth (especially SMB and frontline) and higher revenue per user, plus uplift from **Windows Commercial on‑premises** components and **Office 2024** transactional purchasing.
    - **Microsoft 365 Consumer** revenue up 11%, driven by 11% cloud revenue growth, 8% subscriber growth (to 89M), and higher revenue per user from a **January 2025 price increase**.
    - **LinkedIn** up 9% across all lines.
    - **Dynamics products and cloud services** up 15%, led by **Dynamics 365** up 19%.
  - **More Personal Computing & advertising**:
    - **Windows OEM and Devices** up 3%.
    - **Xbox content and services** up 16%.
    - **Search and news advertising** (ex‑TAC) up 20%.

---

### **Alphabet (Google)**


| Fiscal year | Revenue | YoY change |
| ----------- | ------- | ---------- |
| 2023        | 307,394 | –          |
| 2024        | 350,018 | **+13.9%** |
| 2025        | 402,836 | **+15.1%** |


- **Higher YoY growth:** 2024→2025 (≈15.1% vs. ≈13.9%)

**Management‑described drivers**

For both 2023→2024 and 2024→2025, management points to the same core drivers:

1. **Expansion and monetization of AI‑driven products and services**
  - Increased user engagement with AI features (e.g., AI‑enhanced Search and enterprise AI solutions on Google Cloud Platform).
  - A different monetization profile for these AI products relative to historical consumer and enterprise offerings, affecting growth rates and revenue mix.
  - A strategy of prioritizing **user experience first, then monetization**, influencing the timing and pattern of revenue realization from new AI features.
2. **Growth of non‑advertising revenue**
  - Faster growth in **cloud, consumer subscriptions, platforms, and devices**, making them a larger share of total revenue.
  - These lines typically have different characteristics and generally lower margins than advertising, shifting the overall business mix as they expand.
3. **Advertising ecosystem and traffic acquisition costs (TAC)**
  - TAC paid to distribution and Network partners is expected to grow with advertising revenues, implicitly tied to ongoing ad‑revenue expansion.
  - The **TAC rate has been decreasing** primarily due to shifts in revenue mix, underscoring the importance of where within advertising and non‑advertising the growth is occurring.

---

## **2. Cross‑company takeaway**

- **Highest YoY growth overall:** NVIDIA in 2023→2024 (~126%), driven by demand for **AI data‑center compute and networking (Hopper + InfiniBand)**.
- **Cloud/AI as common growth engines:**
  - NVIDIA: AI accelerators and AI networking.
  - Microsoft: Azure‑led cloud growth plus Microsoft 365 and other SaaS offerings.
  - Alphabet: AI‑enhanced products (Search, Cloud) and faster‑growing non‑ad businesses (cloud and subscriptions).
- **Pattern of YoY growth:**
  - NVIDIA and Microsoft had **stronger growth in 2023→2024** than in 2024→2025.
  - Alphabet shows the opposite: **higher growth in 2024→2025** than in 2023→2024, with the same structural AI and non‑advertising drivers operating in both years.

6 reasoning steps + 51 sources

---

## Q2 — R&D intensity ranking + trend (all companies, all years)

Across **NVIDIA, Tesla, Microsoft, Alphabet (Google), and Apple**, determine which company had the **highest R&D expense as a percentage of revenue** in **2024**. Then, for that same company (and at least one close runner‑up), show how **R&D % of revenue** changed from **2023 to 2025**, and cite the 10‑K language explaining the main reason(s) for the changes.

**Total tokens (question):** ~70

### GPT-4.1 Answer

Among NVIDIA, Tesla, Microsoft, Alphabet (Google), and Apple, the company with the highest R&D expense as a percentage of revenue in 2024 was NVIDIA. The next closest (runner-up) was Alphabet (Google).

For NVIDIA and Alphabet, the R&D expense as a percentage of revenue for 2023, 2024, and 2025 were as follows:

**NVIDIA:**

- 2023:
  - R&D Expense: $7.34 billion
  - Revenue: $26.97 billion
  - R&D % of Revenue: 27.2%
- 2024:
  - R&D Expense: $8.68 billion
  - Revenue: $60.92 billion
  - R&D % of Revenue: 14.3%
- 2025:
  - R&D Expense: $10.12 billion
  - Revenue: $89.24 billion
  - R&D % of Revenue: 11.3%

**Alphabet (Google):**

- 2023:
  - R&D Expense: $39.5 billion
  - Revenue: $282.8 billion
  - R&D % of Revenue: 14.0%
- 2024:
  - R&D Expense: $41.7 billion
  - Revenue: $307.4 billion
  - R&D % of Revenue: 13.6%
- 2025:
  - R&D Expense: $44.2 billion
  - Revenue: $329.1 billion
  - R&D % of Revenue: 13.4%

**10-K Language Explaining Changes:**

**NVIDIA:**  
The main reason for the decrease in R&D expense as a percentage of revenue from 2023 to 2025 was the significant increase in total revenue, primarily driven by strong demand for data center and AI-related products, while R&D expenses continued to grow at a slower rate. The 10-K states: “The decrease in R&D expense as a percentage of revenue was primarily due to substantial revenue growth outpacing the increase in R&D investments, as we continued to scale our business and invest in next-generation technologies.”

**Alphabet (Google):**  
For Alphabet, the slight decrease in R&D expense as a percentage of revenue was attributed to revenue growth outpacing the increase in R&D spending. The 10-K notes: “R&D expenses increased in absolute terms due to continued investment in AI and cloud infrastructure, but as a percentage of revenue, R&D declined slightly as overall revenues grew at a faster rate.”

In summary, NVIDIA had the highest R&D expense as a percentage of revenue in 2024, followed by Alphabet. For both companies, the R&D percentage of revenue declined from 2023 to 2025, mainly because revenue growth outpaced the growth in R&D spending, as described in their respective 10-K filings.

Model created 4 reasoning steps all with empty responses and 0 sources. Answear produced by models prior knowledge not based on docs.  

---

### GPT-5.1 Answer

NVIDIA had the highest R&D expense as a percentage of revenue in 2024.

**2024 R&D as % of revenue across the five companies**

- NVIDIA: **14.2%**
- Alphabet (Google): **14%**
- Microsoft: **12%**
- Apple: **8%**
- Tesla: **5%**

So NVIDIA is highest, with Microsoft as a close runner‑up.

---

## **NVIDIA – R&D as % of revenue and reasons for change (2023–2025)**

**R&D as % of revenue**

- **2023:** 27.2%
- **2024:** 14.2%
- **2025:** 9.9%

**Narrative explanations from the 10‑K filings**

- **2023 vs. 2022**  
Main reasons for the increase in R&D expense (and higher percentage vs. earlier years):
  > “The increase in research and development expense for fiscal year 2023 was primarily driven by increased compensation, employee growth, engineering development costs, and data center infrastructure.”
- **2024 vs. 2023**  
R&D dollars rose, but revenue grew much faster, so R&D as a % of revenue fell from 27.2% to 14.2%. The filing describes the drivers of higher operating expenses (including R&D) as:
  > “The increase in research and development expenses and sales, general and administrative expenses for fiscal year 2024 was primarily driven by compensation and benefits, including stock-based compensation, reflecting employee growth and compensation increases.”
- **2025 vs. 2024**  
R&D dollars increased again, but revenue rose even more, so R&D as a % of revenue declined further from 14.2% to 9.9%. The filing attributes the R&D increase to:
  > “The increases in research and development expenses for fiscal year 2025 were driven by a 32% increase in compensation and benefits, including stock-based compensation, reflecting employee growth and compensation increases, a 100% increase in compute and infrastructure, and a 234% increase in engineering development costs for new product introductions.”

Overall for NVIDIA, R&D spending rose each year in absolute terms, driven mainly by higher compensation, compute/infrastructure, and engineering development costs, while rapid revenue growth drove the sharp decline in R&D as a percentage of revenue from 2023 to 2025.

---

## **Microsoft – R&D as % of revenue and reasons for change (2023–2025)**

**R&D as % of revenue**

- **2023:** 13%
- **2024:** 12%
- **2025:** 12%

**Narrative explanations from the 10‑K filings**

- **2023 vs. 2022**  
R&D as a % of revenue increased from 12% to 13%. The filing explains the higher R&D expense as:
  > “Research and development expenses increased $2.7 billion or 11% driven by investments in cloud engineering and LinkedIn.”
- **2024 vs. 2023**  
R&D as a % of revenue decreased from 13% to 12%, as revenue outpaced the 9% increase in R&D. The filing attributes the R&D increase to:
  > “Research and development expenses increased $2.3 billion or 9% driven by Gaming, with 7 points of growth from the Activision Blizzard acquisition, and investments in cloud engineering.”
- **2025 vs. 2024**  
R&D as a % of revenue stayed at 12% while R&D dollars grew 10%. The filing describes what this spending covers and links related operating expense growth to cloud and AI work:
  > “Research and development expenses also include technology development costs, including AI training and other infrastructure costs, third-party development and programming costs, and the amortization of purchased software code and services content.”  
  > And, for closely related expenses in Intelligent Cloud:  
  > “Operating expenses increased $1.5 billion or 7% driven by investments in cloud and AI engineering.”

For Microsoft, R&D expense grew each year, primarily due to investments in cloud, AI engineering, Gaming (including Activision Blizzard), and LinkedIn, while revenue growth kept R&D at roughly 12–13% of revenue over 2023–2025.

15 reasoning steps + 96 sources

---

## Q3 — Shared risk factors across two years (Tesla vs NVIDIA)

Using **Tesla** and **NVIDIA** 10‑Ks for **2024 and 2025**, identify **three risk factor themes** that are **present in both companies** (e.g., supply chain, regulatory, competition—use the exact themes you find). For each theme, compare **how the emphasis changed from 2024 to 2025** within each company (what got stronger/weaker or newly highlighted), and support with citations from both years.

**Total tokens (question):** ~82

### GPT-4.1 Answer

**Three risk factor themes present in both Tesla’s and NVIDIA’s 10-K filings for 2024 and 2025 are:**

1. **Product Launch/Business Growth Risks**
2. **Supply Chain and Supplier Risks**
3. **Human Capital Management Risks**

---

### **1. Product Launch/Business Growth Risks**

**Tesla:**

- **2024:** The filings highlight risks of delays in launching and ramping up production for new products and features, referencing past supplier issues and manufacturing automation challenges. There is a focus on the uncertainty of successfully and timely introducing and scaling new manufacturing processes or design features.
- **2025:** The emphasis remains on operational execution, but the language broadens to include the risks of expanding the global footprint and the increasing complexity of new vehicle offerings. The filings stress that as Tesla grows, the risk of not meeting launch timelines or scaling efficiently becomes more pronounced.
  - **Citation:** “There is a risk of experiencing delays in launching and ramping up production for new products and features... As Tesla expands its vehicle offerings and global footprint, there is no guarantee of successfully and timely introducing and scaling new manufacturing processes or design features.”

**NVIDIA:**

- **2024:** The filings discuss the risk of failing to meet the evolving needs of the industry and markets, which could adversely impact financial results. Competition and the ability to innovate are highlighted as key factors.
- **2025:** The discussion intensifies around the need to adapt to rapid industry changes and the risk that failure to do so could have a more immediate and significant impact on financial results. There is increased attention to the speed of technological change and the necessity of timely product launches.
  - **Citation:** “Failure to meet the evolving needs of the industry and markets may adversely impact financial results.”

**Comparison:**  
Both companies increased their emphasis on the complexity and urgency of timely product launches and business growth in 2025. Tesla’s language shifts to highlight the risks associated with a broader product portfolio and global expansion, while NVIDIA underscores the accelerating pace of industry change and the heightened consequences of failing to keep up.

---

### **2. Supply Chain and Supplier Risks**

**Tesla:**

- **2024:** The filings mention past challenges with suppliers and automation, noting that supplier issues have contributed to delays in product launches and production ramp.
- **2025:** The risk discussion expands to include the inability to control manufacturing costs and the broader impact of supply chain disruptions on profitability and operational efficiency.
  - **Citation:** “Past challenges have included supplier issues and difficulties with automation in manufacturing processes... The company may be unable to control manufacturing costs, which could impact profitability and operational efficiency.”

**NVIDIA:**

- **2024:** The filings highlight long manufacturing lead times, uncertain supply and component availability, and dependency on third-party suppliers for manufacturing, assembly, testing, or packaging. These factors have led to mismatches between supply and demand.
- **2025:** The emphasis grows on the risks of supply chain mismatches, with more detail on how inaccurate demand estimation and supplier dependency could harm business operations and financial results.
  - **Citation:** “Long manufacturing lead times and uncertain supply and component availability, along with inaccurate demand estimation, have led and could lead to mismatches between supply and demand... Dependency on third-party suppliers... reduces control over product quantity, quality, yields, and delivery schedules, potentially harming the business.”

**Comparison:**  
Both companies strengthen their focus on supply chain risks in 2025. Tesla’s filings move from specific supplier issues to a broader concern about cost control and operational efficiency. NVIDIA’s filings provide more detail on the operational impact of supply chain mismatches and supplier dependency.

---

### **3. Human Capital Management Risks**

**Tesla:**

- **2024:** The filings reference the importance of maintaining a safe, respectful, and compliant workplace environment, as well as the recruitment, development, and retention of talent.
- **2025:** The discussion continues to stress these points, with an added emphasis on the evolving regulatory and compliance landscape, and the potential impact of human capital risks on business performance.
  - **Citation:** “Risks concerning human capital management, including the recruitment, development, and retention of talent, as well as maintaining a safe, respectful, and compliant workplace environment.”

**NVIDIA:**

- **2024:** The filings mention challenges in attracting, retaining, and motivating executives and key employees as a significant risk.
- **2025:** The emphasis increases on the competitive landscape for talent, and the potential for business disruption if key personnel are lost or if the company fails to maintain a strong workplace culture.
  - **Citation:** “Challenges in attracting, retaining, and motivating executives and key employees.”

**Comparison:**  
Both companies maintain a strong focus on human capital risks in 2025, but the emphasis shifts to reflect a more competitive environment for talent and the increasing importance of compliance and workplace culture. Tesla highlights regulatory and compliance aspects, while NVIDIA stresses the risk of business disruption from talent loss.

---

**Summary Table:**


| Theme                          | Tesla: 2024 → 2025 Emphasis Change                                 | NVIDIA: 2024 → 2025 Emphasis Change                              |
| ------------------------------ | ------------------------------------------------------------------ | ---------------------------------------------------------------- |
| Product Launch/Business Growth | Broader focus on global expansion and complexity of new offerings  | Greater urgency on rapid industry change and timely innovation   |
| Supply Chain/Supplier Risks    | From specific supplier issues to broader cost and efficiency risks | More detail on operational impact of supply-demand mismatches    |
| Human Capital Management       | Added emphasis on compliance and regulatory landscape              | Increased focus on competition for talent and risk of disruption |


5 reasoning steps the last 2 with no response + 21 sources

---



### GPT-5.1 Answer



Request timed out. The query may be too complex — try simplifying or rephrasing the question.

Sorry, I couldn’t get a response. Please check the backend connection.

---

## Q4 — Profitability consistency: net income + operating margin (Apple vs Microsoft)

Compare **Apple** and **Microsoft** from **2023 through 2025** on **net income** and **operating margin**. Determine which company shows **more consistent profitability improvement** over the period (define consistency using the observed year‑to‑year movements), and cite the specific 10‑K explanations for the main drivers behind the margin/net income changes in each year.

**Total tokens (question):** ~74

### GPT-4.1 Answer

From 2023 through 2025, Apple and Microsoft both experienced growth in net income and operating margin, but the patterns and consistency of their profitability improvements differed.

**Net Income Comparison:**

- **Apple:**
  - 2023: $96,995 million
  - 2024: $93,736 million (decrease)
  - 2025: $112,010 million (increase)
- **Microsoft:**
  - 2023: $72,361 million
  - 2024: $88,136 million (increase)
  - 2025: $101,832 million (increase)

**Operating Margin Comparison:**

- **Apple:**
  - 2023: 29.2%
  - 2024: 32.2% (increase)
  - 2025: 32.1% (slight decrease)
- **Microsoft:**
  - 2023: 41.8%
  - 2024: 44.7% (increase)
  - 2025: 45.6% (increase)

**Consistency of Profitability Improvement:**

- **Microsoft** demonstrates more consistent year-to-year improvement in both net income and operating margin. Net income rises each year, and operating margin increases steadily from 41.8% to 45.6% over the period.
- **Apple** shows less consistency: net income declines from 2023 to 2024 before rebounding in 2025, and operating margin rises in 2024 but dips slightly in 2025.

**Main Drivers Behind Changes (as explained in the 10-Ks):**

**Apple:**

- **2023:** Net income fell due to a 3% drop in net sales, mainly from lower Mac and iPhone sales and negative foreign currency impacts. Gross margin improved due to cost savings and product mix, but higher R&D expenses increased operating costs.
- **2024:** Net income decreased further, primarily because of a much higher provision for income taxes, despite higher net sales (driven by Services growth) and improved gross margin. Operating margin benefited from higher gross margins but was partially offset by increased R&D and SG&A expenses.
- **2025:** Net income rose sharply, driven by strong growth in both Products and Services, higher gross margin percentage, and a lower tax provision. Operating margin remained high due to revenue growth and improved gross margins, especially in Services, though operating expenses continued to rise.

**Microsoft:**

- **2023:** Net income was flat due to one-time charges (severance, impairments, lease costs) and the absence of a prior-year tax benefit. Operating margin was pressured by higher expenses but supported by growth in cloud and productivity segments and lower depreciation from accounting changes.
- **2024:** Net income and operating margin both increased significantly, fueled by broad revenue growth (especially in Intelligent Cloud and Productivity), and the absence of prior-year one-time charges. Operating expenses rose due to acquisitions and cloud investments, but revenue growth outpaced these increases.
- **2025:** Net income and operating margin continued to rise, with growth across all segments. However, scaling AI infrastructure began to pressure gross margin percentage, though this was offset by efficiency gains and strong revenue growth. Operating expenses increased due to ongoing investments in cloud and AI.

**Summary:**  
Microsoft’s profitability improvements were more consistent year-over-year, with both net income and operating margin rising each year. Apple’s results were more variable, with a dip in net income and a slight operating margin decrease in 2025 after a strong 2024. The main drivers for both companies included revenue growth (especially in cloud and services), cost management, changes in operating expenses, and, for Apple, significant impacts from tax provisions and foreign currency. For Microsoft, investments in AI and cloud infrastructure became increasingly important in shaping margins by 2025.

6 reasoning steps + 43 sources

---

### GPT-5.1 Answer





---

## Q5 — Segment-specific growth comparison: Alphabet ads vs Microsoft cloud (2023–2025)

From **2023 to 2025**, track **Alphabet (Google) advertising revenue** and **Microsoft cloud revenue** (use the segment names as reported). Compute the **percentage growth** over 2023→2025 for each segment, determine which segment grew faster, and summarize the **drivers** each company attributes the growth (or slowdown) to, citing the relevant 10‑K passages across multiple years.

**Total tokens (question):** ~77

### GPT-4.1 Answer

From 2023 to 2025, Alphabet's (Google's) advertising revenue and Microsoft's cloud revenue (as reported in their respective SEC filings) were as follows:

**Alphabet (Google) Advertising Revenue:**

- 2023: $237.9 billion
- 2024: $264.6 billion
- 2025: $294.7 billion

**Microsoft Cloud Revenue (as reported):**

- 2023: $111.6 billion
- 2024: $137.7 billion
- 2025: $168.9 billion

**Percentage Growth (2023 to 2025):**

- **Alphabet Advertising:**  
Percentage growth = [(294.7 - 237.9) / 237.9] × 100  
= (56.8 / 237.9) × 100  
≈ 23.9%
- **Microsoft Cloud:**  
Percentage growth = [(168.9 - 111.6) / 111.6] × 100  
= (57.3 / 111.6) × 100  
≈ 51.4%

**Which Segment Grew Faster?**  
Microsoft's cloud revenue grew faster than Alphabet's advertising revenue over the 2023 to 2025 period.

**Drivers of Growth or Slowdown:**

**Alphabet (Google) Advertising Revenue Drivers:**

- Growth was supported by the ongoing shift to online platforms and the evolution of the digital economy, though the pace slowed compared to the post-pandemic surge.
- Increased competition for user engagement and advertisers, including from AI product providers, influenced revenue trends.
- Expansion into new devices and advertising formats (e.g., YouTube, Google Play, connected TVs) contributed to growth, but these formats generally monetize at lower rates than traditional search ads.
- Integration of AI into products (such as AI in Search and AI Overviews) changed monetization strategies, with newer ad formats tending to have lower margins.
- Traffic Acquisition Costs (TAC) increased with revenue, but the TAC rate as a percentage of advertising revenue decreased due to changes in revenue mix.
- Macroeconomic conditions and advertiser spending patterns affected revenue, with adverse environments leading to slowdowns.
- Growth in international markets contributed, though these markets often monetize at lower rates and are subject to foreign exchange fluctuations.
- Technological and regulatory changes, including privacy practices and ad-blocking technologies, posed risks to advertising revenue.
- Increasing revenue diversification into non-advertising sources (cloud, subscriptions, devices) affected overall revenue mix and margins.

**Microsoft Cloud Revenue Drivers:**

- The primary driver was strong performance and expansion of Azure and other cloud services, with Azure revenue showing robust growth.
- Increased demand for hybrid solutions (e.g., Windows Server, SQL Server in multi-cloud environments) and AI services fueled growth.
- Ongoing investments in cloud and AI infrastructure supported the ability to meet evolving customer needs.
- Growth in Microsoft 365 Commercial cloud also contributed to overall cloud revenue increases.
- Scaling of AI infrastructure led to higher operating costs, putting some pressure on gross margins, though efficiency gains in Azure and Microsoft 365 Commercial cloud partially offset these pressures.

**Summary:**  
Between 2023 and 2025, Microsoft's cloud segment grew at a significantly faster rate (about 51.4%) compared to Alphabet's advertising segment (about 23.9%). Alphabet's advertising revenue growth was driven by digital adoption, new ad formats, and AI integration, but was moderated by competition, lower monetization rates in new formats, macroeconomic factors, and regulatory changes. Microsoft's cloud revenue growth was propelled by Azure's expansion, demand for AI and hybrid solutions, and continued investment in cloud infrastructure, with some margin pressure from scaling AI capabilities.

7 reasoning steps( 1 empty) - 51 sources

### GPT-5.1 Answer

