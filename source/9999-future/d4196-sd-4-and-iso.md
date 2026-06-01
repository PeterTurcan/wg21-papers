---
title: "Discrepancies Between SD-4 and the ISO Directives"
document: P4196R0
date: 2026-04-19
intent: info
audience: WG21
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

WG21 has two procedural documents. One is binding. The other is followed.

SD-4<sup>[1]</sup> governs the day-to-day operation of WG21 - subgroup chair appointments, consensus thresholds, escalation procedures, ballot comment handling, and work prioritization. The ISO/IEC Directives Part 1<sup>[2]</sup> govern the same topics for all JTC 1 working groups. This paper places the two documents side by side on twelve points: seven where SD-4 deviates from or operates outside the Directives' framework, and five where SD-4 is silent on Directive provisions within its declared scope. SD-4 does not appear in any WG21 document list.

---

## Revision History

### R0: August 2026

- Initial version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

This paper takes no position on the technical quality of any feature, including Contracts. The analysis is procedural.

The author asks for nothing.

---

## 2. Two Documents

WG21 participants follow SD-4<sup>[1]</sup>. SD-4 describes itself as the "How We Work Cheat Sheet" and states that "everyone who participates in WG21 is expected to be familiar with this information."

All JTC 1 working groups, including WG21, are bound by the ISO/IEC Directives Part 1<sup>[2]</sup><sup>[15]</sup>. The Directives are maintained by the ISO/IEC Joint Directives Maintenance Team and approved by the ISO Technical Management Board and IEC Standardization Management Board. The Directives exist to safeguard six WTO principles: Transparency, Openness, Impartiality and consensus, Effectiveness and relevance, Coherence, and Development dimension<sup>[15]</sup>. SD-4 describes itself as supplementing the Directives: it "summarizes some of WG21's current practices and procedures, in addition to the requirements of the ISO/IEC Directives and JTC 1 Supplement."

The Directives provide for this arrangement. The Foreword states that "additional documents may require referencing, such as Standing Documents (SD) for JTC 1 to complement the ISO/IEC Directives and the Consolidated JTC 1 Supplement"<sup>[15]</sup>. Other WG21 standing documents fit this description: SD-3 organizes study groups, SD-5 contains meeting information, SD-7 describes mailing procedures. Each complements the Directives with logistics and reference information consistent with them. SD-4 is the only standing document that interprets the ISO consensus definition, creates voting thresholds, restricts National Body ballot comments, establishes escalation deadlines, and penalizes repeated objection.

Both documents are publicly available. The comparison below is systematic.

**What the current system produces.** Four consecutive on-time releases from C++14 through C++23. Major compiler implementations tracking the standard within months of publication. A volunteer workforce that has produced modules, concepts, ranges, coroutines, `std::expected`, `std::print`, and `std::mdspan`. WG21's subgroup structure is an adaptation to a scale the Directives did not anticipate. The procedural deviations documented below purchased something - speed, decisiveness, simplified administration. The cost is measured in Directive compliance.

### 2.1 How ISO Defines a Subgroup

The Directives describe working groups as small, task-specific, and temporary. Directive 1.12.1<sup>[2]</sup> says a working group comprises "a restricted number of Experts individually appointed by the P-members," that it is "recommended that working groups be reasonably limited in size," and that the group is "brought together to deal with the specific task allocated to the working group." On completion of its tasks, the working group is disbanded.

Within this model, the Directives authorize working groups to subdivide. The full extent of what they say is:

> "Working Groups may establish subgroups."
>
> Directive 1.12.1<sup>[2]</sup>

That single sentence - with no appointment procedure, no term limits, no oversight requirements - is the entire Directive framework for subgroups.

WG21's siblings in SC 22 operate within this model:

| Working Group | Typical Attendance | Internal Subgroups |
|---|---|---|
| WG14 (C) | ~25 | Informal parallel breakouts during the week; all decisions in single plenary |
| WG5 (Fortran) | ~23 | None; delegates to US national body |
| WG21 (C++) | 200+ | 23 subgroups, multiple parallel tracks |

Appendix A extends this comparison across JTC 1. The only other JTC 1 working group that developed a comparable internal subgroup structure with permanent chairs was MPEG (SC 29/WG 11)<sup>[9]</sup>. MPEG grew to several hundred participants per meeting, with subgroups for Audio, Video, Systems, and other domains, each with appointed chairs. In 2020, SC 29 formally restructured MPEG, elevating its subgroups into proper SC-level working groups<sup>[10]</sup>. The restructuring acknowledged that a single working group had outgrown the ISO organizational model. WG21 has not undergone any such restructuring.

WG21's four main subgroups - CWG, LWG, EWG, LEWG - satisfy every functional criterion the Directives assign to a working group:

| Directive Working Group Criterion | WG21 Subgroups |
|---|---|
| Established for specific tasks (1.12.1: "working groups for specific tasks") | Yes - each has a defined technical domain |
| Operates by consensus (1.12.1: "A working group operates by consensus") | Yes - holds straw polls on every proposal |
| Reports to parent body through a leader (1.12.1: "reports and gives recommendations... through a Convenor") | Yes - chairs present to plenary and forward approved work |
| Leader sets agenda and runs meetings | Yes - SD-4: "Subgroup chairs prioritize... papers" |
| Comprises experts who do the technical work (1.12.1: "a restricted number of Experts") | Yes - though SD-4 allows "each person in the room" to vote |
| Processes assigned work items | Yes - every paper is assigned to subgroups |
| Standing body with continuous operation | Yes - CWG and LWG since the 1990s, EWG and LEWG for over a decade |

Every functional attribute the Directives assign to a working group is present in WG21's subgroups. Every governance requirement the Directives impose on a working group is absent.

| Directive Working Group Governance | WG21 Subgroups |
|---|---|
| Leader appointed by the committee (1.12.1) | No - appointed by the convener |
| Leader serves fixed terms of up to three years (1.12.1) | No - no fixed term |
| Leader confirmed by National Body (1.12.1) | No |

WG21's subgroups do not merely match the Directives' working group model. They exceed it:

- No language feature enters the working draft without passing through EWG (design) and CWG (wording). No library feature enters without passing through LEWG (design) and LWG (wording). These subgroups are mandatory gates, not optional reviewers.
- Subgroup chairs control which papers appear on the agenda and in what order.
- Subgroup chairs can request that authors revise and return. SD-4 provides no limit on how many times this can occur; advancement depends on the chair's judgment that "a general consensus of the design subgroup" has been achieved.
- A proposal that fails to gain subgroup consensus is effectively dead; plenary reversal is rare.

Bodies that satisfy every functional criterion of a working group, exceed working groups in gatekeeping authority, and operate on standing schedules across decades are working groups in all but name. The comparison in Section 3 proceeds on that basis.

---

## 3. What SD-4 Changes

Each entry below examines an SD-4 provision against the applicable Directive framework. The Directive clause numbers refer to the ISO/IEC Directives Part 1 - Consolidated JTC 1 Supplement 2024<sup>[2]</sup>. Where a provision originates in the Consolidated ISO Supplement rather than the JTC 1 Supplement, the reference is to [15].

### 3.1 Subgroup Chair Appointment

Directive 1.12.1<sup>[2]</sup> governs the appointment of working group convenors:

> "Working group Convenors shall be appointed by the committee for up to three-year terms. Such appointments shall be confirmed by the National Body (or liaison)."

The Directives prescribe no procedure for appointing leaders of subgroups within a working group. Section 2.1 establishes that WG21's subgroups satisfy every functional criterion of a Directive working group while exceeding them in gatekeeping authority. The nearest applicable Directive provision is 1.12.1.

SD-4<sup>[1]</sup> states:

> "Subgroup chairs are appointed by the convener, and are selected to match the current needs of the subgroup. They have no fixed term."

| Requirement | Directives (1.12.1) | SD-4 |
|-------------|-----------|------|
| Appointing authority | The committee | The Convener |
| Term length | Up to three years | No fixed term |
| NB confirmation | Required | Not mentioned |

### 3.2 Consensus Threshold

Directive 1.12.1<sup>[2]</sup> requires that working groups "operate by consensus." The Directives define consensus via ISO/IEC Guide 2:2004, quoted at Directive 2.5.6<sup>[2]</sup>:

> "General agreement, characterized by the absence of sustained opposition to substantial issues by any important part of the concerned interests and by a process that involves seeking to take into account the views of all parties concerned and to reconcile any conflicting arguments. NOTE Consensus need not imply unanimity."

SD-4<sup>[1]</sup> replaces this qualitative standard with a numeric threshold:

> "A proposal normally advances if there are more than twice as many in favor of a proposal as against, after discussion of the concerns of those voting against and possibly a re-poll to see if opinions have improved."

The "after discussion" clause reflects Guide 2's principle of seeking to take into account all views. But the numeric rule permits advancement over sustained opposition from up to a third of the room. Whether Guide 2's qualitative standard would treat that level of opposition as "sustained opposition to substantial issues by any important part of the concerned interests" is a question the text leaves to judgment. That judgment, however, was designed to operate alongside structural safeguards the Directives provide and SD-4 does not reproduce: participants individually appointed by National Bodies (1.12.1), formal dispute resolution (5.1.1, 5.1.2), and the requirement that the convenor "act in a purely international capacity" (1.12.1). SD-4 replaces the qualitative standard with a numeric threshold while removing the structural context in which that standard was meant to operate, and applies the result to a room whose composition is untethered from NB appointment.

The measurement instrument compounds the concern. WG21's practice for these polls is a show of hands — a visible, sequential expression of position. The academic literature documents that visible voting systematically suppresses opposition in committee settings. Asch's conformity experiments found 36.8% of participants conformed to a clearly wrong majority under social pressure<sup>[19]</sup>. In the Italian Parliament in 2017, a technical malfunction briefly revealed individual votes during a secret ballot; within eight seconds, at least 62 members (15% of those voting) switched their votes<sup>[22]</sup>. A 2019 structural-model study of FDA advisory committees, exploiting the FDA's 2007 switch from sequential to simultaneous voting as a natural experiment, found that roughly half of expert panelists would vote against their private assessment in response to earlier voters' positions<sup>[20]</sup>. The 2007 switch itself was prompted by the Institute of Medicine's 2006 report and the FDA Amendments Act, on the concern that sequential public voting could compromise the integrity of the result through momentum effects among later voters. The spiral-of-silence literature found the strongest silencing effect (r = .34) in face-to-face settings with known associates<sup>[21]</sup>. Beyond conformity, visible dissent carries social cost: Schachter's foundational experiments showed that group members who consistently disagreed with the majority received the lowest likability ratings, were assigned menial tasks, and in cohesive groups were ultimately marginalized within the group<sup>[23]</sup>. A 2:1 count taken by show of hands in a room where participants know each other and will continue working together is drawn from an instrument the literature identifies as systematically biased toward the majority position.

Section 2.1 establishes that WG21's subgroups function as working groups. If they are working groups, 1.12.1 requires them to operate by consensus as the Directives define it.

Separately, SD-4 allows "each person in the room" to vote in subgroup polls<sup>[1]</sup>. The Directives require working group participants to be "Experts individually appointed by the P-members" and registered in the ISO Global Directory (1.12.1, 1.12.2)<sup>[2]</sup>. SD-4 itself distinguishes these levels: plenary polls require ISO directory registration, but subgroup polls do not. The 2024 edition of the Directives<sup>[15]</sup> elevates voting principles to the main Part 1 text at 1.7.5: a simple majority of P-members voting is required for approval, proxy voting is not permitted, and formal discussion during ballot periods is prohibited. SD-4's subgroup polls operate outside this framework entirely.

### 3.3 Priority Allocation

SD-4<sup>[1]</sup> delegates work prioritization to a Direction Group:

> "The direction group is a small by-invitation group of experienced participants who are asked to recommend priorities for WG21."

> "The design group chairs use that list to prioritize work at meetings."

The Directives define three types of subsidiary body relevant here. Working groups (1.12)<sup>[2]</sup> are established by a committee for specific tasks - the Direction Group is not a working group. Groups having advisory functions within a committee (1.13)<sup>[2]</sup> may be "established by a committee to assist the Chair and secretariat in tasks concerning coordination, planning and steering of the committee's work" - this is the closest functional match, but 1.13 is available to committees (TCs/SCs), not to working groups. Ad hoc groups (1.14)<sup>[2]</sup> may be created by working groups in JTC 1, but require committee-approved convenors, terms of reference, and a target completion date - the Direction Group has none of these.

The Direction Group exercises a function the Directives assign to formal structures but is constituted as none of them. Its relationship to the Directives' organizational categories is unclear. Formalization under Directive 1.4<sup>[2]</sup> would remove the ambiguity.

### 3.4 Ballot Comment Scope

SD-4<sup>[1]</sup> declares two categories of NB ballot comments "not appropriate":

> "A ballot comment that requests adding an additional feature that is not already in the document is out of scope."

> "A ballot comment that requests a change that was already considered and decided otherwise at a WG21 meeting, and comes from a national body that was present at the meeting and had an opportunity to have their objections be heard and considered, is out of harmony with the ISO Code of Conduct's commitment to 'accept group decisions.'"

SD-4's provisions govern how a subgroup disposes of a comment, not whether an NB may submit it. NBs retain the right to submit any comment and to vote accordingly.

Directive 0.7(c)<sup>[2]</sup> is partially aligned in principle: it states that NBs have "the responsibility of ensuring that their technical standpoint... is made clear at an early stage of the work rather than, for example, at the final (approval) stage." SD-4's concern about re-litigating decided issues reflects this spirit.

What SD-4 adds is the normative label. The Directives place the responsibility for timely position-taking on the NB (0.7(c)). SD-4 places a characterization on the comment itself - "out of scope" and "out of harmony with the ISO Code of Conduct's commitment to 'accept group decisions.'" The Directives contain no provision authorizing a working group to pre-categorize NB ballot comments in these terms. "Out of harmony with the ISO Code of Conduct" is a serious characterization to attach to the exercise of a Directive right. (The attribution of "accept group decisions" to the ISO Code of Conduct is examined separately in §3.6.)

### 3.5 Escalation and Credibility

SD-4<sup>[1]</sup> states that escalation becomes inappropriate:

> "when a participant or national body regularly uses the escalation process to express a pattern of strong disagreement on topic after topic, which erodes their credibility."

The Directives contain no provision that penalizes repeated use of dispute resolution mechanisms.

SD-4 also imposes a deadline for raising objections. Serious concerns must be posted to committee email lists "no later than the deadline of 5pm the evening before the closing plenary session"<sup>[1]</sup>. SD-4 states:

> "Objections that are not so escalated, but are raised or re-raised in plenary, should not be given weight in plenary."

The Directives contain no comparable cutoff after which objections lose standing.

### 3.6 Code of Conduct Attribution

SD-4 invokes the ISO Code of Conduct to characterize participant behavior. Section 3.4 documents that SD-4 labels ballot comments re-litigating decided issues as "out of harmony with the ISO Code of Conduct." SD-4 also states that the ISO Code of Conduct requires participants to "accept group decisions."

The ISO Code of Ethics and Conduct<sup>[18]</sup> says:

> "we accept and respect consensus decisions"

Three differences matter.

First, SD-4 drops the word "consensus." The ISO Code conditions the acceptance obligation on a specific deliberative process — the consensus process defined in Guide 2 — not on whatever the group decides by any method. "Accept group decisions" and "accept and respect consensus decisions" impose different obligations.

Second, the source is misidentified. The phrase "accept group decisions" does not appear in the ISO Code of Ethics and Conduct<sup>[18]</sup>. It appears on a JTC 1 presentation slide. SD-4 attributes a slide's paraphrase to the Code itself.

Third, the pairing is severed. The ISO Code pairs the acceptance obligation with the full framework of participant rights, including escalation. SD-4 pairs acceptance with credibility erosion (Section 3.5) and a 5pm deadline for raising objections (Section 3.5), adding conditions the Code does not impose.

| | ISO Code of Ethics and Conduct<sup>[18]</sup> | SD-4<sup>[1]</sup> |
|---|---|---|
| Acceptance language | "accept and respect **consensus** decisions" | "accept **group** decisions" |
| Source | ISO Code of Ethics and Conduct (PUB100011) | Attributed to "ISO Code of Conduct"; actual source is a JTC 1 slide |
| Paired with | Full participant rights including escalation | Credibility erosion, 5pm objection deadline |

### 3.7 Meeting Record Transparency

SD-4<sup>[1]</sup> states:

> "Meeting records of subgroup discussion, meeting wikis, and non-public committee email lists (aka reflectors)... often include personal positions and discussion. It is not allowed to quote from these publicly."

The Directives require transparency at multiple levels. At the working group level directly, Annex SK Clause SK.4<sup>[15]</sup> states that "The minutes of WG meetings shall be circulated within 4 weeks after the WG meeting," with Table SK.2 reaffirming a +4 weeks deadline for WG minutes including the list of attendees. Directive 1.12.6<sup>[2]</sup> further requires working groups to use the electronic platform provided by the Office of the CEO "for transparency and traceability." At the committee level, Directive 1.8.2(e)<sup>[2]</sup> requires the Chair to "ensure at meetings that all decisions are clearly formulated and made available in written form," and Directive 1.9.2(c)<sup>[2]</sup> requires decisions to be "posted within 48 hours after the meeting" and minutes to be "circulated within 4 weeks." By the functional equivalence established in Section 2.1, these committee-level transparency duties also apply to WG21's de facto working groups (CWG, LWG, EWG, LEWG). The Directives' Foreword lists Transparency as the first of six WTO principles the procedures exist to safeguard<sup>[15]</sup>.

The Directives do not require that working group records be world-readable. They do, however, address meeting records directly. Directive SF.10<sup>[15]</sup> provides a consent-based framework for meeting recordings: recording by the Secretary/Committee Manager is acceptable if participants are informed at the start and no one objects, any participant may require recording be turned off during their intervention, and recordings are to help prepare minutes and may be used to resolve disputes. JTC 1 Standing Document 19 (2022), Section 9 explicitly adopts this framework: "JTC 1 follows the ISO policy on recording technical meetings which are included in the Consolidated ISO Supplement, Annex SF Clause 10"<sup>[24]</sup>. In March 2025, ISO published guidance explicitly permitting the use of AI tools for meeting transcription under SF.10<sup>[16]</sup>.

WG21's opening meeting guidelines state: "Meetings are not public, we want everyone to be able to speak freely. Please refrain from live tweeting, blogging, taking photos or videos"<sup>[17]</sup>. SD-4's blanket prohibition operates outside the SF.10 framework rather than within it. SF.10 provides a consent-based process that balances transparency with participant comfort. WG21's guidelines skip the framework and default to prohibition.

WG21's practice is unusual among comparable bodies. WG21's sibling working groups in SC 22 publish their meeting minutes as public documents: WG14 (C) publishes minutes as N-numbered documents on open-std.org; WG5 (Fortran) publishes minutes on its official site; WG9 (Ada) lists draft minutes in its public Electronic Documents Log. Outside ISO, ECMA TC39 (JavaScript) publishes full meeting transcripts on a public GitHub repository; the IETF publishes working group minutes and recordings on its Datatracker; W3C publishes working group minutes on w3.org. No other JTC 1 working group examined maintains a comparable prohibition on recording or public quotation of meeting discussions. Appendix B documents this comparison. Appendix C documents the recording and transcription practices.

---

## 4. What SD-4 Does Not Mention

SD-4 describes itself as a comprehensive procedural guide: "everyone who participates in WG21 is expected to be familiar with this information." The following Directive provisions address topics within SD-4's scope but do not appear in SD-4.

| Directive Provision | Subject | SD-4 |
|--------------------|---------|----|
| 1.12.1 | Convenor "shall act in a purely international capacity" | |
| 5.1.1 | NB right of appeal to parent committee, TMB, and council board | |
| 5.1.2 | P-member may appeal any action "not in accordance with the ISO/IEC Directives" | |
| 5.3.4 | TMB Chair "shall form a conciliation panel" to hear appeals | |
| 1.13.2 | Advisory groups require committee approval of convenor, membership type, and terms of reference prior to establishment<sup>[15]</sup> | |

The right column is empty because SD-4 is silent on each of these provisions.

The "purely international capacity" requirement (1.12.1) applies directly to the WG21 Convenor, and via the functional equivalence established in Section 2.1, to subgroup chairs who exercise working-group-level authority.

The advisory group requirement (1.13.2) applies to the Direction Group. The 2024 edition of the Directives<sup>[15]</sup> specifies that committee advisory groups require committee approval of the convenor, the type of membership, and the terms of reference - all prior to establishment. The Direction Group has none of these.

The appeal provisions (5.1.1, 5.1.2, 5.3.4) exist regardless of whether SD-4 restates them - NB rights under the Directives do not depend on being echoed in a WG procedural guide. But a guide that is comprehensive about how the process works and silent about what happens when participants believe the process has failed is incomplete in a way that matters. A participant who reads only SD-4 would not learn that these mechanisms exist.

---

## 5. SD-4 in the Document System

SD-1 is the official PL22.16/WG21 document list, maintained continuously since the committee's founding.

The 2009 SD-1<sup>[3]</sup> enumerates the then-current standing documents SD-1, SD-2, and SD-5 as document rows; the 2012 SD-1<sup>[4]</sup> enumerates SD-1, SD-2, SD-3, and SD-5. From 2016 onward, the SD-1 lists<sup>[5]</sup><sup>[6]</sup><sup>[7]</sup><sup>[8]</sup> list only SD-1 itself as an SD row; other standing documents are referenced only when a numbered paper is about them (for example, "P0835 Adopt SD-6 feature macros…", "P1919 Expanding the Rights in SD-8"). SD-4 does not appear as a row in any year examined.

The more telling observation is publication location. WG21's document pipeline hosts pre-publication drafts (D-papers) on isocpp.org and formally published papers (P-papers, N-papers, and published standing documents) on open-std.org. Published standing documents - SD-3, SD-5, SD-7 - appear on open-std.org. SD-4 appears on isocpp.org alongside pre-publication drafts.

---

## 6. Why SD-4?

No other JTC 1 working group maintains a comparable procedural supplement. WG9 (Ada) states that all its standards are "developed in accordance with the JTC1 Directives"<sup>[11]</sup> - no supplement needed. WG14 (C) maintains only meeting-logistics documents<sup>[12]</sup>. WG5 (Fortran) has a strategic plan. Appendix A documents this comparison.

Even MPEG (SC 29/WG 11), the only other JTC 1 working group that grew to comparable scale, never wrote a comprehensive procedural supplement<sup>[9]</sup>. At several hundred attendees per meeting with permanent subgroups, MPEG operated under the Directives framework with only narrow ad hoc group rules. When the organizational model became unsustainable, ISO restructured MPEG into proper SC-level working groups<sup>[10]</sup> rather than having it write its own governance document.

SD-4 exists because WG21 has built a structure the Directives were not designed to govern. A working group of 200+ participants with 23 subgroups, multiple parallel tracks, and mandatory gatekeeping sub-bodies needs procedures the Directives do not provide. SD-4 fills that gap. The deviations documented in Sections 3-5 are a consequence of that gap.

---

## 7. Frequently Cited Misconceptions

The following responses address objections raised in early review of this paper.

### "The Directives don't cover WG internal substructure"

The claim is that ISO only sees WG21 as a single working group with a convener, and that everything inside - subgroup chairs, consensus procedures, scheduling - is the WG's private business that the Directives do not reach.

The Directives are silent on subgroup chair appointment specifically. Directive 1.12.1<sup>[2]</sup> says "Working Groups may establish subgroups" and prescribes nothing further - no appointment procedure, no term limits, no oversight requirements. That silence is real.

But the silence reflects an assumption: that working group subgroups would remain modest internal subdivisions, not permanent standing bodies that process the committee's entire technical workload. Section 2.1 documents what WG21's subgroups have become - mandatory gates for every feature, with chairs who set agendas, run multi-day sessions, and exercise de facto authority over what reaches the working draft. The Directives' organizational categories (working groups at 1.12, advisory groups at 1.13, ad hoc groups at 1.14) do not include bodies of this kind. WG21's subgroups have outgrown the category the Directives placed them in.

The alternative reading - that the Directives intentionally left bodies of this scale and authority unregulated - implies that any working group can create permanent substructures with unlimited power and no oversight, provided it calls them subgroups rather than working groups. That reading makes the governance requirements of 1.12.1 avoidable by nomenclature.

### "Subgroup chairs derive authority from the convener, so the convener can appoint them however they wish"

The convener's authority to create subgroups is not in question - Directive 1.12.1<sup>[2]</sup> authorizes it. The question is whether that authority extends to creating bodies that exercise working-group-level power without working-group-level oversight.

The Directives' appointment requirements for convenors - committee appointment, fixed terms, NB confirmation - exist to ensure accountability and oversight over the people who lead the bodies doing the standardization work. Section 2.1 documents that WG21's subgroup chairs are those people. They set agendas, run sessions, hold polls whose outcomes determine what enters the working draft, and serve with no fixed term and no NB confirmation. The authority to create subgroups does not self-evidently include the authority to staff them outside the governance framework the Directives apply to every comparable role.

### "The Directives govern the convenor; the convenor governs the subgroups — so the chain is complete"

The argument is that Directive governance runs through a chain: National Bodies appoint experts, the committee appoints the convenor, the convenor manages the subgroups. Since the convenor is subject to Directive governance (committee appointment, fixed terms, NB confirmation), subgroup governance is unnecessary because the convenor is the accountability checkpoint.

The chain requires the convenor to actually exercise oversight, and the Directives' enforcement mechanism is periodic reappointment: terms of up to three years, with NB confirmation at each renewal (1.12.1)<sup>[2]</sup>. SD-4 creates no comparable mechanism at the subgroup level. Subgroup chairs serve with "no fixed term"<sup>[1]</sup>, and SD-4 prescribes no periodic review, reappointment process, or NB confirmation for them. The accountability chain exists in principle but the Directives' enforcement mechanism does not operate below the convenor.

The chain also assumes a single individual can provide effective oversight over bodies that collectively process the committee's entire technical workload. Section 2.1 documents 23 subgroups running in multiple parallel tracks simultaneously across a full-week meeting. The MPEG precedent (Appendix A.3) illustrates ISO's own response when a single convenor's oversight capacity proved insufficient for an organization of comparable scale: restructuring the subgroups into proper working groups, not continued reliance on the chain.

### "SD-4 supplements the Directives; it doesn't replace them"

SD-4 describes itself this way. The question is whether this self-description is accurate. On every topic where both documents speak - chair appointment, consensus thresholds, ballot comment scope, escalation, priority allocation - the SD-4 provision is the one followed in practice. A supplement that is followed instead of the document it supplements is a replacement.

### "These deviations are harmless / the system works fine"

This paper takes no position on whether the deviations produce good or bad technical outcomes. Section 2 acknowledges that the current system has produced four consecutive on-time releases and major features. The question is procedural compliance, not technical quality. Directive 1.4<sup>[2]</sup> requires authorization for deviations. Whether the deviations are beneficial is a separate question from whether they are authorized.

### "This paper doesn't have a point"

The comparison had not been made. Both documents are public. The deviations documented in Sections 3-5 are either authorized under Directive 1.4<sup>[2]</sup> or they are not. This paper provides the information needed to ask that question.

---

## 8. Available Processes

The Directives provide two mechanisms.

**Formalization.** Directive 1.4<sup>[2]</sup> provides a path for committees whose practices necessarily differ from the Directives' defaults:

> "Deviations from the procedures set out in the present document shall not be made without the authorization of the Chief Executive Officers of ISO or IEC or the technical management boards for deviations in the respective organizations."

**Objection.** Directive 5.1.2<sup>[2]</sup> provides a path for National Bodies to align the committee's practices with the Directives:

> A P-member of a committee may appeal against any action or inaction "not in accordance with" the Statutes and Rules of Procedure or the ISO/IEC Directives.

A committee that knows when to exercise either mechanism is in control of its own governance.

---

## References

1. Guy Davidson, "SD-4: WG21 Practices and Procedures," ISO/IEC JTC1/SC22/WG21/SD-4, 2026-05-11. [https://isocpp.org/std/standing-documents/sd-4-wg21-practices-and-procedures](https://isocpp.org/std/standing-documents/sd-4-wg21-practices-and-procedures) (This paper was drafted against the pre-2026-05-11 version of SD-4; the cited provisions have been stable across revisions. SD-4 provisions quoted in this paper predate the current convenor and were authored and maintained by Herb Sutter during his tenure as convenor through 2025.)
2. ISO/IEC, "ISO/IEC Directives, Part 1 - Consolidated JTC 1 Supplement," 2024. [https://www.pkn.pl/sites/default/files/sites/default/files/imce/files/ISO-IEC%20Consolidated%20JTC%201%20Supplement%202024.pdf](https://www.pkn.pl/sites/default/files/sites/default/files/imce/files/ISO-IEC%20Consolidated%20JTC%201%20Supplement%202024.pdf) (Hosted by the Polish Committee for Standardization, an ISO national body. The 2023 edition is also available at [jtc1info.org](https://jtc1info.org/wp-content/uploads/2023/11/ISO-IEC-Consolidated-JTC-1-Supplement-2023.pdf); clause references are stable across the 2023 and 2024 editions.)
3. SD-1: 2009 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2009/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2009/sd-1.htm)
4. SD-1: 2012 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2012/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2012/sd-1.htm)
5. SD-1: 2016 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/sd-1.htm)
6. SD-1: 2019 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/sd-1.htm)
7. SD-1: 2023 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/sd-1.htm)
8. SD-1: 2024 PL22.16/WG21 document list. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/sd-1.htm](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/sd-1.htm)
9. Leonardo Chiariglione, "The MPEG Special Forces: Subgroups," 2020. [https://blog.chiariglione.org/the-mpeg-special-forces-subgroups/](https://blog.chiariglione.org/the-mpeg-special-forces-subgroups/)
10. JTC 1, "Future of SC 29 with JPEG and MPEG," 2020. [https://jtc1info.org/future-of-sc-29-with-jpeg-and-mpeg/](https://jtc1info.org/future-of-sc-29-with-jpeg-and-mpeg/)
11. WG9 (Ada) organizational page. [https://open-std.org/JTC1/SC22/WG9/organize.htm](https://open-std.org/JTC1/SC22/WG9/organize.htm)
12. WG14 (C) Standing Document 1: Joint Mailing and Meeting Information, N1829. [https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1829.htm](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1829.htm)
13. ISO/TC 211, "Roles in Committee Work," Good Practices. [https://committee.iso.org/sites/tc211/home/resolutions/isotc-211-good-practices/--roles-in-committee-work.html](https://committee.iso.org/sites/tc211/home/resolutions/isotc-211-good-practices/--roles-in-committee-work.html)
14. Herb Sutter, WG21 trip reports, 2024-2026. [https://herbsutter.com/](https://herbsutter.com/)
15. ISO/IEC, "ISO/IEC Directives, Part 1 - Consolidated ISO Supplement," Edition 2024. [https://www.iso.org/sites/directives/current/consolidated/index.html](https://www.iso.org/sites/directives/current/consolidated/index.html)
16. ISO, "Guidance on use of artificial intelligence (AI) for ISO committees," Version 1.1, March 2025. [https://www.iso.org/files/live/sites/isoorg/files/developing_standards/who_develops_standards/docs/use%20of%20AI.pdf](https://www.iso.org/files/live/sites/isoorg/files/developing_standards/who_develops_standards/docs/use%20of%20AI.pdf)
17. N4916, "WG21 2022-07 Virtual Meeting Minutes of Meeting," Section 1.2 Meeting guidelines. [https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2022/n4916.pdf](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2022/n4916.pdf). See also N4933 (November 2022, Kona), same section.
18. ISO, "ISO Code of Ethics and Conduct," PUB100011, First Edition, 2023. [https://www.iso.org/files/live/sites/isoorg/files/store/en/PUB100011.pdf](https://www.iso.org/files/live/sites/isoorg/files/store/en/PUB100011.pdf)
19. Solomon E. Asch, "Studies of Independence and Conformity: I. A Minority of One Against a Unanimous Majority," *Psychological Monographs: General and Applied*, 70(9), 1956.
20. Melissa Newham and Rune Midjord, "Do Expert Panelists Herd? Evidence from FDA Committees," *DIW Discussion Papers*, No. 1825, 2019.
21. Jörg Matthes, Johannes Knoll, and Christian von Sikorski, "The 'Spiral of Silence' Revisited: A Meta-Analysis on the Relationship Between Perceptions of Opinion Support and Political Opinion Expression," *Communication Research*, 45(1), 2018.
22. Andrea Mattozzi and Marcos Y. Nakaguma, "Public versus Secret Voting in Committees," *Journal of the European Economic Association*, 21(3), 2023. (Documents the 2017 Italian Parliament incident in which a malfunction briefly revealed individual votes during a secret ballot.)
23. Stanley Schachter, "Deviation, Rejection, and Communication," *Journal of Abnormal and Social Psychology*, 46(2), 1951, pp. 190-207.
24. JTC 1, Standing Document 19, "Meetings," 2022, Section 9 "Recording of meetings."

\newpage

## Appendix A: WG21's Subgroup Structure in Context

This appendix provides the evidence summarized in Section 2.1.

### A.1 Working Group Comparison Across JTC 1

The Directives describe working groups as comprising "a restricted number of Experts" that should be "reasonably limited in size." The table below compares WG21 to other JTC 1 working groups.

| Working Group | Parent SC | Typical Attendance | Internal Subgroups | Meeting Format |
|---|---|---|---|---|
| WG14 (C) | SC 22 | ~25 | Informal parallel breakouts during the week; all decisions in single plenary | 2x/year |
| WG5 (Fortran) | SC 22 | ~23 | None; delegates to US national body J3 | 2x/year |
| WG9 (Ada) | SC 22 | Small | 3 rapporteur groups meeting between sessions | 1-day meetings, 2x/year |
| WG4 (COBOL) | SC 22 | Very small | None; delegates to US national body | As needed |
| WG23 (Vulnerabilities) | SC 22 | Small | None | As needed |
| SC 27 WGs (Cybersecurity) | SC 27 | Small per WG | None per WG; structure is at the SC level (5 WGs) | 2x/year |
| SC 7 WGs (Software Eng.) | SC 7 | Small per WG | None per WG; 14 WGs at SC level | 2x/year |
| SC 42 WGs (AI) | SC 42 | Small per WG | None per WG; 5 WGs at SC level | 2x/year |
| **WG21 (C++)** | **SC 22** | **200+** | **23 subgroups, multiple parallel tracks** | **3x/year, full week** |

In every other JTC 1 context examined, when a technical domain requires hundreds of experts and parallel work streams, the work is organized as a subcommittee with multiple focused working groups. WG21 has instead built a subcommittee-scale organization inside what ISO considers a single working group.

### A.2 The Directives' Organizational Taxonomy

The Directives define three types of subsidiary body that a committee or working group may create:

**Working groups (1.12).** Established by a committee for specific tasks. Convenors appointed by the committee for up to three-year terms with NB confirmation. Comprise experts individually appointed by P-members. Operate by consensus. "Reasonably limited in size." Disbanded on task completion.

**Groups having advisory functions within a committee (1.13).** Established by a committee "to assist the Chair and secretariat in tasks concerning coordination, planning and steering of the committee's work." Available to committees (TCs/SCs), not to working groups.

**Ad hoc groups (1.14).** Study a "precisely defined problem" and report to the parent committee. In JTC 1, working groups may create ad hoc groups. Require committee-approved convenors, terms of reference, and a target completion date. Disbanded when the work is complete.

WG21's four main subgroups (CWG, LWG, EWG, LEWG) match none of these types. They are not working groups because they were not established by a committee and their chairs lack the prescribed appointment process. They are not advisory groups because 1.13 is available only to committees. They are not ad hoc groups because they have no terms of reference, no target completion dates, and have operated continuously for decades.

### A.3 The MPEG Precedent

MPEG (SC 29/WG 11) was established in 1988 as a working group of SC 29. It grew from 100 members within 18 months to 200 within two years<sup>[9]</sup>, eventually reaching several hundred participants per meeting with a substantially larger community of registered experts over its 32-year history.

Like WG21, MPEG developed permanent internal subgroups with appointed chairs - Audio, Video, Systems, Test, Requirements, 3D Graphics, and others. Like WG21, MPEG's subgroup chairs set agendas, ran multi-day sessions, and exercised de facto authority over their technical domains.

In 2020, SC 29 formally restructured MPEG<sup>[10]</sup>. Its subgroups were elevated into proper SC 29-level working groups (WG 2 through WG 8) and advisory groups. Leonardo Chiariglione, who had served as MPEG's convenor for 32 years, resigned during this process<sup>[9]</sup>.

The restructuring acknowledged that a single working group had outgrown the ISO organizational model. The solution was to make the organizational chart match the organizational reality - the subgroups became working groups with all the governance requirements that entails. WG21 has not undergone any such restructuring.

### A.4 TC 211's Self-Assessment

ISO/TC 211 (Geographic Information) published internal documentation that addresses this structural question directly<sup>[13]</sup>:

> "According to ISO directives and how most of the support IT-system is built, ISO expects a working group to work on one Standard. Within ISO/TC 211, we have working groups that have more than one project within the same area of expertise. Our working groups have then more the function of what in ISO Directives is described as subcommittees."

TC 211 considers having multiple projects per working group unusual enough to explain. WG21's four main subgroups collectively process hundreds of proposals across the entire C++ language and standard library.

### A.5 WG21 by the Numbers

Attendance at recent WG21 plenary meetings<sup>[14]</sup>:

| Meeting | Date | Attendees | Nations |
|---|---|---|---|
| St. Louis | July 2024 | 180+ | 20+ |
| Wroclaw | November 2024 | 220+ | 31 |
| Kona | November 2025 | ~200 | 21 |
| London/Croydon | March 2026 | ~210 | 24 |

WG21's internal structure:

- 4 permanent main subgroups: CWG, LWG, EWG, LEWG
- 13+ Study Groups (SG1, SG4, SG6, SG7, SG9, SG10, SG14, SG15, SG16, SG19, SG20, SG22, SG23, and others)
- 3 advisory/administrative groups: AG (Admin), DG (Direction), ARG (ABI Review)
- Multiple parallel tracks running simultaneously at plenary meetings
- Full-week meetings (5-6 days), 3 times per year

### A.6 Procedural Supplements Across JTC 1

No other JTC 1 working group maintains a procedural supplement comparable to SD-4.

| Body | Standing Documents | Procedural Scope | Comparable to SD-4? |
|---|---|---|---|
| WG9 (Ada) | "Developed in accordance with the JTC1 Directives"<sup>[11]</sup> | None - follows Directives directly | No |
| WG14 (C) | SD-1: meeting logistics<sup>[12]</sup>; SD-2: study group organization | Logistics only | No |
| WG5 (Fortran) | SD-4: strategic plan | Strategic/organizational | No |
| SC 27 (Cybersecurity) | Programme-of-work SDs | No procedural governance | No |
| SC 29/MPEG | 15 narrow ad hoc group rules | One organizational unit type | No |
| **WG21 (C++)** | **SD-4: 47KB procedural supplement** | **Consensus interpretation, escalation, ballot comments, subgroup structure, direction group, TS lifecycle** | **Unique** |

SD-4 interprets the ISO consensus definition, creates escalation deadlines, pre-categorizes NB ballot comments, names a Direction Group roster, defines subgroup chair appointment procedures, and prescribes the entire proposal lifecycle. No other WG or SC standing document in JTC 1 attempts any of this.

\newpage

## Appendix B: Meeting Record Transparency Across Standards Bodies

This appendix provides the evidence summarized in Section 3.7. For each body, it documents what meeting records are publicly available, where they are published, and whether any prohibition on public quotation exists.

### B.1 JTC 1 / SC 22 Working Groups

- **WG14 (C):** Meeting minutes published as N-numbered documents in the WG14 document log on open-std.org. Publicly accessible. No prohibition on quoting found. [https://www.open-std.org/jtc1/sc22/wg14/www/wg14_document_log.htm](https://www.open-std.org/jtc1/sc22/wg14/www/wg14_document_log.htm)

- **WG5 (Fortran):** Meeting minutes published on the official WG5 site under documents. Publicly accessible. [https://wg5-fortran.org/documents.html](https://wg5-fortran.org/documents.html)

- **WG9 (Ada):** Draft and final minutes listed in the WG9 Electronic Documents Log on open-std.org. Publicly accessible. [https://open-std.org/JTC1/SC22/WG9/documents.htm](https://open-std.org/JTC1/SC22/WG9/documents.htm)

- **WG21 (C++):** Formal Minutes of Meeting papers (N-series) are public on open-std.org. Subgroup discussion, meeting wikis, and non-public reflectors are sealed. SD-4 states: "It is not allowed to quote from these publicly" except straw poll questions/results or attributed quotes with prior consent.

### B.2 Other JTC 1 Bodies

- **SC 29/MPEG:** Public meeting reports and outcome summaries published on mpeg.org. No SD-4-style quoting prohibition found in public-facing documents. [https://www.mpeg.org/](https://www.mpeg.org/)

### B.3 Non-ISO Standards Bodies

- **ECMA TC39 (JavaScript/ECMAScript):** Full verbatim meeting transcripts published on a public GitHub repository. Publicly quotable. [https://github.com/tc39/notes](https://github.com/tc39/notes)

- **W3C:** Working group minutes published on w3.org as dated HTML documents. Publicly quotable. Minutes are the durable public record of decisions and actions.

- **WHATWG (HTML):** Meeting discussions documented in public GitHub issues and joint session minutes published via W3C. Publicly quotable. [https://github.com/whatwg/html](https://github.com/whatwg/html)

- **IETF:** Working group and plenary minutes published on Datatracker. Recordings and materials also commonly linked. The IETF Note Well governs IPR and contribution licensing, not confidentiality of meeting content. [https://datatracker.ietf.org](https://datatracker.ietf.org)

- **Rust Leadership Council:** Meeting minutes published in a public GitHub repository. Explicit private carve-outs for moderation and conflicts; default is transparency. [https://github.com/rust-lang/leadership-council/tree/main/minutes](https://github.com/rust-lang/leadership-council/tree/main/minutes)

- **Python Steering Council:** High-level activity updates published on public GitHub. PEP discussions conducted on public forums. [https://github.com/python/steering-council](https://github.com/python/steering-council)

### B.4 Summary

Every body examined defaults to making meeting records a public artifact. WG21 is the only body that combines public formal minutes with a prohibition on quoting subgroup discussions. WG21's three sibling working groups in SC 22 - the C, Fortran, and Ada committees - all publish their minutes without restriction.

\newpage

## Appendix C: Meeting Recording and Transcription Practices

This appendix provides the evidence for the recording and transcription comparison in Section 3.7.

### C.1 The ISO Framework

Directive SF.10<sup>[15]</sup> provides a consent-based framework for meeting recordings:

- Recording by the Secretary/Committee Manager is acceptable if all participants are informed at the start and no one objects
- Any participant may require recording be turned off during their intervention
- Recordings are to help prepare minutes/reports and may be used to resolve disputes
- Recordings are property of the Secretary, must respect confidentiality, must not be shared with third parties, and should preferably be destroyed once minutes are approved

In March 2025, ISO published guidance explicitly permitting the use of AI tools (including generative AI) for meeting transcription under SF.10<sup>[16]</sup>. The guidance states that Committee Managers/Secretaries may use AI tools to record a meeting for the purpose of writing meeting minutes.

### C.2 WG21's Practice

WG21 meeting guidelines (N4916<sup>[17]</sup>, N4933) state: "Meetings are not public, we want everyone to be able to speak freely. Please refrain from live tweeting, blogging, taking photos or videos."

This is stricter than SF.10. The Directive provides a framework that balances transparency with participant comfort (consent, per-intervention opt-out, secretary custody, destruction after approval). WG21 skips the framework and defaults to prohibition.

### C.3 Recording Practices Across Standards Bodies

- **IETF:** Meetings routinely recorded via Meetecho. Recordings published on YouTube and Datatracker. Community AI-assisted minutes projects operate on top of official transcripts (e.g. ietfminutes.org). [https://www.ietf.org/meeting/technology/](https://www.ietf.org/meeting/technology/)

- **W3C:** Recording optional per working group if consent process is followed. W3C Process (2021+) requires that recording intent be announced at the start, required details given (access, purpose, retention), and no participant withholds consent. If anyone objects, recording must not occur. Some groups use automated transcripts as a minutes aid.

- **ECMA TC39:** Primary artifact is human-written collaborative notes (not A/V recording). Notes are drafted in Google Docs during the meeting, reviewed for accuracy, then published to the public tc39/notes GitHub repository. [https://github.com/tc39/notes](https://github.com/tc39/notes)

- **Rust (lang team):** Default is no recording for triage and design meetings "to encourage engagement." Certain design meetings may be recorded with agreement of all participants, decided when scheduled. A YouTube playlist exists with some past recorded meetings and auto-generated subtitles. [https://lang-team.rust-lang.org/meetings.html](https://lang-team.rust-lang.org/meetings.html)

- **Python Steering Council:** Regular internal meetings are not published as full A/V. High-level written updates published on public GitHub. PyCon panels with the Steering Council are recorded and published on YouTube. [https://github.com/python/steering-council](https://github.com/python/steering-council)

### C.4 Summary

The ISO Directives provide a consent-based framework (SF.10) that allows recording with safeguards. ISO's own 2025 AI guidance explicitly permits AI transcription under this framework. The IETF records routinely and publishes recordings. W3C provides an opt-in recording process with participant consent. WG21 prohibits recording outright, going beyond what the Directives restrict.

ISO's direction of travel is toward AI-assisted documentation. WG21's practice moves in the opposite direction.
