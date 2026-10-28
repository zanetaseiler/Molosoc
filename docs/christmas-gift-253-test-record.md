# Christmas gift landing: image import and checkout test record (Issue #253)

Follow-up to Issue #251 / PR #252. Page stays draft, noindex and sitemap-excluded. Nothing was published, deployed or checked out live. No evergreen landing A/B file and no regular product pricing was touched; this change is documentation only.

## 1. Image import: NOT DONE (access blocked)

The cloud session cannot reach Google Drive (egress proxy returns 403 for `drive.google.com`), so none of the three files was downloaded, size-checked or committed. No image was invented or substituted. The ~10 KB size seen in Drive metadata is therefore still unverified and likely means Drive returned thumbnails, not the full originals.

Minimal owner step:

1. From Drive folder `1T2Cs9oeyLrDucPkMS8tfYjD_DvSzj2T7`, use Download (not preview) for Scene_01 (`1JHezsiFVICxddNfOX1_7AQfe1Nq36u9k`), Scene_02 (`12WhUf4aciD21JAoG1_X1cC1-mY8Sto0M`), Scene_03 (`18RlEVxkbHFW0hH7LRUlLBitualjBxsvm`). Confirm each is megabytes in size, not ~10 KB.
2. Commit them to `site/theme/assets/images/landing-xmas/source/` on a branch (or attach to a GitHub comment) and re-fire this task; web renditions (`.webp`, ~1600 px) will then be generated.

## 2. Image slots (mobile/desktop, CZ/EN): NOT TESTED

Blocked on step 1. Offline `tests/test_landing_xmas_251.py` confirms the template renders nothing for missing files and registers all three Drive IDs; no browser rendering was performed.

## 3. Bundle checkout on staging: NOT TESTED

No staging URL or credentials are available to this session, and a live checkout was not performed. Offline checks only (`python -m unittest tests.test_landing_xmas_251 tests.test_thank_you_gift tests.test_landing_b_buy_209`: 126 tests, OK) cover by static analysis of the code: 209/199/199 schedule (209/408/607), price taken from the `molosoc_xmas_slot` tag, repack and base-price restore, add-to-cart rollback on failure, gift add-on (`molosoc_gift_slot`) rows skipped, size validation, one sold-out size not disabling the picker.

| Case | Status |
| --- | --- |
| 1/2/3 pairs = 209/408/607 CZK in real cart | not tested live (code-level test only) |
| Size M/L combinations | not tested live |
| Cart removal / repricing | not tested live (repack covered in code test) |
| Stock failure rollback | not tested live (rollback covered in code test) |
| Quantity changes | not tested |
| Regular 229 CZK elsewhere | not tested live (code test only) |
| Gift add-on isolation | not tested live (code test only) |

Needs from owner: a staging URL plus a test-order approval (ZANETA_DECISION) or a test user, or run the matrix above manually and paste results.
