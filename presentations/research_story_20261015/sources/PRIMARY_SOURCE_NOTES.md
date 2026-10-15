# External primary-source verification

Verified for the presentation on 15 October 2026. The statements below are research notes, not claims about deployed collusion.

- **Microsoft CNA:** retained machine-readable record `CVE-2025-32711.json`, published 11 June 2025. The description establishes an M365 Copilot AI command injection vulnerability enabling unauthorized network information disclosure. It does not establish a known victim breach or collusion. [Vendor advisory](https://msrc.microsoft.com/update-guide/vulnerability/CVE-2025-32711).
- **Nakamura et al., Colosseum v2:** [primary paper](https://arxiv.org/abs/2602.15198v2), Section 5.4 and Figure 4. The Emergent group reports 57.89% of 19 models with action-advantage change greater than zero and 10.53% with judge-score change at least one. These yield 11/19 and 2/19 respectively. The thresholds differ and do not give statistical significance counts or a detector false-negative rate. Checked against the locally downloaded primary text, lines 207–212, before building this presentation.
- **Mathew et al., Hidden in Plain Text v2:** [primary paper](https://arxiv.org/abs/2410.03768v2), Sections 4.1 and 5.1, Table 1. The paper studies optimized steganography in constructed tasks, including candidate screening under oversight and paraphrasing. This motivates the presentation's capability-risk example. It is not evidence of a deployed hiring incident. The presentation does not transfer the paper's best task-success number to our setup.

Full external paper texts are not required to rebuild the charts. Consult the linked primary papers for the complete methods and qualifications.
