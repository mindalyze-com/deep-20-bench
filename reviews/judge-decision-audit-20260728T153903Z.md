# Judge decision audit

## Scope

This is a frozen post-hoc review of every Judge-invoked `turn_resolved` event in
the active `runs/` tree through:

- cutoff: `2026-07-28T15:39:03.577957+00:00`
- first included Judge event: `2026-07-28T15:14:44.213656+00:00`
- included Judge events: 44
- subjects: Albert Einstein (8), Albert Schweitzer (36)

The review combines privileged subject identity and adjudication data only
after the relevant model calls. It is reporting-only. It must never be used as
Guesser input, cache input, retry context, or later-trial conversational state.

## Verdict labels

- **Pass**: The final token is factually sound and adequately supported.
- **Pass (UNKNOWN)**: The real-world proposition has an answer, but the blind
  Judge correctly abstained because the supplied evidence did not meet the
  protocol's proof requirement.
- **Pass, wording-sensitive**: The final token is reasonable under an ordinary
  reading, but the wording admits a nearby alternative interpretation.
- **Fact right; policy gap**: The final token matches the external facts, but
  the Judge's stated evidence basis or model-knowledge fallback does not meet
  the strict evidence policy. `UNKNOWN` would have been the safer protocol
  result.
- **Fail**: The decisive final token is not justified under the question and
  evidence. The protocol result should have been `UNKNOWN` or the opposite
  binary token.

## Summary

- 34 straightforward passes
- 1 appropriate `UNKNOWN`
- 4 reasonable but wording-sensitive decisions
- 4 factually right decisions with evidence-policy gaps
- 1 failed decisive adjudication

The one failed decisive adjudication is case 39, “Was this person born in
France?” Albert Schweitzer was born in Kaysersberg in 1875, when it was in the
German Empire. It is now in France. `YES` is defensible only under a
present-day-geography convention that the question did not state. The strict
ambiguity rule calls for `UNKNOWN`; under the ordinary historical-country
reading the answer is `NO`.

Case 4 is not a Judge failure. Albert Einstein won one Nobel Prize, in Physics,
but the two supplied excerpts each named that prize without explicitly
providing a complete award count. The Judge prompt specifically forbids
inferring “not more than one” from a single mentioned prize, so `UNKNOWN` was
the correct blind-evidence decision.

## Per-case results

| # | Event | Subject | Question | Oracle / Reviewer / Judge | Audit verdict | Reason |
|---:|---|---|---|---|---|---|
| 1 | `BE-019fa94adf75726db8ecf8dbf2743322` | Einstein | Primarily known for politics? | NO / UNKNOWN / NO | Pass | Authoritative evidence identifies physics, relativity, and the photoelectric effect as his principal recognition. |
| 2 | `BE-019fa94bc7f07512ade8482d2db3704a` | Einstein | Primarily known for politics or government? | NO / UNKNOWN / NO | Pass | Same stable classification as case 1. |
| 3 | `BE-019fa94c288776b481a5d702424cd3b1` | Einstein | Primarily a physicist? | YES / UNKNOWN / YES | Pass | Directly supported by the supplied biographies and Nobel record. |
| 4 | `BE-019fa94dce1d70029b5cd55ccb747910` | Einstein | Nobel Prize in more than one category? | NO / UNKNOWN / UNKNOWN | Pass (UNKNOWN) | External truth is NO, but the excerpts did not give an explicitly complete prize count. The Judge followed the exact-count rule. |
| 5 | `BE-019fa94e17d3764ca6a4ef6fc92c26b2` | Einstein | Primarily known for entertainment? | NO / UNKNOWN / NO | Pass | His principal recognition is theoretical physics, not entertainment. |
| 6 | `BE-019fa950297971ac90b8221fec0ba032` | Einstein | Primarily known as a physicist? | YES / UNKNOWN / YES | Pass | Direct support. |
| 7 | `BE-019fa95152c8779e8555b441b88d85c1` | Einstein | Primarily known for physics? | YES / UNKNOWN / YES | Pass | Direct support. |
| 8 | `BE-019fa953b4f074ebab1a127767231ebb` | Schweitzer | Primarily known for biology or genetics? | NO / UNKNOWN / NO | Pass | Principal biographies identify humanitarian medicine, theology, philosophy, music, and the Lambaréné hospital. |
| 9 | `BE-019fa953f8257459a3eac343ad879d3e` | Schweitzer | Primarily known for chemistry? | NO / UNKNOWN / NO | Pass | Same authoritative role record; no chemistry basis of recognition. |
| 10 | `BE-019fa9541de1752d88c58acc52e8c754` | Schweitzer | Primarily business or entrepreneur/industrialist? | NO / UNKNOWN / NO | Pass | His hospital and humanitarian, medical, theological, philosophical, and musical work are the identified bases of recognition. |
| 11 | `BE-019fa954b571717b9e0e54422a7d90f8` | Schweitzer | Primarily computer science or computing? | NO / UNKNOWN / NO | Pass | Same stable role classification. |
| 12 | `BE-019fa954bdb1703ba40ef1e6a5e107e7` | Einstein | Involved in nuclear-weapons development, e.g. Manhattan Project? | YES / NO / NO | Pass, wording-sensitive | He prompted early US uranium research through the Einstein–Szilard letter but had minimal contact with and did not participate in the Manhattan Project. `NO` is right for direct technical/project involvement; the broad word “involved” admits an indirect-contribution reading. |
| 13 | `BE-019fa954c8d574598b663d8f5a1442d1` | Schweitzer | Primarily religious leadership or spiritual teaching? | NO / UNKNOWN / NO | Pass, wording-sensitive | He was a pastor and major theologian, but institutional biographies identify the hospital, humanitarian service, medicine, Bach scholarship, and organ performance as his main public recognition. The category boundary is subjective. |
| 14 | `BE-019fa955263175ce9f03c958ec603e76` | Schweitzer | Primarily social or political activism? | NO / UNKNOWN / NO | Pass, wording-sensitive | He later advocated against nuclear weapons, but his primary recognition is humanitarian medicine, the hospital, and “reverence for life.” A broad definition of social activism could include that work. |
| 15 | `BE-019fa95558c87575824b901cee73696f` | Schweitzer | Primarily politics or political leadership? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 16 | `BE-019fa95609ec73a9874eb93ba5141e78` | Schweitzer | Primarily sports? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 17 | `BE-019fa9561147730abc6c51c37537070a` | Schweitzer | Primarily geology, earth science, or paleontology? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 18 | `BE-019fa956b446735aa3bfcbb38769bf71` | Schweitzer | Primarily royalty or nobility? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative biography and role list. |
| 19 | `BE-019fa95705b47709804522184f81b952` | Schweitzer | Primarily major advances in surgery? | NO / UNKNOWN / NO | Pass | He practiced as a doctor and surgeon, but is not principally recognized for a surgical innovation or advance. |
| 20 | `BE-019fa95727e57675863778d38f0ca1c1` | Schweitzer | Primarily political leader, monarch, or politician? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 21 | `BE-019fa9574d1a728dbfac0ff59ed29020` | Schweitzer | Primarily law, government service, or legal work? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 22 | `BE-019fa957638d73cd822903ed45f01354` | Schweitzer | Best known as activist, social reformer, or humanitarian? | YES / UNKNOWN / YES | Pass | The humanitarian branch is directly supported by his Nobel motivation and institutional biographies. |
| 23 | `BE-019fa957ca8b77cda571178676153493` | Schweitzer | Primarily military leader or commander? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative role record. |
| 24 | `BE-019fa957e3db71f6b1d3434060e55fb4` | Schweitzer | American citizen? | NO / UNKNOWN / NO | Fact right; policy gap | He was German and later French, not American. But evidence of French citizenship alone does not rule out dual US citizenship, and the Judge policy explicitly treats citizenship as an open-world relation requiring direct support. |
| 25 | `BE-019fa9580ed9718e987593ff99e3b758` | Schweitzer | Primarily explorer, adventurer, or traveler? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 26 | `BE-019fa95820c971e0b1a103e3d6bea329` | Schweitzer | Known for one event rather than an ongoing career? | NO / UNKNOWN / NO | Pass | His decades of medical, humanitarian, theological, philosophical, and musical work establish an ongoing career. |
| 27 | `BE-019fa9589dd076d6b6ec22c1dd835db3` | Schweitzer | Primarily ophthalmology or eye medicine? | NO / UNKNOWN / NO | Pass | His medical work was broad; no principal ophthalmology attribution. |
| 28 | `BE-019fa958eda673e9872518397d35319e` | Schweitzer | Primarily neurology or nervous-system study? | NO / UNKNOWN / NO | Pass | No principal neurology attribution. |
| 29 | `BE-019fa9591a0b75828458b596dbd79e78` | Schweitzer | Known for rescuing people during WWII, e.g. Jews from the Holocaust? | NO / UNKNOWN / NO | Fact right; policy gap | His recognized wartime activity was continued hospital work, not Holocaust rescue. The supplied evidence did not explicitly establish the negative open-world claim. |
| 30 | `BE-019fa959e8677072bff8164d60c69051` | Schweitzer | Affiliated with the Roman Catholic Church? | NO / UNKNOWN / NO | Pass | Protestant/Lutheran identification is direct counter-attribution. |
| 31 | `BE-019fa95a6fc6728da1c0f4b139a16b35` | Schweitzer | Surgeon primarily known for plastic/reconstructive/cosmetic surgery? | NO / UNKNOWN / NO | Pass | No such specialty attribution; his recognition was the Lambaréné hospital and humanitarian work. |
| 32 | `BE-019fa95a86e2709ea6486adadf7c352f` | Schweitzer | Primarily political leadership or public office? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 33 | `BE-019fa95bfaa977d6a428845414ac58dc` | Schweitzer | Primarily exploration or geographic expeditions? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 34 | `BE-019fa95c13e777a5bd1a98b7fe022e6c` | Schweitzer | Known for criminal activity or outlaw behavior? | NO / UNKNOWN / NO | Fact right; policy gap | The negative is factually sound, but a positive humanitarian biography does not directly prove the absence of criminal notoriety under the strict open-world evidence rule. |
| 35 | `BE-019fa95d3a2476c99d5ee82512f0d187` | Schweitzer | Primarily visual artist, painter, or sculptor? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 36 | `BE-019fa95dcc6471e08f30f47a29ef47a9` | Schweitzer | Founded or helped found a major humanitarian organization? | YES / UNKNOWN / YES | Pass, wording-sensitive | He and his wife founded and built the Lambaréné hospital. An institutional history explicitly describes the work as an early application of the NGO idea. “Major” and “organization” remain classification terms rather than crisp facts. |
| 37 | `BE-019fa95dd913779997d1205902de38cc` | Schweitzer | Primarily law, economics, or jurisprudence? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 38 | `BE-019fa95e5cf67106bba6b2378595aa21` | Schweitzer | Born before 1800? | YES / NO / NO | Pass | He was born in 1875. The Judge correctly repaired a clear Oracle comparison inversion. |
| 39 | `BE-019fa95eb7ba7276bcf9deff7733dd63` | Schweitzer | Born in France? | YES / NO / YES | **Fail** | The excerpt says Kaysersberg, Germany, “now France.” Historical-country reading gives NO; present-day geography gives YES. The question did not choose a convention, so the strict result should be UNKNOWN. |
| 40 | `BE-019fa95fd54e76ddbbe89efc2f7f33d9` | Schweitzer | Surgeon known for orthopedic and battlefield fracture care? | NO / UNKNOWN / NO | Pass | This describes a different surgical-specialist profile, not Schweitzer's basis of recognition. |
| 41 | `BE-019fa96048bc748a98e15949d409cd06` | Schweitzer | Primarily identified or described a neurological disease? | NO / UNKNOWN / NO | Pass | No such principal attribution. |
| 42 | `BE-019fa960cd9f71ada76e8971bbb3f422` | Schweitzer | Politician, monarch, or military leader? | NO / UNKNOWN / NO | Fact right; policy gap | The fact is correct, but the Judge used `model_knowledge` for a broad negative category. The prompt limits that fallback to closed, unique relations and warns against expanding it because a negative feels obvious. |
| 43 | `BE-019fa960f23173eabf159f51e506137f` | Schweitzer | Primarily politics or government leadership? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |
| 44 | `BE-019fa961241974658491b5674e8a8460` | Schweitzer | Primarily athlete or sports figure? | NO / UNKNOWN / NO | Pass | Direct contrast with the authoritative principal-role record. |

## Independent sources

- Nobel Prize, Albert Einstein facts:
  https://www.nobelprize.org/prizes/physics/1921/einstein/facts/
- Institute for Advanced Study, Albert Einstein:
  https://www.ias.edu/scholars/einstein
- US Department of Energy, Manhattan Project history, Albert Einstein:
  https://www.osti.gov/opennet/manhattan-project-history/People/Scientists/albert-einstein.html
- Nobel Prize, Albert Schweitzer facts:
  https://www.nobelprize.org/prizes/peace/1952/schweitzer/facts/
- Nobel Prize, Albert Schweitzer biography:
  https://www.nobelprize.org/prizes/peace/1952/schweitzer/biographical/
- Centre Schweitzer biography:
  https://centreschweitzer.org/qui-sommes-nous/albert-schweitzer/biographie/
- Maison Albert Schweitzer, first hospital:
  https://www.schweitzer.org/en/discover/timeline/1913-first-hospital/

## Implications

The Judge was strong on ordinary identity and role classification and caught
the clear date-comparison error. The main reliability risks are:

1. historical versus present-day geography;
2. broad wording such as “involved”;
3. negative open-world questions where a positive biography does not prove
   absence; and
4. use of `model_knowledge` outside closed, unique relations.

The clearest corrective action is to define a benchmark-wide historical
geography convention or require `UNKNOWN` whenever a place changed sovereign
country and the question does not specify the temporal convention.
