# Remaining short-form candidates: primary metadata audit

Checked 2026-11-02 against public YouTube pages. All eight primary player video IDs match the requested lead. Every player reports `OK`, `isShortsEligible=true`, a 25–91-second duration, and portrait video-format dimensions. This is useful platform metadata, not byte-based inspection, full viewing, claim extraction, or rights clearance. No media was downloaded.

The initial broad page-duration scan was only diagnostic: pages can contain recommended videos. This audit uses the matching primary player only. The solar-charger oEmbed request returned 401, but its publicly accessible primary page returned matching metadata and playability OK; no login or access bypass was attempted.

| Lead | Verified creator | Seconds | Published | Next gate |
| --- | --- | ---: | --- | --- |
| [health_aging](https://www.youtube.com/shorts/cEweWu4HcHw) | Matt Randon | 40 | 2021-04-17 | Rights + full review + local media checks |
| [policy_tariff_india](https://www.youtube.com/shorts/AxfbYNwmCiA) | ForumIAS Official | 91 | 2025-04-03 | Rights + full review + local media checks |
| [policy_ivf](https://www.youtube.com/shorts/_eovRWq6cpA) | Right Side Broadcasting Network | 55 | 2024-08-29 | Rights + full review + local media checks |
| [policy_tax](https://www.youtube.com/shorts/O5kzZzQwiAI) | Right Side Broadcasting Network | 29 | 2024-08-19 | Rights + full review + local media checks |
| [energy_heatpump](https://www.youtube.com/shorts/54XeLtz_a00) | HVAC Guide for Homeowners | 25 | 2024-11-28 | Rights + full review + local media checks |
| [energy_solar](https://www.youtube.com/shorts/fWAotkyBunE) | JMG Limited | 35 | 2025-07-15 | Rights + full review + local media checks |
| [tech_battery](https://www.youtube.com/shorts/bQ4RAGeFeXk) | HTX Studio | 79 | 2025-06-07 | Rights + full review + local media checks |
| [tech_solar_charger](https://www.youtube.com/shorts/RFV76Fisyhc) | Gosolar Balafoutis | 65 | 2025-04-29 | Rights + full review + local media checks |

The updated candidate manifest is `data/shortform_candidates.metadata_verified.jsonl`. The original acquisition manifest and collection hash binding remain unchanged. Raw compact metadata is in `data/shortform_primary_metadata_20261102.json`. Reproduce into a fresh output file with:

```bash
python3 scripts/audit_shortform_leads.py --out data/new-primary-metadata.json
```

## Selection consequences

- Both RSBN clips share a creator and must remain in the same split. Campaign promises are not enacted benefits; select precise factual claims only after watching, with an explicit temporal interpretation.
- The heat-pump title concerns efficiency; a bill-savings claim cannot be inferred solely from the secondary article. The actual spoken/visual claim still needs inspection.
- The solar-charger title is Greek. Spoken language remains unverified; decide whether it fits the language scope after viewing.
- These videos were published in 2021–2025. They are newly sourced leads, not newly published news. Date-bound claims need evidence appropriate to the clip and chosen as-of date.
- Keep misleading charts as a separate discovery need: no clip in this queue has been verified as containing one.

## Current counts and next action

12 candidate links; four permitted local MP4s with technical checks; eight additional YouTube leads now verified at the primary-metadata level; **zero fully admitted benchmark clips**. The eight YouTube leads still have download and redistribution permission set to false. Ask each rights holder for a permitted source file and explicit license covering public dataset redistribution, frames/transcripts and model evaluation, or replace the lead with an appropriately licensed source. No outreach or publication has been performed.

The user is reviewing the first three clips and six claims using the independent review page. After reference adjudication, finish rights/media verification and add diverse claims before freezing a new evaluation. Do not count candidates as completed dataset examples.
