# Research, data quality and model evaluation

## Research questions
1. Which licensed English ASR model performs best on Cambodian English and telecom speech?
2. Which English→Khmer MT model provides adequate meaning, register, and terminology?
3. Can approved human corrections improve domain-specific scores without regression?
4. Which Khmer ASR and Khmer→English MT options justify V2 deployment under offline constraints?

## Candidate selection
Evaluate Whisper-like multilingual ASR, fine-tunable ASR alternatives and Khmer-specific ASR; compare multilingual/translation-specific MT choices. Record exact checkpoint, revision, license, compute cost, language coverage, dependencies and offline packaging feasibility before adoption.

## Dataset policy
- Collect recordings only with documented rights, consent, allowed purpose and retention policy.
- Keep speaker/session-disjoint train/validation/test partitions; hash audio and detect duplicates.
- Tag language, accent, background noise, device and domain where permitted; avoid unnecessary personal data.
- Reviewers edit **source transcript** and **target translation** independently.
- Enforce approval state and provenance; revoked items must be excluded from future training snapshots.
- Keep a private, immutable held-out evaluation set. Never tune on it.
- Do not assume public Khmer datasets are licensed or suitable; inspect each dataset individually.

## Evaluation metrics

| Stage | Automated | Human / operational |
| --- | --- | --- |
| ASR | WER, CER, deletion/insertion/substitution rates | named-entity recall, accent/noise slices |
| MT | chrF, BLEU and optionally semantic metrics | adequacy, fluency, terminological correctness, harmful mistranslation |
| End to end | task success and aggregate error | usefulness and reviewer correction time |
| Operations | p50/p95 latency, throughput, GPU/CPU memory, failure rate | offline install, recovery and rollback |

Khmer word tokenization and Unicode normalization policies must be fixed across baselines. Confidence scores from different models are not automatically calibrated.

## Experiment protocol
1. Freeze and checksum reference data and benchmark scripts.
2. Run baseline ASR and MT separately, then end-to-end.
3. Create reviewed training snapshots; fine-tune isolated candidate models.
4. Compare identical test slices and compute uncertainty intervals where practical.
5. Publish regressions and trade-offs, not only mean accuracy.
6. Require human reviewer approval and a rollback mechanism before model promotion.

## Research deliverables
Versioned data dictionary, annotation guide, benchmark report, model card, evaluation artifacts, compute/cost report, safety and privacy audit, and repeatable offline deployment verification.
