---
title: About MABIMS.dev
description: Free open-source API for the Indonesian Hijri calendar based on official MABIMS data from Kementerian Agama RI.
---

## What is MABIMS.dev?

MABIMS.dev is a free open-source API that provides an ecosystem for the Indonesian Hijri calendar. It uses official MABIMS data published by Indonesia's [Ministry of Religious Affairs (Kementerian Agama RI)](https://kemenag.go.id), not [Umm al-Qura](https://en.wikipedia.org/wiki/Umm_al-Qura_calendar) (Saudi Arabia's standard).

## Who is it for?

- **Developers** building web or mobile apps with Hijri calendar features
- **Mosque and pesantren apps** that need to display fasting start, Eid al-Fitr, and Eid al-Adha dates matching Kemenag announcements
- **Islamic schools and universities** integrating Hijri dates into academic systems
- **Anyone** who needs accurate Indonesian Hijri dates

## Why MABIMS, Not Umm al-Qura?

Almost all Hijri calendar APIs and libraries default to [Umm al-Qura](https://en.wikipedia.org/wiki/Umm_al-Qura_calendar). Umm al-Qura is Saudi Arabia's official calendar, designed for their needs — not Indonesia's.

Because the rukyah method and observation location differ, results can be ±1 day off from Kemenag's official decisions — especially for Ramadan start, Eid al-Fitr, and Eid al-Adha. MABIMS.dev uses public Kemenag RI table data and [Neo MABIMS criteria](https://mui.or.id/baca/berita/mengenal-kriteria-hilal-mabims-standard-penentuan-awal-bulan-hijriyah-pemerintah-indonesia) (moon altitude ≥ 3°, elongation ≥ 6.4° at local sunset, evaluated at coastal observation points across Indonesia) for dates beyond table coverage.

## Compared to Alternatives

For the Indonesian context, MABIMS.dev is more accurate than [Umm al-Qura](https://en.wikipedia.org/wiki/Umm_al-Qura_calendar) (Saudi standard, ±1 day off) and [Aladhan API](https://aladhan.com) (which also defaults to Umm al-Qura). MABIMS.dev uses official Kemenag RI data, not data from another country's authority.

If you're currently using the Aladhan API, see the [Migration from Aladhan](/en/migration) guide for response format comparison and migration code examples.

## Repository

Source code is available at [github.com/PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api). Contributions are welcome via pull request.

## License

MABIMS.dev is licensed under the [MIT License](https://github.com/PijarAdiluhung/mabims-api/blob/main/LICENSE).

## Contact

For questions, technical support, or commercial partnerships:
- Email: [halo@pixostudio.id](mailto:halo@pixostudio.id)
- GitHub: [PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api)
