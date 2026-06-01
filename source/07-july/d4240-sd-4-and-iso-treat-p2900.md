---
title: "Did ISO or SD-4 Govern the P2900 Ballot?"
document: P4240R0
date: 2026-05-19
intent: info
audience: WG21
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

P3846R1 quotes SD-4: "we do not significantly delay progress on concrete proposals in order to wait for alternative proposals we might get in the future." The ISO/IEC Directives say: consensus is "a process that involves seeking to take into account the views of all parties concerned and to reconcile any conflicting arguments."

Nineteen of twenty-six national bodies filed comments on P2900. Spain, the United States, France, and Finland requested removal. This paper applies both procedural systems - one at a time, same facts - to the same NB comment phase and documents what each produces. One system requires reconciliation. The other provides a mechanism for dismissal. Both are publicly available. The comparison is systematic.

---

## Revision History

### R0: July (Post-Brno Mailing)

- Initial version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author asks for nothing.

---

## 2. What P2900 Achieved

SG21 spent five years gathering use cases<sup>[6]</sup>, exploring the design space, and refining the proposal before forwarding it to EWG, where it was examined for another year. [P2900R14](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2900r14.html)<sup>[7]</sup> was adopted with strong consensus<sup>[8]</sup> into the C++26 working draft at Hagenberg in February 2025. Complete implementations exist in publicly available forks of GCC and Clang<sup>[9]</sup>. The implementers reported P2900's specification as "clear and implementable."

P3846R1<sup>[10]</sup> addresses eighteen concerns raised in NB comments and opposition papers. It carries twenty-two co-authors, including implementers from GCC and Clang, static analysis vendors, library authors, and committee veterans. Each concern receives a structured treatment: summary, discussion status, response, and detailed analysis with citations. The paper is thorough, systematic, and represents the largest coordinated defense of a single feature in WG21's published record.

The quality of the technical work and the depth of the procedural defense are not in question. What is in question is which procedural system governs how NB comments interact with that defense.

---

## 3. The Quote

Doumler et al. write in P3846R1<sup>[10]</sup>, Concern 15:

> Procedurally, delaying the standardisation of P2900 due the concerns of [P3829R0] about interactions with hypothetical proposals would be against WG21 practice. According to [SD4], 'we do not significantly delay progress on concrete proposals in order to wait for alternative proposals we might get in the future'.

P3846R1 invokes this principle to argue that P3829R0's<sup>[11]</sup> concerns about P2900's interactions with deep const and generic decorators cannot justify delay. The principle is cited as settled WG21 practice.

---

## 4. What The Principle Says

SD-4<sup>[12]</sup> states, under "Delay vs. bird in the hand":

> We cannot act on ideas without papers, and we do not significantly delay progress on concrete proposals in order to wait for alternative proposals we might get in the future. If we have an active proposal that is making progress, and an objection is raised that a different competing approach would be better but that other approach does not yet have a paper, the EWG or LEWG subgroup chair may elect to delay the progress of the active proposal by one meeting to give the objector(s) opportunity to bring an on-time proposal paper. Otherwise, if a competing alternative does not have a paper, it does not exist and will not block progress of a proposal that we do have before us.

A following paragraph extends the same logic to the TS-to-IS pipeline:

> If by the time the TS is ready to be considered for merging into the IS we do not have alternative proposals actively progressing, the default action is to move forward with the proposal we have, we will not wait indefinitely for something better.

The principle establishes structural priority for first-movers. The concrete proposal advances. The alternative that has not materialized as a paper does not procedurally exist. The chair may grant a one-meeting delay. Beyond that, the incumbent proceeds.

This principle was deployed during the P2900 ballot. On 2025-10-23, Nevin Liber quoted it on the SG15 mailing list, asking opponents: "What is the paper number of the proposal of the contract feature which the C++26 CD is blocking later adoption of?"<sup>[13]</sup> John Spicer responded that the bird-in-hand principle does not apply "when the feature in hand is itself harmful," citing P3829R0 and P3835R0 as new technical information<sup>[14]</sup>. Spicer also noted historical precedent: C++0x concepts were pulled in 2009 and not replaced until 2017; contracts were removed from C++20 in 2019 without a replacement<sup>[15]</sup>.

---

## 5. What The ISO Directives Say Instead

The ISO/IEC Directives Part 1<sup>[16]</sup> contain no first-mover doctrine. No provision anywhere in the Directives establishes priority based on order of arrival, revision count, or accumulated procedural momentum.

The Directives define consensus (Clause 2.5.6):

> General agreement, characterized by the absence of sustained opposition to substantial issues by any important part of the concerned interests and by a process that involves seeking to take into account the views of all parties concerned and to reconcile any conflicting arguments.

Seven properties of this system bear on the P2900 NB comment phase:

**1. Consensus requires reconciliation.** The definition is not "absence of opposition." It is "absence of sustained opposition" achieved through "a process that involves seeking to take into account the views of all parties concerned and to reconcile any conflicting arguments" (Clause 2.5.6)<sup>[16]</sup>. The reconciliation obligation is structural, not optional.

**2. Negative votes require technical comments.** A P-member voting negative must provide technical reasons (Clause 2.6.2)<sup>[16]</sup>. The Directives do not restrict the content of technical comments. No category of ballot comment is declared "not appropriate."

**3. Every attempt must be made to resolve negative votes.** The exact text: "every attempt shall be made to resolve negative votes" (Clause 2.6.5)<sup>[16]</sup>. The obligation is on the project, not on the objector.

**4. Disagreement triggers mandatory discussion.** If two or more P-members disagree with the chair's decision on comment disposition, discussion at a meeting is required (Clause 2.6.5)<sup>[16]</sup>.

**5. Objection carries no credibility penalty.** The Directives treat objection as information, not disruption. Those with sustained opposition are explicitly directed to the appeals process (Clause 2.5.6)<sup>[16]</sup>. No Directive provision states that repeated objection "erodes credibility."

**6. The appeal chain provides a credible outside option.** National Bodies may appeal any action or inaction to the parent TC, TMB, or council board within eight weeks (Clause 5.1)<sup>[16]</sup>. The existence of the appeal chain disciplines the inside game without being exercised.

**7. No first-mover doctrine.** The Directives contain no equivalent of SD-4's "bird in the hand." A competing or alternative approach receives the same procedural access as the incumbent. The system selects for designs that reconcile conflicting arguments, not designs that arrived first.

---

## 6. The Same NB Comments, Two Systems

The C++26 Committee Draft ballot closed on 2025-10-01. N5028<sup>[17]</sup> records the official collated comments. Nineteen of twenty-six P-member national bodies responded: Austria, Brazil, Bulgaria, Canada, China, Czech Republic, Finland, France, Germany, Italy, Netherlands, Poland, Romania, Russia, Spain, Sweden, Switzerland, United Kingdom, and the United States<sup>[18]</sup>.

Of these nineteen, the following filed comments requesting removal of P2900 from the C++26 working draft: Spain (ES-049, ES-050), the United States (US-051, US-052), France (FR-053, FR-054), and Finland (FI-071). Romania (RO-056) requested removing the "ignore" semantic or removing contracts entirely<sup>[18]</sup>.

Ville Voutilainen, a co-author of P2900, characterized the response in P4009R0<sup>[19]</sup>: "We have never had this much and this strong opposition to a feature in a DIS."

P3846R1<sup>[10]</sup> addresses these comments across eighteen structured sections. Each section includes a "Discussion Status" subsection. In the portions of P3846R1 the author was able to verify, the phrase "No new information has been presented since" appears eight times. Other Discussion Status sections conclude with "no concerns raised by that group" or equivalent language indicating prior resolution. P3846R1's abstract states: "Almost all objections are repetitions of those raised in earlier papers, addressed in subsequent responses, and extensively discussed in EWG."

EWG confirmed contracts in the C++26 CD at Croydon in March 2026<sup>[20]</sup>.

The table below applies each procedural system to these facts.

| Procedural Event | SD-4 Treatment | ISO Directives Treatment |
|---|---|---|
| P2900 adopted at Hagenberg with strong consensus (February 2025) | Directional consensus declared. Reversing it is procedurally near-impossible: ballot comments that revisit past decisions are "not appropriate" (SD-4)<sup>[12]</sup> | Consensus requires ongoing reconciliation of conflicting arguments (2.5.6)<sup>[16]</sup>. NB ballot comments may raise any technical concern (2.6.2)<sup>[16]</sup> |
| 19 of 26 NBs file comments; 5 request removal | Concerns are "repetitions of those raised in earlier papers" (P3846R1)<sup>[10]</sup>. "No new information has been presented since" (P3846R1)<sup>[10]</sup> | "Every attempt shall be made to resolve negative votes" (2.6.5)<sup>[16]</sup>. The obligation is on the project |
| Opponents lack a complete alternative proposal | "If a competing alternative does not have a paper, it does not exist" (SD-4)<sup>[12]</sup>. Liber: "What is the paper number?"<sup>[13]</sup> | No first-mover doctrine exists. The Directives contain no provision that conditions procedural standing on having a replacement ready |
| Objectors escalate repeatedly | Repeated escalation "erodes credibility" (SD-4)<sup>[12]</sup> | Objection carries no credibility penalty. Objectors are directed to the appeals process (2.5.6)<sup>[16]</sup> |
| Concerns were previously discussed in SG21 and EWG | Prior discussion satisfies procedural due diligence. "These concerns have been heard and considered, and they have been at each stage in the past" (P3846R1)<sup>[10]</sup> | Prior discussion does not extinguish NB ballot comment rights. Comments must be addressed (2.6.5)<sup>[16]</sup>. If 2+ P-members disagree with disposition, meeting discussion is required (2.6.5)<sup>[16]</sup> |
| A co-author of P2900 writes: "We have never had this much and this strong opposition to a feature in a DIS" (P4009R0)<sup>[19]</sup> | The level of opposition does not alter the procedural calculus. The concrete proposal has a paper. Alternatives do not. The proposal advances | The level of opposition is itself a signal. "Sustained opposition to substantial issues by any important part of the concerned interests" is the definitional boundary of consensus (2.5.6)<sup>[16]</sup> |

---

## 7. The Chain

P3846R1 does not invoke a single SD-4 mechanism. It chains several together. Each link is individually cited. No single link is unreasonable. The chain is the finding.

**Link 1: Bird-in-hand.** SD-4<sup>[12]</sup> establishes structural priority for the concrete proposal. P3846R1<sup>[10]</sup> invokes it at Concern 15 to dismiss interactions with hypothetical future features. The principle's logic extends beyond Concern 15: it is the structural reason P2900 advances and alternatives that lack papers do not procedurally exist.

**Link 2: Prior consideration.** P3846R1<sup>[10]</sup> characterizes the NB concerns as previously considered: "Almost all objections are repetitions of those raised in earlier papers." The phrase "No new information has been presented since" appears eight times across the Discussion Status sections. Prior consideration becomes a reason to treat the concern as resolved rather than as a concern that persists.

**Link 3: Consensus ratchet.** P2900 was adopted with strong consensus at Hagenberg<sup>[8]</sup>. SD-4<sup>[12]</sup> treats ballot comments that revisit past decisions as "not appropriate." The directional consensus, once declared, is procedurally difficult to reverse. P3846R1 operates within this structure: the NB comments arrive after the ratchet has engaged.

**Link 4: Credibility cost.** SD-4<sup>[12]</sup> states that repeated escalation "erodes credibility." The objector who raises a concern that has been "previously considered" and escalates it through NB comments bears a procedural cost. The Directives impose no such cost.

**Link 5: No feedback loop.** Neither SD-4 nor the committee's practice includes a mechanism for asking whether P2900 achieved its claimed benefits after adoption. P3846R1 defends what was decided. No procedure requires examining whether the decision was correct. The loop is never opened.

Each link serves a function. Link 1 gives the incumbent priority. Link 2 converts NB comments into repetitions. Link 3 makes the original decision structurally irreversible. Link 4 attaches a cost to objection. Link 5 ensures the system never revisits its own output.

The ISO Directives provide a countermeasure to each link. Fixed terms and reappointment provide accountability moments (Directive 1.12.1)<sup>[16]</sup>. Unrestricted ballot comments prevent Link 2 (Directive 2.6.2)<sup>[16]</sup>. The obligation to resolve negative votes prevents Link 3 (Directive 2.6.5)<sup>[16]</sup>. Protected objection prevents Link 4 (Directive 2.5.6)<sup>[16]</sup>. Mandatory project review and cancellation after five years prevent Link 5 (Directives 2.1.6, 2.6.5)<sup>[16]</sup>.

---

## 8. Conclusion

One system asks the proposal author to reconcile conflicting arguments. The other asks the objector for a paper number.

---

## References

[1] [P4003R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p4003r0.html) - "A Coroutine Lazy Type" (Vinnie Falco, 2025).

[2] [P4007R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p4007r0.html) - "Deficiencies in std::execution" (Vinnie Falco, 2025).

[3] [P4100R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p4100r0.html) - "Asynchronous I/O with Coroutines" (Vinnie Falco, 2025).

[4] [P4196R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4196r0.html) - "Discrepancies Between SD-4 and the ISO Directives" (Vinnie Falco, 2026).

[5] [P4201R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4201r0.html) - "Two Systems, One Committee: A Game-Theoretical Analysis of ISO Governance vs. SD-4" (Vinnie Falco, 2026).

[6] [P1995R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2020/p1995r1.html) - "Contracts - Use Cases" (Timur Doumler, Joshua Berne, 2020).

[7] [P2900R14](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2900r14.html) - "Contracts for C++" (Joshua Berne, Timur Doumler, Andr&eacute; Maurer, 2024).

[8] [N5007](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/n5007.pdf) - "2025-02 Hagenberg Meeting Minutes" (Nina Dinka Ranns, 2025).

[9] [P3460R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3460r0.html) - "Contracts Implementation Report" (Timur Doumler, 2024).

[10] [P3846R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3846r1.pdf) - "C++26 Contract Assertions, Reasserted" (Timur Doumler, Joshua Berne, Ga&scaron;per A&zcaron;man, Peter Bindels, Peter Dimov, Louis Dionne, Eric Fiselier, Mungo Gill, Pablo Halpern, Tom Honermann, Corentin Jabot, John Lakos, Nevin Liber, Lisa Lippincott, Ryan McDougall, Jason Merrill, Roger Orr, Nina Dinka Ranns, Ren&eacute; Ferdinand Rivera Morell, Oliver Rosten, Iain Sandoe, Hui Xie, 2025).

[11] [P3829R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3829r0.pdf) - "Contracts Do Not Belong in the Language" (David Chisnall, John Spicer, Ville Voutilainen, Gabriel Dos Reis, Carlos Garcia Sanchez, 2025).

[12] [SD-4](https://isocpp.org/std/standing-documents/sd-4-wg21-practices-and-procedures) - "WG21 Practices and Procedures" (Guy Davidson, 2026).

[13] Nevin Liber on the SG15 mailing list, 2025-10-23. [https://lists.isocpp.org/sg15/2025/10/2933.php](https://lists.isocpp.org/sg15/2025/10/2933.php)

[14] John Spicer on the SG15 mailing list, 2025-10-23. [https://lists.isocpp.org/sg15/2025/10/2936.php](https://lists.isocpp.org/sg15/2025/10/2936.php)

[15] John Spicer on the SG15 mailing list, 2025-10-23. [https://lists.isocpp.org/sg15/2025/10/2931.php](https://lists.isocpp.org/sg15/2025/10/2931.php)

[16] ISO/IEC. "ISO/IEC Directives, Part 1 - Consolidated JTC 1 Supplement." 2023. [https://jtc1info.org/wp-content/uploads/2023/11/ISO-IEC-Consolidated-JTC-1-Supplement-2023.pdf](https://jtc1info.org/wp-content/uploads/2023/11/ISO-IEC-Consolidated-JTC-1-Supplement-2023.pdf)

[17] [N5028](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/n5028.pdf) - "C++26 CD Collated Comments" (2025).

[18] Arthur O'Dwyer. "The C++26 NB comments have arrived." 2025-10-12. [https://quuxplusone.github.io/blog/2025/10/12/nb-comments/](https://quuxplusone.github.io/blog/2025/10/12/nb-comments/)

[19] [P4009R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4009r0.html) - "A Proposal for Solving All of the Contracts Concerns" (Ville Voutilainen, 2026).

[20] [cplusplus/papers Issue #2455](https://github.com/cplusplus/papers/issues/2455) - P3846R1 tracking issue, closed March 2026.
