# TraceKE Missing Persons Identification Support System

> *Tupatane. Let's find each other.*

---
## Live Demo : https://traceke.streamlit.app/

## App Snippet
<img width="1249" height="595" alt="image" src="https://github.com/user-attachments/assets/2f87097e-d382-49aa-8d52-1f35e2116817" />

## The problem we are trying to solve

In 2024, 170 women were killed in Kenya one woman every other day. It was the deadliest year on record for Kenyan women, double the annual average recorded from 2016 to 2023.

They were found in rivers. In lodges. In thickets. On roadsides. 75 percent of them were killed by someone they knew a husband, a boyfriend, a family member. Nairobi recorded the highest number of cases, followed by Nakuru and Kiambu. And these are only the cases that made it into media reports. The real number is almost certainly higher.

The women have names. Starlet Wahu. Mercy Kwamboka. Rebecca Cheptegei, an Olympic athlete, set on fire by her ex-partner in September 2024. Agnes Tirop. Damaris Mutua. Each one a daughter, a sister, a mother. Each one reduced by the system to a case number, if she was lucky enough to get one at all.

Children are disappearing too. Over 8,800 children were reported missing in Kenya in 2024 alone and that is just the documented cases. Roughly 17 to 18 children are reported missing every single day. In the 2023–2024 fiscal year, over 7,000 children vanished nationwide, and only 1,383 were ever reunited with their families. The rest are still out there somewhere. Or they are not.

There is no single national database that tracks every missing child. Many disappearances go unreported or are logged too late. A child reported missing in Eldoret and found confused and alone in a Nairobi hospital may never be connected to the family that is looking for them not because nobody cares, but because no shared system exists to make that connection.

This is the gap TraceKE tries to close.

---

## What TraceKE does

TraceKE is a web-based identification support system with two entry points and one matching engine.

**Reporters** families, police officers, neighbours, social workers register a missing person with photos, physical description, and case details. The system generates a facial profile from those photos and stores it alongside the case.

**Institutions** hospitals, mortuaries, children's homes, police stations, NGOs upload a photo of an unidentified person they have encountered. The system searches the database for similar facial profiles and returns the closest matches, ranked by a multi-signal confidence score.

When a potential match is found above the confidence threshold, it is logged in an auditable match record and surfaced to a human reviewer. The reviewer not the algorithm decides whether to contact the family.

### Features

**Reporters Portal**
- Register a missing persons case with name, age, sex, height, last seen location, clothing description, and distinguishing features
- Upload up to 5 photos per case multiple angles and lighting conditions produce a more robust facial profile
- Automatic age progression display if someone has been missing for years, the system shows their estimated current age so reviewers think in present terms, not past ones
- Unique case ID generated per registration, shareable with police or NGOs

**Institution Portal**
- Upload a photo of an unidentified person found at a hospital, mortuary, shelter, or police station
- System searches all registered missing persons and returns up to 3 closest potential matches
- Every match shows a full confidence breakdown face similarity, estimated age match, gender so reviewers understand *why* the system flagged this as a potential match
- Location is shown as context, never used to lower a score a person found 400km from where they went missing may have been trafficked, and the system accounts for that explicitly with a trafficking flag rather than penalising the distance

**Tip Submission**
- Anyone can submit a tip no account, no registration required
- A boda boda rider, a neighbour, a shopkeeper anyone who spots someone can upload a photo and a location
- Tips are checked against active cases and flagged for human review before any family is ever contacted

**Dashboard**
- All active cases sorted by urgency children missing in the last 72 hours surface first, not buried under older cases
- Case status tracking: Open, Under Review, Resolved, Closed
- Summary statistics open cases, resolved cases, matches flagged, tips received

**Match Log**
- Every potential match the system flags is permanently recorded with timestamp, confidence scores, and case IDs
- Full audit trail institutions and NGOs can review every match decision, including who reviewed it and what outcome followed

### How the matching works

TraceKE does not rely on face similarity alone. Every match is scored across multiple signals:

| Signal | Role |
|---|---|
| Face similarity (Facenet) | Primary 55% of final score |
| Estimated age match | Supporting 25% |
| Gender | Supporting 20% |
| Location distance | **Context only** never penalises distance |
| Distinguishing features | **Human review only** shown side by side, never scored |

If a signal is missing the institution did not record the found person's height, or the family did not know the distinguishing marks that signal is excluded from the calculation entirely. The remaining signals redistribute their weights proportionally. No case is penalised for incomplete data.

---

## What TraceKE does NOT do

TraceKE is an identification **support** system, not an identification **decision** system. This distinction matters enormously.

**It does not confirm identity.** Every result is labelled a *potential match requiring human verification*. The system never tells a family "we found your child." It tells a trained reviewer "this case is worth a second look."

**It does not monitor or surveil.** There are no cameras, no live feeds, no real-time scanning. The system only processes photos that are deliberately uploaded by registered institutions or family members.

**It does not replace the police, NGOs, or community networks.** It is one additional tool. The human work of investigation, community mobilisation, and family support cannot be automated.

---

## Technical stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Face detection | YuNet via OpenCV better dark skin tone performance than Haar Cascade |
| Face embeddings | facenet-pytorch / InceptionResnetV1 512-dimension vectors, no TensorFlow dependency |
| Vector similarity search | ChromaDB (cosine similarity) |
| Case metadata storage | SQLite |
| Image preprocessing | OpenCV + CLAHE normalisation for skin-tone neutral quality assessment |

---

## Running locally

```bash
git clone https://github.com/your-username/traceke
cd traceke

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

streamlit run main.py
```

On first run, the app will:
1. Download the YuNet face detection model (~200KB) automatically
2. Download the Facenet model weights via facenet-pytorch (~90MB, one time only)
3. Seed the database with 15 realistic demo cases so the app is immediately usable

First startup takes approximately 30-60 seconds. Subsequent startups are fast.

---

## Limitations we are honest about

**1. The face recognition model was not trained on Kenyan data.**
Facenet was trained predominantly on Western datasets. Detection and embedding accuracy on dark-skinned East African faces especially in the low-light, low-resolution conditions common in real intake scenarios has not been independently benchmarked for this context. This is the single most important limitation of the current system.

**2. Photo quality affects accuracy.**
A blurry, poorly lit, or very low-resolution photo will produce a less reliable facial embedding. TraceKE accepts all photos regardless of quality and flags low-quality images to reviewers, but accuracy will be lower for these cases. We made the deliberate decision never to reject a photo for quality because for some families, one blurry photo taken years ago is all they have.

**3. There is no identity verification on case registration.**
Anyone can register a missing person case. In the current prototype, there is no OTP verification or identity check on the reporters portal. This is a known gap that introduces a risk of abuse.

**4. The system requires institutional adoption to be useful.**
TraceKE only connects missing persons to found persons if hospitals, mortuaries, and police stations are actively uploading. Without uptake from institutions that encounter unidentified people, the matching engine has nothing to search against. Technology alone does not solve this.

**5. Demo data uses synthetic embeddings.**
The 15 pre-loaded demo cases use random mathematical vectors, not real facial embeddings. Real matching only works with real photos uploaded through the portals.

---

## What we want to build next

**A model fine-tuned on African faces.**
The most impactful improvement would be retraining or fine-tuning the embedding model on a dataset that reflects the faces it will actually encounter East African, diverse lighting, diverse image quality. This requires a labelled dataset, compute resources, and ethical data collection with full consent.

**Africa's Talking SMS alerts.**
When a high-confidence match is found, the system should automatically notify the registered contact via SMS using Africa's Talking Kenya's own communications infrastructure. One confirmed match, one SMS, one family reunited. The architecture already supports this.

**OTP verification on case registration.**
A simple Kenya phone number plus OTP check before a case is saved would significantly reduce the risk of abuse, add accountability, and create a direct communication channel back to the reporter when a match is found.

**Multilingual support.**
Kenya has over 40 languages. A tool built for Kenyan families should work in Kiswahili at minimum. The Streamlit interface can be adapted the challenge is ensuring that voice descriptions of distinguishing features, which are the most culturally specific data point, are captured accurately across languages.

**Integration with DCI, CPIMS, and NGO databases.**
The most powerful version of TraceKE is not a standalone system it is a shared layer connecting the Directorate of Criminal Investigations, Kenya's Child Protection Information Management System, Missing Child Kenya, COVAW, and the other organisations already doing this work manually. The technical architecture is designed with this integration in mind.

---

## A note on ethics

TraceKE handles some of the most sensitive data that exists photographs of missing and vulnerable people, biometric facial data, the details of disappearances that in many cases involve violence, trafficking, or abuse.

We take this seriously.

- No photo is ever shared between parties without a human reviewer in the loop
- No family is ever contacted directly by the system only by a human who has reviewed the match
- All match decisions are logged permanently for accountability
- The system's limitations are documented explicitly so no one over-trusts it
- Demo data uses fictional cases and synthetic embeddings no real vulnerable person's data was used in development

This is a prototype built by one developer. It is not production-ready. It should not be deployed in a real institutional context without independent security review, bias testing on a representative Kenyan dataset, legal review under the Kenya Data Protection Act 2019, and formal partnership with organisations that have the expertise, the mandate, and the trust of the communities this tool is meant to serve.

But the problem is real. The gap is real. And someone has to start.

---

## Built by

**Kerubo Bosire** ML Engineer & Data Scientist, Nairobi, Kenya.

*Actuarial brain. Data science hands. Built for the people who look like me, who live where I live, who are still waiting.*

---

*If you are working on missing persons technology in Kenya or East Africa and want to collaborate, please reach out.*
