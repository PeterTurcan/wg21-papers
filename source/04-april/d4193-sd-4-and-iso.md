---
title: "Discrepancies Between SD-4 and the ISO Directives"
document: D4193R0
date: 2026-04-19
intent: info
audience: WG21
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

WG21 has two procedural documents. One is binding. The other is followed.

SD-4<sup>[1]</sup> governs the day-to-day operation of WG21 - subgroup chair appointments, consensus thresholds, escalation procedures, ballot comment handling, and work prioritization. The ISO/IEC Directives Part 1<sup>[2]</sup> govern the same topics for all JTC 1 working groups. This paper places the two documents side by side on eleven points where both address the same subject. On every point, SD-4 deviates from the Directives. SD-4 does not appear in any WG21 document list.

---

## Revision History

### R0: April 2026 (post-Croydon mailing)

- Initial version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

This paper takes no position on the technical quality of any feature, including Contracts. The analysis is procedural.

The author asks for nothing.

---

## 2. Two Documents

WG21 participants follow SD-4<sup>[1]</sup>. SD-4 describes itself as the "How We Work Cheat Sheet" and states that "everyone who participates in WG21 is expected to be familiar with this information."

All JTC 1 working groups, including WG21, are bound by the ISO/IEC Directives Part 1<sup>[2]</sup>. The Directives are maintained by the ISO/IEC Joint Directives Maintenance Team and approved by the ISO Technical Management Board and IEC Standardization Management Board. SD-4 describes itself as supplementing the Directives: it "summarizes some of WG21's current practices and procedures, in addition to the requirements of the ISO/IEC Directives and JTC 1 Supplement."

Both documents are publicly available. The comparison below is mechanical.

**What the current system produces.** Four consecutive on-time releases from C++14 through C++23. Major compiler implementations tracking the standard within months of publication. A volunteer workforce that has produced modules, concepts, ranges, coroutines, `std::expected`, `std::print`, and `std::mdspan`. The procedural deviations documented below purchased something - speed, decisiveness, simplified administration. The cost is measured in Directive compliance.

---

## 3. What SD-4 Changes

Each entry below places a Directive provision next to the corresponding SD-4 provision. The Directive clause numbers refer to the ISO/IEC Directives Part 1 - Consolidated JTC 1 Supplement 2023<sup>[2]</sup>.

### 3.1 Subgroup Chair Appointment

Directive 1.12.1<sup>[2]</sup> governs the appointment of working group convenors in all JTC 1 working groups:

> "Working group Convenors shall be appointed by the committee for up to three-year terms. Such appointments shall be confirmed by the National Body (or liaison organization)."

SD-4<sup>[1]</sup> states:

> "Subgroup chairs are appointed by the convener, and are selected to match the current needs of the subgroup. They have no fixed term."

| Requirement | Directives | SD-4 |
|-------------|-----------|------|
| Appointing authority | The committee | The Convener |
| Term length | Up to three years | No fixed term |
| NB confirmation | Required | Not mentioned |

### 3.2 Consensus Threshold

The Directives define consensus in ISO/IEC Guide 2:2004, quoted at Directive 2.5.6<sup>[2]</sup>. Voting thresholds are specified at defined stages: 2/3 of P-members for new work items (2.3.5), for DIS approval (2.6), and for other formal actions. No "2:1 favor-to-against" threshold appears anywhere in the Directives.

SD-4<sup>[1]</sup> states:

> "A proposal normally advances if there are more than twice as many in favor of a proposal as against."

The 2:1 rule applies in subgroup polls where "each person in the room can cast one vote"<sup>[1]</sup>. The Directives require that working group participants be registered experts appointed by P-members (1.12.1, 1.12.2)<sup>[2]</sup>.

### 3.3 Priority Allocation

Directive 1.1(f)<sup>[2]</sup> reserves to the technical management board the "allocation of priorities, if necessary, to particular items of technical work."

SD-4<sup>[1]</sup> delegates this function to a Direction Group:

> "The direction group is a small by-invitation group of experienced participants who are asked to recommend priorities for WG21."

> "The design group chairs use that list to prioritize work at meetings."

Directive 1.2<sup>[2]</sup> provides that advisory groups may be established "by one of the technical management boards" with defined terms of reference. Directive 1.2.7<sup>[2]</sup> requires that "such a group shall be disbanded once its specified tasks have been completed."

### 3.4 Ballot Comment Scope

The Directives impose no content restrictions on National Body ballot comments beyond relevance to the balloted document. Directive 0.7(c)<sup>[2]</sup> states that National Bodies have "the responsibility of ensuring that their technical standpoint is established taking account of all interests concerned at the national level."

SD-4<sup>[1]</sup> declares two categories of NB comments "not appropriate":

> "A ballot comment that requests adding an additional feature that is not already in the document is out of scope."

> "A ballot comment that requests a change that was already considered and decided otherwise at a WG21 meeting, and comes from a national body that was present at the meeting and had an opportunity to have their objections be heard and considered, is out of harmony with the ISO Code of Conduct."

### 3.5 Escalation and Credibility

SD-4<sup>[1]</sup> states that escalation becomes inappropriate:

> "when a participant or national body regularly uses the escalation process to express a pattern of strong disagreement on topic after topic, which erodes their credibility."

The Directives contain no provision that penalizes repeated use of dispute resolution mechanisms.

---

## 4. What SD-4 Does Not Mention

SD-4 describes itself as a comprehensive procedural guide. The following Directive provisions address topics within SD-4's scope but do not appear in SD-4.

| Directive Provision | Subject | SD-4 |
|--------------------|---------|----|
| 1.8.2(a) | Chair "shall act in a purely international capacity, divesting him- or herself of a national position" | |
| 1.12.1 | Convenor "shall act in a purely international capacity" | |
| 1.8.2(d) | Chair must "ensure at meetings that all points of view expressed are adequately summed up" | |
| 5.1.1 | NB right of appeal to parent committee, TMB, and council board | |
| 5.1.2 | P-member may appeal any action "not in accordance with the ISO/IEC Directives" | |
| 5.3.4 | TMB Chair "shall form a conciliation panel" to hear appeals | |
| 1.8.2(e) | Decisions "made available in written form for confirmation during the meeting" | |
| 1.9.2(c) | Decisions "posted within 48 hours after the meeting" | |

**The right column is empty because SD-4 is silent on each of these provisions.**

---

## 5. SD-4 in the Document System

SD-1 is the official WG21 document list, maintained continuously since the committee's founding. It records every standing document, every paper, and every numbered document produced by the committee.

SD-4 does not appear in SD-1 for any year examined: 2009<sup>[3]</sup>, 2012<sup>[4]</sup>, 2016<sup>[5]</sup>, 2019<sup>[6]</sup>, 2023<sup>[7]</sup>, or 2024<sup>[8]</sup>. Other standing documents - SD-3, SD-5, SD-6, SD-7, SD-8, SD-9, SD-10 - appear in these lists. SD-4 alone is absent.

SD-4 is published on isocpp.org, the website of the Standard C++ Foundation. It is not published on open-std.org, the official WG21 document archive.

---

## 6. Frequently Cited Misconceptions

The following responses address objections raised in early review of this paper.

### "The Directives don't cover WG internal substructure"

The claim is that ISO only sees WG21 as a single working group with a convener, and that everything inside — subgroup chairs, consensus procedures, scheduling — is the WG's private business that the Directives do not reach.

Directive 1.12.1<sup>[2]</sup> refutes this directly. It prescribes how working group convenors are appointed (by the committee), for how long (up to three-year terms), and with what oversight (National Body confirmation). These are internal working group matters. The Directives regulate them anyway.

If internal WG procedures were exempt from the Directives, then any JTC 1 working group could adopt whatever procedures it likes — abolish term limits, restrict ballot comments, create unaccountable advisory bodies — and the Directives would have nothing to say. That reading makes the Directives' working-group-level provisions dead letters. The Directives contain those provisions precisely because WG internals are within scope.

### "Subgroup chairs derive authority from the convener, so the convener can appoint them however they wish"

The convener's authority is itself delegated from the ISO framework. Directive 1.4<sup>[2]</sup> states that deviations from the Directives require TMB or CEO authorization. It contains no exception for delegated authority exercised within a working group. A convener who creates substructures is exercising ISO-derived authority and remains bound by the Directives when doing so.

### "SD-4 supplements the Directives; it doesn't replace them"

SD-4 describes itself this way. The question is whether this self-description is accurate. On every topic where both documents speak — chair appointment, consensus thresholds, ballot comment scope, escalation, priority allocation — the SD-4 provision is the one followed in practice. A supplement that is followed instead of the document it supplements is a replacement.

### "These deviations are harmless / the system works fine"

This paper takes no position on whether the deviations produce good or bad technical outcomes. Section 2 acknowledges that the current system has produced four consecutive on-time releases and major features. The question is procedural compliance, not technical quality. Directive 1.4<sup>[2]</sup> requires authorization for deviations. Whether the deviations are beneficial is a separate question from whether they are authorized.

### "This paper doesn't have a point"

The comparison had not been made. Both documents are public. The deviations documented in Sections 3-5 are either authorized under Directive 1.4<sup>[2]</sup> or they are not. This paper provides the information needed to ask that question.

---

## 7. How Deviations Are Reported

Directive 1.4<sup>[2]</sup> states:

> "Deviations from the procedures set out in the present document shall not be made without the authorization of the Chief Executive Officers of ISO or IEC or the technical management boards for deviations in the respective organizations."

Directive 5.1.2<sup>[2]</sup> states that a P-member of a committee may appeal against any action or inaction "not in accordance with" the ISO/IEC Directives.

---

## References

1. Herb Sutter, "SD-4: WG21 Practices and Procedures," ISO/IEC JTC1/SC22/WG21/SD-4, 2024-12-30. [https://isocpp.org/std/standing-documents/sd-4-wg21-practices-and-procedures](https://isocpp.org/std/standing-documents/sd-4-wg21-practices-and-procedures)
2. ISO/IEC, "ISO/IEC Directives, Part 1 - Consolidated JTC 1 Supplement," 2023. [https://jtc1info.org/wp-content/uploads/2023/11/ISO-IEC-Consolidated-JTC-1-Supplement-2023.pdf](https://jtc1info.org/wp-content/uploads/2023/11/ISO-IEC-Consolidated-JTC-1-Supplement-2023.pdf)
3. SD-1: 2009 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2009/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2009/sd-1.htm)
4. SD-1: 2012 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2012/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2012/sd-1.htm)
5. SD-1: 2016 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/sd-1.htm)
6. SD-1: 2019 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/sd-1.htm)
7. SD-1: 2023 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/sd-1.htm)
8. SD-1: 2024 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/sd-1.htm)
