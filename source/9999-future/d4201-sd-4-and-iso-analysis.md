---
title: "Two Systems, One Committee: A Game-Theoretical Analysis of ISO Governance vs. SD-4"
document: P4201R0
date: 2026-04-20
intent: info
audience: WG21
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

Two procedural documents govern WG21. One was designed by the international standards system over decades of institutional evolution across hundreds of working groups. The other was written by one person on a private foundation's website. They produce different systems. The systems produce different outcomes. The outcomes serve different constituencies.

This paper applies game-theoretic reasoning, six institutional forces documented in published research from 1911 to 2003, ten principles of human action from Ludwig von Mises, five diagnostic tests from Great Founder Theory, and more than twenty empirical studies on committee decision-making and the social cost of visible dissent to both systems. For each of eight player classes, it identifies the dominant strategy each system creates, the mechanism that creates it, and what the reader should look for in WG21's published record to observe the effect. Every central claim is accompanied by a falsification criterion - a named condition under which the claim would be wrong. The institutional prognosis distinguishes three layers: a living technical tradition, a dead governance tradition, and a direction-setting process that exhibits cargo cult properties.

The analysis names no individuals. Every structural observation applies to the office, not the occupant. The analysis is a comparison, not a recommendation. The comparison does the work.

---

## Revision History

### R0: August 2026 (post-St. Louis mailing)

- Initial version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author is the founder of the C++ Alliance and maintains competing proposals in the `std::execution` space: [P4003R0](https://wg21.link/p4003r0), [P4007R0](https://wg21.link/p4007r0), and [P4100R0](https://wg21.link/p4100r0). The author's first attended WG21 meeting was in 2018. The institutional-theory literature presented here applies to every consensus body, including bodies whose decisions the author agrees with.

The author asks for nothing.

---

## 2. Executive Summary

Two procedural documents govern WG21. The ISO/IEC Directives create a multi-principal oversight system - a constitutional republic of sovereign National Bodies with separated powers, fixed terms, formal appeals, forced feedback loops, and transparency obligations. SD-4 replaces this with a single-principal delegation model: unilateral chair appointments with no terms, a by-invitation Direction Group controlling scheduling priorities without committee authorization, consensus determined by the chair alone using a 2:1 threshold absent from the Directives, meeting records sealed from public quotation, and no retrospective mechanism to evaluate whether shipped features achieved their claimed benefits.

The gap between these two systems is the structural explanation for what the committee has become. The ISO system was designed to prevent the concentration of procedural power in a self-replicating appointment chain. SD-4 dismantled every prevention mechanism. What grew in the space SD-4 created is a peerage - a system of rank in which titles confer authority independent of technical contribution, patronage determines advancement, and social trust substitutes for independent evaluation. The peerage was not designed. It was the predictable institutional outcome of removing structural safeguards in a body where the median delegate is rationally ignorant about 90% of the polls they vote on, and where consensus-as-silence converts that rational ignorance into procedural legitimacy.

The institutional prognosis requires a three-layer distinction. The technical tradition is living: the committee ships world-class features, implementers carry genuine expertise, four consecutive on-time releases demonstrate real engineering capacity. The governance tradition is dead: participants follow SD-4 without knowing the Directives, perform consensus ceremonies without the structural safeguards that give consensus meaning. The direction-setting process exhibits cargo cult properties: the committee performs the ceremony of shipping a language feature (coroutines, C++20) and the ceremony of advancing a library framework (senders, C++26), but never performs the engineering act of asking whether the two are compatible. The process measures ceremonies completed, not outcomes achieved.

---

## 3. Analytical Framework

### 3.1 Game-Theoretic Foundations

The analysis identifies players, payoff functions, dominant strategies, and equilibria for each of eight player classes under both rule sets. It assumes purposeful action (Mises 1949) - each player acts to remove their most pressing uneasiness given what they know - rather than classical rationality. The WG21 game is sequential within meetings, simultaneous across six parallel tracks, repeated indefinitely since 1990, and played under incomplete information (papers public; reflector discussions, scheduling rationales, and subgroup votes sealed).

Every analytical claim is accompanied by an observability statement - what the reader should look for in WG21's published record to confirm or disconfirm the stated effect. Claims that cannot be connected to observable evidence are not made. Specifically, the following conditions would disconfirm the central claims:

- If process-reform papers that constrain chair discretion survive at the same rate as papers that reduce chair burden, the "immune system" claim is wrong.
- If the next convener restructures the appointment chain without external pressure, the "self-replicating" claim is wrong.
- If Direction Group-endorsed priorities ship at the same rate as non-endorsed items, "advisory without accountability" is wrong.
- If competing proposals receive scheduling priority comparable to incumbents, the "bird-in-hand" claim is wrong.

### 3.2 Institutional Forces

Six academic forces act on consensus-driven institutions. Each names a mechanism and predicts an observable effect tested against WG21's published record (P4171R0, Falco 2026).

1. **Goal Displacement** (Merton 1940): procedures become more important than their objective. WG21 has no requirement on implementation experience to adopt a proposal (P2274R0).
2. **Professional Socialization** (Lave & Wenger 1991): newcomers internalize community norms. Implementer feedback is "often introduced late, treated as adversarial" (P3962R0).
3. **Representational Capture** (Stigler 1971): entities that participate most consistently shape output. Five companies hold the majority of chair positions across EWG, LEWG, CWG, and LWG.
4. **The Iron Law** (Michels 1911, Pournelle 2006): procedural skill predicts advancement more reliably than deployment evidence.
5. **Shifting Baseline Syndrome** (Pauly 1995): each generation accepts current conditions as normal. Twenty-one-year networking/executor timeline described internally as a consequence of the problem's difficulty.
6. **Going Native** (Checkel 2003): sustained engagement produces genuine preference change. Profiles endorsed unanimously by the Direction Group, voted 47-2, reaffirmed by six senior members in P3970R0 - and not in C++26.

### 3.3 Praxeological Principles

Ten principles from Mises' *Human Action* (1949) provide the economic foundations. The essential ones for this analysis:

- **Uncertainty is built into action (#1).** Every committee vote is speculative; delegates rely on heuristics.
- **Methodological individualism (#2).** Groups do not act. Specific individuals vote, schedule, and determine consensus.
- **Division of cognitive labor (#3).** The median delegate contributes deeply in their own domain and is rationally ignorant about the rest. This is specialization, not moral failure.
- **Effort at the margin (#4).** When marginal cost of engagement exceeds marginal benefit, rational disengagement follows on that issue.
- **Practical ignorance permits purposeful choice (#5).** Delegates acting on coarse information are still acting purposefully. Each vote is a genuine choice, not random noise.
- **Coordination control is outcome control (#6).** Whoever controls scheduling, poll framing, and consensus determination controls outcomes without needing to do the thinking. The pattern is publicly documented: David Abrahams (Boost mailing list, 2006) reported that a proposal he submitted in 2002 had received no serious consideration while a competing proposal had been scheduled in the evolution working group at least three times; Peter Dimov (Boost mailing list, 2024) identified the structural gatekeeping created by the LEWG chair position. Both are committee members speaking on a public list -- the only quotable record, because WG21's own reflectors are sealed.
- **Rules substitute for discretion where feedback is absent (#7).** The ISO Directives are exactly this substitution. SD-4 reverses it - removes the rules, restores discretion. The Misesian prediction: discretion without feedback will be exercised to minimize the officer's personal cost.

### 3.4 Great Founder Theory Diagnostic Tests

Five tests from Samo Burja's GFT separate functional institutions from institutions that merely imitate them: **Live Player** (can the institution do something it has never done?), **Social Technology** (living tradition vs. dead tradition), **Power Source** (owned vs. borrowed), **Functionality** (produces what it claims?), **Imitation Distance** (how many copies from the original?). Applied symmetrically to both systems in Section 6.

### 3.5 Committee Decision-Making Literature

The empirical backbone draws on four strands of literature.

**Decision-making structure under uncertainty:** Bikhchandani et al. (1992, informational cascades); Banerjee (1992, herd behavior); Newham & Midjord (2019, FDA expert herding under sequential voting, which led the FDA to switch to simultaneous voting); Lorenz et al. (2011, social influence reduces diversity without increasing accuracy); Feddersen & Pesendorfer (1998, unanimity rules can produce worse error rates); Visser & Swank (2007, reputational concerns push toward visible unity); Karotkin & Paroush (2003, optimal committee size).

**Public versus secret voting in committees:** Levy (2007, foundational model showing career-concerned committee members vote differently under observability -- secrecy amplifies conservative bias, transparency removes it, and the net effect on decision quality depends on the voting rule); Mattozzi & Nakaguma (2023, public-vs-secret voting in committees; documents the 2017 Italian Parliament natural experiment in which a malfunction briefly revealed individual votes during a secret ballot and 15% of members switched within 8 seconds, and the 2013 Brazil expulsion-procedure change in which public voting nearly doubled votes in favor); Name-Correa & Yildirim (2019, formal model of the blame-fear / audience-cost mechanism); Funk (2010, Swiss mail-ballot natural experiment showing social-pressure effects strongest in small communities of known associates).

**Social cost of visible dissent:** Schachter (1951, foundational experiments on group punishment of deviants -- reduced communication, lowest likability ratings, menial-task assignment); Marques, Yzerbyt & Leyens (1988, Black Sheep Effect: ingroup dissenters are judged more harshly than outsiders with the same views); Asch (1956, 36.8% conform to a clearly-wrong unanimous majority under social pressure); Janis (1972/1982, Groupthink symptoms: self-censorship, direct pressure on dissenters, illusion of unanimity); Noelle-Neumann (1993, spiral of silence: fear of isolation suppresses minority-view expression); Matthes, Knoll & von Sikorski (2018, meta-analysis finding the strongest silencing effect (r=.34) in face-to-face groups of known associates); Braghieri, Bursztyn & Fasnacht (2026, public voting nearly doubles abstention on stigmatized positions).

**Aggregation, agenda, and access:** Downs (1957, rational ignorance); Barbera et al. (1993, median voter is structurally decisive); Romer & Rosenthal (1978, monopoly agenda-setters extract concessions); Olson (1965, collective action failure); Hirschman (1970, exit/voice/loyalty); Arrow (1951, no ranked system satisfies all fairness criteria).

---

## 4. About SD-4

SD-4 creates a governance system with five compounding effects, each individually defensible, each structurally consequential, and none visible from any single rule:

**All power flows from a single appointment chain.** The Convener appoints subgroup chairs with no elections, no fixed terms, and no National Body confirmation. The chairs control scheduling, framing, and consensus determination. A by-invitation Direction Group maintains the priority list that drives chair scheduling. Every structural filter traces back to the Convener. The chain reproduces its own composition because existing gatekeepers select the next gatekeepers (Michels 1911).

**The consensus definition is the load-bearing flaw.** SD-4 quotes the ISO consensus definition but applies it in a system where the vast majority of voters have no informed opinion on any given poll. The committee generates 300-500 papers per year; the median delegate reads 20-40. On approximately 90% of plenary polls, the median delegate is rationally ignorant (Downs 1957). SD-4's consensus mechanism counts this knowledge deficit as agreement. Even informed delegates face systematic conformity pressure under show-of-hands voting: the 2017 Italian Parliament natural experiment is the cleanest demonstration -- during a secret ballot, a technical malfunction briefly displayed individual votes on a large screen; within 8 seconds at least 62 members (15% of those voting) switched (Mattozzi & Nakaguma 2023). Brazil's 2013 switch from secret to public voting on congressional expulsions nearly doubled votes in favor, in the predictable direction when the person being voted on can see the dissenter. The FDA observed the same dynamic in expert advisory committees and switched to simultaneous voting (Newham & Midjord 2019). Levy (2007) provides the theoretical mechanism: career-concerned committee members vote differently when individual votes are observable. Levy's model shows that secrecy amplifies conservative bias while transparency removes it; the relevant insight for WG21 is that observability changes voting behavior regardless of direction. SD-4's consensus mechanism therefore operates under both the bandwidth gap and the conformity gap.

**The rules create a consensus ratchet.** Once a chair declares consensus, reversing it is procedurally nearly impossible. SD-4 says the minority must "accept group decisions" and attributes this to the ISO Code of Conduct. The phrase does not appear in the ISO Code of Ethics and Conduct (PUB100011, March 2023); it appears only on a JTC 1 presentation slide. The actual Code says "we accept and respect *consensus* decisions" -- a narrower obligation paired with explicit appeal and escalation rights. SD-4 drops the word "consensus," broadens the obligation, and severs it from the rights the Code pairs it with, then uses the broadened version to characterize minority positions as Code violations. Ballot comments that revisit past decisions are "not appropriate." Repeated escalation "erodes credibility." The bird-in-hand rule gives structural priority to first-movers. Each rule is individually reasonable. Together they create a one-way valve.

**There is no feedback loop.** No procedure exists for asking "did this feature achieve its claimed benefits?" A search of the entire WG21 paper corpus (1.4 million indexed records) returns zero papers proposing retrospectives, post-adoption evaluation, or outcome measurement for shipped features. The mailing list archives similarly contain no evidence of systematic outcome tracking. The committee measures process completion but never measures outcome quality. The compounding errors are never self-correcting (Mises #7). The coroutines arc illustrates the gap: P0975R0 (2018) called task-type library support "minimal" for a "great out of the box experience"; P2247 (2020) sounded the alarm that this plenary-approved priority was stalling; P3552 (2025) found that P2506's scheduled LEWG discussion left no discussion notes. Seven years later the "minimal" support still hasn't shipped, and no retrospective was conducted.

**The transparency regime prevents external accountability.** Meeting records cannot be quoted publicly. This is anomalous: WG14, WG5, and WG9 publish their minutes; TC39 publishes verbatim transcripts; the IETF publishes recordings. The ISO Directives themselves (Clause SF.10, 2024 edition) provide a consent-based framework for meeting recordings, and JTC 1 Standing Document 19 (2022), Section 9 explicitly adopts that framework by reference: "JTC 1 follows the ISO policy on recording technical meetings which are included in the Consolidated ISO Supplement, Annex SF Clause 10." ISO published guidance in 2025 explicitly permitting AI transcription under this framework. WG21's information seal operates outside not only the ISO framework but the framework JTC 1 has explicitly adopted -- it is an SD-4 invention, not an inherited ISO norm.

---

## 5. Per-Player Analysis

Each entry below presents the SD-4 dominant strategy and the ISO counterfactual. The same players adapt differently under different rules.

### 5.1 The Convener

**Under SD-4:** Preserve the appointment chain. Avoid controversy. Unilateral appointment power with no committee vote, no term limit, no NB confirmation means the selection criterion is institutional alignment, not technical contribution (Michels 1911, Mises #7). The convenership was held by a single occupant for more than two decades. The structural relationships survived the 2026 transition intact.

**Under ISO:** The convener implements TMB policy (1.8.2h). Chairs serve 3-year terms requiring committee reappointment (1.12.1). The incentive shifts from loyalty-based selection to merit-based selection because the committee evaluates performance at reappointment.

### 5.2 The Direction Group

**Under SD-4:** Maintain priority-setting influence without accountability. The DG controls the coordination mechanism (Mises #6) without writing papers, building implementations, or answering to the committee. On a strict textual reading of the Directives, the DG's priority-setting function maps to a power reserved to the TMB (Directive 1.1f), and its formation does not comply with Directive 1.13.2. Decades of TMB and SC22 non-objection constitute a practice-based counterargument - tacit acceptance or institutional tolerance. Whether this textual non-compliance has practical significance remains untested precisely because no superior body has challenged it. The DG has no terms of reference, no committee-approved membership, no sunset clause, and no reporting obligation.

**Under ISO:** The DG would not exist in its current form. Advisory groups require committee approval of convenor, membership, and terms of reference (1.13.2), must be disbanded when tasks are complete (1.13.6), and produce recommendations only (1.13.3).

### 5.3 Subgroup Chairs

**Under SD-4:** Maximize throughput. Minimize conflict. Deprioritize difficult work. SD-4 grants unconstrained discretion over scheduling, time-boxing, poll ordering, and consensus determination with no fixed terms and no ex-post review (Mises #7, Romer & Rosenthal 1978). The chair roster maps directly to employer names: NVIDIA holds the EWG chair and DG rotating chair simultaneously; Microsoft holds LEWG; IBM holds CWG vice-chair and LWG chair (Stigler 1971). The institutional immune system operates through chairs: reforms that address chair pain points succeed (P2138R4 progressed through 5 revisions in ~1 year and was adopted, shifting burden from chairs to design groups); reforms that constrain chair discretion die in the scheduling queue. A search of the entire WG21 paper corpus (1.4 million indexed records) returns zero papers proposing term limits for subgroup chairs, election of chairs, scheduling transparency requirements, or chair accountability mechanisms. The absence is itself data: the immune system operates not by rejecting reforms but by ensuring they are never proposed. P2138R4 is a partial counterexample -- the system can adopt process reforms when they align with chair incentives. The narrower claim is that reforms against chair incentives face structural headwinds, and the test is the differential survival rate.

**Under ISO:** Three-year terms (1.12.1), NB confirmation, consensus judged in consultation with secretary (2.5.6), all views must be summed up (1.8.2d). The immune system is checked by the periodic accountability moment.

### 5.4 National Bodies

**Under SD-4:** Ratify rather than challenge. NB delegates make "good enough" judgments from coarse signals filtered through the information seal (Mises #5, #9). SD-4 declares two categories of ballot comments "not appropriate" and redefines the "No" vote as a kill vote for the entire project, compressing the ballot to a near-binary choice.

**Under ISO:** NBs become active principals. NB confirmation of chair appointments (1.12.1) creates a structural check. Unrestricted ballot comments (2.6.2), all comments must be addressed (2.6.5), and appeal rights at three levels (5.1) provide a credible outside option.

### 5.5 Corporate Delegations

**Under SD-4:** Staff chair positions. Send consistent delegations. Establish bird-in-hand priority. The gains are concentrated (employer product roadmap, competitive positioning), so heavy investment is individually rational (Mises #9 inverted, Stigler 1971).

**Under ISO:** Corporate participants still dominate through expertise and travel capacity. But chair positions are subject to committee-level accountability at reappointment. The NB intermediary is re-inserted into the appointment chain.

### 5.6 Paper Authors

**Under SD-4 (Incumbent):** Accumulate procedural momentum. After years of revision, marginal cost of abandonment exceeds marginal cost of continuing (Mises #4). The revision count becomes a proxy for quality (Merton 1940). The follow-up paper exception lets the incumbent revise in real time while the challenger waits.

**Under SD-4 (Challenger):** Start extremely early or do not challenge at all. Every procedural force works against late entry: one-meeting delay window, leftover scheduling time, bird-in-hand disadvantage (Mises #4).

**Under ISO:** Authors invest in addressing minority concerns because unresolved opposition retains institutional standing and appeal rights (2.5.6). Challengers get a fair hearing - the Directives contain no first-mover doctrine.

### 5.7 The Uncommitted Middle

**Under SD-4:** Vote with the room. Minimize personal exposure. Three Mises principles converge: uncertainty (#1) makes heuristics dominate; division of labor (#3) makes the bandwidth gap structural; marginal effort (#4) makes full engagement irrational. Bikhchandani et al. (1992) describe informational cascades; Barbera et al. (1993) proved the median voter is structurally decisive. WG21 uses sequential hand-raising, and the conformity literature quantifies the effect across multiple settings. The 2017 Italian Parliament incident provides the cleanest natural experiment: during a secret ballot, a technical malfunction briefly displayed individual votes on a large screen; within 8 seconds at least 62 members (15% of those voting) switched (Mattozzi & Nakaguma 2023). Brazil's 2013 switch from secret to public voting on congressional expulsions nearly doubled votes in favor -- the predictable direction when the person being voted on can see the dissenter. Schachter (1951) documents the mechanism: visible dissenters receive reduced communication, lowest likability ratings, and assignment of menial tasks. The Black Sheep Effect (Marques et al. 1988) predicts ingroup dissenters are judged more harshly than outsiders with the same views -- directly applicable to WG21's repeated-interaction structure. Funk (2010) shows the effect is strongest in small communities where members know each other and continue interacting. Janis (1972/1982) catalogs the symptoms in cohesive decision-making groups: self-censorship, direct pressure on dissenters, illusion of unanimity. Matthes et al. (2018) meta-analysis found the strongest silencing effect (r=.34) in face-to-face groups of known associates -- precisely WG21's conditions. The FDA observed the same dynamic with sequential expert voting and switched to simultaneous voting (Newham & Midjord 2019). SA is the most stigmatized position in WG21's five-way poll, and the convergent prediction across this literature is that it is systematically underrepresented in show-of-hands counts. SD-4's consensus-as-silence converts the resulting default mild agreement into procedural legitimacy.

Each individual vote is purposeful (Mises #5) - the delegate applied a heuristic and chose. The critique is not that individual votes are random. It is that the consensus label misrepresents what purposeful-but-coarse votes aggregate into. The aggregation mechanism stamps "consensus" on a collection of individually purposeful choices, implying informed collective agreement that the inputs do not support.

**Under ISO:** The voter pool shifts from "each person in the room" to NB-appointed registered experts (1.12.1). The bandwidth gap still exists, but the evaluation pool is curated by NBs rather than self-selected by attendance.

A documented case from a comparable standards body corroborates the structural concern. In 2024-2025, cryptographer Daniel J. Bernstein filed formal appeals to the IETF Internet Engineering Steering Group alleging that TLS Working Group chairs censored technical objections during "last call" periods by delaying dissenting messages, reducing their impact (Bernstein 2025). Bernstein's appeal documented that participants worried "speaking up will result in retaliation by the WG chairs." The IETF's appeals mechanism exists precisely so this concern can be tested in a process visible to the broader community via a public datatracker. SD-4 contains no comparable mechanism: dissent suppression, if it occurred, would not surface on a public datatracker because there is no public datatracker.

### 5.8 The C++ Public

**Under SD-4:** Voice (Reddit, blogs, conference talks) transitioning to exit. Five million developers cannot vote, cannot submit papers, and experience the committee's output as accomplished facts in compiler release notes. The public-good structure means individual engagement cost exceeds individual benefit (Olson 1965).

The Hirschman (1970) exit trajectory is visible in two distinct layers that should not be conflated. The first is memory-safety exit, driven by a genuine technical gap in C++ that exists regardless of WG21's governance structure:

- Microsoft announced a dedicated team building AI-powered tools to migrate C/C++ to Rust at scale, targeting 2030, with 36K lines of Windows kernel and 152K lines of DirectWrite already rewritten.
- Google Android documented 1000x reduction in memory safety vulnerability density with Rust vs. C++. Chrome policy: handling untrustworthy data in C++ violates security requirements for privileged processes.

These are evidence of technical pressure on C++, not evidence of governance failure. C++ would face the same memory-safety pressure under any procedural regime.

The second layer is process exit -- where individuals or teams disengage because they believe the WG21 process will not produce what they need. This is the relevant evidence for the governance argument:

- Sean Baxter abandoned Safe C++ after WG21 rejected the Rust safety model in favor of Profiles: "The Rust safety model is unpopular with the committee. Further work on my end won't change that."
- Modules shipped in C++20 on a trajectory insiders describe as "borderline unimplementable," with critics "shot down by a group of higher-up people" (see Section 5.9 parallel cases).
- Implementers in P3962R0 document that features accumulate faster than they can implement; the natural response of repeated, sustained complaints from the implementation community is itself a process-exit signal.

The information seal prevents the public from seeing the structure. They correctly identify dysfunction but misattribute its causes to individual actors or corporate conspiracies because the structural understanding is sealed behind the information barriers the structure creates.

**Under ISO:** The information seal is broken. Decisions in writing during meetings (1.8.2e), posted within 48 hours (1.9.2c), electronic platform for transparency (1.12.6). The Hirschman trajectory shifts from exit back toward voice because voice has a verifiable target.

### 5.9 Case Study: Coroutines and Senders

The coroutines/senders arc demonstrates all four SD-4 mechanisms operating on a single technical trajectory - the open-loop failure at its most damaging.

The committee shipped coroutines in C++20. The natural next step - exploring what a coroutine-native asynchronous programming model looks like, what library support it needs, how it composes, what a standard task type built around coroutine primitives would be - was never taken. Instead, the committee invested four years and enormous bandwidth into P2300, a sender/receiver framework designed around a different computational model that treats coroutines as a thing you plug in at the edges rather than the foundation you build on.

**Bird-in-hand:** P2300 had a paper, authors, revisions, and directional consensus from the October 2021 polls. A coroutine-native async model had no paper with comparable institutional momentum. Under SD-4, the concrete proposal advances; the hypothetical alternative "does not exist."

**Consensus ratchet:** The October 2021 poll ("sender/receiver is a good basis for most asynchronous use cases" - SF:24/WF:16/N:3/WA:6/SA:3) locked direction before the alternative was explored. P4129R1 Exhibit N documents that five years later, no sender-based networking shipped, but the directional poll remained the stated direction.

**Scheduling funnel:** P2300 was a Direction Group priority. It consumed LEWG bandwidth across multiple cycles. A coroutine-native alternative competed for whatever time remained. If no time remained, it was never heard. Nobody rejected it. It simply never arrived.

**Bandwidth gap:** The October 2021 poll had 52 voters deciding whether sender/receiver was the right async basis when the alternative - the language feature just shipped in C++20 - had never been prototyped as a complete framework within the committee process. The room voted on a question it lacked the information to answer.

What users got: std::execution::task with 16+ known issues cataloged by its own designer (P3796R1), including stack overflow from iterative co_await, broken RAII guarantees, and dangling references (P3801R0) - shipped known-flawed under time pressure. std::generator still missing from libc++ as of mid-2026, five years after C++20 coroutines. A P2300 co-author acknowledging the framework is "challenging to work with and difficult to fully understand" and "as voted is incomplete." Four structural gaps when senders meet coroutines (P4007R0) characterized as inherent design trade-offs, not fixable defects.

The loop was never closed because it was never opened. No retrospective asked: "we shipped coroutines three years ago - did we build the library support that makes them useful?"

### Parallel Cases: Modules and Contracts

The same four SD-4 mechanisms appear in two other recent trajectories, without the author conflict that colors the senders example.

**Modules (C++20):** Shipped in C++20 with zero practical tooling. Jussi Pakkanen (Meson author, 2025): "There were no implementations, no test code, no prototypes, nothing." An insider reported that "there were people who knew about the implementation difficulty and were quite vocal that modules as specified are borderline unimplementable. They were shot down by a group of higher-up people." CMake module support remains incomplete in 2026 (Ropert 2026); Visual Studio IntelliSense is still flagged as "experimental" seven years after Microsoft pushed for standardization. The loop was never closed: no retrospective asked whether modules achieved the build-time improvements they promised.

**Contracts (C++26):** Adopted into the C++26 Working Draft at Hagenberg (Feb 2025). Twenty-plus NB comments from 19 of 26 national bodies followed (O'Dwyer 2025). Spain, the US, France, and Finland requested complete removal; Romania requested removal conditional on redesign of the "ignore" semantic. P4005R0 (guaranteed enforcement) was rejected by EWG (14 SA). P4043R0 questioned readiness. The final DIS vote was non-unanimous. The consensus ratchet operated as predicted: directional consensus was declared, and NBs who object are told their comments are "not appropriate" or "out of harmony with the ISO Code of Conduct."

Both exhibit the same pattern as senders -- bird-in-hand, consensus ratchet, scheduling funnel, no feedback loop -- without the author conflict that colors the coroutines example.

---

## 6. The Gap

The ISO system provides seven structural properties that serve as countermeasures to the forces identified in Section 3: distributed authority (no single person holds appointment, scheduling, priority-setting, and consensus-determination simultaneously), fixed terms as accountability moments (3-year terms with committee reappointment, 1.12.1), consensus as negotiated outcome (requiring reconciliation of conflicting arguments, 2.5.6), the appeal chain as credible outside option (three levels, 5.1), NB sovereignty (inherent rights not narrowable by committee-level documents), forced feedback loops (comments must be addressed, negative votes resolved, projects cancelled after 5 years, 2.5.3/2.6.5/2.1.6), and no punishment for objection (objectors directed to appeals, 2.5.6).

SD-4 removes every countermeasure:

| Peerage Property | ISO Countermeasure | SD-4 Removes It |
|---|---|---|
| Titles confer authority independent of contribution | Fixed terms force periodic re-earning (1.12.1) | "No fixed term" |
| Patronage determines advancement | Committee appoints, NB confirms (1.12.1) | Convener appoints alone |
| Social trust substitutes for evaluation | Chair must sum up all views (1.8.2d); consensus in consultation (2.5.6) | Chair determines alone; 2:1 threshold |
| Objection is penalized | No penalty; objectors directed to appeals (2.5.6) | "Erodes credibility" |
| The room reads the person, not the paper | Decisions in writing, posted within 48 hours (1.8.2e, 1.9.2c) | Meeting records sealed |
| Priority follows patronage | TMB allocates priorities (1.1f) | Direction Group (by-invitation) |
| System cannot distinguish consensus from compliance | Forced feedback: comments addressed, negative votes resolved (2.5.3, 2.6.5) | No retrospective; revisiting decisions "inappropriate" |

### GFT Prognosis

**ISO - Live Player:** The question is not "does the system produce novel technical output?" - both systems do; modules, concepts, and ranges are genuine technical novelties. The question is "can the system do something it has never done *in governance*?" The answer for ISO in WG21 specifically is untested but structurally enabled: the appeal chain (5.1) provides an adaptation mechanism independent of the officers being challenged; the fixed-term reappointment moment (1.12.1) provides a periodic governance-adaptation opportunity; the multi-principal structure means governance novelty can originate from any NB, not only from the officers being challenged. This is structural capacity, not demonstrated behavior in WG21. **Social Technology:** Living tradition - the Foreword explicitly states the six WTO principles the rules exist to safeguard. **Power Source:** Mixed correctly - NB sovereignty is owned (inherent in P-member status), officer authority is borrowed (revocable at reappointment). **Functionality:** Functional - the system produces what it claims. **Imitation Distance:** First generation - the Directives are the original.

**SD-4 - Live Player:** Tested in governance, and the answer is no. The system has never adopted a governance reform against officer incentives. P2138R4 - the only process reform found - aligned with chair incentives; zero papers constraining chair discretion exist in the entire WG21 corpus. The relevant test is whether the system can adapt its own governance in response to novel conditions (e.g., the NB ballot revolt on contracts). Current evidence: it has not. Three Profiles endorsements, zero structural change. **Social Technology:** The technical social technology is living - implementers and domain experts carry genuine expertise, and the committee ships real features. The governance social technology is dead tradition: participants follow SD-4 without understanding that it deviates from the Directives; the consensus mechanism performs the ceremony of agreement without producing the substance of negotiated consent. The direction-setting process is where the diagnosis lands hardest: the committee shipped coroutines (C++20) and then invested six years into a library framework built on a different computational model without ever asking whether they compose (Section 5.9). The process measures ceremonies completed, not engineering outcomes achieved. **Power Source:** Structurally contradictory - chair authority under SD-4 is owned power (no term, no review), but the legitimacy that makes WG21's output an ISO standard is borrowed from the ISO framework. Metastable: persists as long as no one tests the borrowed component. **Functionality:** Technically productive (ships standards, on-time, high quality) and governance-non-functional: the consensus mechanism does not produce the informed collective agreement it claims. Each individual vote is purposeful (Mises #5), but the aggregation mechanism stamps "consensus" on a collection of purposeful-but-coarse choices, implying informed agreement the inputs do not support. The dysfunction surfaces downstream: in NB comments, in implementer complaints (P3962R0), in the coroutines/senders open-loop failure, and in the Hirschman exit that Microsoft's 2030 Rust migration and Google's Chrome policy represent. **Imitation Distance:** Third-generation copy. SD-4 quotes the ISO consensus definition while replacing every structural safeguard the definition was designed to operate within.

---

## 7. References

1. ISO/IEC. "ISO/IEC Directives, Part 1 - Consolidated JTC 1 Supplement." 2023.
2. ISO/IEC. "ISO/IEC Directives, Part 1 - Consolidated ISO Supplement." Edition 2024.
3. Davidson, G. "SD-4: WG21 Practices and Procedures." ISO/IEC JTC1/SC22/WG21/SD-4, 2026-05-11. (SD-4 provisions quoted in this paper predate the current convenor and were authored and maintained by Herb Sutter during his tenure as convenor through 2025.)
4. Ballman, A. P2274R0. 2020.
5. Ranns, N. et al. P3962R0. 2026.
6. Voutilainen, V. P2138R4. 2021.
7. Dominiak, M. et al. P2300R10. 2024.
8. Vandevoorde, D. et al. P3970R0. 2026.
9. Kühl, D. P3796R1. 2025.
10. Lewis Baker. P3801R0. 2025.
11. Falco, V. P4007R0. 2025.
12. Falco, V. P4129R1. 2025.
13. Falco, V. P4171R0. 2026.
14. Merton, R.K. "Bureaucratic Structure and Personality." *Social Forces* 18(4). 1940.
15. Lave, J. & Wenger, E. *Situated Learning*. Cambridge UP. 1991.
16. Stigler, G. "The Theory of Economic Regulation." *Bell J. Econ.* 2(1). 1971.
17. Michels, R. *Political Parties*. 1911.
18. Pauly, D. "Shifting Baseline Syndrome." *Trends Ecol. Evol.* 10(10). 1995.
19. Checkel, J.T. "'Going Native' in Europe?" *Comp. Pol. Stud.* 36(1-2). 2003.
20. Mises, L. von. *Human Action*. 1949.
21. Bikhchandani, S. et al. "Informational Cascades." *J. Pol. Econ.* 1992.
22. Newham, M. & Midjord, R. "Do Expert Panelists Herd? Evidence from FDA Committees." DIW Discussion Papers, No. 1825, 2019.
23. Lorenz, J. et al. "Social influence undermines wisdom of crowds." *PNAS*. 2011.
24. Feddersen, T. & Pesendorfer, W. "Convicting the Innocent." *APSR* 92(1). 1998.
25. Visser, B. & Swank, O.H. "On Committees of Experts." *QJE* 122(1). 2007.
26. Downs, A. *An Economic Theory of Democracy*. 1957.
27. Barbera, S. et al. "Generalized Median Voter Schemes." *J. Econ. Theory*. 1993.
28. Romer, T. & Rosenthal, H. "Controlled Agendas." *Public Choice*. 1978.
29. Olson, M. *The Logic of Collective Action*. 1965.
30. Hirschman, A.O. *Exit, Voice, and Loyalty*. 1970.
31. Arrow, K.J. *Social Choice and Individual Values*. 1951.
32. Burja, S. *Great Founder Theory*.
33. Teodorescu, L.R. "Senders/Receivers in C++." lucteo.ro. 2024.
34. Levy, G. "Decision Making in Committees: Transparency, Reputation, and Voting Rules." *American Economic Review* 97(1), 2007.
35. Mattozzi, A. & Nakaguma, M.Y. "Public versus Secret Voting in Committees." *Journal of the European Economic Association* 21(3), 2023. (Documents the 2017 Italian Parliament incident and the 2013 Brazil expulsion-procedure change.)
36. Name-Correa, A.J. & Yildirim, H. "Social Pressure, Transparency, and Voting in Committees." *Journal of Economic Theory* 184, 2019.
37. Funk, P. "Social Incentives and Voter Turnout: Evidence from the Swiss Mail Ballot System." *Journal of the European Economic Association* 8(5), 2010.
38. Schachter, S. "Deviation, Rejection, and Communication." *Journal of Abnormal and Social Psychology* 46(2), 1951, pp. 190-207.
39. Marques, J.M., Yzerbyt, V.Y. & Leyens, J.-P. "The 'Black Sheep Effect': Extremity of Judgments towards Ingroup Members as a Function of Group Identification." *European Journal of Social Psychology* 18(1), 1988.
40. Janis, I.L. *Victims of Groupthink*. Houghton Mifflin, 1972; revised as *Groupthink: Psychological Studies of Policy Decisions and Fiascoes*, 1982.
41. Noelle-Neumann, E. *The Spiral of Silence: Public Opinion -- Our Social Skin*. University of Chicago Press, 1993.
42. Matthes, J., Knoll, J. & von Sikorski, C. "The 'Spiral of Silence' Revisited: A Meta-Analysis on the Relationship Between Perceptions of Opinion Support and Political Opinion Expression." *Communication Research* 45(1), 2018.
43. Braghieri, L., Bursztyn, L. & Fasnacht, J. "Threshold Disclosure in Collective Decisions." NBER Working Paper 34827, 2026.
44. Asch, S.E. "Studies of Independence and Conformity: I. A Minority of One Against a Unanimous Majority." *Psychological Monographs: General and Applied* 70(9), 1956.
45. Banerjee, A. "A Simple Model of Herd Behavior." *Quarterly Journal of Economics* 107(3), 1992.
46. Bernstein, D.J. "Appeal v2 -- Complaint to IESG regarding censorship of dissent." IETF IESG Appeals, 2025. [https://datatracker.ietf.org/group/iesg/appeals/artifact/226](https://datatracker.ietf.org/group/iesg/appeals/artifact/226)
47. ISO. "Code of Ethics and Conduct." PUB100011, First Edition, March 2023.
48. JTC 1. Standing Document 19, "Meetings," 2022, Section 9 "Recording of meetings."
49. Pakkanen, J. "We need to seriously think about what to do with C++ modules." Nibble Stew, 2025.
50. Ropert, M. "Can we finally use C++ Modules in 2026?" 2026.
51. O'Dwyer, A. "The C++26 NB comments have arrived." 2025.
52. Adelstein Lelbach, B. P2247R1. "2020 Library Evolution Report." 2020.
53. Karotkin, D. & Paroush, J. "Optimum Committee Size: Quality-versus-Quantity Dilemma." *Social Choice and Welfare* 20(3), 2003.
